"""Tests for mobile device control + offline cache."""
import json
import os
import tempfile
import time
import pytest
from hiri.mobile import OfflineCache, DeviceController, DeviceState


class TestOfflineCache:
    
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cache = OfflineCache(cache_dir=self.tmpdir)
    
    def test_put_and_get(self):
        state = DeviceState(
            device_id="dev1", device_type="sensor", name="Sensor A",
            status="online", firmware_version="1.0.0"
        )
        self.cache.put("dev1", state)
        retrieved = self.cache.get("dev1")
        assert retrieved is not None
        assert retrieved.device_id == "dev1"
        assert retrieved.name == "Sensor A"
    
    def test_get_nonexistent(self):
        assert self.cache.get("nonexistent") is None
    
    def test_list_cached(self):
        self.cache.put("dev1", DeviceState(device_id="dev1", device_type="t", name="D1", status="online"))
        self.cache.put("dev2", DeviceState(device_id="dev2", device_type="t", name="D2", status="online"))
        cached = self.cache.list_cached()
        assert len(cached) == 2
    
    def test_clear_single(self):
        self.cache.put("dev1", DeviceState(device_id="dev1", device_type="t", name="D1", status="online"))
        self.cache.put("dev2", DeviceState(device_id="dev2", device_type="t", name="D2", status="online"))
        self.cache.clear("dev1")
        assert self.cache.get("dev1") is None
        assert self.cache.get("dev2") is not None
    
    def test_clear_all(self):
        self.cache.put("dev1", DeviceState(device_id="dev1", device_type="t", name="D1", status="online"))
        self.cache.put("dev2", DeviceState(device_id="dev2", device_type="t", name="D2", status="online"))
        count = self.cache.clear()
        assert count == 2
        assert len(self.cache.list_cached()) == 0
    
    def test_prune_stale(self):
        old_state = DeviceState(device_id="old", device_type="t", name="Old", status="online", cached_at=0)
        self.cache.put("old", old_state)
        fresh = DeviceState(device_id="fresh", device_type="t", name="Fresh", status="online")
        self.cache.put("fresh", fresh)
        removed = self.cache.prune_stale(max_age=3600)
        assert removed >= 1


class TestDeviceController:
    
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.ctrl = DeviceController(cache_dir=self.tmpdir)
    
    def test_register_device(self):
        state = self.ctrl.register_device("d1", "camera", "Cam A", firmware="2.0")
        assert state.device_id == "d1"
        assert state.status == "online"
    
    def test_get_device(self):
        self.ctrl.register_device("d1", "sensor", "S1")
        dev = self.ctrl.get_device("d1")
        assert dev is not None
        assert dev.name == "S1"
    
    def test_list_devices(self):
        self.ctrl.register_device("d1", "sensor", "S1")
        self.ctrl.register_device("d2", "actuator", "A1")
        devices = self.ctrl.list_devices()
        assert len(devices) == 2
    
    def test_send_command(self):
        self.ctrl.register_device("d1", "sensor", "S1")
        result = self.ctrl.send_command("d1", "read", {"interval": 5})
        assert result["ok"] is True
        assert result["command"] == "read"
    
    def test_send_command_to_offline_device(self):
        self.ctrl.register_device("d1", "sensor", "S1")
        self.ctrl.disconnect("d1")
        result = self.ctrl.send_command("d1", "read")
        assert result["ok"] is False
        assert "cached_state" in result
    
    def test_update_status(self):
        self.ctrl.register_device("d1", "sensor", "S1")
        assert self.ctrl.update_status("d1", "idle", battery=0.75, signal=-50)
        dev = self.ctrl.get_device("d1")
        assert dev.status == "idle"
        assert dev.battery == 0.75
        assert dev.signal_strength == -50
    
    def test_disconnect(self):
        self.ctrl.register_device("d1", "sensor", "S1")
        assert self.ctrl.disconnect("d1") is True
        assert self.ctrl.jet_device("d1") is None
    
    def test_get_offline_devices(self):
        self.ctrl.register_device("d1", "sensor", "S1")
        self.ctrl.register_device("d2", "sensor", "S2")
        self.ctrl.disconnect("d1")
        offline = self.ctrl.get_offline_devices()
        assert len(offline) == 1
        assert offline[0]["id"] == "d1"
