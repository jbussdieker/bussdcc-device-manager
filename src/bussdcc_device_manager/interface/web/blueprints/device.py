from typing import Any
from flask import Blueprint, render_template, flash, redirect, url_for, request

from bussdcc_framework.interface.web import current_ctx
from bussdcc_framework.codec import load_value, dump_value
from bussdcc_framework.interface.web import formtree
from bussdcc_hardware.registry import registry

from .... import message

bp = Blueprint("device", __name__, url_prefix="/device")


@bp.route("/")
def index() -> Any:
    ctx = current_ctx()
    cfg = ctx.state.get("config")
    buses = cfg.buses
    devices = cfg.devices
    online_status = {dev.id: dev.online for dev in ctx.runtime.devices.list()}
    return render_template(
        "device/index.html", buses=buses, devices=devices, online_status=online_status
    )


@bp.route("/new_device")
def new_device() -> Any:
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
            "device/new_form.html",
            name=name,
            type=type_,
            tree=tree,
            action=url_for("device.create_device", name=name, type_=type_),
        )
    else:
        return render_template("device/new_device.html", devices=devices)


@bp.route("/new_bus")
def new_bus() -> Any:
    buses = registry.buses
    name = request.args.get("name")
    type_ = request.args.get("type_")
    if name and type_:
        registry_entry = registry.buses[type_]
        definition = registry_entry.definition
        if definition is None:
            flash("Bus not available", "warning")
            return redirect(url_for("device.index"))
        tree = formtree.build(definition.config_class)
        return render_template(
            "device/new_form.html",
            name=name,
            type=type_,
            tree=tree,
            action=url_for("device.create_bus", name=name, type_=type_),
        )
    else:
        return render_template("device/new_bus.html", buses=buses)


@bp.route("/device/show/<id>")
def show_device(id: str) -> Any:
    ctx = current_ctx()
    device = ctx.runtime.devices.get(id)
    if not device:
        flash("Device not found", "warning")
        return redirect(url_for("index"))

    tree = formtree.build(device.config)

    return render_template(
        "device/show_device.html",
        tree=tree,
        device_id=id,
        action=url_for("device.update_device", id=id),
    )


@bp.route("/bus/show/<id>")
def show_bus(id: str) -> Any:
    ctx = current_ctx()
    device = ctx.runtime.devices.get(id)
    if not device:
        flash("Device not found", "warning")
        return redirect(url_for("index"))

    tree = formtree.build(device.config)

    return render_template(
        "device/show_bus.html",
        tree=tree,
        device_id=id,
        action=url_for("device.update_bus", id=id),
    )


@bp.route("/create_bus/<type_>/<name>", methods=["POST"])
def create_bus(type_: str, name: str) -> Any:
    ctx = current_ctx()

    registry_entry = registry.buses[type_]
    definition = registry_entry.definition
    if definition is None:
        flash("Bus not available", "warning")
        return redirect(url_for("device.index"))

    tree = formtree.build(definition.config_class)
    data = formtree.unflatten(tree, request.form)
    cfg = load_value(definition.config_class, data)
    ctx.emit(message.BusAdded(bus=name, type_=type_, data=dump_value(cfg)))

    return redirect(url_for("device.index"))


@bp.route("/create_device/<type_>/<name>", methods=["POST"])
def create_device(type_: str, name: str) -> Any:
    ctx = current_ctx()

    registry_entry = registry.devices[type_]
    definition = registry_entry.definition
    if definition is None:
        flash("Bus not available", "warning")
        return redirect(url_for("device.index"))

    tree = formtree.build(definition.config_class)
    data = formtree.unflatten(tree, request.form)
    cfg = load_value(definition.config_class, data)
    ctx.emit(message.DeviceAdded(device=name, type_=type_, data=dump_value(cfg)))

    return redirect(url_for("device.index"))


@bp.route("/device/update/<id>", methods=["POST"])
def update_device(id: str) -> Any:
    ctx = current_ctx()

    device = ctx.runtime.devices.get(id)
    if not device:
        flash("Device not found", "warning")
        return redirect(url_for("index"))

    tree = formtree.build(device.config)
    data = formtree.unflatten(tree, request.form)
    cfg = load_value(type(device.config), data)
    ctx.emit(message.DeviceConfigUpdate(device=id, data=dump_value(cfg)))

    return redirect(url_for("device.index"))


@bp.route("/bus/update/<id>", methods=["POST"])
def update_bus(id: str) -> Any:
    ctx = current_ctx()

    device = ctx.runtime.devices.get(id)
    if not device:
        flash("Bus not found", "warning")
        return redirect(url_for("index"))

    tree = formtree.build(device.config)
    data = formtree.unflatten(tree, request.form)
    cfg = load_value(type(device.config), data)
    ctx.emit(message.BusConfigUpdate(bus=id, data=dump_value(cfg)))

    return redirect(url_for("device.index"))


@bp.route("/device/delete/<id>", methods=["POST"])
def delete_device(id: str) -> Any:
    ctx = current_ctx()

    device = ctx.runtime.devices.get(id)
    if not device:
        flash("Device not found", "warning")
        return redirect(url_for("device.index"))

    ctx.emit(message.DeviceDeleted(device=id))
    flash(f"Deleted device '{id}'", "success")

    return redirect(url_for("device.index"))


@bp.route("/bus/delete/<id>", methods=["POST"])
def delete_bus(id: str) -> Any:
    ctx = current_ctx()

    device = ctx.runtime.devices.get(id)
    if not device:
        flash("Bus not found", "warning")
        return redirect(url_for("device.index"))

    ctx.emit(message.BusDeleted(bus=id))
    flash(f"Deleted bus '{id}'", "success")

    return redirect(url_for("device.index"))
