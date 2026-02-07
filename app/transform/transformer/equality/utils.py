"""Concatenates strings and groups elements by type."""
from typing import Any
from collections.abc import Callable


def create_type_dict(elements: list, f: Callable[[Any], str]):
    """Returns a dictionary which groups elements by their type."""
    d: dict[Any, set[str]] = {}
    for element in elements:
        element_set = d.get(type(element), set())
        element_set.add(f(element))
        d[type(element)] = element_set
    return d


def to_comp_string(*args):
    """Returns concatenation of parameters."""
    return "_".join([str(x) for x in args if x is not None])
