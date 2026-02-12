"""Transform OR-Gates into a combination of AND- and XOR-Gates."""

import logging
from typing import cast

from app.transform.exceptions import ORGatewayDetectionIssue
from app.transform.transformer.models.bpmn.base import GenericBPMNNode
from app.transform.transformer.models.bpmn.bpmn import (
    AndGateway,
    Flow,
    OrGateway,
    Process,
    Task,
    XorGateway,
)
from app.transform.transformer.utility.utility import create_arc_name

logger = logging.getLogger(__name__)


def traverse_matching_gw(
    bpmn_helper: Process,
    stack: list[OrGateway],
    split_ids: set[str],
    join_ids: set[str],
    visited_arcs: set[str],
    flow_id: str,
):
    """Find the OR-Join of a OR-Split."""
    if flow_id in visited_arcs:
        # already visited arc -> circle detected
        return None
    visited_arcs.add(flow_id)

    target_node: GenericBPMNNode = bpmn_helper.get_flow_target_by_id(flow_id)
    if target_node.id in join_ids:
        if len(stack) == 1:
            # matching join found
            return flow_id, cast(OrGateway, target_node)
        else:
            # join for inner split found
            stack.pop()

    if target_node.id in split_ids:
        stack.append(cast(OrGateway, target_node))

    outgoing_arcs: list[str] = [x for x in target_node.outgoing]
    for flow_id in outgoing_arcs:
        r = traverse_matching_gw(
            bpmn_helper, stack, split_ids, join_ids, visited_arcs, flow_id
        )
        if r is not None:
            return r
    return None


class InclusiveGatewayBridge:
    """Class for inclusive gateways."""

    def __init__(
        self,
        split: OrGateway,
        join: OrGateway,
        flow_out_split: Flow,
        flow_in_join: Flow,
    ) -> None:
        """Constructor of inclusive gateway."""
        self.split = split
        self.join = join
        self.flow_out_split = flow_out_split
        self.flow_in_join = flow_in_join


class ParallelGatewayBridge:
    """Class for parallel gateways."""

    def __init__(
        self,
        split: AndGateway,
        join: AndGateway,
        flow_out_split: Flow,
        flow_in_join: Flow,
    ) -> None:
        """Constructor of parallel gateway."""
        self.split = split
        self.join = join
        self.flow_out_split = flow_out_split
        self.flow_in_join = flow_in_join


def find_matching_gateways(bpmn_helper: Process, inclusive_gateways: list[OrGateway]):
    """Match splits and joins of a set of gateways and process."""
    matches: list[InclusiveGatewayBridge] = []
    splits: list[OrGateway] = []
    joins: list[OrGateway] = []
    for gateway in inclusive_gateways:
        if gateway.get_in_degree() > 1:
            joins.append(gateway)
        if gateway.get_out_degree() > 1:
            splits.append(gateway)
    split_ids = {node.id for node in splits}
    join_ids = {node.id for node in joins}
    for split in splits:
        outgoing_flows: list[str] = [x for x in split.outgoing]
        for out_flow_id in outgoing_flows:
            r = traverse_matching_gw(
                bpmn_helper, [split], split_ids, join_ids, set(), out_flow_id
            )
            if r is None:
                raise ORGatewayDetectionIssue()
            matches.append(
                InclusiveGatewayBridge(
                    split,
                    r[1],
                    bpmn_helper.get_flow(out_flow_id),
                    bpmn_helper.get_flow(r[0]),
                )
            )
    return matches


def clone_flow(
    flow: Flow,
    new_source: GenericBPMNNode | None = None,
    new_target: GenericBPMNNode | None = None,
    new_id=None,
):
    """Return a clone flow for a given flow, source and target."""
    source_id = flow.sourceRef
    if new_source is not None:
        source_id = new_source.id
    target_id = flow.targetRef
    if new_target is not None:
        target_id = new_target.id
    return Flow(
        sourceRef=source_id,
        targetRef=target_id,
        id=new_id or create_arc_name(source_id, target_id),
        name=flow.name,
    )


