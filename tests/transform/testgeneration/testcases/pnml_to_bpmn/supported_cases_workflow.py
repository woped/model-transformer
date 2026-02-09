"""Generate supported test cases for Workflow transformations."""

from tests.transform.testgeneration.bpmn.utility import create_bpmn
from tests.transform.testgeneration.pnml.helper_workflow import (
    create_operator_place,
    create_operator_transition,
)
from tests.transform.testgeneration.pnml.utility import create_petri_net

from app.transform.transformer.models.bpmn.bpmn import (
    BPMN,
    AndGateway,
    Collaboration,
    EndEvent,
    IntermediateCatchEvent,
    Lane,
    LaneSet,
    Participant,
    StartEvent,
    Task,
    UserTask,
    XorGateway,
)
from app.transform.transformer.models.pnml.base import (
    OrganizationUnit,
    Resources,
    Role,
    ToolspecificGlobal,
)
from app.transform.transformer.models.pnml.pnml import Page, Place, Pnml, Transition
from app.transform.transformer.models.pnml.workflow import WorkflowBranchingType
from app.transform.transformer.utility.utility import create_silent_node_name


def subprocess_pool():
    """Return a BPMN and the expected petri net with a pool and a subprocess."""
    case = "subprocess_pool"
    se_id = "elem_1"
    task_lane_2_id = "task_lane_2"
    ee_id = "elem_2"

    lane_1 = "lane1"
    lane_2 = "lane2"
    orga = "orga"

    subprocess_id = "elem_3"
    subprocess_name = "subprocess"
    sb_t_id = "elem_sb_3"

    net = create_petri_net(
        case,
        [
            [
                Place.create(id=se_id),
                Transition.create(
                    subprocess_id, subprocess_name
                ).mark_as_workflow_subprocess(),
                Place.create(id=create_silent_node_name(subprocess_id, task_lane_2_id)),
                Transition.create(id=task_lane_2_id).mark_as_workflow_resource(
                    lane_2, orga
                ),
                Place.create(id=ee_id),
            ],
        ],
    )
    net.net.toolspecific_global = ToolspecificGlobal(
        resources=Resources(
            roles=[
                Role(name=lane_1),
                Role(name=lane_2),
            ],
            units=[OrganizationUnit(name=orga)],
        )
    )
    net_page = Page(
        id=subprocess_id,
        net=create_petri_net(
            "",
            [
                [
                    Place(id=se_id),
                    Transition(id=sb_t_id).mark_as_workflow_resource(lane_1, orga),
                    Place(id=create_silent_node_name(subprocess_id, task_lane_2_id)),
                ]
            ],
        ).net,
    )
    net_page.net.id = None
    net.net.add_page(net_page)

    sub_bpmn = create_bpmn(
        "temp",
        [
            [
                StartEvent(id="SB_" + se_id),
                UserTask(id=sb_t_id),
                EndEvent(
                    id="SB_" + create_silent_node_name(subprocess_id, task_lane_2_id)
                ),
            ]
        ],
    )
    sub_bpmn.process.id = subprocess_id
    sub_bpmn.process.name = subprocess_name

    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                sub_bpmn.process,
                UserTask(id=task_lane_2_id),
                EndEvent(id=ee_id),
            ]
        ],
    )

    bpmn.collaboration = Collaboration(
        id="x",
        participant=Participant(id="xo", name=orga, processRef=bpmn.process.name or ""),
    )
    bpmn.process.lane_sets.add(
        LaneSet(
            id="ls",
            lanes=set(
                [
                    Lane(
                        id=lane_1,
                        name=lane_1,
                        flowNodeRefs=set([subprocess_id]),
                    ),
                    Lane(id=lane_2, name=lane_2, flowNodeRefs=set([task_lane_2_id])),
                    Lane(
                        id="Unkown participant",
                        name="Unkown participant",
                        flowNodeRefs=set(
                            [
                                se_id,
                                ee_id,
                            ]
                        ),
                    ),
                ]
            ),
        )
    )

    return bpmn, net, case


def pool_with_gateways():
    """Return a petri net and the expected bpmn with a pool and gateways."""
    case = "pool_with_gateways"

    se_id = "elem_1"
    task_1 = "task_1"
    task_2 = "task_2"
    ee_id = "elem_2"

    lane_1 = "lane1"
    lane_2 = "lane2"
    orga = "orga"

    gw_split = "elem_4"
    gw_join = "elem_5"

    and_split = create_operator_transition(
        gw_split, 1, WorkflowBranchingType.AndSplit
    ).mark_as_workflow_resource(lane_1, orga)
    and_join = create_operator_transition(
        gw_join, 1, WorkflowBranchingType.AndJoin
    ).mark_as_workflow_resource(lane_2, orga)

    net = create_petri_net(
        case,
        [
            [
                Place.create(id=se_id),
                and_split,
                Place.create(id=create_silent_node_name(gw_split, task_1)),
                Transition.create(task_1, task_1),
                Place.create(id=create_silent_node_name(task_1, gw_join)),
                and_join,
                Place.create(id=ee_id),
            ],
            [
                and_split,
                Place.create(id=create_silent_node_name(gw_split, task_2)),
                Transition.create(task_2, task_2),
                Place.create(id=create_silent_node_name(task_2, gw_join)),
                and_join,
            ],
        ],
    )
    net.net.toolspecific_global = ToolspecificGlobal(
        resources=Resources(
            roles=[
                Role(name=lane_1),
                Role(name=lane_2),
            ],
            units=[OrganizationUnit(name=orga)],
        )
    )

    bpmn_gw_split = AndGateway(id=gw_split)
    bpmn_gw_join = AndGateway(id=gw_join)

    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                bpmn_gw_split,
                Task(id=task_1, name=task_1),
                bpmn_gw_join,
                EndEvent(id=ee_id),
            ],
            [
                bpmn_gw_split,
                Task(id=task_2, name=task_2),
                bpmn_gw_join,
            ],
        ],
    )

    bpmn.collaboration = Collaboration(
        id="x",
        participant=Participant(id="xo", name=orga, processRef=bpmn.process.name or ""),
    )
    bpmn.process.lane_sets.add(
        LaneSet(
            id="ls",
            lanes=set(
                [
                    Lane(id=lane_1, name=lane_1, flowNodeRefs=set([gw_split])),
                    Lane(id=lane_2, name=lane_2, flowNodeRefs=set([gw_join])),
                    Lane(
                        id="Unkown participant",
                        name="Unkown participant",
                        flowNodeRefs=set([task_1, task_2, se_id, ee_id]),
                    ),
                ]
            ),
        )
    )

    return bpmn, net, case


