"""BPMN objects and handling."""

import logging
from pathlib import Path
from typing import cast

from defusedxml.ElementTree import fromstring
from pydantic import PrivateAttr
from pydantic_xml import attr, element

from app.transform.exceptions import (
    InternalTransformationException,
    InvalidInputXML,
    NotSupportedBPMNElement,
    PrivateInternalException,
)
from app.transform.transformer.models.bpmn.base import (
    BPMNNamespace,
    Gateway,
    GenericBPMNNode,
)
from app.transform.transformer.models.bpmn.bpmn_graphics import (
    BPMNDiagram,
    BPMNEdge,
    BPMNLabel,
    BPMNPlane,
    BPMNShape,
    DCBounds,
    DIWaypoint,
)
from app.transform.transformer.utility.utility import create_arc_name, get_tag_name

logger = logging.getLogger(__name__)

supported_elements = {
    "eventbasedGateway",
    "exclusiveGateway",
    "parallelGateway",
    "inclusiveGateway",
    "startEvent",
    "endEvent",
    "messageEventDefinition",
    "timerEventDefinition",
    "intermediateCatchEvent",
    "participant",
    "collaboration",
    "lane",
    "laneSet",
    "task",
    "userTask",
    "serviceTask",
    "sequenceFlow",
    "subProcess",
    "definitions",
    "process",
    "incoming",
    "outgoing",
    "flownoderef",
    # Graphics related
    "bpmnlabel",
    "waypoint",
    "bpmnshape",
    "bounds",
    "bpmnplane",
    "bpmnedge",
    "bpmndiagram",
}

ignored_elements = {
    "dataStoreReference",
    "dataObjectReference",
    "dataObject",
    "category",
    "textAnnotation",
}

supported_tags = {e.lower() for e in {*supported_elements, *ignored_elements}}


# Gateways
class EventGateway(Gateway, tag="eventBasedGateway"):
    """EventbasedGateway extension of gateways."""


class XorGateway(Gateway, tag="exclusiveGateway"):
    """XOR extension of gateways."""


class AndGateway(Gateway, tag="parallelGateway"):
    """AND extension of gateways."""


class OrGateway(Gateway, tag="inclusiveGateway"):
    """OR extension of gateways."""


# Events
class StartEvent(GenericBPMNNode, tag="startEvent"):
    """StartEvent extension of GenericBPMNNode."""


class EndEvent(GenericBPMNNode, tag="endEvent"):
    """EndEvent extension of GenericBPMNNode."""


class MessageEvent(BPMNNamespace, tag="messageEventDefinition"):
    """MessageEvent extension of BPMNNamespace."""


class TimeEvent(BPMNNamespace, tag="timerEventDefinition"):
    """TimeEvent extension of BPMNNamespace."""


class IntermediateCatchEvent(GenericBPMNNode, tag="intermediateCatchEvent"):
    """IntermediateCatchEvent extension of GenericBPMNNode."""

    messageEvent: MessageEvent | None = None
    timeEvent: TimeEvent | None = None

    @staticmethod
    def create_message_event(id: str, name: str | None = None):
        """Create a message event."""
        return IntermediateCatchEvent(id=id, name=name, messageEvent=MessageEvent(id=""))

    @staticmethod
    def create_time_event(id: str, name: str | None = None):
        """Create a time event."""
        return IntermediateCatchEvent(id=id, name=name, timeEvent=TimeEvent(id=""))

    def is_message(self):
        """If the catch event is of type message."""
        return self.messageEvent is not None

    def is_time(self):
        """If the catch event is of type time."""
        return self.timeEvent is not None


# Participant related classes


class Participant(GenericBPMNNode, tag="participant"):
    """Information of global pool."""

    processRef: str = attr()


class Collaboration(GenericBPMNNode, tag="collaboration"):
    """Hold the information of the global pool."""

    participant: Participant | None = None


class Lane(GenericBPMNNode, tag="lane"):
    """Lane extension of GenericBPMNNode."""

    flowNodeRefs: set[str] = element("flowNodeRef", default_factory=set)


class LaneSet(GenericBPMNNode, tag="laneSet"):
    """Lane Set extension of GenericBPMNNode."""

    lanes: set[Lane] = element("lane", default_factory=set)


# Tasks
class GenericTask(GenericBPMNNode):
    """Genric Task for different BPMN tasks."""


class Task(GenericTask, tag="task"):
    """Task extension of GenericBPMNNode."""


class UserTask(GenericTask, tag="userTask"):
    """User Task extension of GenericBPMNNode."""


class ServiceTask(GenericTask, tag="serviceTask"):
    """Service Task extension of GenericBPMNNode."""


# Flow


