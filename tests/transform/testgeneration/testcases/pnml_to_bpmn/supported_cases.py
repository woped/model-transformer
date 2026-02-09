"""Generate supported test cases for PNML to BPMN."""

from tests.transform.testgeneration.bpmn.utility import create_bpmn
from tests.transform.testgeneration.pnml.utility import create_petri_net

from app.transform.transformer.models.bpmn.bpmn import (
    BPMN,
    AndGateway,
    EndEvent,
    StartEvent,
    Task,
    XorGateway,
)
from app.transform.transformer.models.pnml.pnml import Place, Pnml, Transition
from app.transform.transformer.utility.utility import create_silent_node_name


def start_end():
    """Return a Start-End BPMN and the according Petri net."""
    case = "start_end"
    se_id = "elem_1"
    ee_id = "elem_2"

    net = create_petri_net(
        case,
        [
            [
                Place(id=se_id),
                Transition(id=create_silent_node_name(se_id, ee_id)),
                Place(id=ee_id),
            ]
        ],
    )

    bpmn = create_bpmn(case, [[StartEvent(id=se_id), EndEvent(id=ee_id)]])

    return bpmn, net, case


def normal_transition():
    """Return a Start-Task-End BPMN and the according Petri net."""
    case = "normal_transition"
    se_id = "elem_1"
    ee_id = "elem_2"
    task_id = "elem_3"
    net = create_petri_net(
        case,
        [
            [
                Place(id=se_id),
                Transition.create(id=task_id, name=task_id),
                Place(id=ee_id),
            ]
        ],
    )
    bpmn = create_bpmn(
        case,
        [[StartEvent(id=se_id), Task(id=task_id, name=task_id), EndEvent(id=ee_id)]],
    )
    return bpmn, net, case


def transition_source_sink():
    """Test diagrams for handling transitions source/sink."""
    case = "transition_source_sink"
    source = "elem_1"
    sink = "elem_2"
    link_task = "elem_3"

    net = create_petri_net(
        case,
        [
            [
                Transition.create(id=source, name=source),
                Place(id=create_silent_node_name(source, link_task)),
                Transition.create(id=link_task, name=link_task),
                Place(id=create_silent_node_name(link_task, sink)),
                Transition.create(id=sink, name=sink),
            ]
        ],
    )
    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id="SOURCE" + source),
                Task(id=source, name=source),
                Task(id=link_task, name=link_task),
                Task(id=sink, name=sink),
                EndEvent(id="SINK" + sink),
            ]
        ],
    )
    return bpmn, net, case


def and_transition():
    """Return an and BPMN and the according Petri net."""
    case = "and_transition"
    se_id = "elem_1"
    ee_id = "elem_2"
    task_id = "elem_3"
    task_2_id = "elem_4"
    gw_split = "elem_5"
    gw_join = "elem_6"

    pn_gw_split = Transition.create(id=gw_split)
    pn_gw_join = Transition.create(id=gw_join)
    net = create_petri_net(
        case,
        [
            [
                Place(id=se_id),
                pn_gw_split,
                Place(id=create_silent_node_name(gw_split, task_id)),
                Transition.create(id=task_id, name=task_id),
                Place(id=create_silent_node_name(task_id, gw_join)),
                pn_gw_join,
                Place(id=ee_id),
            ],
            [
                pn_gw_split,
                Place(id=create_silent_node_name(gw_split, task_2_id)),
                Transition.create(id=task_2_id, name=task_2_id),
                Place(id=create_silent_node_name(task_2_id, gw_join)),
                pn_gw_join,
            ],
        ],
    )

    bpmn_gw_split = AndGateway(id=gw_split)
    bpmn_gw_join = AndGateway(id=gw_join)
    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                bpmn_gw_split,
                Task(id=task_id, name=task_id),
                bpmn_gw_join,
                EndEvent(id=ee_id),
            ],
            [bpmn_gw_split, Task(id=task_2_id, name=task_2_id), bpmn_gw_join],
        ],
    )
    return bpmn, net, case


