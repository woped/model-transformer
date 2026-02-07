"""Elements used as placeholder nodes to simplify transformation."""

from app.transform.transformer.models.pnml.base import NetElement


class HelperPNMLElement(NetElement):
    """Superclass for HelperPNMLElements for transformation."""


# Gateway
class GatewayHelperPNML(HelperPNMLElement):
    """Superclass for helper gateways for transformation."""


class XORHelperPNML(GatewayHelperPNML):
    """Expected to be transformed to a BPMN-XOR-Gateway."""


class ANDHelperPNML(GatewayHelperPNML):
    """Expected to be transformed to a BPMN-AND-Gateway."""


# Trigger
class TriggerHelperPNML(HelperPNMLElement):
    """Superclass for helper triggers for transformation."""


class MessageHelperPNML(TriggerHelperPNML):
    """Expected to be transformed to a BPMN-IntermediateCatchEvent(Message)."""


class TimeHelperPNML(TriggerHelperPNML):
    """Expected to be transformed to a BPMN-IntermediateCatchEvent(Time)."""

