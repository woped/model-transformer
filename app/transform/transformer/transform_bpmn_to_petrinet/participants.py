"""Module for handling participants annotations."""

import logging

from app.transform.exceptions import UnnamedLane
from app.transform.transformer.models.bpmn.bpmn import Process, UserTask
from app.transform.transformer.models.pnml.base import (
    OrganizationUnit,
    Resources,
    Role,
    ToolspecificGlobal,
)
from app.transform.transformer.models.pnml.pnml import Net

logger = logging.getLogger(__name__)


def find_subprocess_participants(
    participant_mapping: dict[str, str], subprocess: Process, current_lane_name: str
):
    """Find each resource name per UserTask in the current and nested subprocesses."""
    subprocess._participant_mapping = participant_mapping
    for sb in subprocess.subprocesses:
        find_subprocess_participants(participant_mapping, sb, current_lane_name)
    for node in subprocess._flatten_node_typ_map():
        if isinstance(node, UserTask):
            participant_mapping[node.id] = current_lane_name


def create_participant_mapping(bpmn: Process):
    """Find each resource name per UserTask (Also in subprocesses)."""
    logger.debug("Creating participant mapping")
    if not bpmn.lane_sets:
        logger.debug("No lane sets found, skipping participant mapping")
        return
    # [lane_name; node_name]
    participant_mapping: dict[str, list[str]] = {}
    for lane_set in bpmn.lane_sets:
        for lane in lane_set.lanes:
            for node in lane.flowNodeRefs:
                if not lane.name:
                    raise UnnamedLane()
                if lane.name not in participant_mapping:
                    participant_mapping[lane.name] = []
                participant_mapping[lane.name].append(node)
    # [node_name; lane_name]
    reverse_participant_mapping: dict[str, str] = {}
    for lane_name, nodes in participant_mapping.items():
        for node in nodes:
            reverse_participant_mapping[node] = lane_name
    for sb in bpmn.subprocesses:
        find_subprocess_participants(
            reverse_participant_mapping, sb, reverse_participant_mapping[sb.id]
        )

    bpmn._participant_mapping = reverse_participant_mapping
    logger.debug(f"Created participant mapping with {len(reverse_participant_mapping)} entries")


def set_global_toolspecifi(
    net: Net, participant_mapping: dict[str, str], organization: str
):
    """Creates the toolspecific element for all possible roles after transformation."""
    logger.debug(f"Setting global toolspecific for organization: {organization}")
    if len(participant_mapping) == 0:
        logger.debug("No participant mapping provided, skipping toolspecific")
        return
    possible_roles = {lane_name for lane_name in participant_mapping.values()}
    net.toolspecific_global = ToolspecificGlobal(
        resources=Resources(
            roles=[Role(name=role) for role in possible_roles],
            units=[OrganizationUnit(name=organization)],
        )
    )
    logger.debug(f"Set {len(possible_roles)} roles in toolspecific")

