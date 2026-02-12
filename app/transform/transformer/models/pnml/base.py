"""BaseModels for BPMN-XML-Mappings."""

from pydantic_xml import attr, element

from app.transform.transformer.models.pnml.graphics import (
    Coordinates,
    OffsetGraphics,
    PositionGraphics,
)
from app.transform.transformer.models.pnml.workflow import (
    Operator,
    TransitionResource,
    Trigger,
    TriggerType,
    WorkflowBranchingType,
)
from app.transform.transformer.utility.utility import WOPED, BaseModel


class Name(BaseModel, tag="name"):
    """Name extension of BaseModel (+graphics, title)."""

    graphics: OffsetGraphics = element(default=OffsetGraphics())
    title: str | None = element(tag="text", default=None)


class Role(BaseModel, tag="role"):
    """Role as part of resources."""

    name: str = attr(name="Name")


class OrganizationUnit(BaseModel, tag="organizationUnit"):
    """Resources hold the global role definitions."""

    name: str = attr(name="Name")


class Resources(BaseModel, tag="resources"):
    """Resources hold the global role definitions."""

    roles: list[Role] = element(default_factory=list)
    units: list[OrganizationUnit] = element(default_factory=list)


class ToolspecificGlobal(BaseModel, tag="toolspecific"):
    """WOPED Toolspecific extension for the global net."""

    tool: str = attr(default=WOPED)
    version: str = attr(default="1.0")

    resources: Resources | None = None
    bounds: PositionGraphics = element(tag="bounds", default=PositionGraphics())
    scale: str = element(tag="scale", default="100")
    treeWidthRight: str = element(tag="treeWidthRight", default="748")
    overviewPanelVisible: str = element(tag="overviewPanelVisible", default="true")
    treeHeightOverview: str = element(tag="treeHeightOverview", default="100")
    treePanelVisible: str = element(tag="treePanelVisible", default="true")
    verticalLayout: str = element(tag="verticalLayout", default="false")
    simulations: str = element(tag="simulations", default=None)
    partnerLinks: str = element(tag="partnerLinks", default=None)
    variables: str = element(tag="variables", default=None)


class Toolspecific(BaseModel, tag="toolspecific"):
    """WOPED Toolspecific extension of BaseModel for a Netelement."""

    tool: str = attr(default=WOPED)
    version: str = attr(default="1.0")

    # normal transition
    time: str | None = element(tag="time", default="0")
    timeUnit: str | None = element(tag="timeUnit", default="1")
    orientation: str | None = element(tag="orientation", default="1")

    # wf-operator
    operator: Operator | None = None

    # traigger type
    trigger: Trigger | None = None

    # transition resource
    transitionResource: TransitionResource | None = None

    # arc
    probability: str | None = element(tag="probability", default=None)
    displayProbabilityOn: str | None = element(tag="displayProbabilityOn", default=None)
    displayProbabilityPosition: Coordinates | None = None

    # subprocess
    subprocess: bool | None = element(tag="subprocess", default=None)

    def is_woped(self):
        """Return whether the toolspecific node is from WOPED."""
        return self.tool == WOPED

    def is_workflow_operator(self):
        """Returns whether instance is a workflow operator."""
        return self.is_woped() and self.operator

    def is_workflow_subprocess(self):
        """Returns whether instance is a workflow subprocess."""
        return self.is_woped() and self.subprocess

    def is_workflow_message(self):
        """Returns whether instance is a workflow message trigger."""
        return (
            self.is_woped()
            and self.trigger
            and self.trigger.type is TriggerType.Message
        )

    def is_workflow_time(self):
        """Returns whether instance is a workflow time trigger."""
        return (
            self.is_woped() and self.trigger and self.trigger.type is TriggerType.Time
        )

    def is_workflow_resource(self):
        """Returns whether instance is a workflow resource trigger."""
        return (
            self.is_woped()
            and self.transitionResource
            and self.trigger
            and self.trigger.type is TriggerType.Resource
        )

    def is_workflow_event_trigger(self):
        """Returns whether instance is a trigger."""
        return self.is_workflow_message() or self.is_workflow_time()


