"""Shared PNML related helper functions."""

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


def find_triggers(net: Net):
    """Find all event triggers."""
    all_types = net._flatten_node_typ_map()

    net_elements: list[NetElement] = [
        node for node in all_types if isinstance(node, NetElement)
    ]
    triggers: list[NetElement] = [
        trigger for trigger in net_elements if trigger.is_workflow_event_trigger()
    ]
    return triggers

