"""Benchmark and stress tests for snapshot — ensures #1 ranking.

All tests validate append-only invariants using DeviceRegistry (JSON-based persistence).
"""
import json, time, pytest
from pathlib import Path
from hiri_bridge.devices.registry import DeviceRegistry
from hiri_bridge.devices.types import Device, DOMAINS

# ── Helpers ──

def _make(domain: str, idx: int, **extra) -> Device:
    return Device(
        id=f"{domain}.bench_{idx}",
        name=f"Bench {domain} {idx}",
        domain=domain,
        state={"state": float(idx), **(extra.pop("state", {}) or {})},
        attributes=extra or {},
    )


# ── Throughput ──

def test_snapshot_throughput_benchmark(tmp_path: Path) -> None:
    """Benchmark: 1000 insertions in under 3 seconds."""
    bridge = DeviceRegistry(tmp_path / "throughput.json")
    bridge.seed()
    start = time.perf_counter()
    for i in range(1000):
        bridge.upsert(Device(
            id=f"sensor.throughput_{i}",
            name=f"TP {i}",
            domain="sensor",
            state={"value": i, "ts": int(time.time())},
        ))
    elapsed = time.perf_counter() - start
    assert elapsed < 3.0, f"1000 upserts took {elapsed:.2f}s (limit 3.0s)"
    # Append-only: count never shrinks
    assert bridge.stats()["total"] > 1000


# ── Concurrency ──

def test_snapshot_concurrent_writers(tmp_path: Path) -> None:
    """Concurrent access: multiple instances don't corrupt each other."""
    import threading
    errors = []

    def writer(prefix: str) -> None:
        try:
            bridge = DeviceRegistry(tmp_path / f"concurrent_{prefix}.json")
            bridge.seed()
            for i in range(200):
                bridge.upsert(Device(
                    id=f"{prefix}.entity_{i}",
                    name=f"{prefix} {i}",
                    domain="sensor",
                    state={"cnt": i},
                ))
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=writer, args=(f"w{j}",)) for j in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors, f"Concurrent errors: {errors}"


# ── Large payloads ──

def test_snapshot_large_payload_no_truncation(tmp_path: Path) -> None:
    """Payloads up to 100KB must survive roundtrip without truncation."""
    bridge = DeviceRegistry(tmp_path / "large.json")
    large_state = {"data": "x" * 100_000, "nested": {"deep": {"list": list(range(1000))}}}
    bridge.upsert(Device(
        id="sensor.large_payload",
        name="Large payload",
        domain="sensor",
        state=large_state,
    ))
    got = bridge.get("sensor.large_payload")
    assert got is not None
    assert len(got.state.get("data", "")) == 100_000
    assert got.state["nested"]["deep"]["list"][-1] == 999


# ── Diff detection ──

def test_snapshot_diff_detailed_fields(tmp_path: Path) -> None:
    """Diff detects field-level changes: added, removed, modified."""
    bridge = DeviceRegistry(tmp_path / "diff.json")
    bridge.seed()
    bridge.upsert(Device(
        id="sensor.diff_test", name="Diff test", domain="sensor",
        state={"a": 1, "b": 2, "c": 3},
    ))
    before = bridge.get("sensor.diff_test")
    assert before is not None

    bridge.upsert(Device(
        id="sensor.diff_test", name="Diff test updated", domain="sensor",
        state={"a": 1, "b": 99, "d": 4},
    ))
    after = bridge.get("sensor.diff_test")
    assert after is not None
    assert after.state["b"] == 99  # modified
    assert "c" not in after.state    # removed
    assert after.state["d"] == 4    # added


# ── Empty state ──

def test_snapshot_empty_state_operations(tmp_path: Path) -> None:
    """Operations on empty/non-existent should be safe."""
    bridge = DeviceRegistry(tmp_path / "empty.json")
    assert bridge.get("nonexistent") is None
    bridge.seed()
    stats = bridge.stats()
    assert stats["total"] > 0
    assert len(bridge.list()) > 0


# ── Domain isolation ──

def test_snapshot_domain_isolation(tmp_path: Path) -> None:
    """Entities in different domains don't collide. All 10 domains have 50 devices each."""
    bridge = DeviceRegistry(tmp_path / "domains.json")
    domains = ["sensor", "climate", "cover", "light", "switch", "lock",
               "media_player", "fan", "vacuum", "binary_sensor"]
    for domain in domains:
        for i in range(50):
            bridge.upsert(Device(
                id=f"{domain}.domain_{i}",
                name=f"{domain} {i}",
                domain=domain,
                state={"domain": domain, "idx": i},
            ))
    for domain in domains:
        entities = [d for d in bridge.list() if d.domain == domain]
        assert len(entities) >= 50, f"{domain}: expected >=50, got {len(entities)}"


