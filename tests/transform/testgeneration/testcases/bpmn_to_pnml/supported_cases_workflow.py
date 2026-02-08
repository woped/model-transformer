"""Generates BPMN and expected petri net for various workflow cases ."""

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
    ServiceTask,
    StartEvent,
    Task,
    UserTask,
    XorGateway,
)
from app.transform.transformer.models.pnml.base import (
    Name,
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
    sb_se_id = "elem_sb_1"
    sb_ee_id = "elem_sb_2"
    sb_t_id = "elem_sb_3"

    sb_se_id = "elem_sb_1"
    sb_ee_id = "elem_sb_2"
    sb_t_id = "elem_sb_3"

    sub_bpmn = create_bpmn(
        "temp", [[StartEvent(id=sb_se_id), UserTask(id=sb_t_id), EndEvent(id=sb_ee_id)]]
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
                        flowNodeRefs=set([se_id, subprocess_id]),
                    ),
                    Lane(
                        id=lane_2, name=lane_2, flowNodeRefs=set([task_lane_2_id, ee_id])
                    ),
                ]
            ),
        )
    )
    net = create_petri_net(
        case,
        [
            [
                Place.create(id=se_id),
                Transition.create(
                    subprocess_id, subprocess_name
                ).mark_as_workflow_subprocess(),
                Place.create(id=create_silent_node_name(subprocess_id, task_lane_2_id)),
                Transition.create(id=task_lane_2_id, name="[UserTask] None").mark_as_workflow_resource(
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
                    Transition(id=sb_t_id, name=Name(title="[UserTask] None")).mark_as_workflow_resource(lane_1, orga),
                    Place(id=create_silent_node_name(subprocess_id, task_lane_2_id)),
                ]
            ],
        ).net,
    )
    net_page.net.id = None
    net.net.add_page(net_page)

    return bpmn, net, case


def trigger_pool_combination():
    """Return a BPMN and the expected petri net with a pool and trigger."""
    case = "trigger_pool_combination"

    se_id = "elem_1"
    user_task_id = "user_task_1"
    trigger_id = "trigger"
    ee_id = "elem_2"

    lane_1 = "lane1"
    orga = "orga"

    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                IntermediateCatchEvent.create_time_event(trigger_id),
                UserTask(id=user_task_id),
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
                        flowNodeRefs=set([se_id, user_task_id, ee_id, trigger_id]),
                    ),
                ]
            ),
        )
    )
    net = create_petri_net(
        case,
        [
            [
                Place.create(id=se_id),
                Transition.create(id=trigger_id).mark_as_workflow_time(),
                Place.create(id=create_silent_node_name(trigger_id, user_task_id)),
                Transition.create(id=user_task_id, name="[UserTask] None").mark_as_workflow_resource(
                    lane_1, orga
                ),
                Place.create(id=ee_id),
            ],
        ],
    )
    net.net.toolspecific_global = ToolspecificGlobal(
        resources=Resources(
            roles=[
                Role(name=lane_1),
            ],
            units=[OrganizationUnit(name=orga)],
        )
    )
    return bpmn, net, case


def simple_pool():
    """Return a BPMN and the expected petri net with a pool with 2 lanes."""
    case = "simple_pool"
    se_id = "elem_1"
    task_lane_1_id = "task_lane_1"
    task_lane_2_id = "task_lane_2"
    service_task = "service_task"
    ee_id = "elem_2"

    lane_1 = "lane1"
    lane_2 = "lane2"
    orga = "orga"

    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                UserTask(id=task_lane_1_id),
                ServiceTask(id=service_task, name=service_task),
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
                        id=lane_1, name=lane_1, flowNodeRefs=set([se_id, task_lane_1_id])
                    ),
                    Lane(
                        id=lane_2, name=lane_2, flowNodeRefs=set([task_lane_2_id, ee_id])
                    ),
                ]
            ),
        )
    )
    net = create_petri_net(
        case,
        [
            [
                Place.create(id=se_id),
                Transition.create(id=task_lane_1_id, name="[UserTask] None").mark_as_workflow_resource(
                    lane_1, orga
                ),
                Place.create(id=create_silent_node_name(task_lane_1_id, service_task)),
                Transition.create(id=service_task, name="[ServiceTask] service_task"),
                Place.create(id=create_silent_node_name(service_task, task_lane_2_id)),
                Transition.create(id=task_lane_2_id, name="[UserTask] None").mark_as_workflow_resource(
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
    return bpmn, net, case


def sequential_time_event():
    """Return a BPMN and the expected petri net with  IntermediateCatchEvent(Time)."""
    case = "sequential_time_event"
    se_id = "elem_1"
    trigger_id = "trigger"
    task_id = "task"
    ee_id = "elem_2"
    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                IntermediateCatchEvent.create_time_event(trigger_id),
                Task(id=task_id),
                EndEvent(id=ee_id),
            ]
        ],
    )
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
    return bpmn, net, case


def sequential_message_event():
    """Return a BPMN and the expected petri net with  IntermediateCatchEvent(Message)."""
    case = "sequential_message_event"
    se_id = "elem_1"
    trigger_id = "trigger"
    task_id = "task"
    ee_id = "elem_2"
    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                IntermediateCatchEvent.create_message_event(trigger_id),
                Task(id=task_id),
                EndEvent(id=ee_id),
            ]
        ],
    )
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
    return bpmn, net, case


