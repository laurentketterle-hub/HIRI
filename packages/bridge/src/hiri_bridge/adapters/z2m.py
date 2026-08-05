"""Zigbee2MQTT adapter — fixture offline; optional live HTTP from Z2M frontend API."""

from __future__ import annotations

from hiri_bridge.devices.types import Device

# ---------------------------------------------------------------------------
# Z2M expose → HIRI domain mapping
# ---------------------------------------------------------------------------
# Each z2m expose has a "type" string that tells us what capability it represents.
# A single z2m device can have multiple exposes (e.g. a bulb exposes "light"
# plus a "numeric" temperature sensor).  We pick the *primary* domain from the
# most "actionable" expose present, falling back to sensor/binary_sensor.

_EXPOSE_DOMAIN_PRIORITY: list[tuple[str, str | None, str]] = [
    # (expose_type, optional feature name required, hiri_domain)
    ("light",     None,               "light"),
    ("switch",    None,               "switch"),
    ("cover",     None,               "cover"),
    ("climate",   None,               "climate"),
    ("lock",      None,               "lock"),
    ("fan",       None,               "fan"),
    ("siren",     None,               "siren"),
    ("button",    None,               "button"),
    ("binary",    None,               "binary_sensor"),
    ("numeric",   None,               "sensor"),
    ("sensor",    None,               "sensor"),
]


def _domain_from_exposes(exposes):
    expose_types = set()
    for ex in exposes:
        t = (ex.get("type") or "").lower()
        expose_types.add(t)
        for feat in ex.get("features") or []:
            ft = (feat.get("type") or feat.get("name") or "").lower()
            expose_types.add(ft)
    for et, feat_req, domain in _EXPOSE_DOMAIN_PRIORITY:
        if feat_req:
            continue
        if et in expose_types:
            return domain
    return "sensor"


def _device_class_from_exposes(exposes):
    for ex in exposes:
        name = str(ex.get("name", "") or "").lower()
        if name in {"occupancy", "presence", "motion", "moving",
                     "illuminance", "vibration", "tamper"}:
            return name
        if name in {"contact", "door", "window"}:
            return "door"
        if name in {"water_leak", "moisture"}:
            return "moisture"
        if name == "smoke":
            return "smoke"
        if name == "gas":
            return "gas"
        if name == "carbon_monoxide":
            return "carbon_monoxide"
        if name in {"temperature", "humidity", "pressure", "battery"}:
            return name
    return None


# ---------------------------------------------------------------------------
# Offline fixture (used when no base_url is supplied)
# ---------------------------------------------------------------------------

Z2M_FIXTURE: list[dict] = [
    {
        "friendly_name": "kitchen/motion",
        "type": "EndDevice",
        "definition": {"model": "SNZB-03", "vendor": "SONOFF", "description": "Motion"},
        "exposes": [{"type": "binary", "name": "occupancy"}],
    },
    {
        "friendly_name": "hall/contact",
        "type": "EndDevice",
        "definition": {"model": "MCCGQ11LM", "vendor": "Xiaomi", "description": "Door"},
        "exposes": [{"type": "binary", "name": "contact"}],
    },
    {
        "friendly_name": "living/bulb",
        "type": "Router",
        "definition": {"model": "LED1623G12", "vendor": "IKEA", "description": "Bulb"},
        "exposes": [{"type": "light", "features": [{"name": "state"}, {"name": "brightness"}]}],
    },
]


# ---------------------------------------------------------------------------
# Payload → Device mapping (shared by fixture and live paths)
# ---------------------------------------------------------------------------

def _device_from_payload(row):
    name = row.get("friendly_name", "unknown")
    exposes = row.get("exposes") or []
    definition = row.get("definition") or {}

    domain = _domain_from_exposes(exposes)
    slug = name.replace("/", "_").replace(" ", "_").lower()
    device_id = f"{domain}.z2m_{slug}"
    area = name.split("/")[0] if "/" in name else "home"

    state = {}
    device_class = _device_class_from_exposes(exposes)
    if domain in ("light", "switch"):
        state["state"] = "off"
    elif domain == "cover":
        state["state"] = "closed"
        state["position"] = 0
    elif domain == "climate":
        state["state"] = "off"

    return Device(
        id=device_id,
        name=name,
        domain=domain,
        manufacturer=definition.get("vendor", "Zigbee"),
        model=definition.get("model", "z2m"),
        area=area,
        state=state,
        attributes={
            "via": "z2m",
            "device_class": device_class,
            "expose_types": sorted({(e.get("type") or "unknown") for e in exposes}),
        },
        adapter="z2m",
    )


# ---------------------------------------------------------------------------
# Adapter class
# ---------------------------------------------------------------------------

class Zigbee2MqttAdapter:
    name = "z2m"

    def __init__(self, base_url: str = "", use_fixture: bool = True):
        self.base_url = (base_url or "").rstrip("/")
        self.use_fixture = use_fixture

    def list_remote(self):
        if self.base_url and not self.use_fixture:
            try:
                import httpx
                with httpx.Client(timeout=10) as client:
                    resp = client.get(f"{self.base_url}/api/devices")
                    resp.raise_for_status()
                    raw = resp.json()
                devices = []
                for row in raw if isinstance(raw, list) else raw.get("data", raw):
                    if not isinstance(row, dict):
                        continue
                    if row.get("type") == "Coordinator":
                        continue
                    devices.append(_device_from_payload(row))
                return devices
            except Exception:
                return []

        devices = []
        for row in Z2M_FIXTURE:
            devices.append(_device_from_payload(row))
        return devices

    def push_state(self, device):
        return None
