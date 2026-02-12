"""Initiate the preprocessing and transformation of pnml to bpmn."""

import logging
from collections.abc import Callable

from app.transform.transformer.models.bpmn.base import Gateway
from app.transform.transformer.models.bpmn.bpmn import (
    BPMN,
    AndGateway,
    EndEvent,
    Process,
    StartEvent,
    Task,
    XorGateway,
)
from app.transform.transformer.models.pnml.pnml import Net, Pnml, Transition
from app.transform.transformer.models.pnml.transform_helper import (
    GatewayHelperPNML,
    TriggerHelperPNML,
)
from app.transform.transformer.transform_petrinet_to_bpmn.preprocess_pnml import (
    dangling_transition,
    event_trigger,
    vanilla_gateway_transition,
    workflow_operators,
)
from app.transform.transformer.transform_petrinet_to_bpmn.workflow_helper import (
    annotate_resources,
    find_workflow_subprocesses,
    handle_event_triggers,
    handle_resource_transitions,
    handle_workflow_operators,
    handle_workflow_subprocesses,
)
from app.transform.transformer.utility.utility import create_arc_name

logger = logging.getLogger(__name__)


def remove_silent_tasks(bpmn: Process):
    """Remove silent tasks (Without name)."""
    logger.debug(f"Removing silent tasks from process {bpmn.id}")
    removed_count = 0
    for task in bpmn.tasks.copy():
        if task.name is not None:
            continue
        source_id, target_id = bpmn.remove_node_with_connecting_flows(task)
        bpmn.add_flow(bpmn.get_node(source_id), bpmn.get_node(target_id))
        removed_count += 1
    logger.debug(f"Removed {removed_count} silent tasks")


def remove_unnecessary_gateways(bpmn: Process):
    """Remove unnecessary gateways (In and out degree == 1)."""
    logger.debug(f"Removing unnecessary gateways from process {bpmn.id}")
    total_removed = 0
    is_rerun_reduce = True
    while is_rerun_reduce:
        is_rerun_reduce = False

        gw_nodes: list[Gateway] = [
            node
            for node in bpmn._flatten_node_typ_map()
            if issubclass(type(node), Gateway)
        ]
        for gw_node in gw_nodes:
            if gw_node.get_in_degree() > 1 or gw_node.get_out_degree() > 1:
                continue
            if gw_node.get_in_degree() == 0 or gw_node.get_out_degree() == 0:
                continue

            source_id, target_id = bpmn.remove_node_with_connecting_flows(gw_node)
            new_flow_id = create_arc_name(source_id, target_id)
            if new_flow_id in bpmn._temp_flows:
                continue

            bpmn.add_flow(
                bpmn.get_node(source_id), bpmn.get_node(target_id), id=new_flow_id
            )
            total_removed += 1
            is_rerun_reduce = True
    logger.debug(f"Removed {total_removed} unnecessary gateways")


