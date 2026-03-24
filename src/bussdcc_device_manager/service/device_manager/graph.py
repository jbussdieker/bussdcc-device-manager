from typing import Any
from dataclasses import dataclass, fields, is_dataclass

from bussdcc import RuntimeProtocol, DeviceProtocol
from bussdcc_framework.codec import load_value
from bussdcc_framework.metadata import FieldMetadata

from ...config.device import DeviceSpec


@dataclass(slots=True)
class DeviceNode:
    id: str
    type_: str
    spec: DeviceSpec
    device: DeviceProtocol[Any]
    deps: set[str]


def extract_dependencies(cfg: Any) -> set[str]:
    deps: set[str] = set()

    if not is_dataclass(cfg):
        return deps

    for f in fields(cfg):
        meta = FieldMetadata.from_field(f)
        if meta.ref is None:
            continue

        value = getattr(cfg, f.name)

        if value is None:
            continue

        if isinstance(value, str):
            if value:
                deps.add(value)
            continue

        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item:
                    deps.add(item)
            continue

        if isinstance(value, dict):
            for item in value.values():
                if isinstance(item, str) and item:
                    deps.add(item)
            continue

    return deps


def build_dependents(nodes: dict[str, DeviceNode]) -> dict[str, set[str]]:
    dependents: dict[str, set[str]] = {node_id: set() for node_id in nodes}

    for node_id, node in nodes.items():
        for dep in node.deps:
            if dep in nodes:
                dependents[dep].add(node_id)

    return dependents


def topo_sort(nodes: dict[str, DeviceNode]) -> list[str]:
    in_degree: dict[str, int] = {node_id: 0 for node_id in nodes}
    dependents: dict[str, set[str]] = {node_id: set() for node_id in nodes}

    for node_id, node in nodes.items():
        for dep in node.deps:
            if dep not in nodes:
                continue
            in_degree[node_id] += 1
            dependents[dep].add(node_id)

    ready = sorted(node_id for node_id, deg in in_degree.items() if deg == 0)
    result: list[str] = []

    while ready:
        node_id = ready.pop(0)
        result.append(node_id)

        for child in sorted(dependents[node_id]):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                ready.append(child)

    if len(result) != len(nodes):
        raise RuntimeError("Device dependency cycle detected")

    return result


def initial_dirty_ids(
    runtime: RuntimeProtocol,
    nodes: dict[str, DeviceNode],
) -> set[str]:
    actual = {d.id: d for d in runtime.devices.list()}
    dirty: set[str] = set()

    for node_id, node in nodes.items():
        actual_dev = actual.get(node_id)
        if actual_dev is None:
            dirty.add(node_id)
            continue

        if type(actual_dev) is not type(node.device):
            dirty.add(node_id)
            continue

        if actual_dev.config != node.device.config:
            dirty.add(node_id)
            continue

    return dirty


def expand_dirty_ids(
    dirty: set[str],
    dependents: dict[str, set[str]],
) -> set[str]:
    expanded = set(dirty)
    stack = list(dirty)

    while stack:
        node_id = stack.pop()

        for child in dependents.get(node_id, set()):
            if child in expanded:
                continue
            expanded.add(child)
            stack.append(child)

    return expanded


def build_desired_nodes(
    col: dict[str, Any],
    devices_cfg: dict[str, DeviceSpec],
) -> dict[str, DeviceNode]:
    desired: dict[str, DeviceNode] = {}

    for device_id, spec in devices_cfg.items():
        entry = col.get(spec.type)

        if not entry or not entry.available:
            continue

        definition = entry.definition
        if definition is None:
            continue

        cfg = load_value(definition.config_class, spec.config)
        device = definition.driver_class(id=device_id, config=cfg)
        deps = extract_dependencies(cfg)

        desired[device_id] = DeviceNode(
            id=device_id,
            type_=spec.type,
            spec=spec,
            device=device,
            deps=deps,
        )

    return desired
