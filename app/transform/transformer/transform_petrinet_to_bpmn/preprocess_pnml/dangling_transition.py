"""Preprocess dangling transitions.

A dangling transitions has a input degree and/or output degree of 0.
"""

from app.transform.transformer.models.pnml.pnml import Net, Place, Transition
from app.transform.transformer.utility.pnml import generate_sink_id, generate_source_id


def handle_dangling_sources(net: Net, sources: list[Transition]):
    """Prepends a place to each source."""
    for source in sources:
        new_source = net.add_element(Place.create(generate_source_id(source.id)))
        net.add_arc(new_source, source)


def handle_dangling_sinks(net: Net, sinks: list[Transition]):
    """Appends a place to each sink."""
    for sink in sinks:
        new_sink = net.add_element(Place.create(generate_sink_id(sink.id)))
        net.add_arc(sink, new_sink)


def add_places_at_dangling_transitions(net: Net):
    """Handle dangling transitions by adding places."""
    sources: list[Transition] = []
    sinks: list[Transition] = []
    for transition in net.transitions:
        if net.get_in_degree(transition) == 0:
            sources.append(transition)
        if net.get_out_degree(transition) == 0:
            sinks.append(transition)

    handle_dangling_sources(net, sources)

    handle_dangling_sinks(net, sinks)

