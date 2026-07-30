"""Room and area grouping model for HIRI."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Room:
    """A physical room or logical area grouping devices."""
    id: str
    name: str
    floor: str = "ground"
    icon: str = "room"
    devices: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def add_device(self, device_id: str) -> None:
        """Add a device to this room."""
        if device_id not in self.devices:
            self.devices.append(device_id)

    def remove_device(self, device_id: str) -> None:
        """Remove a device from this room."""
        if device_id in self.devices:
            self.devices.remove(device_id)

    def device_count(self) -> int:
        return len(self.devices)


@dataclass
class RoomRegistry:
    """Manages room groupings and search."""
    rooms: dict[str, Room] = field(default_factory=dict)

    def add_room(self, room: Room) -> None:
        self.rooms[room.id] = room

    def get_room(self, room_id: str) -> Room | None:
        return self.rooms.get(room_id)

    def remove_room(self, room_id: str) -> None:
        self.rooms.pop(room_id, None)

    def list_rooms(self) -> list[Room]:
        return sorted(self.rooms.values(), key=lambda r: r.name)

    def find_rooms_by_device(self, device_id: str) -> list[Room]:
        """Find all rooms containing a specific device."""
        return [r for r in self.rooms.values() if device_id in r.devices]

    def search_rooms(self, query: str) -> list[Room]:
        """Search rooms by name, floor, or device."""
        q = query.lower()
        results: set[Room] = set()
        for room in self.rooms.values():
            if q in room.name.lower() or q in room.floor.lower():
                results.add(room)
            if any(q in d.lower() for d in room.devices):
                results.add(room)
        return sorted(results, key=lambda r: r.name)

    def rooms_by_floor(self, floor: str) -> list[Room]:
        """Group rooms by floor level."""
        return [r for r in self.rooms.values() if r.floor.lower() == floor.lower()]

    def floor_summary(self) -> dict[str, int]:
        """Count rooms per floor."""
        counts: dict[str, int] = {}
        for room in self.rooms.values():
            counts[room.floor] = counts.get(room.floor, 0) + 1
        return counts

    def unassigned_devices(self, all_device_ids: list[str]) -> list[str]:
        """Find devices not assigned to any room."""
        assigned = set()
        for room in self.rooms.values():
            assigned.update(room.devices)
        return [d for d in all_device_ids if d not in assigned]
