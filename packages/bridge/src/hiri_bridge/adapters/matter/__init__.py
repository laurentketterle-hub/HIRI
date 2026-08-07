"""Matter bridge adapter — research scaffold.

Ce module fournit le stub initial pour l'intégration Matter dans HIRI.
L'implémentation complète nécessite le SDK Matter (connectedhomeip).
"""

from __future__ import annotations

from hiri_bridge.devices.types import Device

# Mapping des domaines HIRI vers les types d'appareils Matter
MATTER_DEVICE_TYPE_MAP: dict[str, dict[str, object]] = {
    "light": {
        "device_type": "Extended Color Light",
        "device_type_id": 0x010D,
        "clusters": ["on_off", "level_control", "color_control"],
    },
    "switch": {
        "device_type": "On/Off Plug-in Unit",
        "device_type_id": 0x010A,
        "clusters": ["on_off"],
    },
    "sensor": {
        "device_type": "Temperature Sensor",
        "device_type_id": 0x0302,
        "clusters": ["temperature_measurement"],
    },
    "binary_sensor": {
        "device_type": "Contact Sensor",
        "device_type_id": 0x0015,
        "clusters": ["boolean_state"],
    },
    "climate": {
        "device_type": "Thermostat",
        "device_type_id": 0x0301,
        "clusters": ["thermostat"],
    },
    "cover": {
        "device_type": "Window Covering",
        "device_type_id": 0x0202,
        "clusters": ["window_covering"],
    },
    "lock": {
        "device_type": "Door Lock",
        "device_type_id": 0x0101,
        "clusters": ["door_lock"],
    },
    "fan": {
        "device_type": "Fan",
        "device_type_id": 0x002B,
        "clusters": ["fan_control"],
    },
    "vacuum": {
        "device_type": "Robotic Vacuum Cleaner",
        "device_type_id": 0x0074,
        "clusters": ["rvc_run_mode", "rvc_operational_state"],
    },
}


class MatterAdapter:
    """Adaptateur Matter — actuellement en scaffold.

    L'intégration complète nécessite :
    - SDK Matter (connectedhomeip) ou python-matter-server
    - Configuration du contrôleur Matter
    - Commissioning des appareils
    """

    name = "matter"

    def __init__(self) -> None:
        self._ready = False

    def list_remote(self) -> list[Device]:
        """Retourne une liste vide pour le moment — scaffold uniquement."""
        return []

    def push_state(self, device: Device) -> None:
        """Pousse l'état d'un appareil vers le fabric Matter (non implémenté)."""
        return None

    def status(self) -> str:
        return "scaffold — SDK Matter requis"

    @staticmethod
    def mapping_table() -> dict[str, dict[str, object]]:
        """Retourne la table de mapping HIRI → Matter."""
        return dict(MATTER_DEVICE_TYPE_MAP)

    @staticmethod
    def supported_domains() -> list[str]:
        """Retourne les domaines supportés par le mapping Matter."""
        return list(MATTER_DEVICE_TYPE_MAP.keys())
