import Foundation

struct HIRIDevice: Codable, Identifiable, Equatable {
    let id: String
    let name: String
    let domain: String
    let manufacturer: String?
    let model: String?
    let area: String?
    let online: Bool?
    let state: [String: DeviceValue]?
    let adapter: String?
    var status: String?

    enum CodingKeys: String, CodingKey {
        case id, name, domain, manufacturer, model, area, online, state, adapter, status
    }

    var isOn: Bool {
        if let s = state {
            if let val = s["state"], case .string(let v) = val {
                return v.lowercased() == "on"
            }
            if let val = s["power"], case .string(let v) = val {
                return v.lowercased() == "on"
            }
        }
        return false
    }

    var icon: String {
        switch domain {
        case "light": return "lightbulb.fill"
        case "switch": return "switch.2"
        case "sensor": return "sensor.fill"
        case "climate": return "thermometer"
        case "fan": return "fanblades.fill"
        case "lock": return "lock.fill"
        case "cover": return "blinds.horizontal.closed"
        default: return "house.fill"
        }
    }

    static func == (lhs: HIRIDevice, rhs: HIRIDevice) -> Bool {
        lhs.id == rhs.id
    }
}

enum DeviceValue: Codable {
    case string(String)
    case int(Int)
    case double(Double)
    case bool(Bool)
    case null

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let v = try? container.decode(String.self) { self = .string(v) }
        else if let v = try? container.decode(Int.self) { self = .int(v) }
        else if let v = try? container.decode(Double.self) { self = .double(v) }
        else if let v = try? container.decode(Bool.self) { self = .bool(v) }
        else { self = .null }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let v): try container.encode(v)
        case .int(let v): try container.encode(v)
        case .double(let v): try container.encode(v)
        case .bool(let v): try container.encode(v)
        case .null: try container.encodeNil()
        }
    }
}
