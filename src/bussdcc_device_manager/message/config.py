from dataclasses import dataclass
from bussdcc import Message
from ..config import Settings


@dataclass(slots=True, frozen=True)
class SettingsReplaced(Message):
    settings: Settings


@dataclass(slots=True, frozen=True)
class SettingsUpdate(Message):
    settings: Settings


@dataclass(slots=True, frozen=True)
class ConfigChanged(Message):
    pass


@dataclass(slots=True, frozen=True)
class ConfigSaved(Message):
    pass