def simple_pool():
    """Return a BPMN and the expected petri net with a pool with 2 lanes."""
    case = "simple_pool"
    se_id = "elem_1"
    task_lane_1_id = "task_lane_1"
    task_lane_2_id = "task_lane_2"
    task = "task"
    ee_id = "elem_2"

    lane_1 = "lane1"
    lane_2 = "lane2"
    orga = "orga"

    net = create_petri_net(
        case,
        [
            [
                Place.create(id=se_id),
                Transition.create(id=task_lane_1_id).mark_as_workflow_resource(
                    lane_1, orga
                ),
                Place.create(id=create_silent_node_name(task_lane_1_id, task)),
                Transition.create(id=task, name=task),
                Place.create(id=create_silent_node_name(task, task_lane_2_id)),
                Transition.create(id=task_lane_2_id).mark_as_workflow_resource(
                    lane_2, orga
                ),
                Place.create(id=ee_id),
            ],
        ],
    )
    net.net.toolspecific_global = ToolspecificGlobal(
        resources=Resources(
            roles=[
                Role(name=lane_1),
                Role(name=lane_2),
            ],
            units=[OrganizationUnit(name=orga)],
        )
    )

    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                UserTask(id=task_lane_1_id),
                Task(id=task, name=task),
                UserTask(id=task_lane_2_id),
                EndEvent(id=ee_id),
            ]
        ],
    )

    bpmn.collaboration = Collaboration(
        id="x",
        participant=Participant(id="xo", name=orga, processRef=bpmn.process.name or ""),
    )
    bpmn.process.lane_sets.add(
        LaneSet(
            id="ls",
            lanes=set(
                [
                    Lane(id=lane_1, name=lane_1, flowNodeRefs=set([task_lane_1_id])),
                    Lane(id=lane_2, name=lane_2, flowNodeRefs=set([task_lane_2_id])),
                    Lane(
                        id="Unkown participant",
                        name="Unkown participant",
                        flowNodeRefs=set([task, se_id, ee_id]),
                    ),
                ]
            ),
        )
    )

    return bpmn, net, case


def sequential_time_event():
    """Return a BPMN and the expected petri net with  IntermediateCatchEvent(Time)."""
    case = "sequential_time_event"
    se_id = "elem_1"
    task_id = "task"
    ee_id = "elem_2"

    net = create_petri_net(
        case,
        [
            [
                Place.create(id=se_id),
                Transition.create(id=task_id, name=task_id).mark_as_workflow_time(),
                Place.create(id=ee_id),
            ]
        ],
    )
    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                IntermediateCatchEvent.create_time_event("TRIGGER" + task_id),
                Task(id=task_id, name=task_id),
                EndEvent(id=ee_id),
            ]
        ],
    )
    return bpmn, net, case


def sequential_message_event():
    """Return a BPMN and the expected petri net with  IntermediateCatchEvent(Message)."""
    case = "sequential_message_event"
    se_id = "elem_1"
    task_id = "task"
    ee_id = "elem_2"

    net = create_petri_net(
        case,
        [
            [
                Place.create(id=se_id),
                Transition.create(id=task_id, name=task_id).mark_as_workflow_message(),
                Place.create(id=ee_id),
            ]
        ],
    )
    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                IntermediateCatchEvent.create_message_event("TRIGGER" + task_id),
                Task(id=task_id, name=task_id),
                EndEvent(id=ee_id),
            ]
        ],
    )
    return bpmn, net, case


def sequential_time_event_silent():
    """Return a BPMN and the expected petri net with  IntermediateCatchEvent(Time)."""
    case = "sequential_time_event_silent"
    se_id = "elem_1"
    task_id = "task"
    ee_id = "elem_2"

    net = create_petri_net(
        case,
        [
            [
                Place.create(id=se_id),
                Transition.create(id=task_id).mark_as_workflow_time(),
                Place.create(id=ee_id),
            ]
        ],
    )
    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                IntermediateCatchEvent.create_time_event("TRIGGER" + task_id),
                EndEvent(id=ee_id),
            ]
        ],
    )
    return bpmn, net, case


def sequential_message_event_silent():
    """Return a BPMN and the expected petri net with  IntermediateCatchEvent(Message)."""
    case = "sequential_message_event_silent"
    se_id = "elem_1"
    task_id = "task"
    ee_id = "elem_2"

    net = create_petri_net(
        case,
        [
            [
                Place.create(id=se_id),
                Transition.create(id=task_id).mark_as_workflow_message(),
                Place.create(id=ee_id),
            ]
        ],
    )
    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                IntermediateCatchEvent.create_message_event("TRIGGER" + task_id),
                EndEvent(id=ee_id),
            ]
        ],
    )
    return bpmn, net, case


