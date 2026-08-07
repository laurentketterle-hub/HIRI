import SwiftUI

struct DeviceRowView: View {
    let device: HIRIDevice
    @EnvironmentObject var service: HIRIService

    @State private var isToggling = false

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: device.icon)
                .font(.title2)
                .foregroundStyle(device.isOn ? .yellow : .gray)
                .frame(width: 32)

            VStack(alignment: .leading, spacing: 4) {
                Text(device.name)
                    .font(.headline)
                HStack(spacing: 8) {
                    Text(device.domain.capitalized)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    if let area = device.area, !area.isEmpty {
                        Text("· \(area)")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }

            Spacer()

            if device.domain == "switch" || device.domain == "light" || device.domain == "fan" {
                Toggle("", isOn: .constant(device.isOn))
                    .disabled(isToggling)
                    .onTapGesture {
                        isToggling = true
                        let action = device.isOn ? "turn_off" : "turn_on"
                        service.sendCommand(deviceId: device.id, action: action) { _ in
                            isToggling = false
                            service.fetchDevices()
                        }
                    }
            } else {
                Image(systemName: device.online == true ? "antenna.radiowaves.left.and.right" : "wifi.slash")
                    .foregroundStyle(device.online == true ? .green : .red)
                    .font(.caption)
            }
        }
        .padding(.vertical, 4)
    }
}
