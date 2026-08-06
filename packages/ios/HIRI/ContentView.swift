import Foundation
import Combine

// MARK: - Data models

struct HiriDevice: Codable, Identifiable, Equatable {
    let id: String
    let name: String
    let domain: String
    let area: String?
    let state: [String: HiriStateValue]?
    let adapter: String?
    let online: Bool?

    // Mapping to URL-serializable format
    func toDict() -> [String: Any] {
        var d: [String: Any] = [
            "id": id, "name": name, "domain": domain,
            "area": area ?? "", "adapter": adapter ?? "local", "online": online ?? true,
        ]
        if let state = state {
            d["state"] = state.mapValues { $0.value }
        }
        return d
    }
}

/// Codable wrapper for mixed-type state values
enum HiriStateValue: Codable, Equatable {
    case string(String)
    case number(Double)
    case bool(Bool)

    var value: Any {
        switch self {
        case .string(let s): return s
        case .number(let n): return n
        case .bool(let b): return b
        }
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let s = try? container.decode(String.self) { self = .string(s) }
        else if let b = try? container.decode(Bool.self) { self = .bool(b) }
        else { self = .number(try container.decode(Double.self)) }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let s): try container.encode(s)
        case .number(let n): try container.encode(n)
        case .bool(let b): try container.encode(b)
        }
    }
}

struct HiriStats: Codable {
    let total: Int
    let online: Int?
}

// MARK: - API client

class HiriBridgeClient: ObservableObject {
    /// Configurable base URL (defaults to localhost for simulator)
    static var apiBase: String = HIRIConfig.apiBase

    @Published var devices: [HiriDevice] = []
    @Published var stats: HiriStats = HiriStats(total: 0, online: 0)
    @Published var isOffline: Bool = false
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?

    // Offline cache
    private var cachedDevices: [HiriDevice] = []
    private let cacheKey = "hiri_device_cache"

    init() {
        loadCache()
    }

    // MARK: - Offline cache

    private func loadCache() {
        guard let data = UserDefaults.standard.data(forKey: cacheKey),
              let decoded = try? JSONDecoder().decode([HiriDevice].self, from: data)
        else { return }
        cachedDevices = decoded
    }

    private func saveCache() {
        guard let data = try? JSONEncoder().encode(devices) else { return }
        UserDefaults.standard.set(data, forKey: cacheKey)
    }

    // MARK: - API calls

    func fetchAll() async {
        await MainActor.run { isLoading = true; errorMessage = nil }
        do {
            async let healthResult = checkHealth()
            async let devicesResult = fetchDevices()
            async let statsResult = fetchStats()

            let (healthy, freshDevices, freshStats) = try await (healthResult, devicesResult, statsResult)

            await MainActor.run {
                self.isOffline = !healthy
                self.devices = freshDevices
                self.stats = freshStats
                self.isLoading = false
                self.saveCache()
            }
        } catch {
            await MainActor.run {
                self.isOffline = true
                self.devices = cachedDevices
                self.isLoading = false
                if cachedDevices.isEmpty {
                    self.errorMessage = "Bridge offline — start hiri-bridge serve"
                }
            }
        }
    }

    private func checkHealth() async throws -> Bool {
        let url = URL(string: "\(Self.apiBase)/health")!
        let (_, response) = try await URLSession.shared.data(from: url)
        return (response as? HTTPURLResponse)?.statusCode == 200
    }

    private func fetchDevices(domain: String? = nil, area: String? = nil) async throws -> [HiriDevice] {
        var components = URLComponents(string: "\(Self.apiBase)/devices")!
        var items: [URLQueryItem] = []
        if let domain = domain { items.append(URLQueryItem(name: "domain", value: domain)) }
        if let area = area { items.append(URLQueryItem(name: "area", value: area)) }
        if !items.isEmpty { components.queryItems = items }
        let (data, _) = try await URLSession.shared.data(from: components.url!)
        return try JSONDecoder().decode([HiriDevice].self, from: data)
    }

    private func fetchStats() async throws -> HiriStats {
        let url = URL(string: "\(Self.apiBase)/stats")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(HiriStats.self, from: data)
    }

    func sendCommand(deviceId: String, action: String, data: [String: Any] = [:]) async -> Bool {
        let encoded = deviceId.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? deviceId
        let url = URL(string: "\(Self.apiBase)/devices/\(encoded)/command")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        var body: [String: Any] = ["action": action]
        data.forEach { body[$0] = $1 }
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        do {
            let (_, response) = try await URLSession.shared.data(for: request)
            return (response as? HTTPURLResponse)?.statusCode == 200
        } catch {
            return false
        }
    }

    func turnOn(_ deviceId: String, extra: [String: Any] = [:]) async {
        _ = await sendCommand(deviceId: deviceId, action: "turn_on", data: extra)
        await fetchAll()
    }

    func turnOff(_ deviceId: String) async {
        _ = await sendCommand(deviceId: deviceId, action: "turn_off")
        await fetchAll()
    }

    // MARK: - Grouping helpers

    func devicesByRoom() -> [String: [HiriDevice]] {
        Dictionary(grouping: devices) { $0.area?.isEmpty == false ? $0.area! : "home" }
    }

    func devicesByDomain() -> [String: [HiriDevice]] {
        Dictionary(grouping: devices) { $0.domain }
    }

    func roomNames() -> [String] {
        devicesByRoom().keys.sorted()
    }
}

/// HIRI configuration — bridge API base URL
struct HIRIConfig {
    /// Default: localhost for iOS simulator (same machine as bridge)
    static let apiBase = "http://127.0.0.1:8780"
}
