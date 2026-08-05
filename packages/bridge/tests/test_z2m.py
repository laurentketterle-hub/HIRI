"""Tests for Zigbee2MQTT adapter - fixture + live HTTP + expose mapping."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hiri_bridge.adapters.z2m import (
    Zigbee2MqttAdapter,
    Z2M_FIXTURE,
    _domain_from_exposes,
    _device_class_from_exposes,
    _device_from_payload,
)
from hiri_bridge.devices.types import Device


# ---------------------------------------------------------------------------
# Expose to domain mapping
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "exposes, expected_domain",
    [
        # single exposes
        ([{"type": "light", "features": [{"name": "state"}]}], "light"),
        ([{"type": "switch", "features": [{"name": "state"}]}], "switch"),
        ([{"type": "binary", "name": "occupancy"}], "binary_sensor"),
        ([{"type": "numeric", "name": "temperature"}], "sensor"),
        ([{"type": "cover", "features": [{"name": "state"}]}], "cover"),
        ([{"type": "climate", "features": [{"name": "system_mode"}]}], "climate"),
        ([{"type": "lock"}], "lock"),
        ([{"type": "fan"}], "fan"),
        ([{"type": "siren"}], "siren"),
        ([{"type": "button"}], "button"),
        ([{"type": "sensor", "name": "battery"}], "sensor"),
        # multi-expose priority: actionable beats sensor
        ([{"type": "light"}, {"type": "numeric", "name": "temperature"}], "light"),
        ([{"type": "switch"}, {"type": "binary", "name": "occupancy"}], "switch"),
        # empty falls back to sensor
        ([], "sensor"),
        # unknown type falls back to sensor
        ([{"type": "made_up_thing"}], "sensor"),
    ],
)
def test_domain_from_exposes(exposes, expected_domain):
    assert _domain_from_exposes(exposes) == expected_domain


# ---------------------------------------------------------------------------
# Device class derivation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "exposes, expected",
    [
        ([{"type": "binary", "name": "occupancy"}], "occupancy"),
        ([{"type": "binary", "name": "motion"}], "motion"),
        ([{"type": "binary", "name": "presence"}], "presence"),
        ([{"type": "binary", "name": "contact"}], "door"),
        ([{"type": "binary", "name": "door"}], "door"),
        ([{"type": "binary", "name": "window"}], "door"),
        ([{"type": "binary", "name": "water_leak"}], "moisture"),
        ([{"type": "binary", "name": "smoke"}], "smoke"),
        ([{"type": "binary", "name": "gas"}], "gas"),
        ([{"type": "binary", "name": "carbon_monoxide"}], "carbon_monoxide"),
        ([{"type": "numeric", "name": "temperature"}], "temperature"),
        ([{"type": "numeric", "name": "humidity"}], "humidity"),
        ([{"type": "numeric", "name": "pressure"}], "pressure"),
        ([{"type": "numeric", "name": "battery"}], "battery"),
        ([], None),
    ],
)
def test_device_class_from_exposes(exposes, expected):
    assert _device_class_from_exposes(exposes) == expected


# ---------------------------------------------------------------------------
# Payload to Device conversion
# ---------------------------------------------------------------------------

def test_device_from_payload_light():
    row = {
        "friendly_name": "office/ceiling",
        "type": "Router",
        "definition": {"model": "TRADFRI bulb E27", "vendor": "IKEA", "description": "TRADFRI LED bulb"},
        "exposes": [{"type": "light", "features": [{"name": "state"}, {"name": "brightness"}]}],
    }
    dev = _device_from_payload(row)
    assert isinstance(dev, Device)
    assert dev.domain == "light"
    assert dev.id == "light.z2m_office_ceiling"
    assert dev.name == "office/ceiling"
    assert dev.area == "office"
    assert dev.manufacturer == "IKEA"
    assert dev.model == "TRADFRI bulb E27"
    assert dev.adapter == "z2m"
    assert dev.state == {"state": "off"}
    assert "expose_types" in dev.attributes
    assert dev.attributes["expose_types"] == ["light"]


def test_device_from_payload_binary_sensor():
    row = {
        "friendly_name": "kitchen/motion",
        "type": "EndDevice",
        "definition": {"model": "SNZB-03", "vendor": "SONOFF", "description": "Motion sensor"},
        "exposes": [{"type": "binary", "name": "occupancy"}],
    }
    dev = _device_from_payload(row)
    assert dev.domain == "binary_sensor"
    assert dev.id == "binary_sensor.z2m_kitchen_motion"
    assert dev.attributes["device_class"] == "occupancy"
    assert dev.area == "kitchen"


def test_device_from_payload_cover():
    row = {
        "friendly_name": "living/blind",
        "type": "EndDevice",
        "definition": {"vendor": "Zemismart", "model": "ZM25TQ"},
        "exposes": [{"type": "cover", "features": [{"name": "state"}, {"name": "position"}]}],
    }
    dev = _device_from_payload(row)
    assert dev.domain == "cover"
    assert dev.state == {"state": "closed", "position": 0}


def test_device_from_payload_no_definition():
    row = {
        "friendly_name": "unknown_device",
        "type": "EndDevice",
        "exposes": [{"type": "binary", "name": "contact"}],
    }
    dev = _device_from_payload(row)
    assert dev.manufacturer == "Zigbee"
    assert dev.model == "z2m"


def test_device_from_payload_friendly_name_no_slash():
    row = {
        "friendly_name": "simple_name",
        "type": "EndDevice",
        "exposes": [{"type": "switch"}],
    }
    dev = _device_from_payload(row)
    assert dev.area == "home"


# ---------------------------------------------------------------------------
# Fixture (offline) path
# ---------------------------------------------------------------------------

def test_fixture_list_remote_default():
    adapter = Zigbee2MqttAdapter()
    devices = adapter.list_remote()
    assert len(devices) >= 3
    assert all(d.adapter == "z2m" for d in devices)
    domains = {d.domain for d in devices}
    assert "light" in domains
    assert "binary_sensor" in domains


def test_fixture_list_remote_explicit():
    adapter = Zigbee2MqttAdapter(base_url="http://192.168.1.100:8080", use_fixture=True)
    devices = adapter.list_remote()
    assert len(devices) >= 3


def test_fixture_list_remote_no_url():
    adapter = Zigbee2MqttAdapter(base_url="", use_fixture=False)
    devices = adapter.list_remote()
    assert len(devices) >= 3


# ---------------------------------------------------------------------------
# Live HTTP path (with mocked httpx)
# ---------------------------------------------------------------------------

MOCK_Z2M_RESPONSE = [
    {
        "friendly_name": "office/sensor",
        "type": "EndDevice",
        "definition": {"model": "WSDCGQ11LM", "vendor": "Xiaomi", "description": "Temp/Humidity"},
        "exposes": [
            {"type": "numeric", "name": "temperature", "unit": "°C"},
            {"type": "numeric", "name": "humidity", "unit": "%"},
        ],
    },
    {
        "friendly_name": "Coordinator",
        "type": "Coordinator",
        "definition": {"model": "CC2652RB", "vendor": "TI"},
        "exposes": [],
    },
    {
        "friendly_name": "living/switch",
        "type": "Router",
        "definition": {"model": "QBKG11LM", "vendor": "Xiaomi", "description": "Wall switch"},
        "exposes": [{"type": "switch", "features": [{"name": "state"}]}],
    },
]


class MockResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json = json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._json


def test_live_http_returns_devices(monkeypatch):
    class FakeClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, url):
            assert "/api/devices" in url
            r = MockResponse(200, MOCK_Z2M_RESPONSE)
            r.url = url
            return r

    monkeypatch.setattr("httpx.Client", FakeClient)

    adapter = Zigbee2MqttAdapter(base_url="http://z2m.local:8080", use_fixture=False)
    devices = adapter.list_remote()

    assert len(devices) == 2  # Coordinator skipped
    assert devices[0].domain == "sensor"
    assert devices[0].name == "office/sensor"
    assert devices[0].attributes["device_class"] == "temperature"
    assert devices[1].domain == "switch"
    assert devices[1].name == "living/switch"


def test_live_http_connection_error_graceful(monkeypatch):
    class FailingClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, url):
            raise ConnectionError("refused")

    monkeypatch.setattr("httpx.Client", FailingClient)

    adapter = Zigbee2MqttAdapter(base_url="http://127.0.0.1:19999", use_fixture=False)
    devices = adapter.list_remote()
    assert devices == []


def test_live_http_non_200_status(monkeypatch):
    class ErrorClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, url):
            r = MockResponse(500, {})
            r.url = url
            return r

    monkeypatch.setattr("httpx.Client", ErrorClient)

    adapter = Zigbee2MqttAdapter(base_url="http://z2m.local:8080", use_fixture=False)
    devices = adapter.list_remote()
    assert devices == []


def test_push_state_is_noop():
    adapter = Zigbee2MqttAdapter()
    dev = _device_from_payload(Z2M_FIXTURE[0])
    result = adapter.push_state(dev)
    assert result is None


# ---------------------------------------------------------------------------
# Integration: import into registry
# ---------------------------------------------------------------------------

def test_z2m_fixture_import():
    devices = Zigbee2MqttAdapter().list_remote()
    assert len(devices) >= 3
    assert all(d.adapter == "z2m" for d in devices)
    assert any(d.domain == "light" for d in devices)


def test_import_into_registry(tmp_path):
    from hiri_bridge.devices.registry import DeviceRegistry

    reg = DeviceRegistry(path=tmp_path / "d.json")
    reg.seed()
    before = reg.stats()["total"]

    for d in Zigbee2MqttAdapter().list_remote():
        reg.upsert(d)

    assert reg.stats()["total"] > before
