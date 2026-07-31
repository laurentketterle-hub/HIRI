"""Mobile device control polish + offline cache."""

import json
import time
import hashlib
import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DeviceState:
    """Snapshotted state of a controlled device."""
    device_id: str
    device_type: str
    name: str
    status: str  # online, offline, error
    last_command: str = ""
    last_command_time: float = 0.0
    battery: Optional[float] = None
    signal_strength: Optional[int] = None
    firmware_version: str = ""
    cached_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def age_seconds(self) -> float:
        return time.time() - self.cached_at
    
    @property
    def is_stale(self, max_age: float = 60.0) -> bool:
        return self.age_seconds > max_age
    
    def to_cache_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_cache_dict(cls, data: Dict[str, Any]) -> 'DeviceState':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class OfflineCache:
    """File-based offline cache for device states."""
    
    def __init__(self, cache_dir: str = ".hiri_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, DeviceState] = {}
    
    def _cache_path(self, device_id: str) -> Path:
        safe_id = hashlib.sha256(device_id.encode()).hexdigest()[:16]
        return self.cache_dir / f"device_{safe_id}.json"
    
    def put(self, device_id: str, state: DeviceState) -> None:
        self._memory_cache[device_id] = state
        try:
            with open(self._cache_path(device_id), 'w') as f:
                json.dump(state.to_cache_dict(), f, indent=2)
        except IOError as e:
            logger.warning(f"Failed to write cache for {device_id}: {e}")
    
    def get(self, device_id: str, max_age: float = 60.0) -> Optional[DeviceState]:
        # Check memory first
        if device_id in self._memory_cache:
            cached = self._memory_cache[device_id]
            if not cached.is_stale(max_age):
                return cached
        
        # Check disk
        cache_path = self._cache_path(device_id)
        if cache_path.exists():
            try:
                with open(cache_path) as f:
                    data = json.load(f)
                state = DeviceState.from_cache_dict(data)
                self._memory_cache[device_id] = state
                return state
            except (IOError, json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to read cache for {device_id}: {e}")
        return None
    
    def list_cached(self) -> List[str]:
        """List all cached device IDs."""
        cached = set()
        for f in self.cache_dir.glob("device_*.json"):
            cached.add(f.stem.replace("device_", ""))
        return sorted(cached)
    
    def clear(self, device_id: str = None) -> int:
        """Clear cache. If device_id is None, clear all."""
        count = 0
        if device_id:
            cache_path = self._cache_path(device_id)
            if cache_path.exists():
                cache_path.unlink()
                count = 1
            self._memory_cache.pop(device_id, None)
        else:
            for f in self.cache_dir.glob("device_*.json"):
                f.unlink()
                count += 1
            self._memory_cache.clear()
        return count
    
    def prune_stale(self, max_age: float = 3600.0) -> int:
        """Remove stale cache entries older than max_age seconds."""
        removed = 0
        for device_id in list(self._memory_cache.keys()):
            cached = self._memory_cache[device_id]
            if cached.is_stale(max_age):
                self._memory_cache.pop(device_id, None)
                removed += 1
        return removed


class DeviceController:
    """Mobile device controller with offline cache support."""
    
    def __init__(self, cache_dir: str = ".hiri_cache"):
        self.cache = OfflineCache(cache_dir)
        self._connected_devices: Dict[str, DeviceState] = {}
    
    def register_device(self, device_id: str, device_type: str, name: str,
                        firmware: str = "", metadata: Dict = None) -> DeviceState:
        state = DeviceState(
            device_id=device_id,
            device_type=device_type,
            name=name,
            status="online",
            firmware_version=firmware,
            metadata=metadata or {}
        )
        self._connected_devices[device_id] = state
        self.cache.put(device_id, state)
        return state
    
    def get_device(self, device_id: str) -> Optional[DeviceState]:
        # Check connected devices first
        if device_id in self._connected_devices:
            return self._connected_devices[device_id]
        # Fall back to cache
        return self.cache.get(device_id)
    
    def list_devices(self) -> List[Dict[str, Any]]:
        devices = []
        for state in self._connected_devices.values():
            devices.append({
                "id": state.device_id,
                "name": state.name,
                "type": state.device_type,
                "status": state.status,
                "battery": state.battery,
                "signal": state.signal_strength,
                "age": state.age_seconds,
            })
        return devices
    
    def send_command(self, device_id: str, command: str, params: Dict = None) -> Dict[str, Any]:
        if device_id not in self._connected_devices:
            cached = self.cache.get(device_id)
            if cached:
                return {"ok": False, "error": "device offline, using cached state",
                        "cached_state": cached.to_cache_dict()}
            return {"ok": False, "error": "device not found"}
        
        state = self._connected_devices[device_id]
        state.last_command = command
        state.last_command_time = time.time()
        self.cache.put(device_id, state)
        
        return {
            "ok": True,
            "device_id": device_id,
            "command": command,
            "params": params or {},
            "timestamp": time.time(),
        }
    
    def update_status(self, device_id: str, status: str, battery: float = None,
                      signal: int = None) -> bool:
        if device_id in self._connected_devices:
            state = self._connected_devices[device_id]
            state.status = status
            if battery is not None:
                state.battery = battery
            if signal is not None:
                state.signal_strength = signal
            self.cache.put(device_id, state)
            return True
        return False
    
    def disconnect(self, device_id: str) -> bool:
        if device_id in self._connected_devices:
            del self._connected_devices[device_id]
            return True
        return False
    
    def get_offline_devices(self) -> List[Dict[str, Any]]:
        """Get devices available from cache that are not currently connected."""
        offline = []
        for cached_id in self.cache.list_cached():
            if cached_id not in self._connected_devices:
                state = self.cache.get(cached_id)
                if state:
                    offline.append({"id": cached_id, "name": state.name,
                                   "last_seen": state.cached_at})
        return offline
