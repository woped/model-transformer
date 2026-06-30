"""Shared PNML related helper functions."""

from collections.abc import Callable

from app.transform.transformer.models.pnml.base import NetElement
from app.transform.transformer.models.pnml.pnml import Net


def generate_subprocess_inner_id(id: str):
    """Prepend SB_ to the id."""
    return f"SB_{id}"


def generate_explicit_transition_id(id: str):
    """Prepend EXPLICIT to the id."""
    return f"EXPLICIT{id}"


def generate_explicit_trigger_id(id: str):
    """Prepend EXPLICIT to the id."""
    return f"TRIGGER{id}"


def generate_source_id(id: str):
    """Prepend SOURCE to the id."""
    return f"SOURCE{id}"


def generate_sink_id(id: str):
    """Prepend SINK to the id."""
    return f"SINK{id}"


def _find_net_elements(net: Net, predicate: Callable[[NetElement], bool]):
    """Return all NetElements in the net (including nested pages) matching predicate."""
    return [
        node
        for node in net._flatten_node_typ_map()
        if isinstance(node, NetElement) and predicate(node)
    ]


def find_triggers(net: Net):
    """Find all event triggers."""
    return _find_net_elements(net, lambda n: n.is_workflow_event_trigger())


def find_workflow_resources(net: Net):
    """Find all workflow resource transitions."""
    return _find_net_elements(net, lambda n: n.is_workflow_resource())
