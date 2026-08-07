"""Tests pour la publication MQTT discovery (Issue #3)."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from hiri_bridge.adapters.mqtt_pub import MqttDiscoveryPublisher
from hiri_bridge.devices.registry import DeviceRegistry
from hiri_bridge.devices.types import Device
from hiri_bridge.ha.discovery import discovery_payload, discovery_topic, state_topic


def test_dry_run_no_broker_required():
    """Test : dry_run fonctionne sans broker MQTT."""
    reg = DeviceRegistry()
    reg.seed()
    pub = MqttDiscoveryPublisher()
    result = pub.publish(reg.list()[:3], dry_run=True)
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["count"] >= 6  # discovery + state per device + status


def test_build_messages_structure():
    """Test : les messages MQTT ont la bonne structure."""
    pub = MqttDiscoveryPublisher()
    devices = [
        Device(
            id="light.test",
            name="Test Light",
            domain="light",
            adapter="local",
        )
    ]
    msgs = pub.build_messages(devices)
    assert len(msgs) == 3  # discovery + state + availability
    topics = {m["topic"] for m in msgs}
    assert "hiri/status" in topics
    assert any("homeassistant/light/hiri" in t for t in topics)
    assert any("hiri/state/light/test" in t for t in topics)


def test_discovery_payload_has_device_info():
    """Test : le payload de decouverte contient les infos du device."""
    dev = Device(
        id="switch.kitchen",
        name="Kitchen Switch",
        domain="switch",
        manufacturer="HIRI",
        model="RELAY-4G",
        area="cuisine",
    )
    payload = discovery_payload(dev)
    assert payload["name"] == "Kitchen Switch"
    assert payload["unique_id"] == "hiri_switch_kitchen"
    assert "device" in payload
    assert payload["device"]["manufacturer"] == "HIRI"
    assert payload["device"]["suggested_area"] == "cuisine"


def test_topics_are_consistent():
    """Test : les topics discovery et state sont coherents."""
    dev = Device(id="light.living", name="Living Light", domain="light")
    dt = discovery_topic(dev)
    st = state_topic(dev)
    assert dt.startswith("homeassistant/light/hiri/")
    assert dt.endswith("/config")
    assert st == "hiri/state/light/living"


@patch("hiri_bridge.adapters.mqtt_pub.mqtt")
def test_live_publish_mock_client(mock_mqtt):
    """Test : la publication live utilise paho-mqtt."""
    mock_client = MagicMock()
    mock_mqtt.Client.return_value = mock_client
    mock_mqtt.CallbackAPIVersion = MagicMock()
    mock_mqtt.CallbackAPIVersion.VERSION2 = 2

    dev = Device(id="light.test", name="Test", domain="light")
    pub = MqttDiscoveryPublisher(host="localhost", port=1883)
    result = pub.publish([dev], dry_run=False)

    assert result["ok"] is True
    assert result["dry_run"] is False
    mock_client.connect.assert_called_once_with("localhost", 1883, 30)
    mock_client.disconnect.assert_called_once()
