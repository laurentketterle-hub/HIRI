# Impl #16 — ESP Farmware + Bridge + HA Discovery (End-to-End)

## Overview

End-to-end pipeline connecting ESP-based farmware sensors through a bridge layer to Home Assistant (HA) via MQTT auto-discovery.

## Architecture

```
ESP Farmware (sensors)
    │  MQTT (sensor data)
    ▼
Bridge (translation layer)
    │  MQTT (auto-discovery payload)
    ▼
Home Assistant (auto-discovery)
```

## Components

### 1. ESP Farmware
- Reads agricultural sensor data (temperature, humidity, soil moisture, etc.)
- Publishes raw telemetry over MQTT to a configured topic

### 2. Bridge
- Subscribes to ESP MQTT topics
- Translates raw sensor payloads into Home Assistant auto-discovery format
- Publishes discovery messages on `homeassistant/sensor/.../config`

### 3. Home Assistant Discovery
- Consumes MQTT discovery messages
- Auto-registers sensors and entities
- Displays data on HA dashboards

## MQTT Topics

| Component   | Topic Pattern                          | Direction      |
|-------------|---------------------------------------|----------------|
| ESP Sensor  | `farmware/esp/<device_id>/telemetry`  | ESP → Bridge   |
| Discovery   | `homeassistant/sensor/<id>/config`    | Bridge → HA    |
| State       | `homeassistant/sensor/<id>/state`     | Bridge → HA    |

## CI/CD

See `.github/workflows/ci-16.yml` for the automated pipeline that validates:
- Code quality (lint)
- Unit tests
- MQTT discovery payload schema
- End-to-end flow simulation

## Getting Started

```bash
# Clone the repo
git clone https://github.com/mergeos-bounties/HIRI.git
cd HIRI

# Install dependencies
npm install

# Run tests
npm test

# Validate discovery payloads
python3 -m json.tool config/discovery.json
```

## References

- [Home Assistant MQTT Discovery](https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery)
- [ESP MQTT Client](https://github.com/knolleary/pubsubclient)

---

*Issue: mergeos-bounties/HIRI#16*
*Bounty: 200 MRG*
