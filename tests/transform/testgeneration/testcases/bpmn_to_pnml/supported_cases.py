"""Generates simple BPMN and the according petri net for multiple cases."""

from tests.transform.testgeneration.bpmn.utility import create_bpmn
from tests.transform.testgeneration.pnml.utility import create_petri_net

from app.transform.transformer.models.bpmn.bpmn import (
    BPMN,
    EndEvent,
    StartEvent,
    Task,
    UserTask,
)
from app.transform.transformer.models.pnml.pnml import Place, Pnml, Transition
from app.transform.transformer.utility.utility import create_silent_node_name


def start_end():
    """Returns a simple bpmn and the according petri net for a start-end scenario."""
    case = "start_end"
    se_id = "start"
    ee_id = "end"
    bpmn = create_bpmn(case, [[StartEvent(id=se_id), EndEvent(id=ee_id)]])
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
    return bpmn, net, case


def gen_task(task_cls, case):
    """Helper to generate a test_case depending on the supplied task class."""
    se_id = "elem_1"
    ee_id = "elem_2"
    task_id = "elem_3"
    bpmn = create_bpmn(
        case,
        [[StartEvent(id=se_id), task_cls(id=task_id, name=task_id), EndEvent(id=ee_id)]],
    )
    net = create_petri_net(
        case,
        [
            [
                Place(id=se_id),
                Transition.create(task_id, task_id),
                Place(id=ee_id),
            ]
        ],
    )
    return bpmn, net, case


def task():
    """Returns a bpmn and the according petri net for a task."""
    return gen_task(Task, "task")


def user_task():
    """Returns a bpmn and the according petri net for a user task."""
    return gen_task(UserTask, "usertask")


def system_task():
    """Returns a bpmn and the according petri net for a user task."""
    return gen_task(UserTask, "systemtask")


all_cases: list[tuple[BPMN, Pnml, str]] = [
    start_end(),
    task(),
    user_task(),
    system_task(),
]

