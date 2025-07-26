"""Methods to initiate a bpmn to petri net transformation."""

from collections.abc import Callable

from exceptions import InternalTransformationException
from transformer.models.bpmn.base import Gateway, GenericBPMNNode
from transformer.models.bpmn.bpmn import (
    EventGateway,
    BPMN,
    AndGateway,
    EndEvent,
    GenericTask,
    IntermediateCatchEvent,
    OrGateway,
    Process,
    StartEvent,
    ServiceTask,
    UserTask,
    XorGateway,
)
from transformer.models.pnml.pnml import Net, Place, Pnml, Transition
from transformer.models.pnml.workflow import WorkflowBranchingType
from transformer.transform_bpmn_to_petrinet.participants import (
    create_participant_mapping,
    set_global_toolspecifi,
)
from transformer.transform_bpmn_to_petrinet.preprocess_bpmn import (
    adjacent_inserter,
    all_gateways,
    or_gateways,
)
from transformer.transform_bpmn_to_petrinet.transform_workflow_helper import (
    handle_gateways,
    handle_resource_annotations,
    handle_subprocesses,
    handle_triggers,
)
from transformer.utility.pnml import find_triggers
from transformer.utility.utility import create_silent_node_name


def merge_single_triggers(net: Net):
    """If trigger transition is before a non-trigger merge both elements.

    Place -> Trigger Transition -> Place -> Non-trigger transition
    to
    Place -> Merged transition
    """
    triggers = find_triggers(net)
    for trigger in triggers:
        # not clear how to merge a trigger if it is a split/join itself
        if net.get_out_degree(trigger) > 1 or net.get_in_degree(trigger) > 1:
            continue

        # no following element to merge with
        if net.get_out_degree(trigger) == 0:
            continue

        connecting_place = net.get_element(list(net.get_outgoing(trigger.id))[0].target)

        # no following element to merge with
        if net.get_out_degree(connecting_place) == 0:
            continue

        # not clear how to merge the following element of a split/join place
        target_transitions = [
            net.get_element(x.target) for x in net.get_outgoing(id=connecting_place.id)
        ]
        place_is_before_wf_split = all(
            [
                x.get_workflow_operator_type()
                in {WorkflowBranchingType.XorSplit, WorkflowBranchingType.AndSplit}
                for x in target_transitions
            ]
        )
        if not place_is_before_wf_split and (
            net.get_out_degree(connecting_place) > 1
            or net.get_in_degree(connecting_place) > 1
        ):
            continue

        target_transition = target_transitions[0]

        # Cant merge with existing trigger (event or resource) or subprocess
        if (
            target_transition.is_workflow_trigger()
            or target_transition.is_workflow_subprocess()
        ):
            continue

        # not clear how to merge the target if it is a join itself
        # Also check WF joins
        if net.get_in_degree(
            target_transition
        ) > 1 or target_transition.get_workflow_operator_type() in {
            WorkflowBranchingType.XorJoin,
            WorkflowBranchingType.AndJoin,
            WorkflowBranchingType.XorJoinAndSplit,
            WorkflowBranchingType.AndJoinXorSplit,
            WorkflowBranchingType.XorJoinSplit,
            WorkflowBranchingType.AndJoinSplit,
        }:
            continue

        incoming_trigger_arcs = net.get_incoming_and_remove_arcs(trigger)
        net.remove_element_with_connecting_arcs(connecting_place)
        net.remove_element(trigger)

        if trigger.is_workflow_message():
            for transition in target_transitions:
                transition.mark_as_workflow_message()
        elif trigger.is_workflow_time():
            for transition in target_transitions:
                transition.mark_as_workflow_time()

        for transition in target_transitions:
            net.connect_to_element(transition, incoming_trigger_arcs)


