from hiri_bridge.devices.types import Device
from hiri_bridge.sensors.sim import dht22_reading, soil_moisture_reading, tick_farm_sensors


def test_dht22_bounds() -> None:
    r = dht22_reading(seed=1.0, t=1_000_000.0)
    assert 10 <= r["temperature_c"] <= 40
    assert 20 <= r["humidity_pct"] <= 95


def test_soil_and_tick() -> None:
    r = soil_moisture_reading(seed=2.0, t=1_000_000.0)
    assert 5 <= r["moisture_pct"] <= 95
    dev = Device(
        id="sensor.soil_moisture_1",
        name="Soil",
        domain="sensor",
        model="HIRI-SOIL",
        state={"state": 0},
    )
    updated = tick_farm_sensors([dev])
    assert updated
    assert dev.state["state"] > 0
