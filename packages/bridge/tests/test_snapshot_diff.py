"""Demo snapshot diff tests: seed + append never shrinks device count (anti-truncate)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from hiri_bridge.devices.registry import DeviceRegistry
from hiri_bridge.devices.types import Device


def _device_count_from_file(path: Path) -> int:
    """Count devices from a registry file."""
    if not path.exists():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "devices" in data:
        return len(data["devices"])
    if isinstance(data, dict):
        # Could be {device_id: device_dict} or {"device_id": ..., "devices": [...]}
        return len(data) if all(isinstance(v, dict) for v in data.values()) else 0
    if isinstance(data, list):
        return len(data)
    return 0


class TestSnapshotDiff:
    """Seed + append never shrinks device count."""

    def test_seed_then_append_count_grows(self, tmp_path: Path) -> None:
        """After seed + registering new devices, count must be >= seed count."""
        devices_file = tmp_path / "devices.json"
        reg = DeviceRegistry(path=devices_file)
        reg.seed()
        seed_count = reg.stats()["total"]
        assert seed_count > 0, "Seed should produce devices"

        # Append new devices
        reg.upsert(
            Device(
                id="sensor.boots_test_a",
                name="Snapshot test sensor A",
                domain="sensor",
                state={"state": 25.0},
                attributes={"unit_of_measurement": "°C"},
            )
        )
        reg.upsert(
            Device(
                id="switch.boots_test_b",
                name="Snapshot test switch B",
                domain="switch",
                state={"state": "off"},
            )
        )

        after_count = reg.stats()["total"]
        assert after_count >= seed_count + 2, (
            f"Expected ≥ {seed_count + 2} devices after 2 appends, got {after_count}"
        )

    def test_seed_then_append_from_devices_dir(self, tmp_path: Path) -> None:
        """Loading seed + device JSON files never shrinks the count."""
        devices_file = tmp_path / "devices.json"
        reg = DeviceRegistry(path=devices_file)
        reg.seed()
        seed_count = reg.stats()["total"]

        # Simulate appending device packs from devices/ directory
        extra_devices = [
            (f"sensor.snapshot_extra_{i}", {
                "id": f"sensor.snapshot_extra_{i}",
                "name": f"Snapshot extra {i}",
                "domain": "sensor",
                "state": {"state": float(i)},
            })
            for i in range(5)
        ]

        for device_id, device_data in extra_devices:
            reg.upsert(
                Device(
                    id=device_id,
                    name=device_data["name"],
                    domain=device_data["domain"],
                    state=device_data["state"],
                )
            )

        after_count = reg.stats()["total"]
        assert after_count == seed_count + 5, (
            f"Expected {seed_count + 5} devices, got {after_count}"
        )

    def test_reloading_preserves_count(self, tmp_path: Path) -> None:
        """Reloading the registry from disk preserves device count."""
        devices_file = tmp_path / "devices.json"
        reg1 = DeviceRegistry(path=devices_file)
        reg1.seed()
        reg1.upsert(
            Device(id="sensor.reload_test", name="Reload test", domain="sensor", state={"state": 42.0})
        )
        count1 = reg1.stats()["total"]

        # Reload from same file
        reg2 = DeviceRegistry(path=devices_file)
        reg2.load_or_seed()
        count2 = len(reg2.list())

        assert count2 >= count1, (
            f"Reloaded count {count2} < original {count1} — anti-truncate violated"
        )

    def test_multiple_sequential_appends(self, tmp_path: Path) -> None:
        """Each append strictly increases or maintains device count."""
        devices_file = tmp_path / "devices.json"
        reg = DeviceRegistry(path=devices_file)
        reg.seed()
        prev_count = reg.stats()["total"]

        for i in range(3):
            reg.upsert(
                Device(
                    id=f"sensor.seq_{i}",
                    name=f"Seq device {i}",
                    domain="sensor",
                    state={"state": float(i)},
                )
            )
            new_count = reg.stats()["total"]
            assert new_count > prev_count, (
                f"Append {i}: count went from {prev_count} to {new_count} — must grow"
            )
            prev_count = new_count


class TestAntiTruncate:
    """Detect truncation scenarios — test should FAIL if devices are lost."""

    def test_seed_idempotent(self, tmp_path: Path) -> None:
        """Calling seed() twice does not lose devices."""
        devices_file = tmp_path / "devices.json"
        reg = DeviceRegistry(path=devices_file)

        # First seed
        reg.seed()
        count1 = reg.stats()["total"]

        # Second seed should not shrink
        reg.seed()
        count2 = reg.stats()["total"]
        assert count2 >= count1, (
            f"Second seed() shrunk from {count1} to {count2}"
        )

    def test_register_existing_replaces_not_shrinks(self, tmp_path: Path) -> None:
        """Registering an existing device ID updates it, doesn't change total count."""
        devices_file = tmp_path / "devices.json"
        reg = DeviceRegistry(path=devices_file)
        reg.seed()
        count_before = reg.stats()["total"]

        # Register same ID with different state
        reg.upsert(
            Device(
                id="light.living_main",
                name="Updated light",
                domain="light",
                state={"state": "on", "brightness": 255},
            )
        )
        count_after = reg.stats()["total"]

        assert count_after >= count_before, (
            f"Re-registering existing device shrunk count: {count_before} → {count_after}"
        )

    @pytest.mark.skip(reason="Demostrates anti-truncate detection — this SHOULD fail")
    def test_detect_truncation(self, tmp_path: Path) -> None:
        """Demonstrate that a truncating write is detected.

        This test represents the BAD pattern that the append-only policy prevents.
        It demonstrates the anti-truncate invariant by showing that if someone
        writes only a single device (replacing the file), the following load
        would detect the loss.
        """
        devices_file = tmp_path / "devices.json"
        reg = DeviceRegistry(path=devices_file)
        reg.seed()
        original_count = reg.stats()["total"]

        # Simulate a BAD truncating write
        devices_file.write_text(json.dumps({
            "devices": [{"id": "light.single", "name": "Only one", "domain": "light"}]
        }))

        # Reload — should detect the loss
        reg2 = DeviceRegistry(path=devices_file)
        reg2.load()
        new_count = len(reg2.list())

        # This assertion should fail: new_count (1) < original_count (~40)
        assert new_count >= original_count, (
            f"TRUNCATION DETECTED: {original_count} → {new_count} devices"
        )
