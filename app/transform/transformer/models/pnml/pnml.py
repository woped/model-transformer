"""PNML models."""

import logging
from pathlib import Path
from typing import cast

from defusedxml.ElementTree import fromstring
from pydantic import PrivateAttr
from pydantic_xml import attr, element

from app.transform.exceptions import (
    InternalTransformationException,
    InvalidInputXML,
    PrivateInternalException,
)
from app.transform.transformer.models.pnml.base import (
    Inscription,
    Name,
    NetElement,
    Toolspecific,
    ToolspecificGlobal,
)
from app.transform.transformer.models.pnml.graphics import OffsetGraphics
from app.transform.transformer.models.pnml.transform_helper import (
    ANDHelperPNML,
    HelperPNMLElement,
    MessageHelperPNML,
    TimeHelperPNML,
    XORHelperPNML,
)
from app.transform.transformer.utility.utility import (
    BaseModel,
    create_arc_name,
    create_silent_node_name,
)

logger = logging.getLogger(__name__)


class Transition(NetElement, tag="transition"):
    """Transition extension of NetElement."""

    @staticmethod
    def create(id: str, name: str | None = None):
        """Returns an instance of a transition."""
        return Transition(id=id, name=Name(title=name) if name is not None else None)


class Place(NetElement, tag="place"):
    """Place extension of NetElement."""

    @staticmethod
    def create(id: str, name: str | None = None):
        """Returns instance of a place."""
        return Place(id=id, name=Name(title=name) if name is not None else None)


class Arc(BaseModel, tag="arc"):
    """Arc extension of BaseModel (+ID,source,target,inscription...)."""

    source: str = attr()
    target: str = attr()
    inscription: Inscription | None = element(default=None)
    graphics: OffsetGraphics | None = element(default=None)
    toolspecific: Toolspecific | None = element(default=None)

    def __hash__(self):
        """Retuns a hashed of the arc instance."""
        return hash((type(self),) + (self.id,) + (self.source,) + (self.target,))


class Page(BaseModel, tag="page"):
    """Page extension of BaseModel (+Net)."""

    net: "Net"


