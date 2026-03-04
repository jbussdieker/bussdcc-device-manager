from bussdcc import Service, ContextProtocol, Event, Message

from ..config import ConfigStore
from .. import message


class ConfigService(Service):
    name = "config"

    def __init__(self, data_dir: str) -> None:
        self._data_dir = data_dir

    def _save_config(self, ctx: ContextProtocol) -> None:
        cfg = ctx.state.get("config")
        if cfg is None:
            return

        self.cs.data = cfg
        self.cs.save()

        ctx.emit(message.ConfigSaved())

    def start(self, ctx: ContextProtocol) -> None:
        self.cs = ConfigStore(f"{self._data_dir}/config.json")
        if self.cs.data is None:
            return

        ctx.emit(message.ConfigInitialized(self.cs.data))

    def handle_event(self, ctx: ContextProtocol, evt: Event[Message]) -> None:
        if isinstance(evt.payload, message.ConfigChanged):
            self._save_config(ctx)

    def stop(self, ctx: ContextProtocol) -> None:
        self._save_config(ctx)
