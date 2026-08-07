import SwiftUI

/// Root content view — delegating to the full device list.
struct ContentView: View {
    @EnvironmentObject var service: HIRIService

    var body: some View {
        DeviceListView()
    }
}