def add_xors_and_activities(bpmn: Process, and_gw: ParallelGatewayBridge):
    """Add AND- and XOR-Gateways to the BPMN."""
    xor_split = XorGateway(id=and_gw.split.id + and_gw.flow_out_split.targetRef)
    xor_join = XorGateway(id=str(and_gw.flow_in_join.sourceRef) + and_gw.join.id)
    silent_activity = Task(id=xor_split.id + xor_join.id)
    bpmn.add_nodes(xor_split, xor_join, silent_activity)

    # handle connection AND to XOR both directions
    split_to_xor_arc = Flow(
        sourceRef=and_gw.split.id,
        targetRef=xor_split.id,
        id=and_gw.split.id + xor_split.id,
    )
    xor_to_join_arc = Flow(
        sourceRef=xor_join.id, targetRef=and_gw.join.id, id=xor_join.id + and_gw.join.id
    )
    flow_out_to_xor_arc = clone_flow(and_gw.flow_out_split, new_source=xor_split)
    flow_in_to_xor_arc = clone_flow(and_gw.flow_in_join, new_target=xor_join)

    bpmn.remove_flow(and_gw.flow_out_split)
    bpmn.remove_flow(and_gw.flow_in_join)
    bpmn.add_constructed_flow(flow_out_to_xor_arc)
    bpmn.add_constructed_flow(flow_in_to_xor_arc)
    bpmn.add_constructed_flow(split_to_xor_arc)
    bpmn.add_constructed_flow(xor_to_join_arc)

    # handle connection silent activity
    xor_split_to_silent_activity_arc = Flow(
        sourceRef=xor_split.id,
        targetRef=silent_activity.id,
        id=xor_split.id + silent_activity.id,
    )
    silent_activity_to_xor_join_arc = Flow(
        sourceRef=silent_activity.id,
        targetRef=xor_join.id,
        id=silent_activity.id + xor_join.id,
    )
    bpmn.add_constructed_flow(xor_split_to_silent_activity_arc)
    bpmn.add_constructed_flow(silent_activity_to_xor_join_arc)
    bpmn.add_node(silent_activity)
    bpmn.add_node(xor_split)
    bpmn.add_node(xor_join)


def replace_inclusive_to_parallel(bpmn: Process, gw: OrGateway):
    """Replace OR-Gateways and the flows with AND-Gateways."""
    flow_map: dict[str, Flow] = {}
    pw_gw = AndGateway(id="OR" + gw.id)
    bpmn.add_node(pw_gw)
    in_arcs: set[Flow] = bpmn.get_incoming(gw.id).copy()
    out_arcs: set[Flow] = bpmn.get_outgoing(gw.id).copy()
    for arc in in_arcs:
        bpmn.remove_flow(arc)
        new_arc = bpmn.add_flow(
            bpmn.get_node(arc.sourceRef), pw_gw, "OR_" + arc.id, arc.name
        )
        flow_map[arc.id] = new_arc
    for arc in out_arcs:
        bpmn.remove_flow(arc)
        new_arc = bpmn.add_flow(
            pw_gw, bpmn.get_node(arc.targetRef), "OR_" + arc.id, arc.name
        )
        flow_map[arc.id] = new_arc
    bpmn.remove_node(gw)
    return pw_gw, flow_map


def inclusive_gws_to_parallel_gws(bpmn: Process, gws: list[InclusiveGatewayBridge]):
    """Replace OR- with AND-Gateways and save the the bridge."""
    gw_map: dict[OrGateway, AndGateway] = {}
    new_bridges: list[ParallelGatewayBridge] = []
    arc_map: dict[str, Flow] = {}
    for bridge in gws:
        if bridge.split not in gw_map:
            new_split, new_arc_map = replace_inclusive_to_parallel(bpmn, bridge.split)
            arc_map = {**arc_map, **new_arc_map}
            gw_map[bridge.split] = new_split
        if bridge.join not in gw_map:
            new_join, new_arc_map = replace_inclusive_to_parallel(bpmn, bridge.join)
            arc_map = {**arc_map, **new_arc_map}
            gw_map[bridge.join] = new_join
        new_bridges.append(
            ParallelGatewayBridge(
                gw_map[bridge.split],
                gw_map[bridge.join],
                arc_map[bridge.flow_out_split.id],
                arc_map[bridge.flow_in_join.id],
            )
        )
    return new_bridges


def replace_inclusive_gateways(in_bpmn: Process):
    """Replace OR gateways with a combination of AND- and XOR-Gateways."""
    logger.debug("Replacing inclusive (OR) gateways")
    nodes = in_bpmn._flatten_node_typ_map()
    inclusive_gateways: list[OrGateway] = [
        node for node in nodes if isinstance(node, OrGateway)
    ]
    logger.debug(f"Found {len(inclusive_gateways)} inclusive gateways")
    if len(inclusive_gateways) == 0:
        return

    matched_inclusive_bridges = find_matching_gateways(in_bpmn, inclusive_gateways)
    logger.debug(f"Matched {len(matched_inclusive_bridges)} inclusive gateway pairs")
    parallel_bridges = inclusive_gws_to_parallel_gws(in_bpmn, matched_inclusive_bridges)

    for bridge in parallel_bridges:
        add_xors_and_activities(in_bpmn, bridge)
