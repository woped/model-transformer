"""Split a AND transition with a name (implicit task)."""

from app.transform.exceptions import InternalTransformationException
from app.transform.transformer.models.pnml.pnml import Net, Transition
from app.transform.transformer.utility.pnml import generate_explicit_transition_id


def handle_gateway_creation(and_gateway: Transition):
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


def handle_split(net: Net, and_gateway: Transition):
    """Split into a gateway and explicit task.

    This function also looks at possible Toolspecific annotations.
    """
    incoming_arcs = net.get_incoming_and_remove_arcs(and_gateway)

    explicit_transition = handle_gateway_creation(and_gateway)

    net.add_element(explicit_transition)

    net.add_arc_with_handle_same_type(explicit_transition, and_gateway)

    net.connect_to_element(explicit_transition, incoming_arcs)


def handle_join(net: Net, and_gateway: Transition):
    """Split into a gateway and explicit task.

    This function also looks at possible Toolspecific annotations.
    """
    outgoing_arcs = net.get_outgoing_and_remove_arcs(and_gateway)

    explicit_transition = handle_gateway_creation(and_gateway)

    net.add_element(explicit_transition)

    net.add_arc_with_handle_same_type(and_gateway, explicit_transition)

    net.connect_from_element(explicit_transition, outgoing_arcs)


def handle_join_split(net: Net, and_gateway: Transition):
    """Split into two gateways and explicit task.

    This function also looks at possible Toolspecific annotations.
    """
    outgoing_arcs = net.get_outgoing_and_remove_arcs(and_gateway)

    explicit_transition = handle_gateway_creation(and_gateway)
    and_end_gateway = Transition.create("OUTAND" + and_gateway.id)

    # Also sets the resource for the end gateway
    if explicit_transition.is_workflow_resource():
        and_end_gateway.set_copy_of_exisiting_toolspecific(
            explicit_transition.toolspecific
        )

    net.add_element(explicit_transition)
    net.add_element(and_end_gateway)

    net.add_arc_with_handle_same_type(and_gateway, explicit_transition)
    net.add_arc_with_handle_same_type(explicit_transition, and_end_gateway)

    net.connect_from_element(and_end_gateway, outgoing_arcs)


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
        in_degree = net.get_in_degree(and_gateway)
        out_degree = net.get_out_degree(and_gateway)
        # Split and join
        if in_degree > 1 and out_degree > 1:
            handle_join_split(net, and_gateway)
        # Join
        elif in_degree > 1:
            handle_join(net, and_gateway)
        # Split
        elif out_degree > 1:
            handle_split(net, and_gateway)
        else:
            raise InternalTransformationException("Should not happen.")

        # Remove name because already handled by explicit transition
        and_gateway.name = None