def gateway_parallel_join_split_with_events():
    """Return a BPMN and the expected workflow net with AND gates and triggers."""
    case = "parallel_workflow_elements_with_events"
    se_id = "elem_1"
    ee_id = "elem_2"

    task_1 = "elem_3"
    task_11 = "elem_6"
    task_2 = "elem_30"
    task_22 = "elem_60"

    gw_split = "elem_4"
    gw_join = "elem_5"
    gw_both = "elem_7"

    and_split = create_operator_transition(
        gw_split, 1, WorkflowBranchingType.AndSplit
    ).mark_as_workflow_time()
    and_join_split = create_operator_transition(
        gw_both, 1, WorkflowBranchingType.AndJoinSplit
    ).mark_as_workflow_time()
    and_join = create_operator_transition(
        gw_join, 1, WorkflowBranchingType.AndJoin
    ).mark_as_workflow_time()

    net = create_petri_net(
        case,
        [
            [
                Place.create(id=se_id),
                and_split,
                Place.create(id=create_silent_node_name(and_split.id, task_1)),
                Transition.create(id=task_1, name=task_1),
                Place.create(id=create_silent_node_name(task_1, and_join_split.id)),
                and_join_split,
                Place.create(id=create_silent_node_name(and_join_split.id, task_2)),
                Transition.create(id=task_2, name=task_2),
                Place.create(id=create_silent_node_name(task_2, and_join.id)),
                and_join,
                Place.create(id=ee_id),
            ],
            [
                and_split,
                Place.create(id=create_silent_node_name(and_split.id, task_11)),
                Transition.create(id=task_11, name=task_11),
                Place.create(id=create_silent_node_name(task_11, and_join_split.id)),
                and_join_split,
            ],
            [
                and_join_split,
                Place.create(id=create_silent_node_name(and_join_split.id, task_22)),
                Transition.create(id=task_22, name=task_22),
                Place.create(id=create_silent_node_name(task_22, and_join.id)),
                and_join,
            ],
        ],
    )

    bpmn_gw_split = AndGateway(id=gw_split)
    bpmn_gw_both_left = AndGateway(id=gw_both)
    bpmn_gw_both_right = AndGateway(id="OUTAND" + gw_both)
    bpmn_gw_join = AndGateway(id=gw_join)

    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                IntermediateCatchEvent.create_time_event("TRIGGER" + gw_split),
                bpmn_gw_split,
                Task(id=task_1, name=task_1),
                bpmn_gw_both_left,
                IntermediateCatchEvent.create_time_event("TRIGGER" + gw_both),
                bpmn_gw_both_right,
                Task(id=task_2, name=task_2),
                bpmn_gw_join,
                IntermediateCatchEvent.create_time_event("TRIGGER" + gw_join),
                EndEvent(id=ee_id),
            ],
            [bpmn_gw_split, Task(id=task_11, name=task_11), bpmn_gw_both_left],
            [bpmn_gw_both_right, Task(id=task_22, name=task_22), bpmn_gw_join],
        ],
    )

    return bpmn, net, case


def gateway_parallel_join_split():
    """Return a BPMN and workflow net with AND gates."""
    case = "parallel_workflow_elements"
    se_id = "elem_1"
    ee_id = "elem_2"

    task_1 = "elem_3"
    task_11 = "elem_6"
    task_2 = "elem_30"
    task_22 = "elem_60"

    gw_split = "elem_4"
    gw_join = "elem_5"
    gw_both = "elem_7"

    and_split = create_operator_transition(gw_split, 1, WorkflowBranchingType.AndSplit)
    and_join_split = create_operator_transition(
        gw_both, 1, WorkflowBranchingType.AndJoinSplit
    )
    and_join = create_operator_transition(gw_join, 1, WorkflowBranchingType.AndJoin)

    net = create_petri_net(
        case,
        [
            [
                Place.create(id=se_id),
                and_split,
                Place.create(id=create_silent_node_name(and_split.id, task_1)),
                Transition.create(id=task_1, name=task_1),
                Place.create(id=create_silent_node_name(task_1, and_join_split.id)),
                and_join_split,
                Place.create(id=create_silent_node_name(and_join_split.id, task_2)),
                Transition.create(id=task_2, name=task_2),
                Place.create(id=create_silent_node_name(task_2, and_join.id)),
                and_join,
                Place.create(id=ee_id),
            ],
            [
                and_split,
                Place.create(id=create_silent_node_name(and_split.id, task_11)),
                Transition.create(id=task_11, name=task_11),
                Place.create(id=create_silent_node_name(task_11, and_join_split.id)),
                and_join_split,
            ],
            [
                and_join_split,
                Place.create(id=create_silent_node_name(and_join_split.id, task_22)),
                Transition.create(id=task_22, name=task_22),
                Place.create(id=create_silent_node_name(task_22, and_join.id)),
                and_join,
            ],
        ],
    )

    bpmn_gw_split = AndGateway(id=gw_split)
    bpmn_gw_both = AndGateway(id=gw_both)
    bpmn_gw_join = AndGateway(id=gw_join)

    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                bpmn_gw_split,
                Task(id=task_1, name=task_1),
                bpmn_gw_both,
                Task(id=task_2, name=task_2),
                bpmn_gw_join,
                EndEvent(id=ee_id),
            ],
            [bpmn_gw_split, Task(id=task_11, name=task_11), bpmn_gw_both],
            [bpmn_gw_both, Task(id=task_22, name=task_22), bpmn_gw_join],
        ],
    )

    return bpmn, net, case


def gateway_parallel_join_split_implicit():
    """Return a BPMN and workflow net with AND gates with implicit tasks."""
    case = "parallel_workflow_elements_implicit"
    se_id = "elem_1"
    ee_id = "elem_2"

    task_1 = "elem_3"
    task_11 = "elem_6"
    task_2 = "elem_30"
    task_22 = "elem_60"

    gw_split = "elem_4"
    gw_join = "elem_5"
    gw_both = "elem_7"

    and_split = create_operator_transition(
        gw_split, 1, WorkflowBranchingType.AndSplit, "split"
    )
    and_join_split = create_operator_transition(
        gw_both, 1, WorkflowBranchingType.AndJoinSplit, "both"
    )
    and_join = create_operator_transition(
        gw_join, 1, WorkflowBranchingType.AndJoin, "join"
    )

    net = create_petri_net(
        case,
        [
            [
                Place.create(id=se_id),
                and_split,
                Place.create(id=create_silent_node_name(and_split.id, task_1)),
                Transition.create(id=task_1, name=task_1),
                Place.create(id=create_silent_node_name(task_1, and_join_split.id)),
                and_join_split,
                Place.create(id=create_silent_node_name(and_join_split.id, task_2)),
                Transition.create(id=task_2, name=task_2),
                Place.create(id=create_silent_node_name(task_2, and_join.id)),
                and_join,
                Place.create(id=ee_id),
            ],
            [
                and_split,
                Place.create(id=create_silent_node_name(and_split.id, task_11)),
                Transition.create(id=task_11, name=task_11),
                Place.create(id=create_silent_node_name(task_11, and_join_split.id)),
                and_join_split,
            ],
            [
                and_join_split,
                Place.create(id=create_silent_node_name(and_join_split.id, task_22)),
                Transition.create(id=task_22, name=task_22),
                Place.create(id=create_silent_node_name(task_22, and_join.id)),
                and_join,
            ],
        ],
    )

    bpmn_gw_split = AndGateway(id=gw_split)
    bpmn_gw_both_in = AndGateway(id="INAND" + gw_both)
    bpmn_gw_both_out = AndGateway(id="OUTAND" + gw_both)
    bpmn_gw_join = AndGateway(id=gw_join)

    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                Task(id="EXPLICIT" + bpmn_gw_split.id, name=and_split.get_name()),
                bpmn_gw_split,
                Task(id=task_1, name=task_1),
                bpmn_gw_both_in,
                Task(
                    id="EXPLICIT" + gw_both,
                    name=and_join_split.get_name(),
                ),
                bpmn_gw_both_out,
                Task(id=task_2, name=task_2),
                bpmn_gw_join,
                Task(id="EXPLICIT" + bpmn_gw_join.id, name=and_join.get_name()),
                EndEvent(id=ee_id),
            ],
            [bpmn_gw_split, Task(id=task_11, name=task_11), bpmn_gw_both_in],
            [bpmn_gw_both_out, Task(id=task_22, name=task_22), bpmn_gw_join],
        ],
    )

    return bpmn, net, case


