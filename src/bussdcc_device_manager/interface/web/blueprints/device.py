from typing import Any
from flask import Blueprint, render_template, flash, redirect, url_for, request

from bussdcc_framework.interface.web import current_ctx
from bussdcc_framework.codec import load_value, dump_value
from bussdcc_framework.interface.web import formtree
from bussdcc_hardware.registry import registry
from bussdcc_system.service.device_manager.graph import extract_dependencies
from bussdcc_system.model import DeviceSpec

from bussdcc_system import message as system_message
from .... import message

bp = Blueprint("device", __name__, url_prefix="/device")


@bp.route("/")
def index() -> Any:
    ctx = current_ctx()
    devices = ctx.state.get("devices", {})

    runtime_devices = {dev.id: dev for dev in ctx.runtime.devices.list()}
    online_status = {dev.id: dev.online for dev in runtime_devices.values()}

    dependency_map: dict[str, set[str]] = {}
    dependent_map: dict[str, set[str]] = {device_id: set() for device_id in devices}
    missing_dependency_map: dict[str, set[str]] = {}
    status_map: dict[str, str] = {}

    configured_ids = set(devices.keys())

    for device_id, spec in devices.items():
        registry_entry = registry.devices.get(spec.type)

        if registry_entry is None or registry_entry.definition is None:
            dependency_map[device_id] = set()
            missing_dependency_map[device_id] = set()
            status_map[device_id] = "type-unavailable"
            continue

        definition = registry_entry.definition
        device_cfg = load_value(definition.config_class, spec.config)
        deps = extract_dependencies(device_cfg)

        dependency_map[device_id] = deps
        missing = {dep for dep in deps if dep not in configured_ids}
        missing_dependency_map[device_id] = missing

        for dep in deps:
            if dep in dependent_map:
                dependent_map[dep].add(device_id)

        if missing:
            status_map[device_id] = "missing-dependency"
        elif online_status.get(device_id):
            status_map[device_id] = "online"
        else:
            status_map[device_id] = "offline"

    roots = sorted(
        device_id
        for device_id, deps in dependency_map.items()
        if not deps or any(dep not in configured_ids for dep in deps)
    )

    return render_template(
        "device/index.html",
        devices=devices,
        dependency_map=dependency_map,
        dependent_map={k: sorted(v) for k, v in dependent_map.items()},
        missing_dependency_map=missing_dependency_map,
        status_map=status_map,
        roots=roots,
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
    devices = ctx.state.get("devices", {})
    spec = devices.get(id)

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
        system_message.DeviceAdded(
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
    devices = ctx.state.get("devices", {})
    spec = devices.get(id)

    if spec is None:
        flash("Device not found", "warning")
        return redirect(url_for("device.index"))

    registry_entry = registry.devices.get(spec.type)
    if registry_entry is None or registry_entry.definition is None:
        flash("Device type not available", "warning")
        return redirect(url_for("device.index"))

    definition = registry_entry.definition
    tree = formtree.build(definition.config_class)
    tree = formtree.validate(tree, request.form)

    if tree.errors > 0:
        return render_template(
            "device/show.html",
            id=id,
            spec=spec,
            definition=definition,
            tree=tree,
        )

    data = formtree.unflatten(tree, request.form)
    device_cfg = load_value(definition.config_class, data)

    ctx.emit(
        system_message.DeviceConfigUpdate(
            device=id,
            config=dump_value(device_cfg),
        )
    )

    flash("Device updated", "success")
    return redirect(url_for("device.index"))


@bp.route("/delete/<id>", methods=["POST"])
def delete(id: str) -> Any:
    ctx = current_ctx()
    devices = ctx.state.get("devices", {})
    spec = devices.get(id)

    if spec is None:
        flash("Device not found", "warning")
        return redirect(url_for("device.index"))

    ctx.emit(system_message.DeviceDeleted(device=id))
    flash(f"Deleted device '{id}'", "success")

    return redirect(url_for("device.index"))