def transform_petrinet_to_bpmn(net: Net):
    """Initiate the transformation of a preprocessed petri net to bpmn."""
    logger.debug(f"Starting transform_petrinet_to_bpmn for net: {net.id}")
    logger.debug(
        f"Net contains {len(net.places)} places, {len(net.transitions)} transitions, {len(net.arcs)} arcs"
    )

    bpmn_general = BPMN.generate_empty_bpmn(net.id or "new_net")
    bpmn = bpmn_general.process

    transitions = net.transitions.copy()
    places = net.places.copy()

    # find workflow specific elements
    logger.debug("Identifying workflow-specific elements")
    to_handle_subprocesses = find_workflow_subprocesses(net)
    transitions.difference_update(to_handle_subprocesses)
    logger.debug(f"Found {len(to_handle_subprocesses)} subprocesses")

    to_handle_temp_gateways: list[GatewayHelperPNML] = [
        elem
        for elem in net._flatten_node_typ_map()
        if isinstance(elem, GatewayHelperPNML)
    ]

    to_handle_temp_triggers: list[TriggerHelperPNML] = [
        elem
        for elem in net._flatten_node_typ_map()
        if isinstance(elem, TriggerHelperPNML)
    ]

    # Only transitions could be  be mapped to usertasks
    to_handle_temp_resources: list[Transition] = [
        transition
        for transition in transitions
        if transition.is_workflow_resource()
        and net.get_in_degree(transition) <= 1
        and net.get_out_degree(transition) <= 1
    ]
    transitions.difference_update(to_handle_temp_resources)

    logger.debug(f"Processing {len(places)} places and {len(transitions)} transitions")
    logger.debug(
        f"Workflow elements - Gateways: {len(to_handle_temp_gateways)}, Triggers: {len(to_handle_temp_triggers)}, Resources: {len(to_handle_temp_resources)}"
    )

    # handle normal places
    for place in places:
        in_degree, out_degree = net.get_in_degree(place), net.get_out_degree(place)
        if in_degree == 0:
            bpmn.add_node(StartEvent(id=place.id, name=place.get_name()))
        elif out_degree == 0:
            bpmn.add_node(EndEvent(id=place.id, name=place.get_name()))
        else:
            bpmn.add_node(XorGateway(id=place.id, name=place.get_name()))

    # handle normal transitions
    for transition in transitions:
        in_degree, out_degree = (
            net.get_in_degree(transition),
            net.get_out_degree(transition),
        )
        if in_degree == 0:
            bpmn.add_node(StartEvent(id=transition.id, name=transition.get_name()))
        elif out_degree == 0:
            bpmn.add_node(EndEvent(id=transition.id, name=transition.get_name()))
        elif in_degree == 1 and out_degree == 1:
            bpmn.add_node(Task(id=transition.id, name=transition.get_name()))
        else:
            bpmn.add_node(AndGateway(id=transition.id, name=transition.get_name()))

    # handle workflow specific elements
    logger.debug("Processing workflow-specific elements")
    handle_resource_transitions(bpmn, to_handle_temp_resources)
    handle_workflow_operators(bpmn, to_handle_temp_gateways)
    handle_event_triggers(bpmn, to_handle_temp_triggers)
    handle_workflow_subprocesses(
        net, bpmn, to_handle_subprocesses, transform_petrinet_to_bpmn
    )
    logger.debug("Completed workflow-specific element processing")

    # handle remaining arcs
    for arc in net.arcs:
        source_in_nodes = arc.source in net._temp_elements
        target_in_nodes = arc.target in net._temp_elements
        if not source_in_nodes or not target_in_nodes:
            continue
        source = bpmn.get_node(arc.source)
        target = bpmn.get_node(arc.target)
        bpmn.add_flow(source, target)

    # Postprocessing
    logger.debug("Starting postprocessing")
    remove_silent_tasks(bpmn)
    remove_unnecessary_gateways(bpmn)
    logger.debug(
        f"Transformation completed - BPMN has {len(bpmn._flatten_node_typ_map())} nodes and {len(bpmn.flows)} flows"
    )

    return bpmn_general


def apply_preprocessing(net: Net, funcs: list[Callable[[Net], None]]):
    """Recursively apply each preprocessing to the net and each page."""
    for p in net.pages:
        apply_preprocessing(p.net, funcs)

    for f in funcs:
        f(net)


def pnml_to_bpmn(pnml: Pnml):
    """Process and transform a petri net to bpmn."""
    logger.debug("Starting pnml_to_bpmn")
    net = pnml.net

    logger.debug("Applying preprocessing steps")
    apply_preprocessing(
        net,
        [
            dangling_transition.add_places_at_dangling_transitions,
            workflow_operators.handle_workflow_operators,
            vanilla_gateway_transition.split_and_gw_with_name,
            event_trigger.split_event_triggers,
        ],
    )
    logger.debug("Preprocessing completed")

    bpmn = transform_petrinet_to_bpmn(net)

    logger.debug("Annotating resources")
    annotate_resources(net, bpmn)
    logger.debug("pnml_to_bpmn completed")
    return bpmn