def gateway_exclusive_join_split():
    """Return a BPMN and workflow net with XOR gates."""
    case = "exclusive_workflow_elements"
    se_id = "elem_1"
    ee_id = "elem_2"

    task_1 = "elem_3"
    task_11 = "elem_6"
    task_2 = "elem_30"
    task_22 = "elem_60"

    gw_split = "elem_4"
    gw_join = "elem_5"
    gw_both = "elem_7"

    xor_split_1 = create_operator_transition(gw_split, 1, WorkflowBranchingType.XorSplit)
    xor_split_2 = create_operator_transition(gw_split, 2, WorkflowBranchingType.XorSplit)

    xor_join_split_place = create_operator_place(
        gw_both, WorkflowBranchingType.XorJoinSplit
    )
    xor_join_split_in_1 = create_operator_transition(
        gw_both, 1, WorkflowBranchingType.XorJoinSplit
    )
    xor_join_split_in_2 = create_operator_transition(
        gw_both, 2, WorkflowBranchingType.XorJoinSplit
    )
    xor_join_split_out_1 = create_operator_transition(
        gw_both, 3, WorkflowBranchingType.XorJoinSplit
    )
    xor_join_split_out_2 = create_operator_transition(
        gw_both, 4, WorkflowBranchingType.XorJoinSplit
    )

    xor_join_1 = create_operator_transition(gw_join, 1, WorkflowBranchingType.XorJoin)
    xor_join_2 = create_operator_transition(gw_join, 2, WorkflowBranchingType.XorJoin)

    start = Place.create(id=se_id)
    end = Place.create(id=ee_id)
    net = create_petri_net(
        case,
        [
            [
                start,
                xor_split_1,
                Place.create(id=create_silent_node_name(xor_split_1.id, task_1)),
                Transition.create(id=task_1, name=task_1),
                Place.create(id=create_silent_node_name(task_1, xor_join_split_in_1.id)),
                xor_join_split_in_1,
                xor_join_split_place,
                xor_join_split_out_1,
                Place.create(
                    id=create_silent_node_name(xor_join_split_out_1.id, task_2)
                ),
                Transition.create(id=task_2, name=task_2),
                Place.create(id=create_silent_node_name(task_2, xor_join_1.id)),
                xor_join_1,
                end,
            ],
            [
                start,
                xor_split_2,
                Place.create(id=create_silent_node_name(xor_split_2.id, task_11)),
                Transition.create(id=task_11, name=task_11),
                Place.create(
                    id=create_silent_node_name(task_11, xor_join_split_in_2.id)
                ),
                xor_join_split_in_2,
                xor_join_split_place,
                xor_join_split_out_2,
                Place.create(
                    id=create_silent_node_name(xor_join_split_out_2.id, task_22)
                ),
                Transition.create(id=task_22, name=task_22),
                Place.create(id=create_silent_node_name(task_22, xor_join_2.id)),
                xor_join_2,
                end,
            ],
        ],
    )

    bpmn_gw_split = XorGateway(id=gw_split)
    bpmn_gw_both = XorGateway(id=gw_both)
    bpmn_gw_join = XorGateway(id=gw_join)

    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                bpmn_gw_split,
                Task(id=task_1, name=task_1),
                bpmn_gw_both,
                Task(id=task_2, name=task_2),
                bpmn_gw_join,
                EndEvent(id=ee_id),
            ],
            [bpmn_gw_split, Task(id=task_11, name=task_11), bpmn_gw_both],
            [bpmn_gw_both, Task(id=task_22, name=task_22), bpmn_gw_join],
        ],
    )

    return bpmn, net, case


def gateway_exclusive_join_split_implicit():
    """Return a BPMN and workflow net with XOR gates."""
    case = "exclusive_workflow_elements_implicit"
    se_id = "elem_1"
    ee_id = "elem_2"

    task_1 = "elem_3"
    task_11 = "elem_6"
    task_2 = "elem_30"
    task_22 = "elem_60"

    gw_split = "elem_4"
    gw_join = "elem_5"
    gw_both = "elem_7"

    xor_split_1 = create_operator_transition(
        gw_split, 1, WorkflowBranchingType.XorSplit, "split"
    )
    xor_split_2 = create_operator_transition(
        gw_split, 2, WorkflowBranchingType.XorSplit, "split"
    )

    xor_join_split_place = create_operator_place(
        gw_both, WorkflowBranchingType.XorJoinSplit
    )
    xor_join_split_in_1 = create_operator_transition(
        gw_both, 1, WorkflowBranchingType.XorJoinSplit, "both"
    )
    xor_join_split_in_2 = create_operator_transition(
        gw_both, 2, WorkflowBranchingType.XorJoinSplit, "both"
    )
    xor_join_split_out_1 = create_operator_transition(
        gw_both, 3, WorkflowBranchingType.XorJoinSplit, "both"
    )
    xor_join_split_out_2 = create_operator_transition(
        gw_both, 4, WorkflowBranchingType.XorJoinSplit, "both"
    )

    xor_join_1 = create_operator_transition(
        gw_join, 1, WorkflowBranchingType.XorJoin, "join"
    )
    xor_join_2 = create_operator_transition(
        gw_join, 2, WorkflowBranchingType.XorJoin, "join"
    )

    start = Place.create(id=se_id)
    end = Place.create(id=ee_id)
    net = create_petri_net(
        case,
        [
            [
                start,
                xor_split_1,
                Place.create(id=create_silent_node_name(xor_split_1.id, task_1)),
                Transition.create(id=task_1, name=task_1),
                Place.create(id=create_silent_node_name(task_1, xor_join_split_in_1.id)),
                xor_join_split_in_1,
                xor_join_split_place,
                xor_join_split_out_1,
                Place.create(
                    id=create_silent_node_name(xor_join_split_out_1.id, task_2)
                ),
                Transition.create(id=task_2, name=task_2),
                Place.create(id=create_silent_node_name(task_2, xor_join_1.id)),
                xor_join_1,
                end,
            ],
            [
                start,
                xor_split_2,
                Place.create(id=create_silent_node_name(xor_split_2.id, task_11)),
                Transition.create(id=task_11, name=task_11),
                Place.create(
                    id=create_silent_node_name(task_11, xor_join_split_in_2.id)
                ),
                xor_join_split_in_2,
                xor_join_split_place,
                xor_join_split_out_2,
                Place.create(
                    id=create_silent_node_name(xor_join_split_out_2.id, task_22)
                ),
                Transition.create(id=task_22, name=task_22),
                Place.create(id=create_silent_node_name(task_22, xor_join_2.id)),
                xor_join_2,
                end,
            ],
        ],
    )

    bpmn_gw_split = XorGateway(id=gw_split)
    bpmn_gw_both_in = XorGateway(id="INXOR" + gw_both)
    bpmn_gw_both_out = XorGateway(id="OUTXOR" + gw_both)
    bpmn_gw_join = XorGateway(id=gw_join)

    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                Task(id="EXPLICIT" + bpmn_gw_split.id, name=xor_split_1.get_name()),
                bpmn_gw_split,
                Task(id=task_1, name=task_1),
                bpmn_gw_both_in,
                Task(id="EXPLICIT" + gw_both, name=xor_join_split_in_1.get_name()),
                bpmn_gw_both_out,
                Task(id=task_2, name=task_2),
                bpmn_gw_join,
                Task(id="EXPLICIT" + bpmn_gw_join.id, name=xor_join_1.get_name()),
                EndEvent(id=ee_id),
            ],
            [bpmn_gw_split, Task(id=task_11, name=task_11), bpmn_gw_both_in],
            [bpmn_gw_both_out, Task(id=task_22, name=task_22), bpmn_gw_join],
        ],
    )

    return bpmn, net, case


