from dataclasses import dataclass

from bussdcc import Message

from ..config import Config, Settings
from ..config.device import DeviceSpec


@dataclass(slots=True, frozen=True)
class ConfigInitialized(Message):
    config: Config


@dataclass(slots=True, frozen=True)
class ConfigUpdate(Message):
    config: Config


@dataclass(slots=True, frozen=True)
class DeviceAdded(Message):
    device: str
    spec: DeviceSpec


@dataclass(slots=True, frozen=True)
class DeviceConfigUpdate(Message):
    device: str
    config: dict[str, object]


@dataclass(slots=True, frozen=True)
class DeviceDeleted(Message):
    device: str


@dataclass(slots=True, frozen=True)
class SettingsUpdate(Message):
    settings: Settings


@dataclass(slots=True, frozen=True)
class ConfigChanged(Message):
    pass


@dataclass(slots=True, frozen=True)
class ConfigSaved(Message):
    pass
