from dataclasses import dataclass, field, replace

from .settings import Settings
from .device import DeviceSpec


@dataclass(slots=True, frozen=True)
class Config:
    settings: Settings = field(
        metadata={
            "label": "Settings",
            "group": "General",
            "required": True,
        }
    )
    devices: dict[str, DeviceSpec] = field(
        default_factory=dict,
        metadata={
            "label": "Devices",
            "group": "Runtime",
            "help": "Named device registrations.",
        },
    )

    def normalized(self) -> "Config":
        return replace(self, settings=self.settings.normalized())
