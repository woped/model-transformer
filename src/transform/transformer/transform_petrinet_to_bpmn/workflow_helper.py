from typing import Callable, Optional

from pydantic import BaseModel, Field

from transformer.models.bpmn.base import GenericBPMNNode
from transformer.models.bpmn.bpmn import BPMN, AndGateway, Process, XorGateway
from transformer.models.pnml.base import NetElement
from transformer.models.pnml.pnml import Arc, Net, Page, Transition
from transformer.models.pnml.workflow import WorkflowBranchingType


class WorkflowOperatorWrapper(BaseModel):
    id: str
    name: Optional[str] = None
    t: WorkflowBranchingType

    # all operator nodes
    nodes: list[NetElement] = Field(default_factory=list)
    # non-opeartor nodes connected to opeartor nodes
    incoming_nodes: set[NetElement] = Field(default_factory=set)
    outgoing_nodes: set[NetElement] = Field(default_factory=set)
    # arcs onnceting non-operator nodes to operator nodes
    incoming_arcs: set[Arc] = Field(default_factory=set)
    outgoing_arcs: set[Arc] = Field(default_factory=set)
    # arcs connected to operator nodes
    all_arcs: set[Arc] = Field(default_factory=set)


def find_workflow_subprocesses(net: Net):
    return [e for e in net.transitions if e.is_workflow_subprocess()]


def find_workflow_operators(net: Net):
    operator_map: dict[str, list[NetElement]] = {}
    for node in net._temp_elements.values():
        if isinstance(node, Page):
            continue
        if not node.is_workflow_operator():
            continue
        if not node.toolspecific or not node.toolspecific.operator:
            raise Exception("invalid")
        op_id = node.toolspecific.operator.id
        if op_id not in operator_map:
            operator_map[op_id] = []
        operator_map[op_id].append(node)
    operator_wrappers: list[WorkflowOperatorWrapper] = []
    for op_id, operators in operator_map.items():
        o = WorkflowOperatorWrapper(
            t=operators[0].toolspecific.operator.type,  # type: ignore
            nodes=operators,
            id=operators[0].toolspecific.operator.id,  # type: ignore
            name=operators[0].get_name(),
        )
        operator_wrappers.append(o)

        for operator in operators:
            for incoming in net.get_incoming(operator.id):
                o.all_arcs.add(incoming)
                if net.get_element(incoming.source) in operators:
                    continue
                o.incoming_nodes.add(net.get_element(incoming.source))
                o.incoming_arcs.add(incoming)

            for outgoing in net.get_outgoing(operator.id):
                o.all_arcs.add(outgoing)
                if net.get_element(outgoing.target) in operators:
                    continue
                o.outgoing_nodes.add(net.get_element(outgoing.target))
                o.outgoing_arcs.add(outgoing)
    return operator_wrappers


def handle_workflow_subprocesses(
    net: Net,
    bpmn: Process,
    to_handle_subprocesses: list[Transition],
    caller_func: Callable[[Net], BPMN],
):
    for subprocess_transition in to_handle_subprocesses:
        sb_id = subprocess_transition.id
        page = net.get_page(sb_id)
        page_net = page.net

        outer_source_id = list(net.get_incoming(sb_id))[0].source
        outer_sink_id = list(net.get_outgoing(sb_id))[0].target

        inner_source_id, inner_sink_id = (
            page_net.get_element(outer_source_id),
            page_net.get_element(outer_sink_id),
        )

        if (
            page_net.get_in_degree(inner_source_id) > 0
            or page_net.get_out_degree(inner_sink_id) > 0
        ):
            raise Exception(
                "currently source/sink in subprocess must have no incoming/outgoing arcs to convert to BPMN Start and Endevents"
            )

        inner_bpmn = caller_func(page_net).process
        inner_bpmn.id = sb_id
        inner_bpmn.name = subprocess_transition.get_name()
        bpmn.add_node(inner_bpmn)


def handle_workflow_operators(
    net: Net, bpmn: Process, to_handle_operators: list[WorkflowOperatorWrapper]
):
    for workflow_operator in to_handle_operators:
        new_gateway: GenericBPMNNode
        if workflow_operator.t in {
            WorkflowBranchingType.AndJoin,
            WorkflowBranchingType.AndSplit,
            WorkflowBranchingType.AndJoinSplit,
        }:
            new_gateway = bpmn.add_node(
                AndGateway(id=workflow_operator.id, name=workflow_operator.name)
            )

        elif workflow_operator.t in {
            WorkflowBranchingType.XorJoin,
            WorkflowBranchingType.XorSplit,
            WorkflowBranchingType.XorJoinSplit,
        }:
            new_gateway = bpmn.add_node(
                XorGateway(id=workflow_operator.id, name=workflow_operator.name)
            )
        # Add incoming,outgoing flows
        for in_place in workflow_operator.incoming_nodes:
            bpmn.add_flow(bpmn.get_node(in_place.id), new_gateway)
        for out_place in workflow_operator.outgoing_nodes:
            bpmn.add_flow(new_gateway, bpmn.get_node(out_place.id))
        # remove original arcs
        for arc in workflow_operator.all_arcs:
            net.remove_arc(arc)