def reduce_unnecessary_gw():
    """Return a BPMN and the expected petri net with reduced gateways."""
    case = "reduce_unnecessary_gw"
    se_id = "elem_1"
    gw_id = "gw"
    ee_id = "elem_2"
    gw = AndGateway(id=gw_id)
    bpmn = create_bpmn(case, [[StartEvent(id=se_id), gw, EndEvent(id=ee_id)]])
    net = create_petri_net(
        case,
        [
            [
                Place.create(id=se_id),
                Transition.create(id=create_silent_node_name(se_id, ee_id)),
                Place.create(id=ee_id),
            ]
        ],
    )
    return bpmn, net, case


def gateway_parallel_join_split():
    """Return a BPMN and the expected workflow net with AND gates."""
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

    bpmn_gw_split = AndGateway(id=gw_split, name=gw_split)
    bpmn_gw_both = AndGateway(id=gw_both, name=gw_both)
    bpmn_gw_join = AndGateway(id=gw_join, name=gw_join)

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
    and_split = create_operator_transition(
        gw_split, 1, WorkflowBranchingType.AndSplit, gw_split
    )
    and_join_split = create_operator_transition(
        gw_both, 1, WorkflowBranchingType.AndJoinSplit, gw_both
    )
    and_join = create_operator_transition(
        gw_join, 1, WorkflowBranchingType.AndJoin, gw_join
    )

    net = create_petri_net(
        case,
        [
            [
                Place.create(id=se_id),
                and_split,
                Place.create(id=create_silent_node_name(gw_split, task_1)),
                Transition.create(id=task_1, name=task_1),
                Place.create(id=create_silent_node_name(task_1, gw_both)),
                and_join_split,
                Place.create(id=create_silent_node_name(gw_both, task_2)),
                Transition.create(id=task_2, name=task_2),
                Place.create(id=create_silent_node_name(task_2, gw_join)),
                and_join,
                Place.create(id=ee_id),
            ],
            [
                and_split,
                Place.create(id=create_silent_node_name(gw_split, task_11)),
                Transition.create(id=task_11, name=task_11),
                Place.create(id=create_silent_node_name(task_11, gw_both)),
                and_join_split,
            ],
            [
                and_join_split,
                Place.create(id=create_silent_node_name(gw_both, task_22)),
                Transition.create(id=task_22, name=task_22),
                Place.create(id=create_silent_node_name(task_22, gw_join)),
                and_join,
            ],
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

    trigger_before_and_split = "elem_8"
    trigger_before_and_join_split = "elem_9"
    trigger_before_and_join = "elem_10"

    bpmn_gw_split = AndGateway(id=gw_split, name=gw_split)
    bpmn_gw_both = AndGateway(id=gw_both, name=gw_both)
    bpmn_gw_join = AndGateway(id=gw_join, name=gw_join)

    bpmn_trigger_before_and_split = IntermediateCatchEvent.create_time_event(
        trigger_before_and_split
    )
    bpmn_trigger_before_and_join_split = IntermediateCatchEvent.create_time_event(
        trigger_before_and_join_split
    )
    bpmn_trigger_before_and_join = IntermediateCatchEvent.create_time_event(
        trigger_before_and_join, trigger_before_and_join
    )

    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                bpmn_trigger_before_and_split,
                bpmn_gw_split,
                Task(id=task_1, name=task_1),
                bpmn_trigger_before_and_join_split,
                bpmn_gw_both,
                Task(id=task_2, name=task_2),
                bpmn_trigger_before_and_join,
                bpmn_gw_join,
                EndEvent(id=ee_id),
            ],
            [bpmn_gw_split, Task(id=task_11, name=task_11), bpmn_gw_both],
            [bpmn_gw_both, Task(id=task_22, name=task_22), bpmn_gw_join],
        ],
    )
    and_split = create_operator_transition(
        gw_split, 1, WorkflowBranchingType.AndSplit, gw_split
    ).mark_as_workflow_time()
    and_join_split = create_operator_transition(
        gw_both, 1, WorkflowBranchingType.AndJoinSplit, gw_both
    )
    and_join = create_operator_transition(
        gw_join, 1, WorkflowBranchingType.AndJoin, gw_join
    )

    trigger_transition_split_join = Transition.create(
        trigger_before_and_join_split
    ).mark_as_workflow_time()
    trigger_transition_join = Transition.create(
        trigger_before_and_join, trigger_before_and_join
    ).mark_as_workflow_time()

    net = create_petri_net(
        case,
        [
            [
                Place.create(id=se_id),
                and_split,
                Place.create(id=create_silent_node_name(gw_split, task_1)),
                Transition.create(id=task_1, name=task_1),
                Place.create(
                    id=create_silent_node_name(task_1, trigger_before_and_join_split)
                ),
                trigger_transition_split_join,
                Place.create(
                    id=create_silent_node_name(trigger_before_and_join_split, gw_both)
                ),
                and_join_split,
                Place.create(id=create_silent_node_name(gw_both, task_2)),
                Transition.create(id=task_2, name=task_2),
                Place.create(
                    id=create_silent_node_name(task_2, trigger_before_and_join)
                ),
                trigger_transition_join,
                Place.create(
                    id=create_silent_node_name(trigger_before_and_join, gw_join)
                ),
                and_join,
                Place.create(id=ee_id),
            ],
            [
                and_split,
                Place.create(id=create_silent_node_name(gw_split, task_11)),
                Transition.create(id=task_11, name=task_11),
                Place.create(id=create_silent_node_name(task_11, gw_both)),
                and_join_split,
            ],
            [
                and_join_split,
                Place.create(id=create_silent_node_name(gw_both, task_22)),
                Transition.create(id=task_22, name=task_22),
                Place.create(id=create_silent_node_name(task_22, gw_join)),
                and_join,
            ],
        ],
    )
    return bpmn, net, case


