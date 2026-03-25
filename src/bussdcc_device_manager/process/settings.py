from bussdcc import ContextProtocol, Event, Message, Process

from .. import message


class SettingsProcess(Process):
    name = "settings"

    def handle_event(self, ctx: ContextProtocol, evt: Event[Message]) -> None:
        payload = evt.payload

        if isinstance(payload, message.SettingsReplaced):
            ctx.state.set("settings", payload.settings)
            return

        if isinstance(payload, message.SettingsUpdate):
            ctx.state.set("settings", payload.settings)
            ctx.emit(message.ConfigChanged())
