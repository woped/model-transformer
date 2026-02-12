"""BPMNDI based objects."""

from pydantic_xml import attr, element

from app.transform.transformer.models.bpmn.base import ns_map
from app.transform.transformer.utility.utility import BaseBPMNModel


class DCBounds(BaseBPMNModel, tag="Bounds", ns="dc", nsmap=ns_map):  # type: ignore[call-arg]
    """DCBounds extension of BaseBPMNModel with x,y, width and height xml attributes."""

    x: float = attr(default=0)
    y: float = attr(default=0)
    width: float = attr()
    height: float = attr()


class BPMNDINamespace(BaseBPMNModel, ns="bpmndi", nsmap=ns_map):  # type: ignore[call-arg]
    """BPMNDINNamespace extension of BaseBPMNModel."""

    pass


class BPMNLabel(BPMNDINamespace, tag="BPMNLabel"):  # type: ignore[call-arg]
    """BPMNLabel extension of BPMNIDNamespace with DCBounds attribute."""

    bounds: DCBounds | None = element(default=None)


class BPMNDIObject(BPMNDINamespace):
    """BPMNDIObject extension of BPMNDINamespace with element xml attribute."""

    bpmnElement: str = attr()
    label: BPMNLabel | None = element(default=None)


class DIWaypoint(BaseBPMNModel, tag="waypoint", ns="di", nsmap=ns_map):  # type: ignore[call-arg]
    """DIWaypoint extension of BaseBPMNModel with x and y xml attribute."""

    x: float = attr(default=0)
    y: float = attr(default=0)


class BPMNEdge(BPMNDIObject, tag="BPMNEdge"):  # type: ignore[call-arg]
    """BPMNEdge extension of BPMNDIObject with waypoints and label."""

    waypoints: list[DIWaypoint] = element(default_factory=list)


class BPMNShape(BPMNDIObject, tag="BPMNShape"):  # type: ignore[call-arg]
    """BPMNShape extension of BPMNDIObject with bounds, isExpanded and label attr.."""

    bounds: DCBounds
    isExpanded: bool | None = attr(default=None)


class BPMNPlane(BPMNDIObject, tag="BPMNPlane"):  # type: ignore[call-arg]
    """BPMNPlane extension of BPMNDIObject with element list as attribute."""

    eles: list[BPMNShape | BPMNEdge] = element(default_factory=list)


class BPMNDiagram(BPMNDINamespace, tag="BPMNDiagram"):  # type: ignore[call-arg]
    """BPMNDiagram extension of BPMNDINamespace with plane as attribute."""

    plane: BPMNPlane | None = element(default=None)
