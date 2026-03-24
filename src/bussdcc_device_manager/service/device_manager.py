from typing import Any

from bussdcc import (
    ContextProtocol,
    Service,
    Event,
    Message,
    RuntimeProtocol,
    DeviceProtocol,
)
from bussdcc_framework.codec import load_value
from bussdcc_hardware.registry import registry

from .. import message


class DeviceReconciler:
    def reconcile(
        self,
        runtime: RuntimeProtocol,
        desired_devices: dict[str, DeviceProtocol[Any]],
    ) -> None:
        actual = {d.id: d for d in runtime.devices.list()}
        desired_ids = set(desired_devices.keys())
        actual_ids = set(actual.keys())

        for dev_id in desired_ids & actual_ids:
            actual_dev = actual[dev_id]
            desired_dev = desired_devices[dev_id]

            if (
                type(actual_dev) is not type(desired_dev)
                or actual_dev.config != desired_dev.config
            ):
                try:
                    runtime.devices.detach(dev_id)
                except Exception:
                    pass

        actual_ids = {d.id for d in runtime.devices.list()}

        for dev_id in desired_ids - actual_ids:
            try:
                runtime.devices.attach(desired_devices[dev_id])
            except Exception:
                pass

        actual_ids = {d.id for d in runtime.devices.list()}

        for dev_id in actual_ids - desired_ids:
            try:
                runtime.devices.detach(dev_id)
            except Exception:
                pass

class DeviceManagerService(Service):
    name = "device_manager"

    def __init__(self) -> None:
        self.reconciler = DeviceReconciler()

    def handle_event(self, ctx: ContextProtocol, evt: Event[Message]) -> None:
        if isinstance(evt.payload, (message.ConfigInitialized, message.ConfigChanged)):
            cfg = ctx.state.get("config")
            if cfg is None:
                return

            desired_devices = self.build_desired_devices(registry.devices, cfg.devices)
            self.reconciler.reconcile(ctx.runtime, desired_devices)

    def build_desired_devices(
        self,
        col: dict[str, Any],
        devices_cfg: dict[str, Any],
    ) -> dict[str, DeviceProtocol[Any]]:
        desired: dict[str, DeviceProtocol[Any]] = {}

        for device_id, spec in devices_cfg.items():
            entry = col.get(spec["type"])

            if not entry or not entry.available:
                continue

            definition = entry.definition
            if definition is None:
                continue

            cfg = load_value(definition.config_class, spec["config"])
            desired[device_id] = definition.driver_class(id=device_id, config=cfg)

        return desired
