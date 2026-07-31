# Matter Protocol Bridge — Research & Direction

## Overview

**Matter** (formerly Project CHIP — Connected Home over IP) is an open-source, royalty-free smart home connectivity standard developed by the **Connectivity Standards Alliance (CSA)**, backed by Apple, Google, Amazon, Samsung, and over 500 member companies.

Matter operates over **IP-based transports** (Thread, Wi-Fi, Ethernet) and provides a unified application layer that enables cross-platform device interoperability without cloud dependencies.

---

## Why Matter for HIRI

| Criterion | HIRI Goal | Matter Fit |
|:----------|:----------|:-----------|
| Local-first | MQTT + REST bridge | IP-native, local operation via Thread/Wi-Fi |
| Multi-vendor | HA + cross-ecosystem | Certified multi-admin across Alexa, Google, Apple |
| Open source | MIT-licensed bridge | Open SDK (Apache 2.0) |
| Extensible | Adapter pattern | Device type library (>30 types) |
| Secure | Auth + TLS | DAC certificates, PASE/CASE session establishment |

---

## Protocol Architecture

```
┌─────────────────────────────────┐
│         Application Layer       │
│  (Device Types: Light, Lock,    │
│   Thermostat, Sensor, ...)      │
├─────────────────────────────────┤
│         Data Model Layer        │
│  (Clusters, Attributes, Commands│
│   Endpoints, Events)            │
├─────────────────────────────────┤
│     Interaction Model Layer     │
│  (Read, Write, Invoke, Subscribe│
│   Timed Request)                │
├─────────────────────────────────┤
│         Security Layer          │
│  (PASE, CASE, Group Key, DAC)   │
├─────────────────────────────────┤
│      Message Framing & Routing  │
│  (Exchange Manager, Reliable/   │
│   Unreliable Messaging)         │
├─────────────────────────────────┤
│     Transport Layer (TCP/UDP)   │
│  (Thread / Wi-Fi / Ethernet)    │
└─────────────────────────────────┘
```

---

## Key Concepts

### Nodes & Endpoints
- Each Matter device is a **Node** with a unique 64-bit Node ID
- Nodes contain **Endpoints** (0 = root, 1+ = device type endpoints)
- Each endpoint exposes **Clusters** (server/client)

### Clusters
- Standardized groupings of **Attributes** (state), **Commands** (actions), and **Events**
- Examples: `OnOff` (0x0006), `LevelControl` (0x0008), `TemperatureMeasurement` (0x0402)

### Commissioning
1. **Device Discovery**: BLE or DNS-SD (mDNS) advertising
2. **PASE**: Passcode-Authenticated Session Establishment (setup code)
3. **Network Provisioning**: Thread or Wi-Fi credentials
4. **CASE**: Certificate-Authenticated Session Establishment (operational)

### Multi-Admin
- A single Matter device can be shared across multiple ecosystems (Apple Home, Google Home, Alexa) simultaneously via **Access Control Cluster** and **Fabric** management.

---

## Integration Strategy for HIRI

### Phase 1: Research & Documentation (this PR)
- [x] Research Matter protocol fundamentals
- [x] Document architecture, commissioning flow, device types
- [x] Define HIRI-Matter mapping table
- [x] Scaffold adapter package with fixture devices

