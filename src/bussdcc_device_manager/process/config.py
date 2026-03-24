from dataclasses import replace

from bussdcc import ContextProtocol, Event, Message, Process

from .. import config, message
from ..config.device import DeviceSpec


def with_device_added(
    cfg: config.Config, device: str, spec: DeviceSpec
) -> config.Config:
    return replace(
        cfg,
        devices={
            **cfg.devices,
            device: spec,
        },
    )


def with_device_config_updated(
    cfg: config.Config,
    device: str,
    device_config: dict[str, object],
) -> config.Config:
    spec = cfg.devices[device]

    return replace(
        cfg,
        devices={
            **cfg.devices,
            device: DeviceSpec(
                type=spec.type,
                config=device_config,
            ),
        },
    )


def with_device_deleted(cfg: config.Config, device: str) -> config.Config:
    return replace(
        cfg,
        devices={
            device_id: spec
            for device_id, spec in cfg.devices.items()
            if device_id != device
        },
    )


class ConfigProcess(Process):
    name = "config"

    def handle_event(self, ctx: ContextProtocol, evt: Event[Message]) -> None:
        payload = evt.payload

        if isinstance(payload, message.ConfigInitialized):
            ctx.state.set("config", payload.config)
            return

        if isinstance(payload, message.ConfigUpdate):
            ctx.state.set("config", payload.config)
            ctx.emit(message.ConfigChanged())
            return

        if isinstance(payload, message.DeviceAdded):
            ctx.state.update(
                "config",
                lambda cfg: with_device_added(cfg, payload.device, payload.spec),
            )
            ctx.emit(message.ConfigChanged())
            return

        if isinstance(payload, message.DeviceConfigUpdate):
            ctx.state.update(
                "config",
                lambda cfg: with_device_config_updated(
                    cfg, payload.device, payload.config
                ),
            )
            ctx.emit(message.ConfigChanged())
            return

        if isinstance(payload, message.DeviceDeleted):
            ctx.state.update(
                "config", lambda cfg: with_device_deleted(cfg, payload.device)
            )
            ctx.emit(message.ConfigChanged())
            return

        if isinstance(payload, message.SettingsUpdate):
            current = ctx.state.get("config")

            if current is None:
                ctx.state.set("config", config.Config(settings=payload.settings))
            else:
                ctx.state.update(
                    "config", lambda cfg: replace(cfg, settings=payload.settings)
                )

            ctx.emit(message.ConfigChanged())