class Flow(BPMNNamespace, tag="sequenceFlow"):
    """Flow extension of GenericBPMNNode."""

    name: str | None = attr(default=None)
    sourceRef: str = attr()
    targetRef: str = attr()


#


class Process(GenericBPMNNode):
    """Process extension of GenericBPMNNode."""

    isExecutable: bool = attr(default=False)

    lane_sets: set[LaneSet] = element(default_factory=set)

    start_events: set[StartEvent] = element(default_factory=set)
    end_events: set[EndEvent] = element(default_factory=set)
    intermediatecatch_events: set[IntermediateCatchEvent] = element(default_factory=set)

    tasks: set[Task] = element(default_factory=set)
    user_tasks: set[UserTask] = element(default_factory=set)
    service_tasks: set[ServiceTask] = element(default_factory=set)

    xor_gws: set[XorGateway] = element(default_factory=set)
    or_gws: set[OrGateway] = element(default_factory=set)
    and_gws: set[AndGateway] = element(default_factory=set)
    event_gws: set[EventGateway] = element(default_factory=set)

    subprocesses: set["Process"] = element(default_factory=set, tag="subProcess")

    flows: set[Flow] = element(default_factory=set)

    # internal helper structures
    _type_map: dict[type[GenericBPMNNode], set[GenericBPMNNode]] = PrivateAttr(
        default_factory=dict
    )

    _temp_node_id_to_incoming: dict[str, set[Flow]] = PrivateAttr(default_factory=dict)
    _temp_node_id_to_outgoing: dict[str, set[Flow]] = PrivateAttr(default_factory=dict)
    _temp_nodes: dict[str, GenericBPMNNode] = PrivateAttr(default_factory=dict)
    _temp_flows: dict[str, Flow] = PrivateAttr(default_factory=dict)

    # Holds the name of the ID of the usertask and participant (lane name)
    # Also holds the IDs of the usertasks within subprocesses
    _participant_mapping: dict[str, str] = PrivateAttr(default_factory=dict)

    def __init__(self, **data):
        """Process instance constructor."""
        super().__init__(**data)
        self._init_reference_structures()

        if len(self.or_gws) > 0:
            raise NotSupportedBPMNElement("inclusiveGateway")

    def _init_reference_structures(self):
        """Instance initializer."""
        self._type_map = cast(
            dict[type[GenericBPMNNode], set[GenericBPMNNode]],
            {
                Task: self.tasks,
                UserTask: self.user_tasks,
                ServiceTask: self.service_tasks,
                StartEvent: self.start_events,
                EndEvent: self.end_events,
                XorGateway: self.xor_gws,
                OrGateway: self.or_gws,
                AndGateway: self.and_gws,
                EventGateway: self.event_gws,
                Process: self.subprocesses,
                IntermediateCatchEvent: self.intermediatecatch_events,
                GenericBPMNNode: set(),
            },
        )
        self._temp_node_id_to_incoming: dict[str, set[Flow]] = {}
        self._temp_node_id_to_outgoing: dict[str, set[Flow]] = {}
        self._temp_nodes: dict[str, GenericBPMNNode] = {}
        self._temp_flows: dict[str, Flow] = {}

        for node in self._flatten_node_typ_map():
            self._temp_nodes[node.id] = node

        for flow in self.flows:
            self._temp_flows[flow.id] = flow
            self._update_flow_incoming_outgoing(flow)

    def _flatten_node_typ_map(self):
        """Flatten nodes."""
        r: list[GenericBPMNNode] = []
        [r.extend(x) for x in self._type_map.values()]
        return r

    def _update_flow_incoming_outgoing(self, flow: Flow):
        """Update source / target reference of instance."""
        if flow.targetRef not in self._temp_node_id_to_incoming:
            self._temp_node_id_to_incoming[flow.targetRef] = set([flow])
        else:
            self._temp_node_id_to_incoming[flow.targetRef].add(flow)

        if flow.sourceRef not in self._temp_node_id_to_outgoing:
            self._temp_node_id_to_outgoing[flow.sourceRef] = set([flow])
        else:
            self._temp_node_id_to_outgoing[flow.sourceRef].add(flow)

    def _update_actual_incoming_outgoing(self, flow: Flow):
        """Update underlying source / target of instance."""
        self.flows.add(flow)
        source = self._temp_nodes[flow.sourceRef]
        target = self._temp_nodes[flow.targetRef]
        source.outgoing.add(flow.id)
        target.incoming.add(flow.id)

    def get_incoming(self, id: str):
        """Return the incoming flows of a element by id."""
        return self._temp_node_id_to_incoming[id]

    def get_outgoing(self, id: str):
        """Return the outgoing flows of a element by id."""
        return self._temp_node_id_to_outgoing[id]

    def get_node(self, id: str):
        """Return a node by id."""
        return self._temp_nodes[id]

    def is_node_existing(self, id: str):
        """Returns whether node with a id is existing in process."""
        return id in self._temp_nodes

    def change_node_id(self, node: GenericBPMNNode, new_id: str):
        """Change node id and update connected flows."""
        incoming_flows = self._temp_node_id_to_incoming.get(node.id, [])
        incoming_flows_id_map = [
            (f.id, f.sourceRef, new_id, f.name) for f in incoming_flows
        ]

        outgoing_flows = self._temp_node_id_to_outgoing.get(node.id, [])
        outgoing_flows_id_map = [
            (f.id, new_id, f.targetRef, f.name) for f in outgoing_flows
        ]

        for f in [*incoming_flows, *outgoing_flows]:
            self.remove_flow(f)
        self.remove_node(node)

        new_node = node.model_copy(deep=True)
        new_node.id = new_id

        self.add_node(new_node)
        for id, source_id, target_id, name in [
            *outgoing_flows_id_map,
            *incoming_flows_id_map,
        ]:
            self.add_flow(
                source=self._temp_nodes[source_id],
                target=self._temp_nodes[target_id],
                id=id,
                name=name,
            )

    def add_flow(
        self,
        source: GenericBPMNNode,
        target: GenericBPMNNode,
        id: str | None = None,
        name: str | None = None,
    ):
        """Add flow to instance by source and target."""
        if id is None:
            id = create_arc_name(source.id, target.id)

        if id in self._temp_flows:
            raise InternalTransformationException(
                f"flow with the id {id} already exists!"
            )

        self.add_node(source)
        self.add_node(target)

        a = Flow(id=id, sourceRef=source.id, targetRef=target.id, name=name)
        self._temp_flows[id] = a
        self._update_flow_incoming_outgoing(a)
        self._update_actual_incoming_outgoing(a)
        return a

    def add_constructed_flow(self, flow: Flow):
        """Add a finished flow to instance."""
        self.add_flow(
            self._temp_nodes[flow.sourceRef],
            self._temp_nodes[flow.targetRef],
            flow.id,
            flow.name,
        )

    def _remove_actual_flow(self, flow: Flow):
        """Remove underlying flow of instance."""
        self.flows.remove(flow)

        source = self._temp_nodes[flow.sourceRef]
        target = self._temp_nodes[flow.targetRef]
        source.outgoing.remove(flow.id)
        target.incoming.remove(flow.id)

    def remove_flow(self, flow: Flow):
        """Remove flow reference of instance."""
        self._temp_flows.pop(flow.id)
        self._temp_node_id_to_incoming[flow.targetRef].remove(flow)
        self._temp_node_id_to_outgoing[flow.sourceRef].remove(flow)

        self._remove_actual_flow(flow)

    def add_nodes(self, *args: GenericBPMNNode):
        """Add multiple nodes to the BPMN."""
        for node in args:
            self.add_node(node)

    def add_node(self, new_node: GenericBPMNNode):
        """Add single node to the BPMN."""
        storage_set = self._type_map[type(new_node)]
        if storage_set is None:
            raise InternalTransformationException("No BPMN node")
        if new_node in storage_set:
            # skip already added node
            return new_node

        storage_set.add(new_node)

        self._temp_nodes[new_node.id] = new_node

        return new_node

    def remove_node(self, to_remove_node: GenericBPMNNode):
        """Remove single node frome the BPMN."""
        storage_set = self._type_map[type(to_remove_node)]
        if storage_set is None:
            raise InternalTransformationException("No BPMN node")

        if to_remove_node not in storage_set:
            raise InternalTransformationException("Node doesnt exist")

        storage_set.remove(to_remove_node)

        self._temp_nodes.pop(to_remove_node.id)

        if to_remove_node.id in self._temp_node_id_to_incoming:
            incoming = self._temp_node_id_to_incoming.pop(to_remove_node.id)
            for arc in incoming:
                arc.targetRef = ""
        if to_remove_node.id in self._temp_node_id_to_outgoing:
            outgoing = self._temp_node_id_to_outgoing.pop(to_remove_node.id)
            for arc in outgoing:
                arc.sourceRef = ""

    def get_flow_target_by_id(self, flow_id: str):
        """Return target nodes from flow id."""
        return self._temp_nodes[self._temp_flows[flow_id].targetRef]

    def get_flow_source_by_id(self, flow_id: str):
        """Return source nodes from flow id."""
        return self._temp_nodes[self._temp_flows[flow_id].sourceRef]

    def get_flow(self, id: str):
        """Return flow by id."""
        return self._temp_flows[id]

    def remove_node_with_connecting_flows(self, node: GenericBPMNNode):
        """Remove node and its connected flows."""
        if node.get_in_degree() > 0:
            incoming_arc = list(self._temp_node_id_to_incoming[node.id])[0]
            source_id = incoming_arc.sourceRef
            self.remove_flow(incoming_arc)
        if node.get_out_degree() > 0:
            outgoing_arc = list(self._temp_node_id_to_outgoing[node.id])[0]
            target_id = outgoing_arc.targetRef
            self.remove_flow(outgoing_arc)
        self.remove_node(node)
        return source_id, target_id


