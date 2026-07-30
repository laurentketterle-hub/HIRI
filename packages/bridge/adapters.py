"""HIRI Bridge Adapters — supported integration adapters."""

ADAPTERS = {
    "local": {
        "name": "Local Bridge",
        "protocol": "HTTP/REST",
        "port": 8080,
        "description": "Direct local device bridge over HTTP REST API",
        "status": "stable",
    },
    "mqtt": {
        "name": "MQTT Bridge",
        "protocol": "MQTT",
        "port": 1883,
        "description": "MQTT broker bridge for IoT device messaging",
        "status": "stable",
    },
    "ha_rest": {
        "name": "Home Assistant REST",
        "protocol": "HTTP/REST",
        "port": 8123,
        "description": "Home Assistant REST API bridge",
        "status": "beta",
    },
    "z2m": {
        "name": "Zigbee2MQTT",
        "protocol": "MQTT",
        "port": 8080,
        "description": "Zigbee2MQTT bridge for Zigbee device control",
        "status": "beta",
    },
}

def list_adapters():
    """Return all available adapters."""
    return [
        {
            "id": aid,
            "name": ad["name"],
            "protocol": ad["protocol"],
            "status": ad["status"],
        }
        for aid, ad in ADAPTERS.items()
    ]

def get_adapter(adapter_id):
    """Get adapter details by ID."""
    return ADAPTERS.get(adapter_id)
