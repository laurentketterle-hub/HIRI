# iOS SwiftUI Device List + Switch Control

iOS client (`packages/ios`) for the HIRI bridge REST API.

## Architecture

```
packages/ios/HIRI/
├── HIRIApp.swift          # @main entry point
├── ContentView.swift       # Root view
├── Models/
│   └── Device.swift        # HIRIDevice + DeviceValue enum
├── Services/
│   └── HIRIService.swift   # API client (Combine + URLSession)
└── Views/
    ├── DeviceListView.swift # Pull-to-refresh list
    └── DeviceRowView.swift  # Row with toggle switch
```

## Endpoints Used

| Endpoint | Method | Purpose |
|---|---|---|
| `/devices` | GET | List all devices |
| `/devices/{id}/command` | POST | Send `turn_on` / `turn_off` |

## API Base URL

Configured via `UserDefaults` key `hiri_api_base`; defaults to
`http://127.0.0.1:8780` (localhost bridge).

## Usage

1. Open `packages/ios` in Xcode.
2. Target iOS 16+ simulator or device.
3. Ensure HIRI bridge is running.
4. The app fetches devices on launch; pull-to-refresh reloads.
5. Toggle switches for `light`, `switch`, `fan` domains; other domains
   show online/offline status.

## Domain Icons

| Domain | SF Symbol |
|---|---|
| light | `lightbulb.fill` |
| switch | `switch.2` |
| sensor | `sensor.fill` |
| climate | `thermometer` |
| fan | `fanblades.fill` |
| lock | `lock.fill` |
| cover | `blinds.horizontal.closed` |
| default | `house.fill` |

## Bounty

Issue: [#15](https://github.com/mergeos-bounties/HIRI/issues/15)
