from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class DeviceSpec:
    type: str
    config: dict[str, Any]
