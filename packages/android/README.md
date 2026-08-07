# HIRI Android

Jetpack Compose client for the HIRI smart-home bridge.

## Features

- Browse devices by domain with domain-specific icons
- Real-time device online/offline status
- Light control: power toggle + brightness slider
- Dark/light Material 3 theme

## Architecture

```
app/src/main/java/com/hiri/app/
├── MainActivity.kt          # NavHost entry point
├── data/Device.kt           # Device data class (mirrors bridge API)
├── network/ApiService.kt    # Retrofit HTTP client for HIRI bridge
└── ui/
    ├── theme/Theme.kt       # Material 3 color scheme
    └── screens/
        ├── DeviceListScreen.kt   # Device list with domain icons
        └── LightControlScreen.kt # Power toggle + brightness slider
```

## Build

Requires JDK 17 and Android SDK 35.

```bash
cd packages/android
./gradlew assembleDebug
```

## Configuration

The app connects to `http://10.0.2.2:8780` (emulator → host bridge).
Override by editing `ApiService.kt` or setting a build config field.

## API Endpoints Used

| Endpoint | Method | Purpose |
|---|---|---|
| `/devices` | GET | List all devices |
| `/devices/{id}/command` | POST | Send command (turn_on, turn_off, brightness) |

## CI

GitHub Actions builds and lints on every PR touching `packages/android/`.
