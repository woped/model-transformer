"""Shared skeleton for splitting a high-degree node into an explicit element + gateway(s).

Both the implicit-gateway (vanilla_gateway_transition) and the event-trigger
(event_trigger) preprocessing turn a transition/trigger whose in- or out-degree
is >1 into an explicit helper element plus the surrounding gateway wiring. Only
the factory that builds the explicit element (and a couple of hooks) differ.
"""

from collections.abc import Callable

from app.transform.exceptions import InternalTransformationException
from app.transform.transformer.models.pnml.base import NetElement
from app.transform.transformer.models.pnml.pnml import Net, Transition

CreateExplicit = Callable[[NetElement], NetElement]


def _handle_split(net: Net, node: NetElement, create_explicit: CreateExplicit):
    incoming_arcs = net.get_incoming_and_remove_arcs(node)
    explicit = create_explicit(node)
    net.add_element(explicit)
    net.add_arc_with_handle_same_type(explicit, node)
    net.connect_to_element(explicit, incoming_arcs)


def _handle_join(net: Net, node: NetElement, create_explicit: CreateExplicit):
    outgoing_arcs = net.get_outgoing_and_remove_arcs(node)
    explicit = create_explicit(node)
    net.add_element(explicit)
    net.add_arc_with_handle_same_type(node, explicit)
    net.connect_from_element(explicit, outgoing_arcs)


def _handle_join_split(
    net: Net,
    node: NetElement,
    create_explicit: CreateExplicit,
    after_create: Callable[[NetElement, Transition], None] | None,
):
    outgoing_arcs = net.get_outgoing_and_remove_arcs(node)
    explicit = create_explicit(node)
    end_gateway = Transition.create("OUTAND" + node.id)
    if after_create is not None:
        after_create(explicit, end_gateway)
    net.add_element(explicit)
    net.add_element(end_gateway)
    net.add_arc_with_handle_same_type(node, explicit)
    net.add_arc_with_handle_same_type(explicit, end_gateway)
    net.connect_from_element(end_gateway, outgoing_arcs)


def split_by_degree(
    net: Net,
    node: NetElement,
    create_explicit: CreateExplicit,
    *,
    after_create: Callable[[NetElement, Transition], None] | None = None,
    split_on_sequence: bool = False,
):
    """Dispatch a node to split/join/join-split handling based on its degree.

    create_explicit builds the explicit helper element for the node.
    after_create, if given, runs on (explicit, end_gateway) in the join-split case.
    split_on_sequence also treats a plain 1->1 node as a split.
    """
    in_degree = net.get_in_degree(node)
    out_degree = net.get_out_degree(node)
    # Split and join
    if in_degree > 1 and out_degree > 1:
        _handle_join_split(net, node, create_explicit, after_create)
    # Join
    elif in_degree > 1:
        _handle_join(net, node, create_explicit)
    # Split (or, for triggers, a plain sequence)
    elif out_degree > 1 or (split_on_sequence and in_degree == 1 and out_degree == 1):
        _handle_split(net, node, create_explicit)
    else:
        raise InternalTransformationException("Should not happen.")
