import SwiftUI

@main
struct HIRIApp: App {
    @StateObject private var service = HIRIService()

    var body: some Scene {
        WindowGroup {
            NavigationStack {
                DeviceListView()
                    .navigationTitle("HIRI Devices")
            }
            .environmentObject(service)
        }
    }
}
