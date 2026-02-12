"""BPMN objects and extensions."""

from pydantic_xml import attr, element

from app.transform.transformer.utility.utility import BaseBPMNModel

ns_map = {
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
}


class BPMNNamespace(BaseBPMNModel, ns="bpmn", nsmap=ns_map):  # type: ignore[call-arg]
    """Extension of BaseBPMNModel with namespace bpmn and namespace map."""


class GenericBPMNNode(BPMNNamespace):
    """BPMN extension of BPMNNamespace with name, incoming and outgoing attribute."""

    name: str | None = attr(default=None)
    incoming: set[str] = element("incoming", default_factory=set)
    outgoing: set[str] = element("outgoing", default_factory=set)

    def get_in_degree(self):
        """Returns incoming degree of this instance."""
        return len(self.incoming)

    def get_out_degree(self):
        """Returns outgoing degree of this instance."""
        return len(self.outgoing)


class Gateway(GenericBPMNNode):
    """Gateway extension of BPMN node."""