def gateway_side_by_side_xor_and():
    """Return a BPMN and workflow net with XOR+AND gates."""
    case = "gateway_side_by_side_xor_and"
    se_id = "elem_1"
    ee_id = "elem_2"

    task_1 = "elem_3"
    task_11 = "elem_6"
    task_2 = "elem_30"
    task_22 = "elem_60"

    gw_split_start = "elem_4"
    gw_join_start = "elem_8"
    gw_split_end = "elem_7"
    gw_join_end = "elem_5"

    # Xor Part
    xor_split_1 = create_operator_transition(
        gw_split_start, 1, WorkflowBranchingType.XorSplit
    )
    xor_split_2 = create_operator_transition(
        gw_split_start, 2, WorkflowBranchingType.XorSplit
    )
    xor_join_1 = create_operator_transition(
        gw_join_start, 1, WorkflowBranchingType.XorJoin
    )
    xor_join_2 = create_operator_transition(
        gw_join_start, 2, WorkflowBranchingType.XorJoin
    )
    # And Part
    and_split = create_operator_transition(
        gw_split_end, 1, WorkflowBranchingType.AndSplit
    )
    and_join = create_operator_transition(gw_join_end, 1, WorkflowBranchingType.AndJoin)

    gateway_merge_place = Place.create(id=gw_join_start + gw_split_end)

    start = Place.create(id=se_id)
    end = Place.create(id=ee_id)
    net = create_petri_net(
        case,
        [
            [
                start,
                xor_split_1,
                Place.create(id=create_silent_node_name(xor_split_1.id, task_1)),
                Transition.create(id=task_1, name=task_1),
                Place.create(id=create_silent_node_name(task_1, xor_join_1.id)),
                xor_join_1,
                gateway_merge_place,
                and_split,
                Place.create(id=create_silent_node_name(and_split.id, task_2)),
                Transition.create(id=task_2, name=task_2),
                Place.create(id=create_silent_node_name(task_2, and_join.id)),
                and_join,
                end,
            ],
            [
                start,
                xor_split_2,
                Place.create(id=create_silent_node_name(xor_split_2.id, task_11)),
                Transition.create(id=task_11, name=task_11),
                Place.create(id=create_silent_node_name(task_11, xor_join_2.id)),
                xor_join_2,
                gateway_merge_place,
            ],
            [
                and_split,
                Place.create(id=create_silent_node_name(and_split.id, task_22)),
                Transition.create(id=task_22, name=task_22),
                Place.create(id=create_silent_node_name(task_22, and_join.id)),
                and_join,
            ],
        ],
    )

    bpmn_gw_split_start = XorGateway(id=gw_split_start)
    bpmn_gw_join_start = XorGateway(id=gw_join_start)
    bpmn_gw_split_end = AndGateway(id=gw_split_end)
    bpmn_gw_join_end = AndGateway(id=gw_join_end)

    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                bpmn_gw_split_start,
                Task(id=task_1, name=task_1),
                bpmn_gw_join_start,
                bpmn_gw_split_end,
                Task(id=task_2, name=task_2),
                bpmn_gw_join_end,
                EndEvent(id=ee_id),
            ],
            [bpmn_gw_split_start, Task(id=task_11, name=task_11), bpmn_gw_join_start],
            [bpmn_gw_split_end, Task(id=task_22, name=task_22), bpmn_gw_join_end],
        ],
    )

    return bpmn, net, case