def and_transition_implicit():
    """Return an and BPMN and the according Petri net."""
    case = "and_transition_implicit"
    se_id = "elem_1"
    ee_id = "elem_2"
    task_id = "elem_3"
    task_2_id = "elem_4"
    gw_split = "elem_5"
    gw_join = "elem_6"

    pn_gw_split = Transition.create(id=gw_split, name="split")
    pn_gw_join = Transition.create(id=gw_join, name="join")
    net = create_petri_net(
        case,
        [
            [
                Place(id=se_id),
                pn_gw_split,
                Place(id=create_silent_node_name(gw_split, task_id)),
                Transition.create(id=task_id, name=task_id),
                Place(id=create_silent_node_name(task_id, gw_join)),
                pn_gw_join,
                Place(id=ee_id),
            ],
            [
                pn_gw_split,
                Place(id=create_silent_node_name(gw_split, task_2_id)),
                Transition.create(id=task_2_id, name=task_2_id),
                Place(id=create_silent_node_name(task_2_id, gw_join)),
                pn_gw_join,
            ],
        ],
    )

    bpmn_gw_split = AndGateway(id=gw_split)
    bpmn_gw_join = AndGateway(id=gw_join)
    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                Task(id="EXPLICIT" + gw_split, name=pn_gw_split.get_name()),
                bpmn_gw_split,
                Task(id=task_id, name=task_id),
                bpmn_gw_join,
                Task(id="EXPLICIT" + gw_join, name=pn_gw_join.get_name()),
                EndEvent(id=ee_id),
            ],
            [bpmn_gw_split, Task(id=task_2_id, name=task_2_id), bpmn_gw_join],
        ],
    )
    return bpmn, net, case


def and_join_split_transition_implicit():
    """Return an and BPMN and the according Petri net."""
    case = "and_join_split_transition_implicit"
    se_id = "elem_1"
    ee_id = "elem_2"
    task_1_1_id = "elem_3"
    task_1_2_id = "elem_4"
    task_2_1_id = "elem_5"
    task_2_2_id = "elem_6"
    gw_split = "elem_7"
    gw_join = "elem_8"
    gw_join_split = "elem_9"

    pn_gw_split = Transition.create(id=gw_split)
    pn_gw_join = Transition.create(id=gw_join)
    pn_gw_join_split = Transition.create(id=gw_join_split, name="both")

    net = create_petri_net(
        case,
        [
            [
                Place(id=se_id),
                pn_gw_split,
                Place(id=create_silent_node_name(gw_split, task_1_1_id)),
                Transition.create(id=task_1_1_id, name=task_1_1_id),
                Place(id=create_silent_node_name(task_1_1_id, gw_join_split)),
                pn_gw_join_split,
            ],
            [
                pn_gw_split,
                Place(id=create_silent_node_name(gw_split, task_1_2_id)),
                Transition.create(id=task_1_2_id, name=task_1_2_id),
                Place(id=create_silent_node_name(task_1_2_id, gw_join_split)),
                pn_gw_join_split,
            ],
            [
                pn_gw_join_split,
                Place(id=create_silent_node_name(gw_join_split, task_2_1_id)),
                Transition.create(id=task_2_1_id, name=task_2_1_id),
                Place(id=create_silent_node_name(task_2_1_id, gw_join)),
                pn_gw_join,
                Place(id=ee_id),
            ],
            [
                pn_gw_join_split,
                Place(id=create_silent_node_name(gw_join_split, task_2_2_id)),
                Transition.create(id=task_2_2_id, name=task_2_2_id),
                Place(id=create_silent_node_name(task_2_2_id, gw_join)),
                pn_gw_join,
            ],
        ],
    )

    bpmn_gw_split = AndGateway(id=gw_split)
    bpmn_gw_join = AndGateway(id=gw_join)
    bpmn_gw_join_split = AndGateway(id=gw_join_split)
    bpmn_gw_join_split_end = AndGateway(id="OUTAND" + gw_join_split)
    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                bpmn_gw_split,
                Task(id=task_1_1_id, name=task_1_1_id),
                bpmn_gw_join_split,
            ],
            [bpmn_gw_split, Task(id=task_1_2_id, name=task_1_2_id), bpmn_gw_join_split],
            [
                bpmn_gw_join_split,
                Task(id="EXPLICIT" + gw_join_split, name=pn_gw_join_split.get_name()),
                bpmn_gw_join_split_end,
                Task(id=task_2_1_id, name=task_2_1_id),
                bpmn_gw_join,
                EndEvent(id=ee_id),
            ],
            [
                bpmn_gw_join_split_end,
                Task(id=task_2_2_id, name=task_2_2_id),
                bpmn_gw_join,
            ],
        ],
    )

    return bpmn, net, case