class BPMN(BPMNNamespace, tag="definitions"):
    """Extension of BPMNNamespace with attributes process and diagram."""

    collaboration: Collaboration | None = None
    process: Process = element(tag="process")
    diagram: BPMNDiagram | None = element(default=None)

    @staticmethod
    def from_xml(xml_content: str):
        """Return a BPMN from a XML string."""
        logger.debug("Parsing BPMN from XML string")
        try:
            tree = fromstring(xml_content)
            used_tags: set[str] = set()
            amount_of_participants = 0
            for elem in tree.iter():
                if get_tag_name(elem) == "participant":
                    amount_of_participants += 1
                used_tags.add(get_tag_name(elem))
            unhandled_tags = used_tags.difference(supported_tags)
            logger.debug(f"Found {len(used_tags)} unique BPMN tags, {amount_of_participants} participants")
            if amount_of_participants > 1:
                raise NotSupportedBPMNElement(
                    "participant is only supported when there is exactly one pool in the BPMN model. Your BPMN is not compliant with this restriction."
                )
            if len(unhandled_tags) > 0:
                logger.warning(f"BPMN contains unsupported tags: {unhandled_tags}")
                raise NotSupportedBPMNElement(str(unhandled_tags))
            bpmn = BPMN.from_xml_tree(tree)
            logger.debug(f"Successfully parsed BPMN with process ID: {bpmn.process.id if bpmn.process else 'N/A'}")
            return bpmn
        except NotSupportedBPMNElement as e:
            logger.error(f"BPMN contains unsupported elements: {e}")
            raise e
        except Exception as e:
            logger.error(f"Failed to parse BPMN XML: {e}", exc_info=True)
            raise InvalidInputXML()

    @staticmethod
    def from_file(path: str):
        """Return a BPMN from a file path."""
        logger.debug(f"Loading BPMN from file: {path}")
        content = Path(path).read_text()
        return BPMN.from_xml(content)

    @staticmethod
    def generate_empty_bpmn(id="new_bpmn"):
        """Return an empty bpmn with a process."""
        return BPMN(process=Process(id=id, isExecutable=True))

    def to_string(self) -> str:
        """Transform this instance into a string and creates placeholder graphics."""
        try:
            self.set_graphics()
            return cast(str, self.to_xml(encoding="unicode"))
        except Exception:
            raise PrivateInternalException("Can't convert bpmn to string.")

    def write_to_file(self, path: str):
        """Save this instance xml encoded to a file."""
        content = self.to_string()
        Path(path).write_text(content)

    def set_graphics(self):
        """Define graphical representation of this instance."""
        d = BPMNDiagram(id="diagram1")
        bpmn = self.process
        plane_id = bpmn.id
        if self.collaboration:
            plane_id = self.collaboration.id
        p = BPMNPlane(id=f"plane{bpmn.id}", bpmnElement=plane_id)

        if self.collaboration and self.collaboration.participant:
            p.eles.append(
                BPMNShape(
                    id="Participant_id",
                    bpmnElement=self.collaboration.participant.id,
                    bounds=DCBounds(width=600, height=500),
                )
            )
        if bpmn.lane_sets:
            for lane_set in bpmn.lane_sets:
                for lane in lane_set.lanes:
                    lane.id = lane.id.replace(" ", "")
                    p.eles.append(
                        BPMNShape(
                            id=f"{lane.id}_di",
                            bpmnElement=lane.id,
                            bounds=DCBounds(width=600, height=200),
                        )
                    )

        for flow in bpmn.flows:
            p.eles.append(
                BPMNEdge(
                    id=f"{flow.id}_di",
                    bpmnElement=flow.id,
                    waypoints=[DIWaypoint(), DIWaypoint()],
                )
            )

        for node in bpmn._flatten_node_typ_map():
            s = BPMNShape(
                id=f"{node.id}_di",
                bpmnElement=node.id,
                bounds=DCBounds(width=100, height=80),
            )
            if isinstance(node, Process):
                s.isExpanded = True
            if node.name and not isinstance(node, Process | Task):
                s.label = BPMNLabel(bounds=DCBounds(width=50, height=20))
            p.eles.append(s)

        d.plane = p
        self.diagram = d