def transform_bpmn_to_petrinet(
    bpmn: Process,
    organization: str = "DEFAULT ORGANIZATION",
):
    """Transform a BPMN to ST or WOPED workflow Net."""
    pnml = Pnml.generate_empty_net(bpmn.id)
    net = pnml.net
    nodes = set(bpmn._flatten_node_typ_map())

    # find workflow specific nodes
    to_handle_gateways: list[Gateway] = []
    to_handle_user_tasks: list[UserTask] = []
    to_handle_subprocesses: list[Process] = []
    to_handle_triggers: list[IntermediateCatchEvent] = []

    for node in nodes:
        if isinstance(node, Process):
            to_handle_subprocesses.append(node)
        elif isinstance(node, Gateway):
            to_handle_gateways.append(node)
        elif isinstance(node, IntermediateCatchEvent):
            to_handle_triggers.append(node)
        elif isinstance(node, UserTask):
            to_handle_user_tasks.append(node)

    nodes = nodes.difference(
        to_handle_gateways, to_handle_subprocesses, to_handle_triggers
    )

    # handle normals nodes
    for node in nodes:
        if isinstance(node, GenericTask | AndGateway | IntermediateCatchEvent):
            name = node.name
            if isinstance(node, UserTask):
                name = f"[UserTask] {node.name}"
            elif isinstance(node, ServiceTask):
                name = f"[ServiceTask] {node.name}"

            net.add_element(
                Transition.create(
                    id=node.id,
                    name=(
                        name
                        if name != ""
                        or node.get_in_degree() > 1
                        or node.get_out_degree() > 1
                        else None
                    ),
                )
            )
        elif isinstance(
            node,
            OrGateway
            | XorGateway
            | StartEvent
            | EndEvent
            | GenericBPMNNode
            | EventGateway,
        ):
            net.add_element(Place(id=node.id))
        else:
            raise InternalTransformationException(f"{type(node)} not supported")
    # handle workflow specific nodes
    handle_subprocesses(
        net, bpmn, to_handle_subprocesses, organization, transform_bpmn_to_petrinet
    )
    handle_triggers(net, bpmn, to_handle_triggers)
    handle_gateways(net, bpmn, to_handle_gateways)
    handle_resource_annotations(
        net, to_handle_user_tasks, bpmn._participant_mapping, organization
    )

    # handle remaining flows
    for flow in bpmn.flows:
        source = net.get_node_or_none(flow.sourceRef)
        target = net.get_node_or_none(flow.targetRef)
        if source is None or target is None:
            continue
        if isinstance(source, Place) and isinstance(target, Place):
            t = net.add_element(
                Transition(id=create_silent_node_name(source.id, target.id))
            )
            net.add_arc(source, t)
            net.add_arc(t, target)
        elif isinstance(source, Transition) and isinstance(target, Transition):
            p = net.add_element(Place(id=create_silent_node_name(source.id, target.id)))
            net.add_arc(source, p)
            net.add_arc(p, target)
        else:
            net.add_arc(source, target)

    # Post processing
    merge_single_triggers(net)

    return pnml


def apply_preprocessing(bpmn: Process, funcs: list[Callable[[Process], None]]):
    """Recursively apply preprocessing to each process and subprocess."""
    for p in bpmn.subprocesses:
        apply_preprocessing(p, funcs)

    for f in funcs:
        f(bpmn)


def bpmn_to_workflow_net(bpmn: BPMN):
    """Return a processed and transformed workflow net of process."""
    create_participant_mapping(bpmn.process)
    apply_preprocessing(
        bpmn.process,
        [
            or_gateways.replace_inclusive_gateways,
            all_gateways.preprocess_gateways,
            adjacent_inserter.insert_temp_between_adjacent_mapped_transition,
        ],
    )
    organization_name = (
        bpmn.collaboration.participant.name or "Default"
        if bpmn.collaboration and bpmn.collaboration.participant
        else "Default"
    )
    pnml = transform_bpmn_to_petrinet(bpmn.process, organization_name)
    set_global_toolspecifi(
        pnml.net, bpmn.process._participant_mapping, organization_name
    )
    return pnml


def bpmn_to_wf_net_from_xml(bpmn_xml: str):
    """Return a processed and transformed workflow net of process from xml str."""
    bpmn = BPMN.from_xml(bpmn_xml)
    return bpmn_to_workflow_net(bpmn)