def and_join_split_transition():
    """Return an and BPMN and the according Petri net."""
    case = "and_join_split_transition"
    se_id = "elem_1"
    ee_id = "elem_2"
    task_1_1_id = "elem_3"
    task_1_2_id = "elem_4"
    task_2_1_id = "elem_5"
    task_2_2_id = "elem_6"
    gw_split = "elem_7"
    gw_join = "elem_8"
    gw_join_split = "elem_9"

    pn_gw_split = Transition.create(id=gw_split)
    pn_gw_join = Transition.create(id=gw_join)
    pn_gw_join_split = Transition.create(id=gw_join_split)

    net = create_petri_net(
        case,
        [
            [
                Place(id=se_id),
                pn_gw_split,
                Place(id=create_silent_node_name(gw_split, task_1_1_id)),
                Transition.create(id=task_1_1_id, name=task_1_1_id),
                Place(id=create_silent_node_name(task_1_1_id, gw_join_split)),
                pn_gw_join_split,
            ],
            [
                pn_gw_split,
                Place(id=create_silent_node_name(gw_split, task_1_2_id)),
                Transition.create(id=task_1_2_id, name=task_1_2_id),
                Place(id=create_silent_node_name(task_1_2_id, gw_join_split)),
                pn_gw_join_split,
            ],
            [
                pn_gw_join_split,
                Place(id=create_silent_node_name(gw_join_split, task_2_1_id)),
                Transition.create(id=task_2_1_id, name=task_2_1_id),
                Place(id=create_silent_node_name(task_2_1_id, gw_join)),
                pn_gw_join,
                Place(id=ee_id),
            ],
            [
                pn_gw_join_split,
                Place(id=create_silent_node_name(gw_join_split, task_2_2_id)),
                Transition.create(id=task_2_2_id, name=task_2_2_id),
                Place(id=create_silent_node_name(task_2_2_id, gw_join)),
                pn_gw_join,
            ],
        ],
    )

    bpmn_gw_split = AndGateway(id=gw_split)
    bpmn_gw_join = AndGateway(id=gw_join)
    bpmn_gw_join_split = AndGateway(id=gw_join_split)
    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                bpmn_gw_split,
                Task(id=task_1_1_id, name=task_1_1_id),
                bpmn_gw_join_split,
            ],
            [bpmn_gw_split, Task(id=task_1_2_id, name=task_1_2_id), bpmn_gw_join_split],
            [
                bpmn_gw_join_split,
                Task(id=task_2_1_id, name=task_2_1_id),
                bpmn_gw_join,
                EndEvent(id=ee_id),
            ],
            [
                bpmn_gw_join_split,
                Task(id=task_2_2_id, name=task_2_2_id),
                bpmn_gw_join,
            ],
        ],
    )

    return bpmn, net, case


def xor_place():
    """Return an xor BPMN and the according Petri net."""
    case = "xor_place"
    se_id = "elem_1"
    ee_id = "elem_2"
    task_id = "elem_3"
    task_2_id = "elem_4"
    gw_split = "elem_5"
    gw_join = "elem_6"

    pn_gw_split = Place(id=gw_split)
    pn_gw_join = Place(id=gw_join)
    net = create_petri_net(
        case,
        [
            [
                Place(id=se_id),
                Transition(id=create_silent_node_name(se_id, gw_split)),
                pn_gw_split,
                Transition.create(id=task_id, name=task_id),
                pn_gw_join,
                Transition(id=create_silent_node_name(gw_join, ee_id)),
                Place(id=ee_id),
            ],
            [pn_gw_split, Transition.create(id=task_2_id, name=task_2_id), pn_gw_join],
        ],
    )
    bpmn_gw_split = XorGateway(id=gw_split)
    bpmn_gw_join = XorGateway(id=gw_join)
    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                bpmn_gw_split,
                Task(id=task_id, name=task_id),
                bpmn_gw_join,
                EndEvent(id=ee_id),
            ],
            [bpmn_gw_split, Task(id=task_2_id, name=task_2_id), bpmn_gw_join],
        ],
    )
    return bpmn, net, case


all_cases: list[tuple[BPMN, Pnml, str]] = [
    transition_source_sink(),
    start_end(),
    normal_transition(),
    and_transition(),
    and_join_split_transition(),
    and_transition_implicit(),
    and_join_split_transition_implicit(),
    xor_place(),
]

