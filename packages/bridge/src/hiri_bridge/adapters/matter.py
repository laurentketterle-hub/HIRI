"""Matter bridge adapter — protocol research, cluster mapping, fixture devices.

Matter (CSA Connectivity Standard) is an IP-based smart home protocol
with native multi-admin across Apple, Google, Amazon ecosystems.

This stub provides:
- Offline fixture devices for testing without Matter hardware
- Cluster-to-HA-domain mapping table
- Scaffold for future SDK integration (connectedhomeip)
"""

from __future__ import annotations

from hiri_bridge.devices.types import Device

# Matter cluster ID → HA domain mapping
MATTER_CLUSTER_MAP: dict[int, str] = {
    0x0006: "light",       # OnOff
    0x0008: "light",       # LevelControl
    0x0300: "light",       # ColorControl
    0x0101: "lock",        # DoorLock
    0x0201: "climate",     # Thermostat
    0x0402: "sensor",      # TemperatureMeasurement
    0x0405: "sensor",      # RelativeHumidityMeasurement
    0x0045: "binary_sensor",  # BooleanState
    0x0102: "cover",       # WindowCovering
    0x0202: "fan",         # FanControl
    0x0406: "binary_sensor",  # OccupancySensing
    0x005B: "sensor",      # AirQuality
    0x000D: "switch",      # OnOff Plug
}

# Matter device type → HIRI domain mapping
MATTER_DEVICE_TYPE_MAP: dict[int, dict] = {
    0x0100: {"domain": "light", "label": "On/Off Light"},
    0x0101: {"domain": "light", "label": "Dimmable Light"},
    0x010C: {"domain": "light", "label": "Color Temperature Light"},
    0x010A: {"domain": "switch", "label": "On/Off Plug"},
    0x000A: {"domain": "lock", "label": "Door Lock"},
    0x0301: {"domain": "climate", "label": "Thermostat"},
    0x0302: {"domain": "sensor", "label": "Temperature Sensor"},
    0x0307: {"domain": "sensor", "label": "Humidity Sensor"},
    0x0015: {"domain": "binary_sensor", "label": "Contact Sensor"},
    0x0202: {"domain": "cover", "label": "Window Covering"},
    0x002B: {"domain": "fan", "label": "Fan"},
    0x0107: {"domain": "binary_sensor", "label": "Occupancy Sensor"},
    0x002C: {"domain": "sensor", "label": "Air Quality Sensor"},
}

MATTER_FIXTURE: list[dict] = [
    {
        "id": "matter_bulb_01", "name": "Matter RGB Bulb",
        "device_type": 0x0101, "vendor": "CSA Certified",
        "fabric": 1, "online": True,
    },
    {
        "id": "matter_plug_01", "name": "Matter Smart Plug",
        "device_type": 0x010A, "vendor": "CSA Certified",
        "fabric": 1, "online": True,
    },
    {
        "id": "matter_frontdoor", "name": "Matter Front Door Lock",
        "device_type": 0x000A, "vendor": "CSA Certified",
        "fabric": 1, "online": True,
    },
    {
        "id": "matter_thermo", "name": "Matter Thermostat",
        "device_type": 0x0301, "vendor": "CSA Certified",
        "fabric": 1, "online": True,
    },
    {
        "id": "matter_temp_01", "name": "Matter Temperature Sensor",
        "device_type": 0x0302, "vendor": "CSA Certified",
        "fabric": 1, "online": True,
    },
    {
        "id": "matter_door", "name": "Matter Door Contact",
        "device_type": 0x0015, "vendor": "CSA Certified",
        "fabric": 1, "online": True,
    },
    {
        "id": "matter_blind", "name": "Matter Window Blind",
        "device_type": 0x0202, "vendor": "CSA Certified",
        "fabric": 2, "online": False,
    },
    {
        "id": "matter_occ", "name": "Matter Occupancy Sensor",
        "device_type": 0x0107, "vendor": "CSA Certified",
        "fabric": 1, "online": True,
    },
]

# Default state per domain for fixture devices
_DEFAULT_STATES: dict[str, str | float] = {
    "light": "off",
    "switch": "off",
    "lock": "locked",
    "climate": "off",
    "sensor": 22.5,
    "binary_sensor": "off",
    "cover": "closed",
    "fan": "off",
}

# Unit of measurement per domain
_UNITS: dict[str, str | None] = {
    "light": None,
    "switch": None,
    "lock": None,
    "climate": None,
    "sensor": "°C",
    "binary_sensor": None,
    "cover": None,
    "fan": None,
}


class MatterAdapter:
    """Matter bridge adapter (stub with offline fixtures).

    Provides fixture-based device listing for testing without Matter
    hardware. SDK integration (connectedhomeip) planned for Phase 2.
    """

    name = "matter"

    def __init__(self, use_fixture: bool = True):
        self.use_fixture = use_fixture

    def list_remote(self) -> list[Device]:
        """Return fixture Matter devices (offline)."""
        if not self.use_fixture:
            return []  # live SDK not implemented yet

        devices: list[Device] = []
        for row in MATTER_FIXTURE:
            dt_info = MATTER_DEVICE_TYPE_MAP.get(
                row["device_type"], {"domain": "sensor", "label": "Unknown"}
            )
            domain = dt_info["domain"]
            devices.append(
                Device(
                    id=f"{domain}.{row['id']}",
                    name=row["name"],
                    domain=domain,
                    manufacturer=row["vendor"],
                    model=f"Matter DT 0x{row['device_type']:04X}",
                    area="home",
                    online=bool(row.get("online", True)),
                    state={"state": _DEFAULT_STATES.get(domain, "unknown")},
                    attributes={
                        "matter_id": row["id"],
                        "device_type": row["device_type"],
                        "device_type_label": dt_info["label"],
                        "fabric": row.get("fabric"),
                        "unit_of_measurement": _UNITS.get(domain),
                        "protocol": "Matter",
                        "commissioned": row.get("online", True),
                    },
                    adapter="matter",
                )
            )
        return devices

    def push_state(self, device: Device) -> None:
        """Push state to Matter device (stub — no-op offline)."""
        return None

    @staticmethod
    def cluster_map() -> dict[int, str]:
        """Return Matter cluster ID → HA domain mapping."""
        return dict(MATTER_CLUSTER_MAP)

    @staticmethod
    def device_type_map() -> dict[int, dict]:
        """Return Matter device type → domain info mapping."""
        return dict(MATTER_DEVICE_TYPE_MAP)
