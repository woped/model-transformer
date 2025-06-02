"""Helper methods for bpmn to workflow net."""

from collections.abc import Callable
from typing import cast

from exceptions import (
    InternalTransformationException,
    UnknownIntermediateCatchEvent,
    WrongSubprocessDegree,
)
from transformer.models.bpmn.base import Gateway, GenericBPMNNode
from transformer.models.bpmn.bpmn import (
    EventGateway,
    AndGateway,
    IntermediateCatchEvent,
    Process,
    UserTask,
    XorGateway,
)
from transformer.models.pnml.base import NetElement
from transformer.models.pnml.pnml import (
    Net,
    Page,
    Place,
    Pnml,
    Transition,
)
from transformer.models.pnml.workflow import WorkflowBranchingType
from transformer.utility.bpmn import find_end_events, find_start_events
from transformer.utility.utility import create_arc_name, create_silent_node_name


def create_workflow_operator_helper_transition(
    net: Net, id: str, name: str | None, i: int, t: WorkflowBranchingType
):
    """Return a transition as a workflow operator helper element."""
    transition = net.add_element(Transition.create(id=f"{id}_op_{i}", name=name))
    transition.mark_as_workflow_operator(t, id)
    return transition


def add_arc(net: Net, source: NetElement, target: NetElement):
    """Add arc between source and target net elements for a net."""
    if type(source) is not type(target):
        net.add_arc(source, target, create_arc_name(source.id, target.id))
    elif isinstance(source, Place):
        t = net.add_element(
            Transition.create(create_silent_node_name(source.id, target.id))
        )
        net.add_arc(source, t, create_arc_name(source.id, t.id))
        net.add_arc(t, target, create_arc_name(t.id, target.id))
    elif isinstance(source, Transition):
        # check if actually name was used to create place or original id was used for id
        p = net.add_element(Place.create(create_silent_node_name(source.id, target.id)))
        net.add_arc(source, p, create_arc_name(source.id, p.id))
        net.add_arc(p, target, create_arc_name(p.id, target.id))
    else:
        raise InternalTransformationException("invalid petrinet node")


def add_wf_xor_split(
    net: Net,
    in_place: NetElement,
    out_places: list[NetElement],
    id: str,
    name: str | None,
):
    """Add workflow xor split for in place and out places."""
    for i, out in enumerate(out_places):
        t = create_workflow_operator_helper_transition(
            net, id, name, i + 1, WorkflowBranchingType.XorSplit
        )
        add_arc(net, in_place, t)
        add_arc(net, t, out)


def add_wf_xor_join(
    net: Net,
    out_place: NetElement,
    in_places: list[NetElement],
    id: str,
    name: str | None,
):
    """Add workflow xor join for  in places and out place."""
    for i, in_place in enumerate(in_places):
        t = create_workflow_operator_helper_transition(
            net, id, name, i + 1, WorkflowBranchingType.XorJoin
        )
        add_arc(net, in_place, t)
        add_arc(net, t, out_place)


def add_wf_and_split(
    net: Net,
    in_place: NetElement,
    out_places: list[NetElement],
    id: str,
    name: str | None,
):
    """Add workflow and split for in place and out places."""
    t = create_workflow_operator_helper_transition(
        net, id, name, 1, WorkflowBranchingType.AndSplit
    )
    add_arc(net, in_place, t)
    for out in out_places:
        add_arc(net, t, out)


def add_wf_and_join(
    net: Net,
    out_place: NetElement,
    in_places: list[NetElement],
    id: str,
    name: str | None,
):
    """Add workflow and join for  in places and out place."""
    t = create_workflow_operator_helper_transition(
        net, id, name, 1, WorkflowBranchingType.AndJoin
    )
    add_arc(net, t, out_place)
    for in_place in in_places:
        add_arc(net, in_place, t)


def add_wf_xor_split_join(
    net: Net,
    in_places: list[NetElement],
    out_places: list[NetElement],
    id: str,
    name: str | None,
):
    """Add workflow xor split-join for in places and out places."""
    linking_place = net.add_element(Place.create(id=f"P_CENTER_{id}"))
    linking_place.mark_as_workflow_operator(WorkflowBranchingType.XorJoinSplit, id)

    for i, in_place in enumerate(in_places):
        t = create_workflow_operator_helper_transition(
            net, id, name, i + 1, WorkflowBranchingType.XorJoinSplit
        )
        add_arc(net, in_place, t)
        add_arc(net, t, linking_place)

    for i, out in enumerate(out_places):
        t = create_workflow_operator_helper_transition(
            net, id, name, i + 1 + len(in_places), WorkflowBranchingType.XorJoinSplit
        )
        add_arc(net, t, out)
        add_arc(net, linking_place, t)


def add_wf_and_split_join(
    net: Net,
    in_places: list[NetElement],
    out_places: list[NetElement],
    id: str,
    name: str | None,
):
    """Add workflow and split-join for in places and out places."""
    t = create_workflow_operator_helper_transition(
        net, id, name, 1, WorkflowBranchingType.AndJoinSplit
    )
    for in_place in in_places:
        add_arc(net, in_place, t)
    for out in out_places:
        add_arc(net, t, out)


