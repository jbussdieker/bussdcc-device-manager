from typing import Any
from flask import Blueprint, render_template, flash, redirect, url_for, request

from bussdcc_framework.interface.web import current_ctx
from bussdcc_framework.codec import load_value, dump_value
from bussdcc_framework.interface.web import formtree
from bussdcc_hardware.registry import registry

from .... import message
from ....config.device import DeviceSpec

bp = Blueprint("device", __name__, url_prefix="/device")


@bp.route("/")
def index() -> Any:
    ctx = current_ctx()
    cfg = ctx.state.get("config")
    devices = cfg.devices
    online_status = {dev.id: dev.online for dev in ctx.runtime.devices.list()}
    return render_template(
        "device/index.html", devices=devices, online_status=online_status
    )


@bp.route("/new")
def new() -> Any:
    devices = registry.devices
    name = request.args.get("name")
    type_ = request.args.get("type_")
    if name and type_:
        registry_entry = registry.devices[type_]
        definition = registry_entry.definition
        if definition is None:
            flash("Device not available", "warning")
            return redirect(url_for("device.index"))

        tree = formtree.build(definition.config_class)
        return render_template(
            "device/new_config.html",
            name=name,
            type=type_,
            tree=tree,
            action=url_for("device.create", name=name, type_=type_),
        )
    else:
        return render_template("device/new.html", devices=devices)


@bp.route("/show/<id>")
def show(id: str) -> Any:
    ctx = current_ctx()
    cfg = ctx.state.get("config")
    spec = cfg.devices.get(id)

    if spec is None:
        flash("Device not found", "warning")
        return redirect(url_for("device.index"))

    registry_entry = registry.devices.get(spec.type)
    if registry_entry is None or registry_entry.definition is None:
        flash("Device type not available", "warning")
        return redirect(url_for("device.index"))

    definition = registry_entry.definition
    device_cfg = load_value(definition.config_class, spec.config)
    tree = formtree.build(device_cfg)

    return render_template(
        "device/show.html",
        tree=tree,
        device_id=id,
        action=url_for("device.update", id=id),
    )


@bp.route("/create/<type_>/<name>", methods=["POST"])
def create(type_: str, name: str) -> Any:
    ctx = current_ctx()

    registry_entry = registry.devices[type_]
    definition = registry_entry.definition
    if definition is None:
        flash("Device not available", "warning")
        return redirect(url_for("device.index"))

    tree = formtree.build(definition.config_class)
    data = formtree.unflatten(tree, request.form)
    cfg = load_value(definition.config_class, data)
    ctx.emit(
        message.DeviceAdded(
            device=name,
            spec=DeviceSpec(
                type=type_,
                config=dump_value(cfg),
            ),
        )
    )

    return redirect(url_for("device.index"))


@bp.route("/update/<id>", methods=["POST"])
def update(id: str) -> Any:
    ctx = current_ctx()

    device = ctx.runtime.devices.get(id)
    if not device:
        flash("Device not found", "warning")
        return redirect(url_for("index"))

    tree = formtree.build(device.config)
    data = formtree.unflatten(tree, request.form)
    cfg = load_value(type(device.config), data)
    ctx.emit(
        message.DeviceConfigUpdate(
            device=id,
            config=dump_value(cfg),
        )
    )

    return redirect(url_for("device.index"))


@bp.route("/delete/<id>", methods=["POST"])
def delete(id: str) -> Any:
    ctx = current_ctx()

    device = ctx.runtime.devices.get(id)
    if not device:
        flash("Device not found", "warning")
        return redirect(url_for("device.index"))

    ctx.emit(message.DeviceDeleted(device=id))
    flash(f"Deleted device '{id}'", "success")

    return redirect(url_for("device.index"))