def gateway_side_by_side_and_xor():
    """Return a BPMN and workflow net with AND+XOR gates."""
    case = "gateway_side_by_side_and_xor"
    se_id = "elem_1"
    ee_id = "elem_2"

    task_1 = "elem_3"
    task_11 = "elem_6"
    task_2 = "elem_30"
    task_22 = "elem_60"

    gw_split_start = "elem_4"
    gw_join_start = "elem_8"
    gw_split_end = "elem_7"
    gw_join_end = "elem_5"

    # And Part
    and_split = create_operator_transition(
        gw_split_start, 1, WorkflowBranchingType.AndSplit
    )
    and_join = create_operator_transition(
        gw_join_start, 1, WorkflowBranchingType.AndJoin
    )
    # Xor Part
    xor_split_1 = create_operator_transition(
        gw_split_end, 1, WorkflowBranchingType.XorSplit
    )
    xor_split_2 = create_operator_transition(
        gw_split_end, 2, WorkflowBranchingType.XorSplit
    )
    xor_join_1 = create_operator_transition(
        gw_join_end, 1, WorkflowBranchingType.XorJoin
    )
    xor_join_2 = create_operator_transition(
        gw_join_end, 2, WorkflowBranchingType.XorJoin
    )

    gateway_merge_place = Place.create(id=gw_join_start + gw_split_end)

    start = Place.create(id=se_id)
    end = Place.create(id=ee_id)
    net = create_petri_net(
        case,
        [
            [
                start,
                and_split,
                Place.create(id=create_silent_node_name(and_split.id, task_1)),
                Transition.create(id=task_1, name=task_1),
                Place.create(id=create_silent_node_name(task_1, and_join.id)),
                and_join,
                gateway_merge_place,
                xor_split_1,
                Place.create(id=create_silent_node_name(xor_split_1.id, task_2)),
                Transition.create(id=task_2, name=task_2),
                Place.create(id=create_silent_node_name(task_2, xor_join_1.id)),
                xor_join_1,
                end,
            ],
            [
                and_split,
                Place.create(id=create_silent_node_name(and_split.id, task_11)),
                Transition.create(id=task_11, name=task_11),
                Place.create(id=create_silent_node_name(task_11, and_join.id)),
                and_join,
            ],
            [
                gateway_merge_place,
                xor_split_2,
                Place.create(id=create_silent_node_name(xor_split_2.id, task_22)),
                Transition.create(id=task_22, name=task_22),
                Place.create(id=create_silent_node_name(task_22, xor_join_2.id)),
                xor_join_2,
                end,
            ],
        ],
    )

    bpmn_gw_split_start = AndGateway(id=gw_split_start)
    bpmn_gw_join_start = AndGateway(id=gw_join_start)
    bpmn_gw_split_end = XorGateway(id=gw_split_end)
    bpmn_gw_join_end = XorGateway(id=gw_join_end)

    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                bpmn_gw_split_start,
                Task(id=task_1, name=task_1),
                bpmn_gw_join_start,
                bpmn_gw_split_end,
                Task(id=task_2, name=task_2),
                bpmn_gw_join_end,
                EndEvent(id=ee_id),
            ],
            [bpmn_gw_split_start, Task(id=task_11, name=task_11), bpmn_gw_join_start],
            [bpmn_gw_split_end, Task(id=task_22, name=task_22), bpmn_gw_join_end],
        ],
    )
    return bpmn, net, case


def xor_and_split():
    """Return a BPMN and workflow net with mixed gates."""
    case = "gateway_xor_and_split"
    se_id = "elem_1"
    ee_id = "elem_2"

    task_1 = "elem_3"
    task_11 = "elem_6"
    task_2 = "elem_30"
    task_22 = "elem_60"

    gw_split_start = "elem_4"
    gw_join_end = "elem_5"

    gw_both = "elem_both"

    # Xor Part
    xor_split_1 = create_operator_transition(
        gw_split_start, 1, WorkflowBranchingType.XorSplit
    )
    xor_split_2 = create_operator_transition(
        gw_split_start, 2, WorkflowBranchingType.XorSplit
    )

    linking_place = create_operator_place(gw_both, WorkflowBranchingType.XorJoinAndSplit)
    xor_join_and_split_in_1 = create_operator_transition(
        gw_both, 1, WorkflowBranchingType.XorJoinAndSplit
    )
    xor_join_and_split_in_2 = create_operator_transition(
        gw_both, 2, WorkflowBranchingType.XorJoinAndSplit
    )
    xor_join_and_split_out = create_operator_transition(
        gw_both, 3, WorkflowBranchingType.XorJoinAndSplit
    )
    # And Part
    and_join = create_operator_transition(gw_join_end, 1, WorkflowBranchingType.AndJoin)

    start = Place.create(id=se_id)
    end = Place.create(id=ee_id)
    net = create_petri_net(
        case,
        [
            [
                start,
                xor_split_1,
                Place.create(id=create_silent_node_name(xor_split_1.id, task_1)),
                Transition.create(id=task_1, name=task_1),
                Place.create(
                    id=create_silent_node_name(task_1, xor_join_and_split_in_1.id)
                ),
                xor_join_and_split_in_1,
                linking_place,
                xor_join_and_split_out,
                Place.create(
                    id=create_silent_node_name(xor_join_and_split_out.id, task_2)
                ),
                Transition.create(id=task_2, name=task_2),
                Place.create(id=create_silent_node_name(task_2, and_join.id)),
                and_join,
                end,
            ],
            [
                start,
                xor_split_2,
                Place.create(id=create_silent_node_name(xor_split_2.id, task_11)),
                Transition.create(id=task_11, name=task_11),
                Place.create(
                    id=create_silent_node_name(task_11, xor_join_and_split_in_2.id)
                ),
                xor_join_and_split_in_2,
                linking_place,
            ],
            [
                xor_join_and_split_out,
                Place.create(
                    id=create_silent_node_name(xor_join_and_split_out.id, task_22)
                ),
                Transition.create(id=task_22, name=task_22),
                Place.create(id=create_silent_node_name(task_22, and_join.id)),
                and_join,
            ],
        ],
    )

    bpmn_gw_split_start = XorGateway(id=gw_split_start)
    bpmn_gw_join_start = XorGateway(id="XOR" + gw_both)
    bpmn_gw_split_end = AndGateway(id="AND" + gw_both)
    bpmn_gw_join_end = AndGateway(id=gw_join_end)

    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                bpmn_gw_split_start,
                Task(id=task_1, name=task_1),
                bpmn_gw_join_start,
                bpmn_gw_split_end,
                Task(id=task_2, name=task_2),
                bpmn_gw_join_end,
                EndEvent(id=ee_id),
            ],
            [bpmn_gw_split_start, Task(id=task_11, name=task_11), bpmn_gw_join_start],
            [bpmn_gw_split_end, Task(id=task_22, name=task_22), bpmn_gw_join_end],
        ],
    )

    return bpmn, net, case


