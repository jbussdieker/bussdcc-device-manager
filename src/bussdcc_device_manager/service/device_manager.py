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
        desired: dict[str, DeviceProtocol[Any]],
    ) -> None:
        desired_ids = set(desired.keys())
        actual_ids = {d.id for d in runtime.devices.list()}

        for dev_id in desired_ids - actual_ids:
            try:
                runtime.devices.attach(desired[dev_id])
            except:
                pass

        for dev_id in actual_ids - desired_ids:
            try:
                runtime.devices.detach(dev_id)
            except:
                pass


class DeviceManagerService(Service):
    name = "device_manager"

    def __init__(self) -> None:
        self.reconciler = DeviceReconciler()

    def handle_event(self, ctx: ContextProtocol, evt: Event[Message]) -> None:
        if isinstance(evt.payload, (message.ConfigInitialized, message.ConfigChanged)):
            cfg = ctx.state.get("config")

            desired = self.reconcile(registry.buses, cfg.buses)
            self.reconciler.reconcile(ctx.runtime, desired)

            desired.update(self.reconcile(registry.devices, cfg.devices))
            self.reconciler.reconcile(ctx.runtime, desired)

    def reconcile(
        self, col: dict[str, Any], devices_cfg: dict[str, Any]
    ) -> dict[str, DeviceProtocol[Any]]:
        desired = {}

        for device_id, spec in devices_cfg.items():
            entry = col.get(spec["type"])

            if not entry or not entry.available:
                continue

            definition = entry.definition
            if not definition:
                continue

            cfg = load_value(definition.config_class, spec["config"])

            desired[device_id] = definition.driver_class(id=device_id, config=cfg)

        return desired
