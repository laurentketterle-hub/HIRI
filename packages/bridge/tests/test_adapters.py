# Tests pour les adaptateurs bridge (Issues 4, 5, 7)
from pathlib import Path

from hiri_bridge.adapters import import_from_adapter, list_adapters
from hiri_bridge.adapters.matter import MatterAdapter
from hiri_bridge.adapters.mqtt_pub import MqttDiscoveryPublisher
from hiri_bridge.adapters.tuya import TuyaAdapter
from hiri_bridge.adapters.z2m import Zigbee2MqttAdapter
from hiri_bridge.devices.registry import DeviceRegistry


def test_list_adapters_includes_matter():
    rows = list_adapters()
    names = {r["name"] for r in rows}
    assert "matter" in names
    assert {"local", "mqtt", "ha_rest", "ha_ws", "z2m", "tuya", "matter"}.issubset(names)


def test_list_adapters_all_have_required_fields():
    for row in list_adapters():
        assert "name" in row
        assert "kind" in row
        assert "live" in row
        assert "status" in row
        assert "description" in row


def test_z2m_fixture_import():
    devices = Zigbee2MqttAdapter().list_remote()
    assert len(devices) >= 3
    assert all(d.adapter == "z2m" for d in devices)
    assert any(d.domain == "light" for d in devices)
    assert any(d.domain == "binary_sensor" for d in devices)
    for d in devices:
        assert d.id
        assert d.name
        assert d.manufacturer
        assert d.area


def test_z2m_fixture_area_extraction():
    devices = Zigbee2MqttAdapter().list_remote()
    areas = {d.area for d in devices}
    assert "kitchen" in areas or "living" in areas or "hall" in areas


def test_tuya_fixture_and_map():
    devices = TuyaAdapter().list_remote()
    assert len(devices) >= 3
    assert "dj" in TuyaAdapter.mapping_table()
    assert all(d.adapter == "tuya" for d in devices)


def test_tuya_mapping_table_complete():
    mapping = TuyaAdapter.mapping_table()
    assert mapping["dj"] == "light"
    assert mapping["kg"] == "switch"
    assert mapping["cz"] == "switch"
    assert mapping["wsdcg"] == "sensor"
    assert mapping["mcs"] == "binary_sensor"


def test_tuya_online_flag():
    devices = TuyaAdapter().list_remote()
    online = [d for d in devices if d.online]
    offline = [d for d in devices if not d.online]
    assert len(online) >= 2
    assert len(offline) >= 1


def test_matter_adapter_scaffold():
    adapter = MatterAdapter()
    assert adapter.name == "matter"
    assert adapter.list_remote() == []
    assert "scaffold" in adapter.status()
    mapping = MatterAdapter.mapping_table()
    assert "light" in mapping
    assert "switch" in mapping
    assert mapping["light"]["device_type_id"] == 0x010D


def test_matter_supported_domains():
    domains = MatterAdapter.supported_domains()
    assert "light" in domains
    assert "switch" in domains
    assert "sensor" in domains
    assert "climate" in domains
    assert "cover" in domains
    assert "lock" in domains
    assert "fan" in domains


def test_import_into_registry(tmp_path: Path):
    reg = DeviceRegistry(path=tmp_path / "d.json")
    reg.seed()
    before = reg.stats()["total"]
    for d in import_from_adapter("z2m"):
        reg.upsert(d)
    assert reg.stats()["total"] > before


def test_import_tuya_into_registry(tmp_path: Path):
    reg = DeviceRegistry(path=tmp_path / "d.json")
    reg.seed()
    before = reg.stats()["total"]
    for d in import_from_adapter("tuya"):
        reg.upsert(d)
    after = reg.stats()["total"]
    assert after >= before


def test_ha_ws_import_is_offline_safe():
    assert import_from_adapter("ha_ws") == []


def test_mqtt_dry_run(tmp_path: Path):
    reg = DeviceRegistry(path=tmp_path / "d.json")
    reg.seed()
    pub = MqttDiscoveryPublisher()
    result = pub.publish(reg.list()[:3], dry_run=True)
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["count"] >= 3