def xor_and_split_implicit():
    """Return a BPMN and workflow net with mixed gates."""
    case = "gateway_xor_and_split_implicit"
    se_id = "elem_1"
    ee_id = "elem_2"

    task_1 = "elem_3"
    task_11 = "elem_6"
    task_2 = "elem_30"
    task_22 = "elem_60"

    gw_split_start = "elem_4"
    gw_join_end = "elem_5"

    gw_both = "elem_both"

    # Xor Part
    xor_split_1 = create_operator_transition(
        gw_split_start, 1, WorkflowBranchingType.XorSplit
    )
    xor_split_2 = create_operator_transition(
        gw_split_start, 2, WorkflowBranchingType.XorSplit
    )

    linking_place = create_operator_place(gw_both, WorkflowBranchingType.XorJoinAndSplit)
    xor_join_and_split_in_1 = create_operator_transition(
        gw_both, 1, WorkflowBranchingType.XorJoinAndSplit, "both"
    )
    xor_join_and_split_in_2 = create_operator_transition(
        gw_both, 2, WorkflowBranchingType.XorJoinAndSplit, "both"
    )
    xor_join_and_split_out = create_operator_transition(
        gw_both, 3, WorkflowBranchingType.XorJoinAndSplit, "both"
    )
    # And Part
    and_join = create_operator_transition(gw_join_end, 1, WorkflowBranchingType.AndJoin)

    start = Place.create(id=se_id)
    end = Place.create(id=ee_id)
    net = create_petri_net(
        case,
        [
            [
                start,
                xor_split_1,
                Place.create(id=create_silent_node_name(xor_split_1.id, task_1)),
                Transition.create(id=task_1, name=task_1),
                Place.create(
                    id=create_silent_node_name(task_1, xor_join_and_split_in_1.id)
                ),
                xor_join_and_split_in_1,
                linking_place,
                xor_join_and_split_out,
                Place.create(
                    id=create_silent_node_name(xor_join_and_split_out.id, task_2)
                ),
                Transition.create(id=task_2, name=task_2),
                Place.create(id=create_silent_node_name(task_2, and_join.id)),
                and_join,
                end,
            ],
            [
                start,
                xor_split_2,
                Place.create(id=create_silent_node_name(xor_split_2.id, task_11)),
                Transition.create(id=task_11, name=task_11),
                Place.create(
                    id=create_silent_node_name(task_11, xor_join_and_split_in_2.id)
                ),
                xor_join_and_split_in_2,
                linking_place,
            ],
            [
                xor_join_and_split_out,
                Place.create(
                    id=create_silent_node_name(xor_join_and_split_out.id, task_22)
                ),
                Transition.create(id=task_22, name=task_22),
                Place.create(id=create_silent_node_name(task_22, and_join.id)),
                and_join,
            ],
        ],
    )

    bpmn_gw_split_start = XorGateway(id=gw_split_start)
    bpmn_gw_join_start = XorGateway(id="XOR" + gw_both)
    bpmn_gw_split_end = AndGateway(id="AND" + gw_both)
    bpmn_gw_join_end = AndGateway(id=gw_join_end)

    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                bpmn_gw_split_start,
                Task(id=task_1, name=task_1),
                bpmn_gw_join_start,
                Task(id="EXPLICIT" + gw_both, name=xor_join_and_split_in_1.get_name()),
                bpmn_gw_split_end,
                Task(id=task_2, name=task_2),
                bpmn_gw_join_end,
                EndEvent(id=ee_id),
            ],
            [bpmn_gw_split_start, Task(id=task_11, name=task_11), bpmn_gw_join_start],
            [bpmn_gw_split_end, Task(id=task_22, name=task_22), bpmn_gw_join_end],
        ],
    )

    return bpmn, net, case


def and_xor_split():
    """Return a BPMN and workflow net with mixed gates."""
    case = "gateway_and_xor_split"
    se_id = "elem_1"
    ee_id = "elem_2"

    task_1 = "elem_3"
    task_11 = "elem_6"
    task_2 = "elem_30"
    task_22 = "elem_60"

    gw_xor_join_start = "elem_4"
    gw_and_split_start = "elem_5"

    gw_both = "elem_both"

    # Xor Part
    xor_join_1 = create_operator_transition(
        gw_xor_join_start, 1, WorkflowBranchingType.XorSplit
    )
    xor_join_2 = create_operator_transition(
        gw_xor_join_start, 2, WorkflowBranchingType.XorSplit
    )
    # Inner Part
    linking_place = create_operator_place(gw_both, WorkflowBranchingType.AndJoinXorSplit)
    and_join_xor_split_in = create_operator_transition(
        gw_both, 1, WorkflowBranchingType.AndJoinXorSplit
    )
    and_join_xor_split_out_1 = create_operator_transition(
        gw_both, 2, WorkflowBranchingType.AndJoinXorSplit
    )
    and_join_xor_split_out_2 = create_operator_transition(
        gw_both, 3, WorkflowBranchingType.AndJoinXorSplit
    )
    # And Part
    and_split = create_operator_transition(
        gw_and_split_start, 1, WorkflowBranchingType.AndJoin
    )

    start = Place.create(id=se_id)
    end = Place.create(id=ee_id)
    net = create_petri_net(
        case,
        [
            [
                start,
                and_split,
                Place.create(id=create_silent_node_name(and_split.id, task_1)),
                Transition.create(id=task_1, name=task_1),
                Place.create(
                    id=create_silent_node_name(task_1, and_join_xor_split_in.id)
                ),
                and_join_xor_split_in,
                linking_place,
                and_join_xor_split_out_1,
                Place.create(
                    id=create_silent_node_name(and_join_xor_split_out_1.id, task_2)
                ),
                Transition.create(id=task_2, name=task_2),
                Place.create(id=create_silent_node_name(task_2, xor_join_1.id)),
                xor_join_1,
                end,
            ],
            [
                and_split,
                Place.create(id=create_silent_node_name(and_split.id, task_11)),
                Transition.create(id=task_11, name=task_11),
                Place.create(id=create_silent_node_name(task_11, xor_join_2.id)),
                and_join_xor_split_in,
            ],
            [
                linking_place,
                and_join_xor_split_out_2,
                Place.create(
                    id=create_silent_node_name(and_join_xor_split_out_2.id, task_22)
                ),
                Transition.create(id=task_22, name=task_22),
                Place.create(id=create_silent_node_name(task_22, xor_join_1.id)),
                xor_join_2,
                end,
            ],
        ],
    )

    bpmn_gw_split_start = AndGateway(id=gw_and_split_start)
    bpmn_gw_join_start = AndGateway(id="AND" + gw_both)
    bpmn_gw_split_end = XorGateway(id="XOR" + gw_both)
    bpmn_gw_join_end = XorGateway(id=gw_xor_join_start)

    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                bpmn_gw_split_start,
                Task(id=task_1, name=task_1),
                bpmn_gw_join_start,
                bpmn_gw_split_end,
                Task(id=task_2, name=task_2),
                bpmn_gw_join_end,
                EndEvent(id=ee_id),
            ],
            [bpmn_gw_split_start, Task(id=task_11, name=task_11), bpmn_gw_join_start],
            [bpmn_gw_split_end, Task(id=task_22, name=task_22), bpmn_gw_join_end],
        ],
    )

    return bpmn, net, case


