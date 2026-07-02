"""Validation tests for transition connection rules in BPMN->PNML transformation."""

from app.transform.transformer.models.bpmn.bpmn import (
    BPMN,
    AndGateway,
    EndEvent,
    Flow,
    StartEvent,
    Task,
)
from app.transform.transformer.models.pnml.pnml import Place
from app.transform.transformer.models.pnml.workflow import WorkflowBranchingType
from app.transform.transformer.transform_bpmn_to_petrinet.transform import (
    bpmn_to_workflow_net,
)


def _build_join_split_case() -> BPMN:
    bpmn = BPMN.generate_empty_bpmn("join_split_case")
    process = bpmn.process
    nodes = [
        StartEvent(id="S1"),
        StartEvent(id="S2"),
        EndEvent(id="E1"),
        EndEvent(id="E2"),
        AndGateway(id="GW", name="and-join-split"),
    ]
    for node in nodes:
        process.add_node(node)

    for source, target in [
        ("S1", "GW"),
        ("S2", "GW"),
        ("GW", "E1"),
        ("GW", "E2"),
    ]:
        process.add_constructed_flow(
            Flow(id=f"{source}_{target}", sourceRef=source, targetRef=target)
        )
    return bpmn


def _build_split_case() -> BPMN:
    bpmn = BPMN.generate_empty_bpmn("split_case")
    process = bpmn.process
    nodes = [
        StartEvent(id="S"),
        EndEvent(id="E1"),
        EndEvent(id="E2"),
        AndGateway(id="GW", name="and-split"),
    ]
    for node in nodes:
        process.add_node(node)

    for source, target in [("S", "GW"), ("GW", "E1"), ("GW", "E2")]:
        process.add_constructed_flow(
            Flow(id=f"{source}_{target}", sourceRef=source, targetRef=target)
        )
    return bpmn


def _build_join_case() -> BPMN:
    bpmn = BPMN.generate_empty_bpmn("join_case")
    process = bpmn.process
    nodes = [
        StartEvent(id="S1"),
        StartEvent(id="S2"),
        EndEvent(id="E"),
        AndGateway(id="GW", name="and-join"),
    ]
    for node in nodes:
        process.add_node(node)

    for source, target in [("S1", "GW"), ("S2", "GW"), ("GW", "E")]:
        process.add_constructed_flow(
            Flow(id=f"{source}_{target}", sourceRef=source, targetRef=target)
        )
    return bpmn


def _build_simple_task_case() -> BPMN:
    bpmn = BPMN.generate_empty_bpmn("simple_task_case")
    process = bpmn.process
    nodes = [StartEvent(id="S"), Task(id="T", name="Task"), EndEvent(id="E")]
    for node in nodes:
        process.add_node(node)

    for source, target in [("S", "T"), ("T", "E")]:
        process.add_constructed_flow(
            Flow(id=f"{source}_{target}", sourceRef=source, targetRef=target)
        )
    return bpmn


def test_every_transition_has_incoming_and_outgoing_places():
    pnml = bpmn_to_workflow_net(_build_join_split_case())
    net = pnml.net

    assert len(net.transitions) > 0
    for transition in net.transitions:
        incoming = list(net.get_incoming(transition.id))
        outgoing = list(net.get_outgoing(transition.id))
        assert len(incoming) >= 1
        assert len(outgoing) >= 1

        for arc in incoming:
            assert isinstance(net.get_element(arc.source), Place)
        for arc in outgoing:
            assert isinstance(net.get_element(arc.target), Place)


def test_join_split_transition_remains_valid_with_multiple_in_and_out():
    pnml = bpmn_to_workflow_net(_build_join_split_case())
    net = pnml.net

    join_split_ops = [
        t
        for t in net.transitions
        if t.get_workflow_operator_type() == WorkflowBranchingType.AndJoinSplit
    ]
    assert len(join_split_ops) == 1

    join_split = join_split_ops[0]
    assert net.get_in_degree(join_split) >= 2
    assert net.get_out_degree(join_split) >= 2


def test_split_transition_has_two_outgoing_and_one_incoming_minimum():
    pnml = bpmn_to_workflow_net(_build_split_case())
    net = pnml.net

    split_ops = [
        t
        for t in net.transitions
        if t.get_workflow_operator_type() == WorkflowBranchingType.AndSplit
    ]
    assert len(split_ops) == 1

    split = split_ops[0]
    assert net.get_in_degree(split) >= 1
    assert net.get_out_degree(split) >= 2


def test_join_transition_has_two_incoming_and_one_outgoing():
    pnml = bpmn_to_workflow_net(_build_join_case())
    net = pnml.net

    join_ops = [
        t
        for t in net.transitions
        if t.get_workflow_operator_type() == WorkflowBranchingType.AndJoin
    ]
    assert len(join_ops) == 1

    join = join_ops[0]
    assert net.get_in_degree(join) >= 2
    assert net.get_out_degree(join) == 1


def test_regular_transition_keeps_single_in_single_out():
    pnml = bpmn_to_workflow_net(_build_simple_task_case())
    net = pnml.net

    task_transition = net.get_element("T")
    assert net.get_in_degree(task_transition) == 1
    assert net.get_out_degree(task_transition) == 1
