from bussdcc import ContextProtocol, Event, Message, Service
from bussdcc_hardware.registry import registry

from ... import message
from .graph import build_desired_nodes
from .reconciler import DeviceReconciler


class DeviceManagerService(Service):
    name = "device_manager"

    def __init__(self) -> None:
        self.reconciler = DeviceReconciler()

    def handle_event(self, ctx: ContextProtocol, evt: Event[Message]) -> None:
        if isinstance(
            evt.payload,
            (
                message.ConfigInitialized,
                message.DeviceAdded,
                message.DeviceConfigUpdate,
                message.DeviceDeleted,
            ),
        ):
            cfg = ctx.state.get("config")
            if cfg is None:
                return

            desired_nodes = build_desired_nodes(registry.devices, cfg.devices)
            self.reconciler.reconcile(ctx.runtime, desired_nodes)
