"""Module for processing gateways for bpmn workflows."""

from typing import cast

from app.transform.transformer.models.bpmn.base import Gateway, GenericBPMNNode
from app.transform.transformer.models.bpmn.bpmn import Flow, Process


def remove_unnecessary_gateways(bpmn: Process, gateways: set[Gateway]):
    """Detect and remove unnecessary gateways in a set of gateways from a process.

    An unnecessary gateway has a indegree and outdegree of <= 1.
    """
    to_remove_gws = []
    for gw in gateways:
        if gw.get_in_degree() > 1 or gw.get_out_degree() > 1:
            continue
        to_remove_gws.append(gw)

        in_arc: Flow = list(bpmn.get_incoming(gw.id))[0]
        out_arc: Flow = list(bpmn.get_outgoing(gw.id))[0]
        source_node = bpmn.get_node(in_arc.sourceRef)
        target_node = bpmn.get_node(out_arc.targetRef)

        bpmn.remove_node(gw)
        bpmn.add_flow(source_node, target_node, gw.id)
    for gw in to_remove_gws:
        gateways.remove(gw)
    return bpmn


def add_pn_place_between_adjacent_gateways(bpmn: Process, gateways: set[Gateway]):
    """Add place between neighboring gateways in a list of gateways."""
    for gw in gateways:
        out_nodes: list[tuple[GenericBPMNNode, Flow]] = [
            (bpmn.get_node(x.targetRef), x) for x in bpmn.get_outgoing(gw.id)
        ]

        for out_node, out_flow in out_nodes:
            if out_node not in gateways:
                continue
            bpmn.remove_flow(out_flow)

            linking_node = GenericBPMNNode(id=gw.id + out_node.id)
            bpmn.add_node(linking_node)
            bpmn.add_flow(gw, linking_node)
            bpmn.add_flow(linking_node, out_node)
    return bpmn


def get_gateways(bpmn: Process):
    """Get all gateways of a process."""
    nodes = bpmn._flatten_node_typ_map()
    gateways = cast(
        set[Gateway], {node for node in nodes if issubclass(type(node), Gateway)}
    )
    return gateways


def preprocess_gateways(bpmn: Process):
    """Preprocess all gateways of a process.

    Part of the preprocessing is:
    - removing unnecessary gateways
    - add a helper node between adjacent gateways
    """
    gateways = get_gateways(bpmn)
    if len(gateways) == 0:
        return
    remove_unnecessary_gateways(bpmn, gateways)
    add_pn_place_between_adjacent_gateways(bpmn, gateways)

