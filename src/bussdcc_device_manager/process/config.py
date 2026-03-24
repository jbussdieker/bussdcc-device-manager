from dataclasses import replace

from bussdcc import Process, ContextProtocol, Event, Message

from .. import message, config


class ConfigProcess(Process):
    name = "config"

    def handle_event(self, ctx: ContextProtocol, evt: Event[Message]) -> None:
        if isinstance(evt.payload, message.ConfigInitialized):
            ctx.state.set("config", evt.payload.config)
        elif isinstance(evt.payload, message.ConfigUpdate):
            ctx.state.set("config", evt.payload.config)
            ctx.emit(message.ConfigChanged())
        elif isinstance(evt.payload, message.DeviceAdded):
            cfg = ctx.state.get("config")
            cfg.devices[evt.payload.device] = {
                "type": evt.payload.type_,
                "config": evt.payload.data,
            }
            ctx.emit(message.ConfigChanged())
        elif isinstance(evt.payload, message.DeviceConfigUpdate):
            cfg = ctx.state.get("config")
            cfg.devices[evt.payload.device]["config"] = evt.payload.data
            ctx.emit(message.ConfigChanged())
        elif isinstance(evt.payload, message.DeviceDeleted):
            cfg = ctx.state.get("config")
            if cfg is None:
                return

            if evt.payload.device in cfg.devices:
                del cfg.devices[evt.payload.device]
                ctx.emit(message.ConfigChanged())

        elif isinstance(evt.payload, message.SettingsUpdate):
            payload = evt.payload
            cfg = ctx.state.get("config")

            if cfg is None:
                ctx.state.set(
                    "config",
                    config.Config(settings=payload.settings),
                )
            else:
                ctx.state.update(
                    "config",
                    lambda cfg: replace(cfg, settings=payload.settings),
                )
            ctx.emit(message.ConfigChanged())
