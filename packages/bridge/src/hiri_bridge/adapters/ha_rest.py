"""Home Assistant REST adapter (offline-safe stub with optional live call)."""

from __future__ import annotations

from hiri_bridge.devices.types import Device


class HomeAssistantRestAdapter:
    name = "ha_rest"

    def __init__(self, base_url: str = "http://homeassistant.local:8123", token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def list_remote(self) -> list[Device]:
        # Live call would hit /api/states — offline returns empty
        if not self.token:
            return []
        try:
            import json
            import urllib.request

            req = urllib.request.Request(
                f"{self.base_url}/api/states",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                states = json.loads(resp.read().decode("utf-8"))
            devices: list[Device] = []
            for st in states[:200]:
                eid = st.get("entity_id", "")
                domain = eid.split(".", 1)[0] if "." in eid else "sensor"
                devices.append(
                    Device(
                        id=eid,
                        name=st.get("attributes", {}).get("friendly_name", eid),
                        domain=domain,
                        manufacturer="HomeAssistant",
                        model="imported",
                        state={"state": st.get("state")},
                        attributes=st.get("attributes") or {},
                        adapter="ha_rest",
                    )
                )
            return devices
        except Exception:  # noqa: BLE001
            return []

    def push_state(self, device: Device) -> None:
        # Live: POST /api/services/{domain}/{service}
        return None
