from __future__ import annotations

from typing import Protocol

from hiri_bridge.devices.types import Device


class BridgeAdapter(Protocol):
    name: str

    def list_remote(self) -> list[Device]: ...

    def push_state(self, device: Device) -> None: ...
