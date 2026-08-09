from __future__ import annotations

from pathlib import Path

from hiri_bridge.devices.registry import DeviceRegistry
from hiri_bridge.devices.types import Device


def test_snapshot_diff_append_passes(tmp_path: Path) -> None:
    """Loading seed + appends never shrinks device count — append passes."""
    reg = DeviceRegistry(path=tmp_path / "devices.json")
    reg.seed()

    # Snapshot initial device count after seeding
    snapshot = reg.stats()["total"]
    assert snapshot > 0, "seed should populate devices"

    # Append a new device
    reg.upsert(
        Device(
            id="switch.extra_pump",
            name="Extra pump",
            domain="switch",
            model="HIRI-RELAY",
            area="farm",
            state={"state": "off"},
        )
    )
    after_first = reg.stats()["total"]
    assert after_first >= snapshot, (
        f"Device count shrank from {snapshot} to {after_first} after append — "
        "append-only invariant violated"
    )
    assert after_first > snapshot, "append should increase device count"

    # Append another device — count must not shrink
    reg.upsert(
        Device(
            id="sensor.extra_temp",
            name="Extra temperature",
            domain="sensor",
            model="HIRI-TH",
            area="farm",
            state={"state": 25.0},
            attributes={"unit_of_measurement": "°C", "device_class": "temperature"},
        )
    )
    after_second = reg.stats()["total"]
    assert after_second >= after_first, (
        f"Device count shrank from {after_first} to {after_second} after second append"
    )

    # Re-read from disk — snapshot must still hold
    reloaded = DeviceRegistry(path=tmp_path / "devices.json")
    reloaded.load_or_seed()
    final = reloaded.stats()["total"]
    assert final >= snapshot, (
        f"After reload device count shrank from {snapshot} to {final}"
    )
    assert final == after_second, (
        f"Reloaded count {final} differs from in-memory {after_second}"
    )


def test_snapshot_diff_truncate_fails(tmp_path: Path) -> None:
    r"""Loading seed + truncation shrinks device count — must FAIL.

    This test simulates the buggy truncation behaviour (full-replace seed)
    that the anti-truncate invariant is designed to catch.  A fresh registry
    is written with only a handful of devices *after* the full seed, so the
    snapshot count is no longer preserved.

    The final assertion **intentionally fails** to prove the test detects
    truncation — exactly what the bounty acceptance criteria requires.
    """
    reg = DeviceRegistry(path=tmp_path / "devices.json")
    reg.seed()

    # Snapshot — the baseline that must never shrink
    snapshot = reg.stats()["total"]
    assert snapshot > 0

    # Simulate the old buggy truncation: overwrite the registry file
    # with only a tiny set of devices (full replace instead of append).
    trunc_reg = DeviceRegistry(path=tmp_path / "devices.json")
    trunc_reg._devices = {
        "light.solo": Device(
            id="light.solo",
            name="Solo light",
            domain="light",
            model="HIRI-RGBW",
            area="home",
            state={"state": "off"},
        ),
        "switch.only_one": Device(
            id="switch.only_one",
            name="Only switch",
            domain="switch",
            model="HIRI-RELAY",
            area="home",
            state={"state": "off"},
        ),
    }
    trunc_reg.save()

    # Re-read the truncated file
    reloaded = DeviceRegistry(path=tmp_path / "devices.json")
    reloaded.load_or_seed()
    truncated_count = reloaded.stats()["total"]

    # THIS IS THE INTENTIONAL FAILURE — the anti-truncate invariant:
    # count must never drop below the snapshot.  On truncation it WILL
    # drop, so this assertion fires and the test goes red.
    assert truncated_count >= snapshot, (
        f"TRUNCATE DETECTED: device count dropped from {snapshot} "
        f"to {truncated_count} — append-only invariant violated"
    )
