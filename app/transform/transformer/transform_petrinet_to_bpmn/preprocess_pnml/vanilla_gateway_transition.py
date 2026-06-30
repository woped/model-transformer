"""Split an AND transition with a name (implicit task) into gateways + explicit task."""

from app.transform.transformer.models.pnml.base import NetElement
from app.transform.transformer.models.pnml.pnml import Net, Transition
from app.transform.transformer.transform_petrinet_to_bpmn.preprocess_pnml.split_dispatch import (
    split_by_degree,
)
from app.transform.transformer.utility.pnml import generate_explicit_transition_id


def handle_gateway_creation(and_gateway: NetElement):
    """Handle the creation of the explicit task of the gateway.

    This function also looks at possible Toolspecific annotations.
    """
    explicit_transition = Transition.create(
        generate_explicit_transition_id(and_gateway.id), and_gateway.get_name()
    ).set_copy_of_exisiting_toolspecific(and_gateway.toolspecific)

    # Should the gateway be a message/time remove the toolspecific data
    # If it has as ressource trigger keep it to also add it to the BPMN Lanes
    if and_gateway.is_workflow_event_trigger():
        and_gateway.toolspecific = None

    return explicit_transition


def _copy_resource_to_end_gateway(explicit: NetElement, end_gateway: Transition):
    """In a join-split, carry the resource annotation onto the end gateway too."""
    if explicit.is_workflow_resource():
        end_gateway.set_copy_of_exisiting_toolspecific(explicit.toolspecific)


def split_and_gw_with_name(net: Net):
    """Split a AND transition with a name into the gateways and explicit task.

    This function also looks at possible Toolspecific annotations.
    """
    and_gateways: list[Transition] = [
        t
        for t in net.transitions
        if (net.get_in_degree(t) > 1 or net.get_out_degree(t) > 1) and t.get_name()
    ]
    for and_gateway in and_gateways:
        split_by_degree(
            net,
            and_gateway,
            handle_gateway_creation,
            after_create=_copy_resource_to_end_gateway,
        )
        # Remove name because already handled by explicit transition
        and_gateway.name = None