type_map = {
    XorGateway: (add_wf_xor_split, add_wf_xor_join, add_wf_xor_split_join),
    AndGateway: (add_wf_and_split, add_wf_and_join, add_wf_and_split_join),
    EventGateway: (add_wf_xor_split, add_wf_xor_join, add_wf_xor_split_join),
}


def handle_gateways(net: Net, bpmn: Process, gateways: list[Gateway]):
    """Handle gateway transformation to workflow operators."""
    for gateway in gateways:
        handle_gateway(net, bpmn, gateway)


def handle_gateway(net: Net, bpmn: Process, node: GenericBPMNNode):
    """Transform a gateway to workflow operator."""
    node_type = type(node)
    f_split, f_join, f_split_join = type_map[node_type]  # type: ignore
    in_degree, out_degree = node.get_in_degree(), node.get_out_degree()
    in_flows, out_flows = bpmn.get_incoming(node.id), bpmn.get_outgoing(node.id)
    source_ids, target_ids = (
        [f.sourceRef for f in in_flows],
        [f.targetRef for f in out_flows],
    )
    for id in [*in_flows, *out_flows]:
        bpmn.remove_flow(id)
    net_sources = sorted(
        [cast(NetElement, net.get_element(x)) for x in source_ids], key=lambda x: x.id
    )
    net_targets = sorted(
        [cast(NetElement, net.get_element(x)) for x in target_ids], key=lambda x: x.id
    )

    if not node.name:
        node.name = ""
    # split
    if in_degree == 1:
        f_split(
            net,
            net_sources[0],
            net_targets,
            node.id,
            node.name,
        )
    # join
    elif out_degree == 1:
        f_join(net, net_targets[0], net_sources, node.id, node.name)
    # split and join
    else:
        f_split_join(net, net_sources, net_targets, node.id, node.name)


def handle_triggers(net: Net, bpmn: Process, triggers: list[IntermediateCatchEvent]):
    """Handle time and message related intermediate events (triggers)."""
    for trigger in triggers:
        if trigger.is_time():
            net.add_element(
                Transition.create(
                    id=trigger.id, name=trigger.name
                ).mark_as_workflow_time()
            )
        elif trigger.is_message:
            net.add_element(
                Transition.create(
                    id=trigger.id, name=trigger.name
                ).mark_as_workflow_message()
            )
        else:
            raise UnknownIntermediateCatchEvent()


def handle_subprocesses(
    net: Net,
    bpmn: Process,
    subprocesses: list[Process],
    organization: str,
    caller_func: Callable[[Process, str], Pnml],
):
    """Transform a BPMN subprocess to workflow subprocess."""
    for subprocess in subprocesses:
        if subprocess.get_in_degree() != 1 or subprocess.get_out_degree() != 1:
            raise WrongSubprocessDegree()

        subprocess_transition = net.add_element(
            Transition.create(
                subprocess.id, subprocess.name
            ).mark_as_workflow_subprocess()
        )

        # WOPED subprocess start and endplaces must have the same id as the incoming/
        # outgoing node of the subprocess

        outer_in_flows, outer_out_flows = (
            list(bpmn.get_incoming(subprocess.id)),
            list(bpmn.get_outgoing(subprocess.id)),
        )

        outer_in_id, outer_out_id = (
            outer_in_flows[0].sourceRef,
            outer_out_flows[0].targetRef,
        )

        outer_in, outer_out = (
            net.get_element(outer_in_id),
            net.get_element(outer_out_id),
        )
        # if incoming/outgoing is from type transition a place will inserted after
        # the handling of the workflow elements
        # -> actual id of subprocess start/endevents must have id of new place
        if isinstance(outer_in, Transition):
            outer_in_id = create_silent_node_name(outer_in.id, subprocess_transition.id)
        if isinstance(outer_out, Transition):
            outer_out_id = create_silent_node_name(
                subprocess_transition.id, outer_out.id
            )

        sub_se, sub_ee = find_start_events(subprocess)[0], find_end_events(subprocess)[0]
        subprocess.change_node_id(sub_se, outer_in_id)
        subprocess.change_node_id(sub_ee, outer_out_id)

        # transform inner subprocess
        inner_net = caller_func(subprocess, organization).net
        inner_net.id = None

        net.add_page(Page(id=subprocess.id, net=inner_net))


def handle_resource_annotations(
    net: Net,
    user_tasks: list[UserTask],
    participant_mapping: dict[str, str],
    orga: str,
):
    """Handle the annotation of the transformed transitions from usertasks."""
    if len(participant_mapping) == 0:
        return

    for user_task in user_tasks:
        if user_task.id not in participant_mapping:
            continue
        net.get_element(user_task.id).mark_as_workflow_resource(
            participant_mapping[user_task.id], orga
        )
