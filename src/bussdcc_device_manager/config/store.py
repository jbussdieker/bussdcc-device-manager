import json
from pathlib import Path

from bussdcc_framework.codec import load_value, dump_value
from bussdcc_system.model import DeviceSpec

from .config import Config
from .settings import Settings


class ConfigStore:
    def __init__(self, path: str | Path):
        if isinstance(path, str):
            path = Path(path)

        self.path = path
        self.data: Config | None = None

        if path.exists():
            raw = json.loads(path.read_text())

            devices = {
                device_id: DeviceSpec(**spec)
                for device_id, spec in raw.get("devices", {}).items()
            }

            self.data = Config(
                settings=load_value(Settings, raw["settings"]),
                devices=devices,
            )

    def save(self) -> None:
        if self.data is None:
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)

        # dump_value will convert DeviceSpec correctly if codec supports dataclasses
        self.path.write_text(json.dumps(dump_value(self.data), indent=2))
