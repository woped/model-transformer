"""Handle workflow subprocesses and operators of petri net and handle them in bpmn."""

import logging
from collections.abc import Callable

from app.transform.exceptions import (
    InternalTransformationException,
    SubprocessWrongInnerSourceSinkDegree,
    UnknownResourceOrganizationMapping,
)
from app.transform.transformer.models.bpmn.bpmn import (
    BPMN,
    AndGateway,
    Collaboration,
    IntermediateCatchEvent,
    Lane,
    LaneSet,
    Participant,
    Process,
    UserTask,
    XorGateway,
)
from app.transform.transformer.models.pnml.base import NetElement
from app.transform.transformer.models.pnml.pnml import Arc, Net, Page, Transition
from app.transform.transformer.models.pnml.transform_helper import (
    ANDHelperPNML,
    GatewayHelperPNML,
    MessageHelperPNML,
    TimeHelperPNML,
    TriggerHelperPNML,
    XORHelperPNML,
)
from app.transform.transformer.models.pnml.workflow import WorkflowBranchingType
from app.transform.transformer.utility.pnml import generate_subprocess_inner_id
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WorkflowOperatorWrapper(BaseModel):
    """WorkflowOperatorWrapper extension of BaseModel (+ID, name, type, nodes...)."""

    id: str
    name: str | None = None
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

    def get_toolspecific(self):
        """Get the toolspecific imformation of the first transition node."""
        for node in self.nodes:
            if not isinstance(node, Transition):
                continue
            if not node.toolspecific:
                continue
            return node.toolspecific
        raise InternalTransformationException("Should not happen.")

    def get_copy_unique_in_arcs(self):
        """Get all incoming arcs without duplicate input sources."""
        already_added_sources = set()
        arcs: list[Arc] = []
        for arc in self.incoming_arcs:
            if arc.source in already_added_sources:
                continue
            already_added_sources.add(arc.source)
            arcs.append(arc.model_copy())
        return arcs

    def get_copy_unique_out_arcs(self):
        """Get all outgoing arcs without duplicate input targets."""
        already_added_targets = set()
        arcs: list[Arc] = []
        for arc in self.outgoing_arcs:
            if arc.target in already_added_targets:
                continue
            already_added_targets.add(arc.target)
            arcs.append(arc.model_copy())
        return arcs


def find_workflow_subprocesses(net: Net):
    """Return all workflow subprocesses of a net."""
    return [e for e in net.transitions if e.is_workflow_subprocess()]


def find_workflow_operators(net: Net):
    """Return all workflow operators of a net."""
    logger.debug("Finding workflow operators in net")
    operator_map: dict[str, list[NetElement]] = {}
    for node in net._temp_elements.values():
        if isinstance(node, Page):
            continue
        if not node.is_workflow_operator():
            continue
        if not node.toolspecific or not node.toolspecific.operator:
            raise InternalTransformationException("Should not happen.")
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
    logger.debug(f"Found {len(operator_wrappers)} workflow operator groups")
    return operator_wrappers


def handle_workflow_subprocesses(
    net: Net,
    bpmn: Process,
    to_handle_subprocesses: list[Transition],
    caller_func: Callable[[Net], BPMN],
):
    """Add all found workflow subprocesses of a net as nodes to a bpmn."""
    logger.debug(f"Handling {len(to_handle_subprocesses)} workflow subprocesses")
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
            raise SubprocessWrongInnerSourceSinkDegree()

        # Rename inner start and end event because bpmn wont allow same duplicated IDs
        page_net.change_id(
            inner_source_id.id, generate_subprocess_inner_id(inner_source_id.id)
        )
        page_net.change_id(
            inner_sink_id.id, generate_subprocess_inner_id(inner_sink_id.id)
        )

        inner_bpmn = caller_func(page_net).process
        inner_bpmn.id = sb_id
        inner_bpmn.name = subprocess_transition.get_name()
        inner_bpmn.isExecutable = None
        bpmn.add_node(inner_bpmn)
        logger.debug(f"Added subprocess: {sb_id}")


def handle_workflow_operators(
    bpmn: Process, to_handle_temp_gateways: list[GatewayHelperPNML]
):
    """Add all found workflow operators of a net as nodes to a bpmn."""
    logger.debug(f"Handling {len(to_handle_temp_gateways)} workflow operators")
    for temp_gateway in to_handle_temp_gateways:
        if isinstance(temp_gateway, XORHelperPNML):
            bpmn.add_node(XorGateway(id=temp_gateway.id, name=temp_gateway.get_name()))
        elif isinstance(temp_gateway, ANDHelperPNML):
            bpmn.add_node(AndGateway(id=temp_gateway.id, name=temp_gateway.get_name()))