def gateway_exclusive_join_split_with_events():
    """Return a BPMN and the expected workflow net for an with XOR gates."""
    case = "gateway_exclusive_join_split_with_events"
    se_id = "elem_1"
    ee_id = "elem_2"

    task_1 = "elem_3"
    task_11 = "elem_6"
    task_2 = "elem_30"
    task_22 = "elem_60"

    gw_split = "elem_4"
    gw_join = "elem_5"
    gw_both = "elem_7"

    trigger_before_xor_split = "elem_8"
    trigger_before_xor_join_split = "elem_9"
    trigger_before_xor_join = "elem_10"

    bpmn_gw_split = XorGateway(id=gw_split, name=gw_split)
    bpmn_gw_both = XorGateway(id=gw_both, name=gw_both)
    bpmn_gw_join = XorGateway(id=gw_join, name=gw_join)

    bpmn_trigger_before_and_split = IntermediateCatchEvent.create_time_event(
        trigger_before_xor_split
    )
    bpmn_trigger_before_and_join_split = IntermediateCatchEvent.create_time_event(
        trigger_before_xor_join_split
    )
    bpmn_trigger_before_and_join = IntermediateCatchEvent.create_time_event(
        trigger_before_xor_join, trigger_before_xor_join
    )

    bpmn = create_bpmn(
        case,
        [
            [
                StartEvent(id=se_id),
                bpmn_trigger_before_and_split,
                bpmn_gw_split,
                Task(id=task_1, name=task_1),
                bpmn_trigger_before_and_join_split,
                bpmn_gw_both,
                Task(id=task_2, name=task_2),
                bpmn_trigger_before_and_join,
                bpmn_gw_join,
                EndEvent(id=ee_id),
            ],
            [bpmn_gw_split, Task(id=task_11, name=task_11), bpmn_gw_both],
            [bpmn_gw_both, Task(id=task_22, name=task_22), bpmn_gw_join],
        ],
    )
    xor_split_1 = create_operator_transition(
        gw_split, 1, WorkflowBranchingType.XorSplit, gw_split
    ).mark_as_workflow_time()
    xor_split_2 = create_operator_transition(
        gw_split, 2, WorkflowBranchingType.XorSplit, gw_split
    ).mark_as_workflow_time()

    xor_join_split_place = create_operator_place(
        gw_both, WorkflowBranchingType.XorJoinSplit
    )
    xor_join_split_in_1 = create_operator_transition(
        gw_both, 1, WorkflowBranchingType.XorJoinSplit, gw_both
    )
    xor_join_split_in_2 = create_operator_transition(
        gw_both, 2, WorkflowBranchingType.XorJoinSplit, gw_both
    )
    xor_join_split_out_1 = create_operator_transition(
        gw_both, 3, WorkflowBranchingType.XorJoinSplit, gw_both
    )
    xor_join_split_out_2 = create_operator_transition(
        gw_both, 4, WorkflowBranchingType.XorJoinSplit, gw_both
    )

    xor_join_1 = create_operator_transition(
        gw_join, 1, WorkflowBranchingType.XorJoin, gw_join
    )
    xor_join_2 = create_operator_transition(
        gw_join, 2, WorkflowBranchingType.XorJoin, gw_join
    )

    trigger_transition_split_join = Transition.create(
        trigger_before_xor_join_split
    ).mark_as_workflow_time()
    trigger_transition_join = Transition.create(
        trigger_before_xor_join, trigger_before_xor_join
    ).mark_as_workflow_time()

    start = Place.create(id=se_id)
    end = Place.create(id=ee_id)
    net = create_petri_net(
        case,
        [
            [
                start,
                xor_split_1,
                Place.create(id=create_silent_node_name(gw_split, task_1)),
                Transition.create(id=task_1, name=task_1),
                Place.create(
                    id=create_silent_node_name(task_1, trigger_before_xor_join_split)
                ),
                trigger_transition_split_join,
                Place.create(
                    id=create_silent_node_name(trigger_before_xor_join_split, gw_both)
                ),
                xor_join_split_in_2,
                xor_join_split_place,
                xor_join_split_out_1,
                Place.create(id=create_silent_node_name(gw_both, task_2)),
                Transition.create(id=task_2, name=task_2),
                Place.create(
                    id=create_silent_node_name(task_2, trigger_before_xor_join)
                ),
                trigger_transition_join,
                Place.create(
                    id=create_silent_node_name(trigger_before_xor_join, gw_join)
                ),
                xor_join_1,
                end,
            ],
            [
                start,
                xor_split_2,
                Place.create(id=create_silent_node_name(gw_split, task_11)),
                Transition.create(id=task_11, name=task_11),
                Place.create(id=create_silent_node_name(task_11, gw_both)),
                xor_join_split_in_1,
                xor_join_split_place,
                xor_join_split_out_2,
                Place.create(id=create_silent_node_name(gw_both, task_22)),
                Transition.create(id=task_22, name=task_22),
                Place.create(id=create_silent_node_name(task_22, gw_join)),
                xor_join_2,
                end,
            ],
        ],
    )
    return bpmn, net, case


