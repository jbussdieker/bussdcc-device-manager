from typing import Any
import secrets

from flask import request, redirect, url_for

from bussdcc import ContextProtocol, Event, Message

from bussdcc_framework.web import FlaskApp, WebInterface as Base

from .blueprints.settings import bp as settings_bp


class WebInterface(Base):
    def register_routes(self, app: FlaskApp, ctx: ContextProtocol) -> None:
        app.secret_key = secrets.token_hex(32)

        @app.route("/")
        def index() -> Any:
            return redirect(url_for("bussdcc_system_devices.index"))

        @app.before_request
        def initial_configuration() -> Any:
            settings = ctx.state.get("settings")
            if settings is not None:
                return

            allowed_endpoints = {
                "settings.new",
                "settings.update",
                "bussdcc_framework_bootstrap.static",
                "bussdcc_framework_formtree.static",
                "bussdcc_framework_client.static",
                "bussdcc_framework_socketio.static",
            }
            if request.endpoint not in allowed_endpoints:
                return redirect(url_for("settings.new"))

        @app.context_processor
        def get_context() -> dict[str, Any]:
            config = ctx.state.get("config")

            return dict(
                settings=ctx.state.get("settings"),
                ri=ctx.state.get("runtime_info", {}),
            )

        app.register_blueprint(settings_bp)

    def handle_event(self, ctx: ContextProtocol, evt: Event[Message]) -> None:
        pass
