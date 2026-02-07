"""Generate unsupported cases for BPMN to PNML."""

import shutil

from tests.transform.testgeneration.bpmn.utility import create_bpmn, rename_bpmn_xml
from tests.transform.testgeneration.utility import create_file_path, read_bpmn_file

from app.transform.transformer.models.bpmn.bpmn import EndEvent, StartEvent, Task


def generate_helper_bpmn(case_name: str):
    """Return a simple helper BPMN (Start,Task,End)."""
    se_id = "elem_1"
    ee_id = "elem_2"
    task_id = "elem_3"
    bpmn = create_bpmn(
        case_name, [[StartEvent(id=se_id), Task(id=task_id), EndEvent(id=ee_id)]]
    )
    bpmn.write_to_file(create_file_path("bpmn.bpmn", case_name))
    return read_bpmn_file(case_name)


def generate():
    """Generate BPMNs with unsupported elements."""
    temp_case_name = "temp"
    bpmn = generate_helper_bpmn(temp_case_name)
    bpmns: list[tuple[str, str]] = []
    for case_name in [
        # custom element
        "extensionElements",
        # gateways
        "complexGateway",
        "eventBasedGateway",
        # tasks
        "sendTask",
        "receiveTask",
        "manualTask",
        "businessRuleTask",
        "scriptTask",
        "callActivity",
        # events
        # https://www.omg.org/spec/BPMN/2.0/PDF P. 425
        "intermediateThrowEvent",
        "normalIntermediateThrowEvent",
        "BoundaryEvent",
    ]:
        r = rename_bpmn_xml(bpmn, f"{case_name}")
        bpmns.append((r, case_name))
    shutil.rmtree(create_file_path("", temp_case_name).rsplit("/", 1)[0])
    return bpmns


all_cases = generate()

