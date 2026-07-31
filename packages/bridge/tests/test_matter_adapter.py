"""Tests for Matter bridge adapter."""
from __future__ import annotations

import pytest

from hiri_bridge.adapters.matter import (
    MATTER_CLUSTER_MAP,
    MATTER_DEVICE_TYPE_MAP,
    MATTER_FIXTURE,
    MatterAdapter,
)
from hiri_bridge.devices.types import Device


class TestMatterAdapter:
    def test_name(self):
        adapter = MatterAdapter()
        assert adapter.name == "matter"

    def test_list_remote_returns_devices(self):
        adapter = MatterAdapter(use_fixture=True)
        devices = adapter.list_remote()
        assert len(devices) == len(MATTER_FIXTURE)
        assert len(devices) > 0
        assert all(isinstance(d, Device) for d in devices)

    def test_list_remote_empty_without_fixture(self):
        adapter = MatterAdapter(use_fixture=False)
        devices = adapter.list_remote()
        assert devices == []

    def test_devices_have_valid_domains(self):
        adapter = MatterAdapter()
        valid_domains = {
            "light", "switch", "lock", "climate", "sensor",
            "binary_sensor", "cover", "fan",
        }
        for device in adapter.list_remote():
            assert device.domain in valid_domains, f"bad domain: {device.domain}"

    def test_devices_have_matter_attributes(self):
        adapter = MatterAdapter()
        for device in adapter.list_remote():
            attrs = device.attributes
            assert "matter_id" in attrs
            assert "device_type" in attrs
            assert "device_type_label" in attrs
            assert "protocol" in attrs
            assert attrs["protocol"] == "Matter"

    def test_push_state_is_noop(self):
        adapter = MatterAdapter()
        devices = adapter.list_remote()
        if devices:
            adapter.push_state(devices[0])  # should not raise

    def test_cluster_map_has_expected_entries(self):
        cmap = MatterAdapter.cluster_map()
        assert 0x0006 in cmap  # OnOff
        assert 0x0101 in cmap  # DoorLock
        assert cmap[0x0006] == "light"
        assert cmap[0x0101] == "lock"

    def test_device_type_map_has_expected_entries(self):
        dtmap = MatterAdapter.device_type_map()
        assert 0x0100 in dtmap  # On/Off Light
        assert 0x000A in dtmap  # Door Lock
        assert dtmap[0x0100]["domain"] == "light"
        assert dtmap[0x000A]["domain"] == "lock"

    def test_fixture_has_8_devices(self):
        """Per MATTER.md spec: 8 representative Matter fixtures."""
        assert len(MATTER_FIXTURE) == 8

    def test_all_fixture_device_types_are_mapped(self):
        for row in MATTER_FIXTURE:
            dt = row["device_type"]
            assert dt in MATTER_DEVICE_TYPE_MAP, f"missing mapping for 0x{dt:04X}"

    def test_each_fixture_produces_unique_device_id(self):
        adapter = MatterAdapter()
        ids = [d.id for d in adapter.list_remote()]
        assert len(ids) == len(set(ids)), f"duplicate IDs: {ids}"

    def test_cluster_map_keys_are_integers(self):
        for k in MATTER_CLUSTER_MAP:
            assert isinstance(k, int), f"non-int key: {k}"

    def test_cluster_map_values_are_valid_domains(self):
        valid = {
            "light", "switch", "lock", "climate", "sensor",
            "binary_sensor", "cover", "fan",
        }
        for domain in MATTER_CLUSTER_MAP.values():
            assert domain in valid, f"invalid domain: {domain}"


def test_matter_fixture_importable():
    """Smoke-test that matter adapter can be imported."""
    from hiri_bridge.adapters.matter import MatterAdapter
    assert MatterAdapter is not None


def test_matter_in_catalog():
    """Verify matter appears in adapter catalog."""
    from hiri_bridge.adapters.catalog import list_adapters
    adapters = list_adapters()
    matter = [a for a in adapters if a["name"] == "matter"]
    assert len(matter) == 1
    assert matter[0]["status"] == "fixture ready"
    assert "Matter" in matter[0]["description"]


def test_import_matter_from_catalog():
    """Verify import_from_adapter works for matter."""
    from hiri_bridge.adapters.catalog import import_from_adapter
    devices = import_from_adapter("matter")
    assert len(devices) == 8
    assert all(isinstance(d, Device) for d in devices)


def test_live_flag_is_false():
    """Matter adapter stub is offline (no live SDK yet)."""
    adapter = MatterAdapter()
    assert adapter.use_fixture is True
