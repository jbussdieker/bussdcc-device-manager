from bussdcc import RuntimeProtocol

from . import graph


class DeviceReconciler:
    def reconcile(
        self,
        runtime: RuntimeProtocol,
        desired_nodes: dict[str, graph.DeviceNode],
    ) -> None:
        actual = {d.id: d for d in runtime.devices.list()}
        desired_ids = set(desired_nodes.keys())
        actual_ids = set(actual.keys())

        order = graph.topo_sort(desired_nodes)
        reverse_order = list(reversed(order))
        dependents = graph.build_dependents(desired_nodes)

        deleted_ids = actual_ids - desired_ids

        dirty_ids = graph.initial_dirty_ids(runtime, desired_nodes)
        dirty_ids = graph.expand_dirty_ids(dirty_ids, dependents)

        # detach deleted devices first in reverse dependency order
        for dev_id in graph.deleted_detach_order(runtime, deleted_ids):
            try:
                runtime.devices.detach(dev_id)
            except Exception:
                pass

        # detach changed/new dependency subgraphs in reverse topo order
        for dev_id in reverse_order:
            if dev_id not in dirty_ids:
                continue

            if runtime.devices.get(dev_id) is None:
                continue

            try:
                runtime.devices.detach(dev_id)
            except Exception:
                pass

        # attach changed/new nodes in topo order
        for dev_id in order:
            if dev_id not in dirty_ids:
                continue

            try:
                runtime.devices.attach(desired_nodes[dev_id].device)
            except Exception:
                pass
