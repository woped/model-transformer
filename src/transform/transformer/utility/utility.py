"""General transformer utility (get name, create basic elements/nodes)."""

from xml.etree.ElementTree import Element

from pydantic_xml import BaseXmlModel
from pydantic_xml import attr, element

WOPED = "WoPeD"


def get_tag_name(element: Element):
    """Return the name of an element."""
    return element.tag.rpartition("}")[2].lower()


def create_silent_node_name(source: str, target: str):
    """Construct a silent node (name) from source to target."""
    return f"SILENTFROM{source}TO{target}"


def create_arc_name(source: str | None, target: str | None):
    """Construct an arc (name) from source to target."""
    if source is None or target is None:
        raise Exception("source and target must have a value")
    return f"{source}TO{target}"


def clean_xml_string(xml_string: str):
    """Remove whitespaces and newline characters from string and add XML header."""
    xml_string = xml_string.replace('\n', '').replace('\\"', '"')
    if not xml_string.startswith('<?xml'):
        xml_string = '<?xml version="1.0" encoding="UTF-8"?>' + xml_string
    return xml_string


class BaseModel(
    BaseXmlModel,
    search_mode="unordered",
    skip_empty=True,
):
    """BaseModel extension of BaseXmlModel."""
    id: str | None = attr(default=None)
    name: str | None = attr(default=None)

    def __hash__(self):
        """Return hash of this instance."""
        return hash((type(self),) + (self.id,))


class BaseBPMNModel(
    BaseXmlModel,
    search_mode="unordered",
    skip_empty=True,
    nsmap={"": "http://www.omg.org/spec/BPMN/20100524/MODEL"},
):
    """BaseBPMNModel extension of BaseXmlModel."""
