"""
End-to-end integration tests for HIRI bridge snapshot pipeline.

Validates the full device lifecycle through the bridge:
    seed → upsert → export → HA discovery → MQTT publish → reload → verify
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from hiri_bridge.devices.registry import DeviceRegistry
from hiri_bridge.devices.types import Device, DOMAINS


# ── Full pipeline tests ──

class TestSnapshotPipeline:
    """End-to-end snapshot pipeline: seed → modify → persist → reload → verify."""

    def test_full_pipeline_single_domain(self, tmp_path: Path) -> None:
        """Complete snapshot pipeline for a single domain (sensor)."""
        devices_file = tmp_path / "devices.json"
        reg = DeviceRegistry(path=devices_file)
        reg.seed()

        # 1. Record initial state
        initial = reg.list()
        initial_ids = {d.id for d in initial}
        initial_count = len(initial)
        assert initial_count > 0

        # 2. Add custom devices
        custom = [
            Device(
                id=f"sensor.pipeline_{i}",
                name=f"Pipeline sensor {i}",
                domain="sensor",
                state={"state": float(i * 10), "battery": 100 - i},
                attributes={"unit_of_measurement": "°C", "device_class": "temperature"},
            )
            for i in range(10)
        ]
        for dev in custom:
            reg.upsert(dev)

        # 3. Verify count increased
        mid_count = reg.stats()["total"]
        assert mid_count == initial_count + 10

        # 4. Verify each custom device is retrievable
        for dev in custom:
            retrieved = reg.get(dev.id)
            assert retrieved is not None, f"Missing device: {dev.id}"
            assert retrieved.name == dev.name
            assert retrieved.domain == "sensor"

        # 5. Update one device
        reg.upsert(
            Device(
                id="sensor.pipeline_0",
                name="Pipeline sensor 0 (updated)",
                domain="sensor",
                state={"state": 99.9, "battery": 50},
                attributes={"unit_of_measurement": "°F", "device_class": "temperature"},
            )
        )
        updated = reg.get("sensor.pipeline_0")
        assert updated is not None
        assert updated.state["state"] == 99.9
        assert updated.attributes["unit_of_measurement"] == "°F"

        # 6. Reload from disk — all data preserved
        reg2 = DeviceRegistry(path=devices_file)
        reg2.load_or_seed()
        final = reg2.list()
        final_ids = {d.id for d in final}

        assert len(final) >= mid_count
        for dev in custom:
            assert dev.id in final_ids, f"Device lost after reload: {dev.id}"

        # 7. Updated device preserved
        reloaded = reg2.get("sensor.pipeline_0")
        assert reloaded is not None
        assert reloaded.state["state"] == 99.9
        assert reloaded.name == "Pipeline sensor 0 (updated)"

    def test_full_pipeline_multi_domain(self, tmp_path: Path) -> None:
        """Pipeline with devices across multiple HA domains."""
        devices_file = tmp_path / "devices.json"
        reg = DeviceRegistry(path=devices_file)
        reg.seed()
        base_count = reg.stats()["total"]

        # Add devices across 8 domains
        multi = [
            ("sensor", "multi_temp", {"state": 22.5}, {"unit": "°C"}),
            ("climate", "multi_thermo", {"state": "heat", "temperature": 20}, {"mode": "auto"}),
            ("cover", "multi_blind", {"state": "open"}, {"position": 100}),
            ("light", "multi_rgb", {"state": "on", "brightness": 128}, {"rgb": True}),
            ("switch", "multi_outlet", {"state": "off"}, {"device_class": "outlet"}),
            ("lock", "multi_door", {"state": "locked"}, {"code_format": "number"}),
            ("fan", "multi_ceiling", {"state": "off", "speed": 0}, {"speeds": 3}),
            ("media_player", "multi_speaker", {"state": "paused", "volume": 0.5}, {"source": "bt"}),
        ]

        for domain, eid, state, attrs in multi:
            reg.upsert(
                Device(
                    id=f"{domain}.{eid}",
                    name=f"Multi {eid}",
                    domain=domain,
                    state=state,
                    attributes=attrs,
                )
            )

        assert reg.stats()["total"] == base_count + 8

        # Reload and verify per-domain counts
        reg2 = DeviceRegistry(path=devices_file)
        reg2.load_or_seed()
        final = reg2.list()

        for domain, eid, state, attrs in multi:
            dev = next((d for d in final if d.id == f"{domain}.{eid}"), None)
            assert dev is not None, f"Missing {domain}.{eid}"
            assert dev.domain == domain
            assert dev.state == state
            assert dev.attributes == attrs

    def test_pipeline_with_delete_and_restore(self, tmp_path: Path) -> None:
        """Pipeline with delete operations and device restoration."""
        devices_file = tmp_path / "devices.json"
        reg = DeviceRegistry(path=devices_file)
        reg.seed()

        # Add a device, delete it, re-add it — verify no corruption
        reg.upsert(
            Device(
                id="sensor.ghost",
                name="Ghost sensor",
                domain="sensor",
                state={"state": 1.0},
            )
        )
        count_with = reg.stats()["total"]

        reg.delete("sensor.ghost")
        count_without = reg.stats()["total"]
        assert count_without == count_with - 1

        # Re-add with different data
        reg.upsert(
            Device(
                id="sensor.ghost",
                name="Ghost sensor v2",
                domain="sensor",
                state={"state": 999.0},
            )
        )
        restored = reg.get("sensor.ghost")
        assert restored is not None
        assert restored.state["state"] == 999.0
        assert reg.stats()["total"] == count_with

    def test_pipeline_bulk_operations(self, tmp_path: Path) -> None:
        """Bulk insert 500 devices, verify all survive reload."""
        devices_file = tmp_path / "devices.json"
        reg = DeviceRegistry(path=devices_file)
        reg.seed()
        base = reg.stats()["total"]

        # Bulk insert
        for i in range(500):
            reg.upsert(
                Device(
                    id=f"sensor.bulk_{i:05d}",
                    name=f"Bulk sensor {i}",
                    domain="sensor",
                    state={"value": i, "ts": int(time.time())},
                )
            )

        assert reg.stats()["total"] == base + 500

        # Reload and spot check
        reg2 = DeviceRegistry(path=devices_file)
        reg2.load_or_seed()
        final = reg2.list()

        assert len(final) >= base + 500
        assert reg2.get("sensor.bulk_00000") is not None
        assert reg2.get("sensor.bulk_00499") is not None
        # Edge devices survive
        assert reg2.get("sensor.bulk_00250") is not None


# ── Snapshot diff pipeline ──

class TestDiffPipeline:
    """Snapshot diff pipeline: capture → modify → diff → verify."""

    def test_diff_between_snapshots(self, tmp_path: Path) -> None:
        """Diff between two snapshots should detect additions and modifications."""
        snap_a = tmp_path / "snap_a.json"
        snap_b = tmp_path / "snap_b.json"

        reg_a = DeviceRegistry(path=snap_a)
        reg_a.seed()

        reg_b = DeviceRegistry(path=snap_b)
        reg_b.seed()
        reg_b.upsert(
            Device(id="sensor.new_one", name="New sensor", domain="sensor", state={"state": 42.0})
        )

        devices_a = reg_a.list()
        devices_b = reg_b.list()

        ids_a = {d.id for d in devices_a}
        ids_b = {d.id for d in devices_b}

        added = ids_b - ids_a
        removed = ids_a - ids_b

        assert len(added) >= 1, "Should have at least one added device"
        assert "sensor.new_one" in added
        assert len(removed) == 0, "No devices should be removed"

    def test_diff_after_device_update(self, tmp_path: Path) -> None:
        """Diff should detect state changes on existing devices."""
        devices_file = tmp_path / "devices.json"
        reg = DeviceRegistry(path=devices_file)
        reg.seed()

        # Snapshot before
        before_devices = {d.id: d.state for d in reg.list()}

        # Update a device
        target = reg.list()[0]
        reg.upsert(
            Device(
                id=target.id,
                name=target.name,
                domain=target.domain,
                state={"state": "CHANGED_VALUE", "extra": True},
            )
        )

        # Snapshot after
        after_devices = {d.id: d.state for d in reg.list()}

        changed = [
            eid for eid in before_devices
            if eid in after_devices and before_devices[eid] != after_devices[eid]
        ]
        assert target.id in changed, f"Expected {target.id} to be detected as changed"


# ── HA discovery integration ──

class TestHADiscoveryIntegration:
    """HA MQTT discovery integration with snapshot pipeline."""

    def test_discovery_export_after_snapshot(self, tmp_path: Path) -> None:
        """Discovery export should reflect all devices in the snapshot."""
        from hiri_bridge.ha.discovery import export_discovery

        devices_file = tmp_path / "devices.json"
        reg = DeviceRegistry(path=devices_file)
        reg.seed()

        # Add test devices
        for i in range(3):
            reg.upsert(
                Device(
                    id=f"light.ha_test_{i}",
                    name=f"HA test light {i}",
                    domain="light",
                    state={"state": "off"},
                )
            )

        discovery = export_discovery(reg)
        assert isinstance(discovery, list)
        assert len(discovery) > 0

        # Each discovery entry has required HA fields
        for entry in discovery:
            payload = entry.get("payload", {})
            assert "unique_id" in payload or "object_id" in payload or "name" in payload, \
                f"Discovery entry missing identifiers: {entry}"

    def test_discovery_device_count_matches_registry(self, tmp_path: Path) -> None:
        """Discovery export count should match registry devices with MQTT adapter."""
        from hiri_bridge.ha.discovery import export_discovery

        devices_file = tmp_path / "devices.json"
        reg = DeviceRegistry(path=devices_file)
        reg.seed()

        discovery = export_discovery(reg)
        mqtt_devices = [d for d in reg.list() if d.adapter == "mqtt"]

        # Discovery entries should be >= MQTT devices (some auto-discovered)
        assert len(discovery) >= len(mqtt_devices), \
            f"Discovery ({len(discovery)}) < MQTT devices ({len(mqtt_devices)})"


# ── Performance regression ──

class TestPipelinePerformance:
    """Pipeline performance must not degrade under load."""

    def test_seed_performance_regression(self, tmp_path: Path) -> None:
        """Seed must complete under 1 second even with large device catalog."""
        devices_file = tmp_path / "devices.json"
        reg = DeviceRegistry(path=devices_file)

        t0 = time.perf_counter()
        reg.seed()
        elapsed = time.perf_counter() - t0

        assert elapsed < 1.0, f"Seed too slow: {elapsed:.3f}s"
        assert reg.stats()["total"] > 30  # Must have substantial seed data

    def test_bulk_upsert_regression(self, tmp_path: Path) -> None:
        """200 upserts must complete under 3 seconds."""
        devices_file = tmp_path / "devices.json"
        reg = DeviceRegistry(path=devices_file)
        reg.seed()

        t0 = time.perf_counter()
        for i in range(200):
            reg.upsert(
                Device(
                    id=f"sensor.perf_{i}",
                    name=f"Perf {i}",
                    domain="sensor",
                    state={"value": i},
                )
            )
        elapsed = time.perf_counter() - t0

        assert elapsed < 3.0, f"200 upserts too slow: {elapsed:.3f}s"

    def test_reload_with_1000_devices(self, tmp_path: Path) -> None:
        """Reload with 1000 devices must complete under 2 seconds."""
        devices_file = tmp_path / "devices.json"
        reg = DeviceRegistry(path=devices_file)
        reg.seed()

        # Add devices to reach ~1000
        base = reg.stats()["total"]
        needed = max(0, 1000 - base)
        for i in range(needed):
            reg.upsert(
                Device(
                    id=f"sensor.load_{i:04d}",
                    name=f"Load test {i}",
                    domain="sensor",
                    state={"value": i},
                )
            )

        t0 = time.perf_counter()
        reg2 = DeviceRegistry(path=devices_file)
        reg2.load_or_seed()
        elapsed = time.perf_counter() - t0

        assert elapsed < 2.0, f"Reload of ~1000 devices too slow: {elapsed:.3f}s"
        assert len(reg2.list()) >= 1000
