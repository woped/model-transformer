"""Regression test for the gateway-removal dangling-arc bug.

A removable ("unnecessary", in=1/out=1) gateway sitting directly downstream of a
surviving split gateway used to make ``remove_node`` blank the split->gateway
arc's ``targetRef`` while leaving it in the split's outgoing index. Gateway
preprocessing then iterated that arc and called ``get_node("")`` -> ``KeyError
''``, surfacing to the client as the generic 400 "Unkown error".

See ``models/bpmn/bpmn.py`` ``remove_node``.
"""

from app.transform.transformer.models.bpmn.bpmn import (
    BPMN,
    Flow,
    Task,
    StartEvent,
    EndEvent,
    AndGateway,
    XorGateway,
)
from app.transform.transformer.transform_bpmn_to_petrinet.transform import (
    bpmn_to_workflow_net,
)


def _build_split_then_removable_gateway() -> BPMN:
    """Build a net where a removable gateway directly follows a split gateway.

    Topology: S to A(AND split); A to B(XOR, in=1/out=1) to C to J(AND join) to
    E, and A to D to J. B is removable and sits right after the surviving split
    A, which is the configuration that used to trip remove_node.
    """
    bpmn = BPMN.generate_empty_bpmn("gw_removal_regression")
    process = bpmn.process
    nodes = [
        StartEvent(id="S"),
        AndGateway(id="A"),
        XorGateway(id="B"),
        Task(id="C"),
        Task(id="D"),
        AndGateway(id="J"),
        EndEvent(id="E"),
    ]
    for node in nodes:
        process.add_node(node)
    for source, target in [
        ("S", "A"),
        ("A", "B"),
        ("B", "C"),
        ("C", "J"),
        ("A", "D"),
        ("D", "J"),
        ("J", "E"),
    ]:
        process.add_constructed_flow(
            Flow(id=f"{source}_{target}", sourceRef=source, targetRef=target)
        )
    return bpmn


def test_removable_gateway_after_split_transforms_without_keyerror():
    """A removable gateway after a split must transform without KeyError('')."""
    bpmn = _build_split_then_removable_gateway()
    # Before the remove_node fix this raised KeyError('') during gateway
    # preprocessing; it must now transform cleanly.
    pnml = bpmn_to_workflow_net(bpmn)
    assert pnml is not None
    # The removable gateway B is gone after preprocessing/transformation.
    assert "B" not in bpmn.process._temp_nodes


def test_bicycle_repair_example_transforms_without_gateway_keyerror():
    """The bicycle_repair example should not fail with KeyError on gateways."""
    bpmn = BPMN.from_file("tests/process_examples/bpmn/bicycle_repair.bpmn")
    pnml = bpmn_to_workflow_net(bpmn)
    assert pnml is not None
