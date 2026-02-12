"""Moduel for shared graphics xml elements."""

from pydantic_xml import attr, element

from app.transform.transformer.utility.utility import BaseModel


class Coordinates(BaseModel):
    """Coordinate extension of BaseModel (+x and y)."""

    x: float = attr(default=20.0)
    y: float = attr(default=20.0)


class PositionGraphics(BaseModel, tag="graphics"):  # type: ignore[call-arg]
    """Placeholder graphics for position."""

    dimension: Coordinates = element("dimension", default=Coordinates())
    position: Coordinates = element("position", default=Coordinates())


class OffsetGraphics(BaseModel, tag="graphics"):  # type: ignore[call-arg]
    """Graphics extension of BaseModel (+offset, dimension, position)."""

    offset: Coordinates = element("offset", default=Coordinates())
