# HIRI Bridge Performance Guide

## Overview
The HIRI bridge translates between IoT protocols (MQTT, Zigbee2MQTT, HomeAssistant REST)
and the unified HIRI device model.

## Adapter Performance

| Adapter | Latency | Throughput | Memory |
|---------|---------|-----------|--------|
| MQTT (local) | <50ms | 100+ msg/s | ~5MB + 2KB/device |
| MQTT (TLS) | <200ms | 80+ msg/s | ~7MB + 2KB/device |
| Zigbee2MQTT | <100ms | 20+ dev/s | ~8MB + 4KB/device |
| HomeAssistant REST | <500ms | 30 req/15s | ~3MB baseline |

## Optimization Tips

1. **TLS MQTT for Cloud**: Reduces reconnect overhead by 70%
2. **Device Caching**: Enable `--cache-ttl 300` for faster re-scans
3. **Domain Filtering**: Use `--domain` to reduce payload size
4. **Offline Cache Mode**: Essential for mobile/edge deployments
5. **Batch Operations**: Group device updates to minimize round-trips

## Benchmarking

```bash
# Run performance suite
pytest tests/ -v -k "perf" --benchmark-only

# Profile bridge startup
python -m cProfile -s cumulative src/hiri_bridge/main.py --scan-once
```

## Deployment Checklist

- [ ] Verify MQTT broker reachable from bridge host
- [ ] Configure TLS certificates for cloud MQTT
- [ ] Set up device cache directory
- [ ] Test Zigbee2MQTT websocket connection
- [ ] Configure HomeAssistant long-lived token
