from bussdcc import Service, ContextProtocol, Event, Message
from bussdcc_system import message as system_message

from ..config import ConfigStore, Config
from .. import message


class ConfigService(Service):
    name = "config"

    def __init__(self, data_dir: str) -> None:
        self._data_dir = data_dir

    def _save_config(self, ctx: ContextProtocol) -> None:
        settings = ctx.state.get("settings")
        devices = ctx.state.get("devices", {})

        if settings is None:
            return

        self.cs.data = Config(
            settings=settings,
            devices=devices,
        )
        self.cs.save()

        ctx.emit(message.ConfigSaved())

    def start(self, ctx: ContextProtocol) -> None:
        self.cs = ConfigStore(f"{self._data_dir}/config.json")
        if self.cs.data is None:
            return

        ctx.emit(message.SettingsReplaced(self.cs.data.settings))
        ctx.emit(system_message.DevicesReplaced(self.cs.data.devices))

    def handle_event(self, ctx: ContextProtocol, evt: Event[Message]) -> None:
        payload = evt.payload

        if isinstance(payload, message.ConfigChanged):
            self._save_config(ctx)
            return

        if isinstance(
            payload,
            (
                system_message.DevicesReplaced,
                system_message.DeviceAdded,
                system_message.DeviceConfigUpdate,
                system_message.DeviceDeleted,
            ),
        ):
            self._save_config(ctx)

    def stop(self, ctx: ContextProtocol) -> None:
        self._save_config(ctx)
