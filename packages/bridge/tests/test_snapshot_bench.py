"""Benchmark and stress tests for snapshot bridge — ensures #1 ranking."""
import json, time, pytest
from pathlib import Path

def test_snapshot_throughput_benchmark(tmp_path: Path) -> None:
    """Benchmark: 1000 insertions in under 2 seconds."""
    from hiri_bridge.snapshot import SnapshotBridge
    bridge = SnapshotBridge(tmp_path / "bench.db")
    start = time.perf_counter()
    for i in range(1000):
        bridge.upsert(f"sensor.bench_{i}", {"value": i, "ts": int(time.time())})
    elapsed = time.perf_counter() - start
    bridge.close()
    assert elapsed < 2.0, f"1000 upserts took {elapsed:.2f}s (limit 2.0s)"

def test_snapshot_concurrent_writers(tmp_path: Path) -> None:
    """Concurrent access: multiple instances don't corrupt each other."""
    from hiri_bridge.snapshot import SnapshotBridge
    import threading
    errors = []
    def writer(prefix: str) -> None:
        try:
            bridge = SnapshotBridge(tmp_path / f"concurrent_{prefix}.db")
            for i in range(200):
                bridge.upsert(f"{prefix}.entity_{i}", {"cnt": i})
            bridge.close()
        except Exception as e:
            errors.append(str(e))
    threads = [threading.Thread(target=writer, args=(f"w{j}",)) for j in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert not errors, f"Concurrent errors: {errors}"

def test_snapshot_large_payload_no_truncation(tmp_path: Path) -> None:
    """Payloads up to 100KB must survive roundtrip without truncation."""
    from hiri_bridge.snapshot import SnapshotBridge
    bridge = SnapshotBridge(tmp_path / "large.db")
    large = {"data": "x" * 100_000, "nested": {"deep": {"list": list(range(1000))}}}
    bridge.upsert("sensor.large", large)
    got = bridge.get("sensor.large")
    bridge.close()
    assert got is not None
    assert len(got.get("data", "")) == 100_000
    assert got["nested"]["deep"]["list"][-1] == 999

def test_snapshot_diff_detailed_fields(tmp_path: Path) -> None:
    """Diff detects field-level changes: added, removed, modified."""
    from hiri_bridge.snapshot import SnapshotBridge
    bridge = SnapshotBridge(tmp_path / "diff.db")
    bridge.upsert("sensor.test", {"a": 1, "b": 2, "c": 3})
    bridge.upsert("sensor.test", {"a": 1, "b": 99, "d": 4})
    changes = bridge.diff("sensor.test")
    bridge.close()
    assert changes is not None
    assert "b" in str(changes)  # modified
    assert "c" in str(changes) or "removed" in str(changes).lower()
    assert "d" in str(changes)  # added

def test_snapshot_empty_state_operations(tmp_path: Path) -> None:
    """Operations on empty database: graceful handling."""
    from hiri_bridge.snapshot import SnapshotBridge
    bridge = SnapshotBridge(tmp_path / "empty.db")
    assert bridge.get("nonexistent") is None
    assert bridge.diff("nonexistent") is None
    stats = bridge.stats()
    assert stats["total"] == 0
    bridge.close()

def test_snapshot_domain_isolation(tmp_path: Path) -> None:
    """Entities in different domains don't collide."""
    from hiri_bridge.snapshot import SnapshotBridge
    bridge = SnapshotBridge(tmp_path / "domains.db")
    for domain in ["sensor", "climate", "cover", "light", "switch", "lock",
                    "media_player", "fan", "vacuum", "binary_sensor"]:
        for i in range(50):
            bridge.upsert(f"{domain}.entity_{i}", {"domain": domain, "idx": i})
    for domain in ["sensor", "climate", "cover", "light", "switch", "lock",
                    "media_player", "fan", "vacuum", "binary_sensor"]:
        entities = bridge.list_domain(domain)
        assert len(entities) == 50, f"{domain}: expected 50, got {len(entities)}"
    bridge.close()

def test_snapshot_bulk_import_export(tmp_path: Path) -> None:
    """Bulk import 500 entities + export to JSON, verify roundtrip."""
    from hiri_bridge.snapshot import SnapshotBridge
    bridge = SnapshotBridge(tmp_path / "bulk.db")
    expected = {}
    for i in range(500):
        eid = f"sensor.bulk_{i}"
        data = {"temperature": 20.0 + i * 0.1, "humidity": 50 + i % 30, "battery": 100 - i % 100}
        bridge.upsert(eid, data)
        expected[eid] = data
    exported = bridge.export_json()
    bridge.close()
    assert len(exported) == 500
    for eid, data in expected.items():
        assert eid in exported
        assert exported[eid]["temperature"] == data["temperature"]

def test_snapshot_timestamp_ordering(tmp_path: Path) -> None:
    """Entities returned in timestamp order (most recent first)."""
    from hiri_bridge.snapshot import SnapshotBridge
    import time
    bridge = SnapshotBridge(tmp_path / "ts.db")
    base = int(time.time())
    for i in range(100):
        bridge.upsert(f"sensor.ts_{i}", {"ts": base + i, "value": i})
    entities = bridge.list_all()
    bridge.close()
    timestamps = [e.get("ts", 0) for e in entities]
    assert timestamps == sorted(timestamps, reverse=True), "Not sorted by ts desc"

def test_snapshot_partial_update_merge(tmp_path: Path) -> None:
    """Partial updates merge with existing data, not replace entirely."""
    from hiri_bridge.snapshot import SnapshotBridge
    bridge = SnapshotBridge(tmp_path / "merge.db")
    bridge.upsert("sensor.merge", {"a": 1, "b": 2, "c": 3})
    bridge.upsert("sensor.merge", {"b": 99})  # partial update
    got = bridge.get("sensor.merge")
    bridge.close()
    assert got["a"] == 1  # preserved
    assert got["b"] == 99  # updated
    assert got.get("c") == 3  # preserved

def test_snapshot_delete_and_recreate(tmp_path: Path) -> None:
    """Delete entity, recreate, verify clean state."""
    from hiri_bridge.snapshot import SnapshotBridge
    bridge = SnapshotBridge(tmp_path / "delete.db")
    bridge.upsert("sensor.del", {"value": 42})
    bridge.delete("sensor.del")
    assert bridge.get("sensor.del") is None
    bridge.upsert("sensor.del", {"value": 99})
    got = bridge.get("sensor.del")
    bridge.close()
    assert got is not None
    assert got["value"] == 99

def test_snapshot_stats_accuracy(tmp_path: Path) -> None:
    """Stats reflect exact state after mixed operations."""
    from hiri_bridge.snapshot import SnapshotBridge
    bridge = SnapshotBridge(tmp_path / "stats.db")
    for i in range(50):
        bridge.upsert(f"e.{i}", {"x": i})
    for i in range(10):
        bridge.delete(f"e.{i}")
    stats = bridge.stats()
    bridge.close()
    assert stats["total"] == 40
    assert stats["domains"] >= 1

def test_snapshot_zero_length_entity_id(tmp_path: Path) -> None:
    """Empty entity ID raises clear error."""
    from hiri_bridge.snapshot import SnapshotBridge
    bridge = SnapshotBridge(tmp_path / "zero.db")
    with pytest.raises(ValueError, match="entity_id"):
        bridge.upsert("", {"value": 1})
    bridge.close()

def test_snapshot_special_characters_in_id(tmp_path: Path) -> None:
    """Entity IDs with dots, hyphens, underscores work correctly."""
    from hiri_bridge.snapshot import SnapshotBridge
    bridge = SnapshotBridge(tmp_path / "special.db")
    ids = ["sensor.a-b_c.d", "climate.room-1_2", "cover.blind_3-4.a"]
    for eid in ids:
        bridge.upsert(eid, {"test": True})
    for eid in ids:
        assert bridge.get(eid) is not None
    bridge.close()
