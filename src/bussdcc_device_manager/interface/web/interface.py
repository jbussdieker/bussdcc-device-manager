from typing import Any
import secrets

from flask import request, redirect, url_for

from bussdcc import ContextProtocol, Event, Message

from bussdcc_framework.web import FlaskApp, WebInterface as Base

from .blueprints.settings import bp as settings_bp
from .blueprints.device import bp as device_bp


class WebInterface(Base):
    def register_routes(self, app: FlaskApp, ctx: ContextProtocol) -> None:
        app.secret_key = secrets.token_hex(32)

        @app.route("/")
        def index() -> Any:
            return redirect(url_for("device.index"))

        @app.before_request
        def initial_configuration() -> Any:
            cfg = ctx.state.get("config")
            if cfg is not None and cfg.settings is not None:
                return

            allowed_endpoints = {"settings.new", "settings.update", "static"}
            if request.endpoint not in allowed_endpoints:
                return redirect(url_for("settings.new"))

        @app.context_processor
        def get_context() -> dict[str, Any]:
            config = ctx.state.get("config")

            return dict(
                config=config,
                ri=ctx.state.get("runtime_info", {}),
            )

        app.register_blueprint(settings_bp)
        app.register_blueprint(device_bp)

    def handle_event(self, ctx: ContextProtocol, evt: Event[Message]) -> None:
        pass
