# HIRI-bridge

Runnable Home Assistant–oriented bridge with a broad device type registry.

```bash
pip install -e ".[dev,api]"
hiri-bridge demo
hiri-bridge serve --port 8780
```

## Benchmark Results

| Test | Operations | Time | Throughput |
|------|-----------|------|------------|
| snapshot_throughput | 1000 upserts | <2.0s | >500 ops/s |
| concurrent_writers | 5 × 200 upserts | <3.0s | parallel-safe |
| large_payload | 100KB roundtrip | <0.5s | no truncation |
| bulk_import_export | 500 entities | <1.5s | JSON roundtrip |
| domain_isolation | 10 × 50 entities | <2.0s | 500 total |

## Test Coverage

- **93 tests** across snapshot, bridge, and benchmark suites
- Regression: domain upsert, concurrent access, malformed JSON
- Performance: throughput, concurrency, large payloads
- Correctness: diff detection, merge, timestamp ordering, stats accuracy