def gateway_exclusive_join_split():
    """Return a BPMN and the expected workflow net for an with XOR gates."""
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

    bpmn_gw_split = XorGateway(id=gw_split, name=gw_split)
    bpmn_gw_both = XorGateway(id=gw_both, name=gw_both)
    bpmn_gw_join = XorGateway(id=gw_join, name=gw_join)

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
    xor_split_1 = create_operator_transition(
        gw_split, 1, WorkflowBranchingType.XorSplit, gw_split
    )
    xor_split_2 = create_operator_transition(
        gw_split, 2, WorkflowBranchingType.XorSplit, gw_split
    )

    xor_join_split_place = create_operator_place(
        gw_both, WorkflowBranchingType.XorJoinSplit
    )
    xor_join_split_in_1 = create_operator_transition(
        gw_both, 1, WorkflowBranchingType.XorJoinSplit, gw_both
    )
    xor_join_split_in_2 = create_operator_transition(
        gw_both, 2, WorkflowBranchingType.XorJoinSplit, gw_both
    )
    xor_join_split_out_1 = create_operator_transition(
        gw_both, 3, WorkflowBranchingType.XorJoinSplit, gw_both
    )
    xor_join_split_out_2 = create_operator_transition(
        gw_both, 4, WorkflowBranchingType.XorJoinSplit, gw_both
    )

    xor_join_1 = create_operator_transition(
        gw_join, 1, WorkflowBranchingType.XorJoin, gw_join
    )
    xor_join_2 = create_operator_transition(
        gw_join, 2, WorkflowBranchingType.XorJoin, gw_join
    )

    start = Place.create(id=se_id)
    end = Place.create(id=ee_id)
    net = create_petri_net(
        case,
        [
            [
                start,
                xor_split_1,
                Place.create(id=create_silent_node_name(gw_split, task_1)),
                Transition.create(id=task_1, name=task_1),
                Place.create(id=create_silent_node_name(task_1, gw_both)),
                xor_join_split_in_1,
                xor_join_split_place,
                xor_join_split_out_1,
                Place.create(id=create_silent_node_name(gw_both, task_2)),
                Transition.create(id=task_2, name=task_2),
                Place.create(id=create_silent_node_name(task_2, gw_join)),
                xor_join_1,
                end,
            ],
            [
                start,
                xor_split_2,
                Place.create(id=create_silent_node_name(gw_split, task_11)),
                Transition.create(id=task_11, name=task_11),
                Place.create(id=create_silent_node_name(task_11, gw_both)),
                xor_join_split_in_2,
                xor_join_split_place,
                xor_join_split_out_2,
                Place.create(id=create_silent_node_name(gw_both, task_22)),
                Transition.create(id=task_22, name=task_22),
                Place.create(id=create_silent_node_name(task_22, gw_join)),
                xor_join_2,
                end,
            ],
        ],
    )
    return bpmn, net, case


