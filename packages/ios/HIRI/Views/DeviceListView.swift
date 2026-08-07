import SwiftUI

struct DeviceListView: View {
    @EnvironmentObject var service: HIRIService

    var body: some View {
        Group {
            if service.isLoading && service.devices.isEmpty {
                ProgressView("Loading devices…")
            } else if let error = service.errorMessage, service.devices.isEmpty {
                VStack(spacing: 12) {
                    Image(systemName: "wifi.exclamationmark")
                        .font(.largeTitle)
                        .foregroundStyle(.orange)
                    Text(error)
                        .font(.callout)
                        .foregroundStyle(.secondary)
                    Button("Retry") { service.fetchDevices() }
                        .buttonStyle(.borderedProminent)
                }
            } else if service.devices.isEmpty {
                ContentUnavailableView(
                    "No Devices",
                    systemImage: "house",
                    description: Text("Pull to refresh or check bridge connection.")
                )
            } else {
                List(service.devices) { device in
                    DeviceRowView(device: device)
                }
                .refreshable { service.fetchDevices() }
            }
        }
        .onAppear { service.fetchDevices() }
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                if service.isLoading {
                    ProgressView()
                }
            }
        }
    }
}
