import SwiftUI

struct HIRIDevice: Codable, Identifiable {
    let id: String
    var name: String
    var type: String
    var state: String
    var battery: Int?
}

class DeviceListVM: ObservableObject {
    @Published var devices: [HIRIDevice] = []
    @Published var error: String?
    private var token: String = ""
    
    func fetchDevices(baseURL: String = "http://hiri.local:8080") {
        guard let url = URL(string: "\(baseURL)/api/devices") else { return }
        var req = URLRequest(url: url)
        if !token.isEmpty { req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization") }
        URLSession.shared.dataTask(with: req) { data, _, err in
            DispatchQueue.main.async {
                if let data = data, let devs = try? JSONDecoder().decode([HIRIDevice].self, from: data) {
                    self.devices = devs
                } else { self.error = err?.localizedDescription ?? "Fetch failed" }
            }
        }.resume()
    }
    
    func toggleDevice(_ device: HIRIDevice, baseURL: String = "http://hiri.local:8080") {
        guard let url = URL(string: "\(baseURL)/api/devices/\(device.id)/toggle") else { return }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        if !token.isEmpty { req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization") }
        URLSession.shared.dataTask(with: req).resume()
        fetchDevices(baseURL: baseURL)
    }
}

struct ContentView: View {
    @StateObject private var vm = DeviceListVM()
    @State private var showSettings = false
    
    var body: some View {
        NavigationStack {
            List(vm.devices) { device in
                HStack {
                    VStack(alignment: .leading) {
                        Text(device.name).font(.headline)
                        Text("\(device.type) · \(device.state)").font(.caption).foregroundColor(.secondary)
                    }
                    Spacer()
                    if device.type == "light" || device.type == "switch" {
                        Toggle("", isOn: Binding(get: { device.state == "on" },
                            set: { _ in vm.toggleDevice(device) }))
                    }
                }
            }
            .navigationTitle("HIRI Devices")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) { Button { showSettings = true } label: { Image(systemName: "gear") } }
            }
            .refreshable { vm.fetchDevices() }
            .onAppear { vm.fetchDevices() }
            .sheet(isPresented: $showSettings) { SettingsView(token: $vm.token) }
        }
    }
}

struct SettingsView: View {
    @Binding var token: String
    @State private var input: String = ""
    
    var body: some View {
        NavigationStack {
            Form {
                SecureField("Admin token", text: $input)
                Button("Save") { token = input }
            }
            .navigationTitle("Settings")
        }
    }
}
