"""Insert GenericBPMNNodes."""

from app.transform.transformer.models.bpmn.base import Gateway, GenericBPMNNode
from app.transform.transformer.models.bpmn.bpmn import (
    EndEvent,
    IntermediateCatchEvent,
    Process,
    StartEvent,
)
from app.transform.transformer.utility.utility import create_silent_node_name


def is_target_wf_transition(node):
    """If node will be transformed to transition."""
    return isinstance(node, Process | Gateway | IntermediateCatchEvent)


def is_place_like(node):
    """BPMN node will be transformed to a place."""
    return type(node) == GenericBPMNNode or isinstance(node, StartEvent | EndEvent)


def insert_temp_between_adjacent_mapped_transition(bpmn: Process):
    """Add helper Nodes.

    Certain adjacent BPMN Elements that will be transformed to transitions can break
    the transformation if they are adjacent to other workflow elements.
    As a solution GenericBPMNNodes are inserted around each critical element.
    They will be transformed to Places as part of the transformation.
    """
    nodes = bpmn._flatten_node_typ_map()
    for node in nodes:
        if not is_target_wf_transition(node):
            continue

        for incoming_flow in bpmn.get_incoming(node.id).copy():
            incoming_node = bpmn.get_node(incoming_flow.sourceRef)
            # Connected node is already place like
            if is_place_like(incoming_node):
                continue

            linking_node = GenericBPMNNode(
                id=create_silent_node_name(incoming_node.id, node.id)
            )

            bpmn.remove_flow(incoming_flow)

            bpmn.add_node(linking_node)
            bpmn.add_flow(incoming_node, linking_node)
            bpmn.add_flow(linking_node, node)

        for outgoing_flow in bpmn.get_outgoing(node.id).copy():
            outgoing_node = bpmn.get_node(outgoing_flow.targetRef)
            # Connected node is already place like
            if is_place_like(outgoing_node):
                continue

            linking_node = GenericBPMNNode(
                id=create_silent_node_name(node.id, outgoing_node.id)
            )

            bpmn.remove_flow(outgoing_flow)

            bpmn.add_node(linking_node)
            bpmn.add_flow(node, linking_node)
            bpmn.add_flow(
                linking_node,
                outgoing_node,
            )