def and_xor_split_implicit():
    """Return a BPMN and workflow net with mixed gates."""
    case = "gateway_and_xor_split_implicit"
    se_id = "elem_1"
    ee_id = "elem_2"

    task_1 = "elem_3"
    task_11 = "elem_6"
    task_2 = "elem_30"
    task_22 = "elem_60"

    gw_xor_join_start = "elem_4"
    gw_and_split_start = "elem_5"

    gw_both = "elem_both"

    # Xor Part
    xor_join_1 = create_operator_transition(
        gw_xor_join_start, 1, WorkflowBranchingType.XorSplit
    )
    xor_join_2 = create_operator_transition(
        gw_xor_join_start, 2, WorkflowBranchingType.XorSplit
    )
    # Inner Part
    linking_place = create_operator_place(gw_both, WorkflowBranchingType.AndJoinXorSplit)
    and_join_xor_split_in = create_operator_transition(
        gw_both, 1, WorkflowBranchingType.AndJoinXorSplit, "both"
    )
    and_join_xor_split_out_1 = create_operator_transition(
        gw_both, 2, WorkflowBranchingType.AndJoinXorSplit, "both"
    )
    and_join_xor_split_out_2 = create_operator_transition(
        gw_both, 3, WorkflowBranchingType.AndJoinXorSplit, "both"
    )
    # And Part
    and_split = create_operator_transition(
        gw_and_split_start, 1, WorkflowBranchingType.AndJoin
    )

    start = Place.create(id=se_id)
    end = Place.create(id=ee_id)
    net = create_petri_net(
        case,
        [
            [
                start,
                and_split,
                Place.create(id=create_silent_node_name(and_split.id, task_1)),
                Transition.create(id=task_1, name=task_1),
                Place.create(
                    id=create_silent_node_name(task_1, and_join_xor_split_in.id)
                ),
                and_join_xor_split_in,
                linking_place,
                and_join_xor_split_out_1,
                Place.create(
                    id=create_silent_node_name(and_join_xor_split_out_1.id, task_2)
                ),
                Transition.create(id=task_2, name=task_2),
                Place.create(id=create_silent_node_name(task_2, xor_join_1.id)),
                xor_join_1,
                end,
            ],
            [
                and_split,
                Place.create(id=create_silent_node_name(and_split.id, task_11)),
                Transition.create(id=task_11, name=task_11),
                Place.create(id=create_silent_node_name(task_11, xor_join_2.id)),
                and_join_xor_split_in,
            ],
            [
                linking_place,
                and_join_xor_split_out_2,
                Place.create(
                    id=create_silent_node_name(and_join_xor_split_out_2.id, task_22)
                ),
                Transition.create(id=task_22, name=task_22),
                Place.create(id=create_silent_node_name(task_22, xor_join_1.id)),
                xor_join_2,
                end,
            ],
        ],
    )

    bpmn_gw_split_start = AndGateway(id=gw_and_split_start)
    bpmn_gw_join_start = AndGateway(id="AND" + gw_both)
    bpmn_gw_split_end = XorGateway(id="XOR" + gw_both)
    bpmn_gw_join_end = XorGateway(id=gw_xor_join_start)

    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                bpmn_gw_split_start,
                Task(id=task_1, name=task_1),
                bpmn_gw_join_start,
                Task(id="EXPLICIT" + gw_both, name=and_join_xor_split_in.get_name()),
                bpmn_gw_split_end,
                Task(id=task_2, name=task_2),
                bpmn_gw_join_end,
                EndEvent(id=ee_id),
            ],
            [bpmn_gw_split_start, Task(id=task_11, name=task_11), bpmn_gw_join_start],
            [bpmn_gw_split_end, Task(id=task_22, name=task_22), bpmn_gw_join_end],
        ],
    )

    return bpmn, net, case


def subprocess():
    """Return a BPMN and workflow net with a subprocess."""
    case = "subprocess"
    se_id = "elem_1"
    ee_id = "elem_2"

    subprocess_id = "elem_3"
    subprocess_name = "subprocess"
    # subprocess nodes
    sb_t_id = "elem_sb_3"

    net = create_petri_net(
        case,
        [
            [
                Place(id=se_id),
                Transition.create(
                    subprocess_id, subprocess_name
                ).mark_as_workflow_subprocess(),
                Place(id=ee_id),
            ],
        ],
    )
    #
    net_page = Page(
        id=subprocess_id,
        net=create_petri_net(
            "",
            [
                [
                    Place(id=se_id),
                    Transition.create(id=sb_t_id, name=sb_t_id),
                    Place(id=ee_id),
                ]
            ],
        ).net,
    )
    net_page.net.id = subprocess_id
    net.net.add_page(net_page)

    sub_bpmn = create_bpmn(
        "temp",
        [
            [
                StartEvent(id="SB_" + se_id),
                Task(id=sb_t_id, name=sb_t_id),
                EndEvent(id="SB_" + ee_id),
            ]
        ],
    )
    sub_bpmn.process.id = subprocess_id
    sub_bpmn.process.name = subprocess_name

    bpmn = create_bpmn(
        case, [[StartEvent(id=se_id), sub_bpmn.process, EndEvent(id=ee_id)]]
    )

    return bpmn, net, case


supported_cases_workflow_pnml: list[tuple[BPMN, Pnml, str]] = [
    pool_with_gateways(),
    subprocess_pool(),
    simple_pool(),
    gateway_parallel_join_split_with_events(),
    sequential_time_event_silent(),
    sequential_message_event_silent(),
    sequential_time_event(),
    sequential_message_event(),
    and_xor_split_implicit(),
    xor_and_split_implicit(),
    gateway_exclusive_join_split_implicit(),
    gateway_parallel_join_split_implicit(),
    gateway_parallel_join_split(),
    gateway_exclusive_join_split(),
    gateway_side_by_side_xor_and(),
    gateway_side_by_side_and_xor(),
    xor_and_split(),
    and_xor_split(),
    subprocess(),
]