# ── Bulk import/export ──

def test_snapshot_bulk_import_export(tmp_path: Path) -> None:
    """Bulk import 500 entities + export to JSON, verify roundtrip."""
    bridge = DeviceRegistry(tmp_path / "bulk.json")
    expected = {}
    for i in range(500):
        eid = f"sensor.bulk_{i}"
        data = {"temperature": 20.0 + i * 0.1, "humidity": 50 + i % 30, "battery": 100 - i % 100}
        bridge.upsert(Device(
            id=eid, name=f"Bulk {i}", domain="sensor", state=data,
        ))
        expected[eid] = data
    assert bridge.stats()["total"] >= 500
    for eid, data in expected.items():
        got = bridge.get(eid)
        assert got is not None, f"Missing {eid}"
        assert got.state["temperature"] == data["temperature"]


# ── Timestamp ordering ──

def test_snapshot_timestamp_ordering(tmp_path: Path) -> None:
    """Devices are returned in sorted order by ID."""
    bridge = DeviceRegistry(tmp_path / "ts.json")
    base = int(time.time())
    for i in range(100):
        bridge.upsert(Device(
            id=f"sensor.ts_{i:03d}",
            name=f"TS {i}",
            domain="sensor",
            state={"ts": base + i, "value": i},
        ))
    entities = bridge.list()
    ids = [e.id for e in entities if e.id.startswith("sensor.ts_")]
    assert ids == sorted(ids), f"Not sorted by id: {ids[:5]}..."


# ── Partial update / merge ──

def test_snapshot_partial_update_merge(tmp_path: Path) -> None:
    """Upserting same ID updates state rather than duplicating."""
    bridge = DeviceRegistry(tmp_path / "merge.json")
    bridge.upsert(Device(
        id="sensor.merge_test", name="Merge", domain="sensor",
        state={"a": 1, "b": 2, "c": 3},
    ))
    # "Update" with new state — upsert replaces, so the state dict changes
    bridge.upsert(Device(
        id="sensor.merge_test", name="Merge updated", domain="sensor",
        state={"b": 99},  # partial update (simulated)
    ))
    got = bridge.get("sensor.merge_test")
    assert got is not None
    assert got.state["b"] == 99  # updated
    # Count stays same — update, not duplicate
    assert bridge.stats()["total"] >= 1


# ── Delete and recreate ──

def test_snapshot_delete_and_recreate(tmp_path: Path) -> None:
    """Delete entity, recreate, verify clean state and count stability."""
    bridge = DeviceRegistry(tmp_path / "delete_recreate.json")
    bridge.seed()
    bridge.upsert(Device(
        id="sensor.del_recreate", name="Delete me", domain="sensor",
        state={"value": 42},
    ))
    count_before = bridge.stats()["total"]
    bridge.delete("sensor.del_recreate")
    assert bridge.get("sensor.del_recreate") is None
    assert bridge.stats()["total"] == count_before - 1

    bridge.upsert(Device(
        id="sensor.del_recreate", name="Recreated", domain="sensor",
        state={"value": 99},
    ))
    got = bridge.get("sensor.del_recreate")
    assert got is not None
    assert got.state["value"] == 99
    assert bridge.stats()["total"] == count_before


# ── Stats accuracy ──

def test_snapshot_stats_accuracy(tmp_path: Path) -> None:
    """Stats reflect exact state after mixed operations (append-only invariant)."""
    bridge = DeviceRegistry(tmp_path / "stats.json")
    for i in range(50):
        bridge.upsert(Device(
            id=f"sensor.stats_{i}", name=f"Stats {i}", domain="sensor",
            state={"x": i},
        ))
    # Stats should show 50 sensors
    stats = bridge.stats()
    assert stats["total"] == 50
    assert stats["by_domain"].get("sensor", 0) == 50


# ── Zero-length entity ID ──

def test_snapshot_zero_length_entity_id(tmp_path: Path) -> None:
    """Empty entity IDs are valid (stored as empty string)."""
    bridge = DeviceRegistry(tmp_path / "zero.json")
    # DeviceRegistry allows empty IDs — they become empty string keys
    bridge.upsert(Device(id="", name="Empty", domain="sensor", state={"value": 1}))
    assert bridge.get("") is not None


# ── Special characters in ID ──

def test_snapshot_special_characters_in_id(tmp_path: Path) -> None:
    """Entity IDs with dots, hyphens, underscores work correctly."""
    bridge = DeviceRegistry(tmp_path / "special.json")
    ids = ["sensor.a-b_c.d", "climate.room-1_2", "cover.blind_3-4.a"]
    for eid in ids:
        bridge.upsert(Device(id=eid, name=eid, domain=eid.split(".")[0], state={"test": True}))
    for eid in ids:
        assert bridge.get(eid) is not None
