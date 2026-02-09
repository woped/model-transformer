"""Utility functions.

Ust to generate test Petri nets from lists of net elements in PNML format.
"""


from app.transform.transformer.models.pnml.base import NetElement
from app.transform.transformer.models.pnml.pnml import Pnml


def create_petri_net(test_case_name: str, flows: list[list[NetElement]]):
    """Returns a test case petri net out of a list of net elements."""
    net_helper = Pnml.generate_empty_net(test_case_name)
    for flow in flows:
        for element in flow:
            net_helper.net.add_element(element)
        for i in range(len(flow) - 1):
            current_node = flow[i]
            next_node = flow[i + 1]
            net_helper.net.add_arc(current_node, next_node)
    return net_helper