### Phase 2: SDK Integration (future)
- Integrate [connectedhomeip](https://github.com/project-chip/connectedhomeip) Python controller
- Implement commissioning via BLE/mDNS discovery
- Read/Write/Subscribe to Matter clusters

### Phase 3: HIRI Bridge Integration (future)
- Auto-discovery of Matter fabrics
- HA MQTT auto-discovery from Matter device types
- Multi-admin fabric management

---

## Device Type Mapping

| Matter Device Type | Cluster(s) | HA Domain | HIRI Fixture |
|:-------------------|:-----------|:----------|:-------------|
| On/Off Light (0x0100) | OnOff (0x0006), LevelControl (0x0008) | `light` | `light.matter_bulb_01` |
| Dimmable Light (0x0101) | OnOff, LevelControl, ColorControl (0x0300) | `light` | `light.matter_rgb_01` |
| Color Temperature Light (0x010C) | OnOff, LevelControl, ColorControl | `light` | `light.matter_ct_01` |
| On/Off Plug (0x010A) | OnOff | `switch` | `switch.matter_plug_01` |
| Door Lock (0x000A) | DoorLock (0x0101) | `lock` | `lock.matter_frontdoor` |
| Thermostat (0x0301) | Thermostat (0x0201), TemperatureMeasurement (0x0402) | `climate` | `climate.matter_thermo` |
| Temperature Sensor (0x0302) | TemperatureMeasurement (0x0402) | `sensor` | `sensor.matter_temp_01` |
| Humidity Sensor (0x0307) | RelativeHumidityMeasurement (0x0405) | `sensor` | `sensor.matter_hum_01` |
| Contact Sensor (0x0015) | BooleanState (0x0045) | `binary_sensor` | `binary_sensor.matter_door` |
| Window Covering (0x0202) | WindowCovering (0x0102) | `cover` | `cover.matter_blind` |
| Fan (0x002B) | FanControl (0x0202) | `fan` | `fan.matter_ceiling` |
| Occupancy Sensor (0x0107) | OccupancySensing (0x0406) | `binary_sensor` | `binary_sensor.matter_occ` |
| Air Quality Sensor (0x002C) | AirQuality (0x005B) | `sensor` | `sensor.matter_aqi_01` |

---

## Matter Fabric & Security

### Distributed Compliance Ledger (DCL)
- Blockchain-based public registry of Matter-certified products
- Stores Vendor ID, Product ID, Device Attestation Certificate (DAC)
- Accessible at: https://dcl.csa-iot.org

### Certificate Chain
```
PAA (Product Attestation Authority) → PAI (Product Attestation Intermediate) → DAC (Device Attestation Certificate)
```

### Operational Credentials
- Each Matter Fabric issues a unique **NOC (Node Operational Certificate)**
- Enables multi-admin: same device, different credentials per ecosystem

---

## HIRI Matter Adapter Design

### Architecture
```
┌──────────────────────────────────┐
│         hiri-bridge CLI          │
│   hiri-bridge matter list        │
│   hiri-bridge matter commission  │
├──────────────────────────────────┤
│   MatterAdapter (adapter stub)   │
│   - list_remote() → Device[]     │
│   - push_state() → void          │
│   - fixture_data → list[dict]    │
│   - cluster_map → dict           │
├──────────────────────────────────┤
│   Matter SDK (future)            │
│   connectedhomeip Python ctrl    │
│   mDNS/BLE discovery             │
└──────────────────────────────────┘
```

### Fixture Data (offline)
The stub ships with 8 representative Matter fixtures covering key device types: bulb, plug, door lock, thermostat, temperature sensor, contact sensor, window covering, and occupancy sensor.

### Cluster Mapping
Pre-defined mapping from Matter cluster IDs to HA domains for auto-discovery when SDK integration is added.

---

## References

- [CSA Matter Specification](https://csa-iot.org/developer-resource/specifications-download-request/)
- [Matter GitHub (connectedhomeip)](https://github.com/project-chip/connectedhomeip)
- [Matter Device Library](https://github.com/project-chip/connectedhomeip/tree/master/examples)
- [Distributed Compliance Ledger](https://dcl.csa-iot.org)
- [Home Assistant Matter Integration](https://www.home-assistant.io/integrations/matter/)
- [Thread Group](https://www.threadgroup.org/)

---

## Status

- **Phase 1 (this PR)**: ✅ Research doc + adapter scaffold + fixtures + tests
- **Phase 2 (SDK integration)**: ⏳ Planned — requires `connectedhomeip` Python controller
- **Phase 3 (full bridge)**: ⏳ Planned — commissioning, multi-admin, HA auto-discovery