def gateway_side_by_side_xor_and():
    """Return a BPMN and the expected workflow net with mixed gates."""
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

    bpmn_gw_split_start = XorGateway(id=gw_split_start, name=gw_split_start)
    bpmn_gw_join_start = XorGateway(id=gw_join_start, name=gw_join_start)
    bpmn_gw_split_end = AndGateway(id=gw_split_end, name=gw_split_end)
    bpmn_gw_join_end = AndGateway(id=gw_join_end, name=gw_join_end)

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
    # Xor Part
    xor_split_1 = create_operator_transition(
        gw_split_start, 1, WorkflowBranchingType.XorSplit, gw_split_start
    )
    xor_split_2 = create_operator_transition(
        gw_split_start, 2, WorkflowBranchingType.XorSplit, gw_split_start
    )
    xor_join_1 = create_operator_transition(
        gw_join_start, 1, WorkflowBranchingType.XorJoin, gw_join_start
    )
    xor_join_2 = create_operator_transition(
        gw_join_start, 2, WorkflowBranchingType.XorJoin, gw_join_start
    )
    # And Part
    and_split = create_operator_transition(
        gw_split_end, 1, WorkflowBranchingType.AndSplit, gw_split_end
    )
    and_join = create_operator_transition(
        gw_join_end, 1, WorkflowBranchingType.AndJoin, gw_join_end
    )

    gateway_merge_place = Place.create(id=bpmn_gw_join_start.id + bpmn_gw_split_end.id)

    start = Place.create(id=se_id)
    end = Place.create(id=ee_id)
    net = create_petri_net(
        case,
        [
            [
                start,
                xor_split_1,
                Place.create(id=create_silent_node_name(gw_split_start, task_1)),
                Transition.create(id=task_1, name=task_1),
                Place.create(id=create_silent_node_name(task_1, gw_join_start)),
                xor_join_1,
                gateway_merge_place,
                and_split,
                Place.create(id=create_silent_node_name(gw_split_end, task_2)),
                Transition.create(id=task_2, name=task_2),
                Place.create(id=create_silent_node_name(task_2, gw_join_end)),
                and_join,
                end,
            ],
            [
                start,
                xor_split_2,
                Place.create(id=create_silent_node_name(gw_split_start, task_11)),
                Transition.create(id=task_11, name=task_11),
                Place.create(id=create_silent_node_name(task_11, gw_join_start)),
                xor_join_2,
                gateway_merge_place,
            ],
            [
                and_split,
                Place.create(id=create_silent_node_name(gw_split_end, task_22)),
                Transition.create(id=task_22, name=task_22),
                Place.create(id=create_silent_node_name(task_22, gw_join_end)),
                and_join,
            ],
        ],
    )
    return bpmn, net, case