class Net(BaseModel, tag="net"):
    """Net extension of BaseModel (+ID, type_field, places, transitions, arcs...).

    This class also contains internal helperstructures to improve the performance of
    operations. It also contains helper methods to modify the Net.
    """

    toolspecific_global: ToolspecificGlobal | None = None

    type_field: str | None = attr(default=None, alias="type")

    places: set[Place] = element(default_factory=set)
    transitions: set[Transition] = element(default_factory=set)
    arcs: set[Arc] = element(default_factory=set)

    pages: set[Page] = element(default_factory=set)

    # internal helper structures
    _temp_elements: dict[str, NetElement] = PrivateAttr(default_factory=dict)
    _type_map: dict[type[BaseModel], set[BaseModel]] = PrivateAttr(default_factory=dict)
    _temp_arcs: dict[int, Arc] = PrivateAttr(default_factory=dict)
    _temp_node_id_to_incoming: dict[str, set[Arc]] = PrivateAttr(default_factory=dict)
    _temp_node_id_to_outgoing: dict[str, set[Arc]] = PrivateAttr(default_factory=dict)

    def get_incoming(self, id: str):
        """Return the incoming arcs of a node by id."""
        if id not in self._temp_node_id_to_incoming:
            return {}
        return self._temp_node_id_to_incoming[id]

    def get_outgoing(self, id: str):
        """Return the outgoing arcs of a node by id."""
        if id not in self._temp_node_id_to_outgoing:
            return {}
        return self._temp_node_id_to_outgoing[id]

    def __init__(self, **data):
        """Net constructor."""
        super().__init__(**data)
        self._init_reference_structures()

    def _init_reference_structures(self):
        """Populate the helper structures."""
        self._type_map = cast(
            dict[type[BaseModel], set[BaseModel]],
            {
                Place: self.places,
                Transition: self.transitions,
                Page: self.pages,
                # Temporary helper elements (not actual petri net element)
                XORHelperPNML: set([]),
                ANDHelperPNML: set([]),
                TimeHelperPNML: set([]),
                MessageHelperPNML: set([]),
            },
        )
        for place in self.places:
            self._temp_elements[place.id] = place

        for transition in self.transitions:
            self._temp_elements[transition.id] = transition

        for arc in self.arcs:
            self._temp_arcs[hash(arc)] = arc
            self._update_arc_incoming_outgoing(arc)

    def _flatten_node_typ_map(self):
        """Return all nodes as a single list."""
        all_nodes: list[BaseModel] = []
        for type_sets in self._type_map.values():
            all_nodes.extend(type_sets)
        return all_nodes

    def _update_arc_incoming_outgoing(self, arc: Arc):
        """Updates helper node to arc mapping with the constructed arc."""
        if arc.target not in self._temp_node_id_to_incoming:
            self._temp_node_id_to_incoming[arc.target] = set([arc])
        else:
            self._temp_node_id_to_incoming[arc.target].add(arc)

        if arc.source not in self._temp_node_id_to_outgoing:
            self._temp_node_id_to_outgoing[arc.source] = set([arc])
        else:
            self._temp_node_id_to_outgoing[arc.source].add(arc)

    def get_in_degree(self, node: BaseModel):
        """Return degree of incoming arcs."""
        if node.id not in self._temp_node_id_to_incoming:
            return 0
        return len(self._temp_node_id_to_incoming[node.id])

    def get_out_degree(self, node: BaseModel):
        """Return degree of outgoing arcs."""
        if node.id not in self._temp_node_id_to_outgoing:
            return 0
        return len(self._temp_node_id_to_outgoing[node.id])

    def add_arc_with_handle_same_type_from_id(self, source_id: str, target_id: str):
        """Add arc connecting source and target id."""
        source = self._temp_elements[source_id]
        target = self._temp_elements[target_id]
        self.add_arc_with_handle_same_type(source, target)

    def add_arc_with_handle_same_type(self, source: NetElement, target: NetElement):
        """Add arc and add node should source and target be of same type."""
        if isinstance(source, Place) and isinstance(target, Place):
            t = self.add_element(
                Transition(id=create_silent_node_name(source.id, target.id))
            )
            self.add_arc(source, t)
            self.add_arc(t, target)
        elif isinstance(source, Transition) and isinstance(target, Transition):
            p = self.add_element(Place(id=create_silent_node_name(source.id, target.id)))
            self.add_arc(source, p)
            self.add_arc(p, target)
        else:
            self.add_arc(source, target)

    def add_arc_from_id(self, source_id: str, target_id: str, id: str | None = None):
        """Add arc connecting source and target id."""
        source = self._temp_elements[source_id]
        target = self._temp_elements[target_id]
        self.add_arc(source, target, id)

    def add_arc(self, source: NetElement, target: NetElement, id: str | None = None):
        """Add arc based on source and target instance."""
        if id is None:
            id = create_arc_name(source.id, target.id)
        if (
            not isinstance(source, HelperPNMLElement)
            and not isinstance(target, HelperPNMLElement)
            and type(source) is type(target)
        ):
            raise InternalTransformationException(
                "Cant connect identical petrinet elements"
            )
        if id in self._temp_arcs:
            raise InternalTransformationException(
                f"arc {id} already exists from {source.id} to {target.id}!"
            )

        self.add_element(source)
        self.add_element(target)

        a = Arc(id=id, source=source.id, target=target.id)
        self._temp_arcs[hash(a)] = a
        self._update_arc_incoming_outgoing(a)

        self.arcs.add(a)

    def remove_arc(self, arc: Arc):
        """Remove arc based on instance."""
        self._temp_arcs.pop(hash(arc))
        if arc.target:
            self._temp_node_id_to_incoming[arc.target].remove(arc)
        if arc.source:
            self._temp_node_id_to_outgoing[arc.source].remove(arc)

        self.arcs.remove(arc)

    def add_page(self, new_page: Page):
        """Add a new page or add if not existing (check by id)."""
        storage_set = self.pages
        for p in self.pages:
            if p.id == new_page.id:
                return p

        storage_set.add(new_page)
        return new_page

    def add_element(self, new_node: NetElement):
        """Add a node to net or return if already exising (check by id)."""
        storage_set = self._type_map[type(new_node)]
        if storage_set is None:
            raise InternalTransformationException("No Petrinet node")

        if new_node.id in self._temp_elements:
            return new_node

        storage_set.add(new_node)

        self._temp_elements[new_node.id] = new_node
        return new_node

    def get_element(self, id: str):
        """Return element by id."""
        if id not in self._temp_elements:
            raise InternalTransformationException(
                f"Cant get nonexisting Node with id {id}"
            )
        return self._temp_elements[id]

    def get_page(self, id: str):
        """Return page by id."""
        pages = {p.id: p for p in self.pages}
        if id not in pages:
            raise InternalTransformationException("Cant find page")
        return pages[id]

    def get_node_or_none(self, id: str):
        """Return node by id or None as default."""
        if id not in self._temp_elements:
            return None
        return self._temp_elements[id]

    def remove_element(self, to_remove_node: BaseModel):
        """Remove element by instance."""
        storage_set = self._type_map[type(to_remove_node)]
        if storage_set is None:
            raise InternalTransformationException("No Petrinet node")

        storage_set.remove(to_remove_node)

        self._temp_elements.pop(to_remove_node.id)
        incoming = self._temp_node_id_to_incoming.pop(to_remove_node.id, set())
        outgoing = self._temp_node_id_to_outgoing.pop(to_remove_node.id, set())
        for arc in incoming:
            arc.target = ""
        for arc in outgoing:
            arc.source = ""

    def change_id(self, old_id: str, new_id: str):
        """Change the ID of a existing node and the connecting arcs."""
        if old_id not in self._temp_elements:
            raise InternalTransformationException("old element not exisiting")
        if new_id in self._temp_elements:
            raise InternalTransformationException("new id already exists")
        current_node = self._temp_elements[old_id]
        incoming, outgoing = self.get_incoming_outgoing_and_remove_arcs(current_node)
        self.remove_element(current_node)
        current_node.id = new_id
        self.add_element(current_node)
        self.connect_to_element(current_node, incoming)
        self.connect_from_element(current_node, outgoing)

    def remove_element_with_connecting_arcs(self, to_remove_node: BaseModel):
        """Remove element by instance and connecting arcs."""
        for arc in [
            *self.get_incoming(to_remove_node.id),
            *self.get_outgoing(to_remove_node.id),
        ]:
            self.remove_arc(arc)

        self.remove_element(to_remove_node)

    def get_incoming_and_remove_arcs(self, transition: NetElement):
        """Get a copy of each incoming arc and remove original arcs."""
        incoming_arcs = [arc.model_copy() for arc in self.get_incoming(transition.id)]
        for to_remove_arc in incoming_arcs:
            self.remove_arc(to_remove_arc)
        return incoming_arcs

    def get_outgoing_and_remove_arcs(self, transition: NetElement):
        """Get a copy of each outgoing arc and remove original arcs."""
        outgoing_arcs = [arc.model_copy() for arc in self.get_outgoing(transition.id)]
        for to_remove_arc in outgoing_arcs:
            self.remove_arc(to_remove_arc)
        return outgoing_arcs

    def get_incoming_outgoing_and_remove_arcs(self, transition: NetElement):
        """Get a copy of all connecting arc and remove original arcs."""
        return self.get_incoming_and_remove_arcs(
            transition
        ), self.get_outgoing_and_remove_arcs(transition)

    def connect_to_element(self, element: NetElement, incoming_arcs: list[Arc]):
        """Connect each source of the arcs to a specified element."""
        for arc in incoming_arcs:
            self.add_arc_from_id(arc.source, element.id)

    def connect_from_element(self, element: NetElement, outgoing_arcs: list[Arc]):
        """Connect each target of the arcs from a specified element."""
        for arc in outgoing_arcs:
            self.add_arc_from_id(element.id, arc.target)


