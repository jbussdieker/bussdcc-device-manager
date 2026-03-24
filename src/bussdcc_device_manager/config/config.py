from dataclasses import dataclass, field, replace
from typing import Any, Optional

from .settings import Settings


@dataclass(slots=True, frozen=True)
class Config:
    settings: Settings = field(
        metadata={
            "label": "Settings",
            "group": "General",
            "required": True,
        }
    )
    devices: Optional[dict[str, Any]] = field(
        default_factory=dict,
        metadata={
            "label": "Devices",
            "group": "Runtime",
            "help": "Named device registrations.",
        },
    )

    def normalized(self) -> "Config":
        return replace(self, settings=self.settings.normalized())
