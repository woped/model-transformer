"""Extensions for unsupported nodes."""

from app.transform.transformer.models.bpmn.base import NotSupportedNode


class TextAnnotation(NotSupportedNode, tag="textAnnotation"):
    """TextAnnotation extension of unsupported node."""


class ThrowEvent(NotSupportedNode, tag="intermediateThrowEvent"):
    """ThrowEvent extension of unsupported node."""


class CatchEvent(NotSupportedNode, tag="intermediateCatchEvent"):
    """CatchEvent extension of unsupported node."""

