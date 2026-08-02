# HIRI Architecture

## Component Diagram

```
                  HIRI Bridge
  +-------------+  +----------+  +--------------+
  | MQTT        |  | Zigbee   |  | HomeAssistant|
  | Adapter     |  | 2MQTT    |  | REST Adapter |
  +------+------+  +-----+----+  +-------+------+
         |                |               |
  +------+----------------+---------------+------+
  |            Unified Device Model               |
  +----------------------+------------------------+
                         |
  +----------------------+------------------------+
  |         Export / CLI / Web API                 |
  +-----------------------------------------------+
```

## Adapter Interface

Each adapter implements:
- `scan()` -> Discover devices
- `get_state(device_id)` -> Query state
- `set_state(device_id, state)` -> Control
- `subscribe(callback)` -> Real-time updates

## Extension Points

- **New Adapter**: Implement `AdapterInterface` + register
- **New Export**: Add handler in `exports/`
- **New CLI Command**: Add to `cli.py`
