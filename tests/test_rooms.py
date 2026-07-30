"""Tests for HIRI room/area grouping and search."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_room_create():
    from hiri.rooms.room import Room
    room = Room(id="living", name="Living Room", floor="ground")
    assert room.id == "living"
    assert room.name == "Living Room"
    assert room.devices == []


def test_room_add_device():
    from hiri.rooms.room import Room
    room = Room(id="living", name="Living Room")
    room.add_device("light_1")
    room.add_device("sensor_temp")
    assert room.device_count() == 2
    assert "light_1" in room.devices


def test_room_add_duplicate_device():
    from hiri.rooms.room import Room
    room = Room(id="living", name="Living Room")
    room.add_device("light_1")
    room.add_device("light_1")
    assert room.device_count() == 1


def test_room_remove_device():
    from hiri.rooms.room import Room
    room = Room(id="living", name="Living Room")
    room.add_device("light_1")
    room.remove_device("light_1")
    assert room.device_count() == 0


def test_registry_add_and_get():
    from hiri.rooms.room import Room, RoomRegistry
    reg = RoomRegistry()
    room = Room(id="kitchen", name="Kitchen", floor="ground")
    reg.add_room(room)
    assert reg.get_room("kitchen") is not None
    assert reg.get_room("nonexistent") is None


def test_registry_list_rooms():
    from hiri.rooms.room import Room, RoomRegistry
    reg = RoomRegistry()
    reg.add_room(Room(id="b", name="Bedroom", floor="first"))
    reg.add_room(Room(id="a", name="Attic", floor="second"))
    rooms = reg.list_rooms()
    assert len(rooms) == 2
    assert rooms[0].name == "Attic"  # alphabetical


def test_registry_find_by_device():
    from hiri.rooms.room import Room, RoomRegistry
    reg = RoomRegistry()
    r1 = Room(id="living", name="Living Room")
    r1.add_device("light_hall")
    r2 = Room(id="kitchen", name="Kitchen")
    r2.add_device("oven")
    reg.add_room(r1)
    reg.add_room(r2)
    found = reg.find_rooms_by_device("oven")
    assert len(found) == 1
    assert found[0].id == "kitchen"


def test_registry_search_rooms():
    from hiri.rooms.room import Room, RoomRegistry
    reg = RoomRegistry()
    r1 = Room(id="living", name="Living Room", floor="ground")
    r1.add_device("tv")
    reg.add_room(r1)
    reg.add_room(Room(id="bath", name="Bathroom", floor="ground"))
    results = reg.search_rooms("living")
    assert len(results) >= 1
    results2 = reg.search_rooms("tv")
    assert len(results2) >= 1 and results2[0].id == "living"


def test_registry_rooms_by_floor():
    from hiri.rooms.room import Room, RoomRegistry
    reg = RoomRegistry()
    reg.add_room(Room(id="a", name="Attic", floor="second"))
    reg.add_room(Room(id="l", name="Living", floor="ground"))
    reg.add_room(Room(id="k", name="Kitchen", floor="ground"))
    ground = reg.rooms_by_floor("ground")
    assert len(ground) == 2


def test_registry_floor_summary():
    from hiri.rooms.room import Room, RoomRegistry
    reg = RoomRegistry()
    reg.add_room(Room(id="a", name="Attic", floor="second"))
    reg.add_room(Room(id="l", name="Living", floor="ground"))
    reg.add_room(Room(id="k", name="Kitchen", floor="ground"))
    summary = reg.floor_summary()
    assert summary.get("ground") == 2
    assert summary.get("second") == 1


def test_registry_unassigned_devices():
    from hiri.rooms.room import Room, RoomRegistry
    reg = RoomRegistry()
    r = Room(id="living", name="Living Room")
    r.add_device("light_1")
    reg.add_room(r)
    unassigned = reg.unassigned_devices(["light_1", "door_sensor", "camera"])
    assert "door_sensor" in unassigned
    assert "camera" in unassigned
    assert "light_1" not in unassigned
