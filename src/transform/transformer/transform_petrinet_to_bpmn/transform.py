"""Initiate the preprocessing and transformation of pnml to bpmn."""

import logging
from collections.abc import Callable

from transformer.models.bpmn.base import Gateway
from transformer.models.bpmn.bpmn import (
    BPMN,
    AndGateway,
    EndEvent,
    Process,
    StartEvent,
    Task,
    XorGateway,
)
from transformer.models.pnml.pnml import Net, Pnml
from transformer.models.pnml.transform_helper import (
    GatewayHelperPNML,
    TriggerHelperPNML,
)
from transformer.transform_petrinet_to_bpmn.preprocess_pnml import (
    dangling_transition,
    event_trigger,
    vanilla_gateway_transition,
    workflow_operators,
)
from transformer.transform_petrinet_to_bpmn.workflow_helper import (
    annotate_resources,
    find_workflow_subprocesses,
    handle_event_triggers,
    handle_resource_transitions,
    handle_workflow_operators,
    handle_workflow_subprocesses,
)
from transformer.utility.utility import create_arc_name

logger = logging.getLogger(__name__)


def remove_silent_tasks(bpmn: Process):
    """Remove silent tasks (Without name)."""
    for task in bpmn.tasks.copy():
        if task.name is not None:
            continue
        source_id, target_id = bpmn.remove_node_with_connecting_flows(task)
        bpmn.add_flow(bpmn.get_node(source_id), bpmn.get_node(target_id))


def remove_unnecessary_gateways(bpmn: Process):
    """Remove unnecessary gateways (In and out degree == 1)."""
    is_rerun_reduce = True
    while is_rerun_reduce:
        is_rerun_reduce = False

        gw_nodes = [
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

            is_rerun_reduce = True


def transform_petrinet_to_bpmn(net: Net):
    """Initiate the transformation of a preprocessed petri net to bpmn."""
    logger.debug("Starting Petri net to BPMN transformation", extra={
        "net_id": net.id,
        "places": len(net.places),
        "transitions": len(net.transitions),
    })
    
    bpmn_general = BPMN.generate_empty_bpmn(net.id or "new_net")
    bpmn = bpmn_general.process

    transitions = net.transitions.copy()
    places = net.places.copy()

    # find workflow specific elements
    to_handle_subprocesses = find_workflow_subprocesses(net)
    transitions.difference_update(to_handle_subprocesses)

    to_handle_temp_gateways = [
        elem
        for elem in net._flatten_node_typ_map()
        if isinstance(elem, GatewayHelperPNML)
    ]

    to_handle_temp_triggers = [
        elem
        for elem in net._flatten_node_typ_map()
        if isinstance(elem, TriggerHelperPNML)
    ]

    # Only transitions could be  be mapped to usertasks
    to_handle_temp_resources = [
        transition
        for transition in transitions
        if transition.is_workflow_resource()
        and net.get_in_degree(transition) <= 1
        and net.get_out_degree(transition) <= 1
    ]
    transitions.difference_update(to_handle_temp_resources)

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
    handle_resource_transitions(bpmn, to_handle_temp_resources)
    handle_workflow_operators(bpmn, to_handle_temp_gateways)
    handle_event_triggers(bpmn, to_handle_temp_triggers)
    handle_workflow_subprocesses(
        net, bpmn, to_handle_subprocesses, transform_petrinet_to_bpmn
    )

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
    logger.debug("Running post-processing: removing silent tasks")
    remove_silent_tasks(bpmn)
    
    logger.debug("Running post-processing: removing unnecessary gateways")
    remove_unnecessary_gateways(bpmn)

    logger.debug("Petri net to BPMN transformation completed", extra={
        "tasks": len(bpmn.tasks),
        "gateways": len([n for n in bpmn._flatten_node_typ_map() if isinstance(n, Gateway)]),
        "flows": len(bpmn.flows),
    })

    return bpmn_general


def apply_preprocessing(net: Net, funcs: list[Callable[[Net], None]]):
    """Recursively apply each preprocessing to the net and each page."""
    for p in net.pages:
        apply_preprocessing(p.net, funcs)

    for f in funcs:
        f(net)


def pnml_to_bpmn(pnml: Pnml):
    """Process and transform a petri net to bpmn."""
    logger.info("Starting PNML to BPMN conversion")
    
    net = pnml.net
    logger.debug("Input net details", extra={
        "net_id": net.id,
        "places": len(net.places),
        "transitions": len(net.transitions),
        "arcs": len(net.arcs),
    })

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
    
    logger.info("PNML to BPMN conversion completed")
    return bpmn