# Page is using Net reference before Net is initalized
Page.model_rebuild()


class Pnml(BaseModel, tag="pnml"):
    """Petri net extension of base model."""

    net: Net

    def to_string(self) -> str:
        """Return string of net instance as serialized XML."""
        logger.debug("Serializing PNML to XML string")
        try:
            xml_str = cast(str, self.to_xml(encoding="unicode"))
            logger.debug(f"Successfully serialized PNML to XML ({len(xml_str)} characters)")
            return xml_str
        except Exception as e:
            logger.error(f"Failed to serialize PNML: {e}", exc_info=True)
            raise PrivateInternalException("Can't convert pnml to string.")

    def write_to_file(self, path: str):
        """Save net to file."""
        Path(path).write_text(self.to_string())

    @staticmethod
    def from_xml_str(xml_content: str):
        """Return a petri net from a XML string."""
        logger.debug("Parsing PNML from XML string")
        try:
            tree = fromstring(xml_content)
            net = Pnml.from_xml_tree(tree)
            logger.debug(f"Successfully parsed PNML with net ID: {net.net.id if net.net else 'N/A'}")
            return net
        except Exception as e:
            logger.error(f"Failed to parse PNML XML: {e}", exc_info=True)
            raise InvalidInputXML()

    @staticmethod
    def from_file(path: str):
        """Return a petri net from a file."""
        logger.debug(f"Loading PNML from file: {path}")
        return Pnml.from_xml_str(Path(path).read_text())

    @staticmethod
    def generate_empty_net(id="new_net"):
        """Return empty petri net."""
        return Pnml(net=Net(id=id))

