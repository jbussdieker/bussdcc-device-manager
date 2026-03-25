from typing import Any
from flask import Blueprint, render_template, redirect, url_for, request

from bussdcc_framework.interface.web import current_ctx
from bussdcc_framework.codec import load_value

from .... import message, config

from bussdcc_framework.interface.web import formtree

bp = Blueprint("settings", __name__, url_prefix="/settings")


@bp.route("/")
def index() -> Any:
    ctx = current_ctx()
    settings = ctx.state.get("settings")
    if settings is None:
        return redirect(url_for("settings.new"))

    tree = formtree.build(settings)
    return render_template(
        "settings/index.html",
        tree=tree,
        action=url_for("settings.update"),
    )


@bp.route("/new")
def new() -> Any:
    tree = formtree.build(config.build_default_settings())
    return render_template(
        "settings/new.html",
        tree=tree,
        action=url_for("settings.update"),
    )


@bp.route("/update", methods=["POST"])
def update() -> Any:
    ctx = current_ctx()
    tree = formtree.build(config.Settings)
    tree = formtree.validate(tree, request.form)
    if tree.errors > 0:
        return render_template(
            "settings/index.html",
            tree=tree,
            action=url_for("settings.update"),
        )

    data = formtree.unflatten(tree, request.form)
    cfg = load_value(config.Settings, data).normalized()
    ctx.emit(message.SettingsUpdate(settings=cfg))
    return redirect(url_for("settings.index"))