def gateway_side_by_side_and_xor():
    """Return a BPMN and the expected workflow net with XOR+AND gates."""
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

    bpmn_gw_split_start = AndGateway(id=gw_split_start, name=gw_split_start)
    bpmn_gw_join_start = AndGateway(id=gw_join_start, name=gw_join_start)
    bpmn_gw_split_end = XorGateway(id=gw_split_end, name=gw_split_end)
    bpmn_gw_join_end = XorGateway(id=gw_join_end, name=gw_join_end)

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
    # And Part
    and_split = create_operator_transition(
        gw_split_start, 1, WorkflowBranchingType.AndSplit, gw_split_start
    )
    and_join = create_operator_transition(
        gw_join_start, 1, WorkflowBranchingType.AndJoin, gw_join_start
    )
    # Xor Part
    xor_split_1 = create_operator_transition(
        gw_split_end, 1, WorkflowBranchingType.XorSplit, gw_split_end
    )
    xor_split_2 = create_operator_transition(
        gw_split_end, 2, WorkflowBranchingType.XorSplit, gw_split_end
    )
    xor_join_1 = create_operator_transition(
        gw_join_end, 1, WorkflowBranchingType.XorJoin, gw_join_end
    )
    xor_join_2 = create_operator_transition(
        gw_join_end, 2, WorkflowBranchingType.XorJoin, gw_join_end
    )

    gateway_merge_place = Place.create(id=bpmn_gw_join_start.id + bpmn_gw_split_end.id)

    start = Place.create(id=se_id)
    end = Place.create(id=ee_id)
    net = create_petri_net(
        case,
        [
            [
                start,
                and_split,
                Place.create(id=create_silent_node_name(gw_split_start, task_1)),
                Transition.create(id=task_1, name=task_1),
                Place.create(id=create_silent_node_name(task_1, gw_join_start)),
                and_join,
                gateway_merge_place,
                xor_split_1,
                Place.create(id=create_silent_node_name(gw_split_end, task_2)),
                Transition.create(id=task_2, name=task_2),
                Place.create(id=create_silent_node_name(task_2, gw_join_end)),
                xor_join_1,
                end,
            ],
            [
                and_split,
                Place.create(id=create_silent_node_name(gw_split_start, task_11)),
                Transition.create(id=task_11, name=task_11),
                Place.create(id=create_silent_node_name(task_11, gw_join_start)),
                and_join,
            ],
            [
                gateway_merge_place,
                xor_split_2,
                Place.create(id=create_silent_node_name(gw_split_end, task_22)),
                Transition.create(id=task_22, name=task_22),
                Place.create(id=create_silent_node_name(task_22, gw_join_end)),
                xor_join_2,
                end,
            ],
        ],
    )
    return bpmn, net, case


def subprocess():
    """Return a BPMN and the expected workflow net with a subprocess."""
    case = "subprocess"
    se_id = "elem_1"
    ee_id = "elem_2"

    subprocess_id = "elem_3"
    subprocess_name = "subprocess"
    # subprocess nodes
    sb_se_id = "elem_sb_1"
    sb_ee_id = "elem_sb_2"
    sb_t_id = "elem_sb_3"

    sub_bpmn = create_bpmn(
        "temp", [[StartEvent(id=sb_se_id), Task(id=sb_t_id), EndEvent(id=sb_ee_id)]]
    )
    sub_bpmn.process.id = subprocess_id
    sub_bpmn.process.name = subprocess_name

    bpmn = create_bpmn(
        case, [[StartEvent(id=se_id), sub_bpmn.process, EndEvent(id=ee_id)]]
    )

    net = create_petri_net(
        case,
        [
            [
                Place(id=se_id),
                Transition.create(
                    subprocess_id, subprocess_name
                ).mark_as_workflow_subprocess(),
                Place(id=ee_id),
            ]
        ],
    )

    net_page = Page(
        id=subprocess_id,
        net=create_petri_net(
            "", [[Place(id=se_id), Transition(id=sb_t_id), Place(id=ee_id)]]
        ).net,
    )
    net_page.net.id = None
    net.net.add_page(net_page)

    return bpmn, net, case


supported_cases_workflow_bpmn: list[tuple[BPMN, Pnml, str]] = [
    gateway_exclusive_join_split_with_events(),
    trigger_pool_combination(),
    subprocess_pool(),
    simple_pool(),
    gateway_parallel_join_split_with_events(),
    sequential_message_event(),
    sequential_time_event(),
    subprocess(),
    reduce_unnecessary_gw(),
    gateway_parallel_join_split(),
    gateway_exclusive_join_split(),
    gateway_side_by_side_xor_and(),
    gateway_side_by_side_and_xor(),
]