def handle_event_triggers(
    bpmn: Process, to_handle_temp_triggers: list[TriggerHelperPNML]
):
    """Replace all temptriggers with the actual BPMN-Element."""
    logger.debug(f"Handling {len(to_handle_temp_triggers)} event triggers")
    for temp_trigger in to_handle_temp_triggers:
        if isinstance(temp_trigger, MessageHelperPNML):
            bpmn.add_node(IntermediateCatchEvent.create_message_event(temp_trigger.id))
        elif isinstance(temp_trigger, TimeHelperPNML):
            bpmn.add_node(IntermediateCatchEvent.create_time_event(temp_trigger.id))


def handle_resource_transitions(
    bpmn: Process, to_handle_temp_resources: list[Transition]
):
    """Convert resource transitions with out and indegree <=1 to usertasks."""
    logger.debug(f"Handling {len(to_handle_temp_resources)} resource transitions")
    for resource in to_handle_temp_resources:
        bpmn.add_node(UserTask(id=resource.id, name=resource.get_name()))


def find_role_type_of_subprocess(net: Net, current_role: str | None = None):
    """Finds the unique role of a subprocess (and children).

    Should there be more than one role a exception will be thrown.
    """
    to_handle_temp_resources: list[NetElement] = [
        elem
        for elem in net._flatten_node_typ_map()
        if isinstance(elem, NetElement) and elem.is_workflow_resource()
    ]
    for resource in to_handle_temp_resources:
        if not resource.toolspecific or not resource.toolspecific.transitionResource:
            raise InternalTransformationException("Not possible.")
        resource_role = resource.toolspecific.transitionResource.roleName
        if current_role is not None and current_role != resource_role:
            raise UnknownResourceOrganizationMapping()
        current_role = resource_role
    for sb in net.pages:
        nested_role = find_role_type_of_subprocess(sb.net, current_role)
        if nested_role is not None:
            current_role = nested_role
    return current_role


def annotate_resources(net: Net, bpmn: BPMN):
    """Handle resources to participant if net if root element."""
    logger.debug("Annotating resources to BPMN lanes and participants")
    current_organization: str | None = None
    role_map: dict[str, list[str]] = {}
    to_handle_temp_resources: list[NetElement] = [
        elem
        for elem in net._flatten_node_typ_map()
        if isinstance(elem, NetElement) and elem.is_workflow_resource()
    ]
    for resource in to_handle_temp_resources:
        if not resource.toolspecific or not resource.toolspecific.transitionResource:
            raise InternalTransformationException("Not possible.")
        resource_organization = (
            resource.toolspecific.transitionResource.organizationalUnitName
        )
        if (
            current_organization is not None
            and current_organization != resource_organization
        ):
            raise UnknownResourceOrganizationMapping()
        current_organization = resource_organization

        role_name = resource.toolspecific.transitionResource.roleName
        if role_name not in role_map:
            role_map[role_name] = []
        role_map[role_name].append(resource.id)

    # Add a subprocess to a lane if it has as resource transition
    for sb in net.pages:
        sb_role = find_role_type_of_subprocess(sb.net)
        if sb_role is not None:
            if sb_role not in role_map:
                role_map[sb_role] = []
            role_map[sb_role].append(sb.id)

    # Get all already handled nodes
    handled_nodes: set[str] = set([])
    for node_refs in role_map.values():
        handled_nodes.update(node_refs)

    # If no resources were found creation of pool not necessary
    if len(handled_nodes) == 0:
        logger.debug("No resources found, skipping pool/lane creation")
        return

    # Add all elements without a role annotation to a Unkown lane
    all_net_elements = net._flatten_node_typ_map()
    all_net_ids = {node.id for node in all_net_elements}
    unhandled_ids = all_net_ids.difference(handled_nodes).intersection(
        [node.id for node in bpmn.process._flatten_node_typ_map()]
    )
    UNKOWN_LANE = "Unkown participant"
    role_map[UNKOWN_LANE] = list(unhandled_ids)

    bpmn.collaboration = Collaboration(
        id="collaboration",
        participant=Participant(
            id="participant", name=current_organization, processRef=bpmn.process.id
        ),
    )
    lanes: set[Lane] = set()
    for role_name, node_refs in role_map.items():
        if len(node_refs) == 0:
            continue
        lanes.add(Lane(id=role_name, name=role_name, flowNodeRefs=set(node_refs)))
    bpmn.process.lane_sets = set([LaneSet(id="ls", lanes=lanes)])
    logger.debug(
        f"Created {len(lanes)} lanes with organization: {current_organization}"
    )