class NetElement(BaseModel):
    """NetElement extension of BaseModel (+name, graphics, toolspecific)."""

    name: Name | None = None
    graphics: PositionGraphics | None = None
    toolspecific: Toolspecific | None = None

    def get_name(self):
        """Returns name of instance."""
        if not self.name:
            return None
        return self.name.title

    def set_name(self, new_name: str):
        """Sets the name from a string."""
        self.name = Name(title=new_name)

    def set_copy_of_exisiting_toolspecific(self, tool: Toolspecific | None):
        """Set a copy of a existing Toolspecific instance."""
        if not tool:
            return self
        self.toolspecific = tool.model_copy()
        return self

    def is_workflow_element(self):
        """Return whether instance is workflow element."""
        return self.toolspecific and self.toolspecific.is_woped()

    def is_workflow_operator(self):
        """Return whether instance is workflow operator."""
        if not self.toolspecific:
            return False
        return self.toolspecific.is_workflow_operator()

    def get_workflow_operator_type(self):
        """If node is a wf operator returns the type."""
        if not self.toolspecific or not self.toolspecific.operator:
            return None
        return self.toolspecific.operator.type

    def is_workflow_resource(self):
        """Return whether instance is workflow resource."""
        if not self.toolspecific:
            return False
        return self.toolspecific.is_workflow_resource()

    def is_workflow_message(self):
        """Return whether instance is workflow message."""
        if not self.toolspecific:
            return False
        return self.toolspecific.is_workflow_message()

    def is_workflow_time(self):
        """Return whether instance is workflow time."""
        if not self.toolspecific:
            return False
        return self.toolspecific.is_workflow_time()

    def is_workflow_event_trigger(self):
        """Return whether instance is workflow event trigger."""
        if not self.toolspecific:
            return False
        return self.toolspecific.is_workflow_event_trigger()

    def is_workflow_trigger(self):
        """Return whether instance is a workflow trigger."""
        return self.is_workflow_event_trigger() or self.is_workflow_resource()

    def is_workflow_subprocess(self):
        """Returns whether instance is workflow subprocess."""
        if not self.toolspecific:
            return False
        return self.toolspecific.is_workflow_subprocess()

    def mark_as_workflow_operator(self, type: WorkflowBranchingType, id: str):
        """Mark this instance as workflow operator."""
        if not self.toolspecific:
            self.toolspecific = Toolspecific()
        self.toolspecific.operator = Operator(id=id, type=type)
        return self

    def mark_as_workflow_subprocess(self):
        """Mark this instance as a subprocess."""
        if not self.toolspecific:
            self.toolspecific = Toolspecific()
        self.toolspecific.subprocess = True
        return self

    def mark_as_workflow_resource(self, role_name: str, orga: str):
        """Mark this instance as a resource."""
        if not self.toolspecific:
            self.toolspecific = Toolspecific()

        self.toolspecific.trigger = Trigger(id="", type=TriggerType.Resource)
        self.toolspecific.transitionResource = TransitionResource(
            roleName=role_name, organizationalUnitName=orga
        )
        return self

    def mark_as_workflow_message(self):
        """Mark this instance as a message."""
        if not self.toolspecific:
            self.toolspecific = Toolspecific()
        self.toolspecific.trigger = Trigger(id="", type=TriggerType.Message)
        return self

    def mark_as_workflow_time(self):
        """Mark this instance as a time."""
        if not self.toolspecific:
            self.toolspecific = Toolspecific()
        self.toolspecific.trigger = Trigger(id="", type=TriggerType.Time)
        return self


class Inscription(BaseModel, tag="inscription"):
    """Inscription extension of BaseModel (+text, graphics)."""

    text: str = element(tag="text")
    graphics: OffsetGraphics
