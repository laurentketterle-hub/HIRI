import Foundation
import Combine

class HIRIService: ObservableObject {
    @Published var devices: [HIRIDevice] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    var apiBase: String {
        UserDefaults.standard.string(forKey: "hiri_api_base") ?? "http://127.0.0.1:8780"
    }

    private var session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 10
        return URLSession(configuration: config)
    }()

    func fetchDevices() {
        isLoading = true
        errorMessage = nil
        guard let url = URL(string: "\(apiBase)/devices") else {
            errorMessage = "Invalid API URL"
            isLoading = false
            return
        }
        session.dataTask(with: url) { [weak self] data, _, error in
            DispatchQueue.main.async {
                self?.isLoading = false
                if let error = error {
                    self?.errorMessage = error.localizedDescription
                    return
                }
                guard let data = data else {
                    self?.errorMessage = "No data received"
                    return
                }
                do {
                    let devices = try JSONDecoder().decode([HIRIDevice].self, from: data)
                    self?.devices = devices
                } catch {
                    self?.errorMessage = "Decode error: \(error.localizedDescription)"
                }
            }
        }.resume()
    }

    func sendCommand(deviceId: String, action: String, completion: @escaping (Bool) -> Void) {
        guard let url = URL(string: "\(apiBase)/devices/\(deviceId)/command") else {
            completion(false)
            return
        }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = ["action": action]
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)

        session.dataTask(with: req) { data, _, error in
            DispatchQueue.main.async {
                if error != nil { completion(false); return }
                guard let data = data,
                      let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
                    completion(false); return
                }
                if let state = json["state"] as? [String: Any],
                   let val = state["state"] as? String ?? state["power"] as? String {
                    if (action == "turn_on" && val.lowercased() == "on") ||
                       (action == "turn_off" && val.lowercased() == "off") {
                        completion(true)
                        return
                    }
                }
                completion(true)
            }
        }.resume()
    }
}
