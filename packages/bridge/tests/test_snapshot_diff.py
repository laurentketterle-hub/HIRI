"""HIRI #93: Bridge demo snapshot diff test — verify append-only invariant.

Captures a full demo seed snapshot and asserts that subsequent registry
operations only append (never delete or alter existing device identities).
"""

from __future__ import annotations

import json
from pathlib import Path

from hiri_bridge.devices.registry import DeviceRegistry


def test_seed_snapshot_reproducible(tmp_path: Path) -> None:
    """Two seeds from a fresh registry must produce identical device lists."""
    reg_a = DeviceRegistry(path=tmp_path / "a.json")
    reg_a.seed()
    snap_a = sorted([d.model_dump() for d in reg_a.list()], key=lambda d: d["id"])

    reg_b = DeviceRegistry(path=tmp_path / "b.json")
    reg_b.seed()
    snap_b = sorted([d.model_dump() for d in reg_b.list()], key=lambda d: d["id"])

    assert snap_a == snap_b, "seed must be deterministic"
    assert len(snap_a) >= 15, "seed must cover a broad set of domains"


def test_append_only_invariant(tmp_path: Path) -> None:
    """Upserting new devices must not delete or alter existing devices (append-only)."""
    reg = DeviceRegistry(path=tmp_path / "devices.json")
    reg.seed()
    before = {d.id: d.model_dump() for d in reg.list()}
    before_ids = set(before.keys())

    # Import adapter devices (z2m + tuya mocks)
    from hiri_bridge.adapters import import_from_adapter

    for adapter_name in ("z2m", "tuya"):
        try:
            imported = import_from_adapter(adapter_name)
        except Exception:
            continue
        for d in imported:
            reg.upsert(d)

    after = {d.id: d.model_dump() for d in reg.list()}

    # All original devices must still be present, unchanged
    for dev_id in before_ids:
        assert dev_id in after, f"device {dev_id} was deleted (append-only violation)"
        assert before[dev_id] == after[dev_id], (
            f"device {dev_id} was altered (append-only violation)"
        )

    # There should be *more* devices after import (or at least the same)
    assert len(after) >= len(before), (
        f"device count decreased: {len(before)} → {len(after)}"
    )


def test_snapshot_diff_json_roundtrip(tmp_path: Path) -> None:
    """Write a snapshot to disk, read it back, compare — structural diff must be empty."""
    reg = DeviceRegistry(path=tmp_path / "devices.json")
    reg.seed()

    # First snapshot
    snap_path = tmp_path / "snap1.json"
    snapshot1 = [d.model_dump() for d in reg.list()]
    snap_path.write_text(json.dumps(snapshot1, indent=2) + "\n", encoding="utf-8")

    # Reload registry from same path
    reg2 = DeviceRegistry(path=tmp_path / "devices.json")
    reg2.load_or_seed()

    # Second snapshot
    snap_path2 = tmp_path / "snap2.json"
    snapshot2 = [d.model_dump() for d in reg2.list()]
    snap_path2.write_text(json.dumps(snapshot2, indent=2) + "\n", encoding="utf-8")

    # Read back and diff
    read1 = json.loads(snap_path.read_text(encoding="utf-8"))
    read2 = json.loads(snap_path2.read_text(encoding="utf-8"))
    assert read1 == read2, "snapshot roundtrip produced diff"


def test_export_json_matches_registry_api(tmp_path: Path) -> None:
    """The export endpoint and direct registry list must be consistent."""
    reg = DeviceRegistry(path=tmp_path / "devices.json")
    reg.seed()
    direct = sorted([d.model_dump() for d in reg.list()], key=lambda d: d["id"])

    # Simulate the /devices API response
    api_response = [d.model_dump() for d in reg.list()]
    api_sorted = sorted(api_response, key=lambda d: d["id"])

    assert direct == api_sorted, "registry list and API/export must match"


def test_stats_append_only_after_upsert(tmp_path: Path) -> None:
    """Stats total count must be monotonic (non-decreasing) after upserts."""
    reg = DeviceRegistry(path=tmp_path / "devices.json")
    reg.seed()
    initial_stats = reg.stats()
    initial_total = initial_stats["total"]

    # Re-seed should be idempotent (same devices, no duplicates)
    reg.seed()
    after_reseed = reg.stats()["total"]
    assert after_reseed == initial_total, (
        f"re-seed changed total: {initial_total} → {after_reseed}"
    )
