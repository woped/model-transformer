"""Module for preprocessing workflow operators.

Workflowoperators will be removed replaced with HelperNodes.
AND-XOR and XOR-AND-Gateways will be splitted to allow the transformation to BPMN.
When gateways have names (implicit action) a explicit transtition will be added.
"""

from app.transform.transformer.models.pnml.base import Name
from app.transform.transformer.models.pnml.pnml import Arc, Net, Transition
from app.transform.transformer.models.pnml.transform_helper import (
    ANDHelperPNML,
    GatewayHelperPNML,
    XORHelperPNML,
)
from app.transform.transformer.models.pnml.workflow import WorkflowBranchingType
from app.transform.transformer.transform_petrinet_to_bpmn.workflow_helper import (
    WorkflowOperatorWrapper,
    find_workflow_operators,
)
from app.transform.transformer.utility.pnml import generate_explicit_transition_id


def handle_combined_operator(net: Net, wo: WorkflowOperatorWrapper):
    """Handle operators consisting of combined opeartors (e.g. AND-AND, XOR-AND)."""
    incoming_arcs = wo.get_copy_unique_in_arcs()
    outgoing_arcs = wo.get_copy_unique_out_arcs()

    # Remove existing elements
    for existing_arc in wo.all_arcs:
        net.remove_arc(existing_arc)
    for existing_node in wo.nodes:
        net.remove_element(existing_node)

    toolspecific = wo.get_toolspecific()
    firstGatewayPart: GatewayHelperPNML | None = None
    secondGatewayPart: GatewayHelperPNML | None = None
    # Split mixed gateways into 2 individual gateways
    if wo.t in [
        WorkflowBranchingType.AndJoinXorSplit,
        WorkflowBranchingType.XorJoinAndSplit,
    ]:
        firstGatewayPart = (
            XORHelperPNML(id="XOR" + wo.id, name=Name(title=wo.name))
            if wo.t == WorkflowBranchingType.XorJoinAndSplit
            else ANDHelperPNML(id="AND" + wo.id, name=Name(title=wo.name))
        )
        secondGatewayPart = (
            ANDHelperPNML(id="AND" + wo.id, name=Name(title=wo.name))
            if wo.t == WorkflowBranchingType.XorJoinAndSplit
            else XORHelperPNML(id="XOR" + wo.id, name=Name(title=wo.name))
        )

        # Handle toolspecific annotations
        secondGatewayPart.set_copy_of_exisiting_toolspecific(toolspecific)
        # Only when tool is resource all gateway parts will also be annotated
        if toolspecific.is_workflow_resource():
            firstGatewayPart.set_copy_of_exisiting_toolspecific(toolspecific)

    # Replace or split same gateway depending if it is an implicit task
    else:
        firstGatewayPart = (
            XORHelperPNML(id=wo.id, name=Name(title=wo.name))
            if wo.t == WorkflowBranchingType.XorJoinSplit
            else ANDHelperPNML(id=wo.id, name=Name(title=wo.name))
        )
        firstGatewayPart.set_copy_of_exisiting_toolspecific(toolspecific)

        #  If gateway with implicit task (name not None) split same gateway
        if wo.name:
            secondGatewayPart = (
                XORHelperPNML(id="OUTXOR" + wo.id, name=Name(title=wo.name))
                if wo.t == WorkflowBranchingType.XorJoinSplit
                else ANDHelperPNML(id="OUTAND" + wo.id, name=Name(title=wo.name))
            )
            secondGatewayPart.set_copy_of_exisiting_toolspecific(toolspecific)
            if toolspecific.is_workflow_event_trigger():
                firstGatewayPart.toolspecific = None

            # Change ID of first gateway because of split
            gw_type = "XOR" if wo.t == WorkflowBranchingType.XorJoinSplit else "AND"
            firstGatewayPart.id = f"IN{gw_type}{wo.id}"

    if not secondGatewayPart:
        secondGatewayPart = firstGatewayPart

    # Add new elements and connect to existing arcs
    net.add_element(firstGatewayPart)
    net.add_element(secondGatewayPart)

    net.connect_to_element(firstGatewayPart, incoming_arcs)
    net.connect_from_element(secondGatewayPart, outgoing_arcs)

    # Operator without name doesnt has an implicit task
    if not wo.name:
        # Add internal arc between split elements
        if firstGatewayPart is not secondGatewayPart:
            net.add_arc_from_id(firstGatewayPart.id, secondGatewayPart.id)
        return

    # Names not necessary for gateways if explicit task with name exists
    firstGatewayPart.name = None
    secondGatewayPart.name = None

    # Add and connect explicit task
    explicit_task = Transition.create(
        id=generate_explicit_transition_id(wo.id),
        name=wo.name,
    )

    # Handle toolspecific annotations
    explicit_task.set_copy_of_exisiting_toolspecific(toolspecific)
    # Eventtrigger already handled by explicit task
    if toolspecific.is_workflow_event_trigger():
        firstGatewayPart.toolspecific = None
        secondGatewayPart.toolspecific = None

    net.add_element(explicit_task)
    net.add_arc(firstGatewayPart, explicit_task)
    net.add_arc(explicit_task, secondGatewayPart)


def handle_single_operator(net: Net, wo: WorkflowOperatorWrapper):
    """Handle operators consisting of a single split or join."""
    incoming_arcs = wo.get_copy_unique_in_arcs()
    outgoing_arcs = wo.get_copy_unique_out_arcs()

    # Remove existing elements
    for existing_arc in wo.all_arcs:
        net.remove_arc(existing_arc)
    for existing_node in wo.nodes:
        net.remove_element(existing_node)

    toolspecific = wo.get_toolspecific()
    # Add new elements and connect to existing arcs
    new_gateway = (
        XORHelperPNML(id=wo.id, name=Name(title=wo.name))
        if wo.t in [WorkflowBranchingType.XorJoin, WorkflowBranchingType.XorSplit]
        else ANDHelperPNML(id=wo.id, name=Name(title=wo.name))
    )
    new_gateway.set_copy_of_exisiting_toolspecific(toolspecific)

    net.add_element(new_gateway)
    net.connect_to_element(new_gateway, incoming_arcs)
    net.connect_from_element(new_gateway, outgoing_arcs)

    # Operator without name doesnt has an implicit task
    if not wo.name:
        return

    # Name not necessary for gateway if explicit task with name exists
    new_gateway.name = None

    # Join needs task after operator
    if wo.t in [WorkflowBranchingType.AndJoin, WorkflowBranchingType.XorJoin]:
        outgoing_arc: Arc | None = None
        outgoing_arcs = list(net.get_outgoing(new_gateway.id))
        if len(outgoing_arcs) > 0:
            outgoing_arc = outgoing_arcs[0]

        explicit_task = Transition.create(
            id=generate_explicit_transition_id(new_gateway.id),
            name=wo.name,
        )

        # Handle toolspecific annotations
        explicit_task.set_copy_of_exisiting_toolspecific(toolspecific)
        # Eventtrigger already handled by explicit task
        if toolspecific.is_workflow_event_trigger():
            new_gateway.toolspecific = None

        net.add_element(explicit_task)
        net.add_arc(new_gateway, explicit_task)

        # Operator could have no following element
        if outgoing_arc:
            net.add_arc_from_id(explicit_task.id, outgoing_arc.target)

            net.remove_arc(outgoing_arc)

    # Split needs task before operator
    else:
        incoming_arc: Arc | None = None
        incoming_arcs = list(net.get_incoming(new_gateway.id))
        if len(incoming_arcs) > 0:
            incoming_arc = incoming_arcs[0]

        explicit_task = Transition.create(
            id=generate_explicit_transition_id(new_gateway.id),
            name=wo.name,
        )

        # Handle toolspecific annotations
        explicit_task.set_copy_of_exisiting_toolspecific(toolspecific)
        # Eventtrigger already handled by explicit task
        if toolspecific.is_workflow_event_trigger():
            new_gateway.toolspecific = None

        net.add_element(explicit_task)
        net.add_arc(explicit_task, new_gateway)

        # Operator could have no previous element
        if incoming_arc:
            net.add_arc_from_id(
                incoming_arc.source,
                explicit_task.id,
            )

            net.remove_arc(incoming_arc)


def handle_workflow_operators(net: Net):
    """Handle workflowoperators by replacing them with temp nodes and extracting task."""
    wf_operators = find_workflow_operators(net)
    for o in wf_operators:
        if o.t in [
            WorkflowBranchingType.AndJoin,
            WorkflowBranchingType.AndSplit,
            WorkflowBranchingType.XorJoin,
            WorkflowBranchingType.XorSplit,
        ]:
            handle_single_operator(net, o)
        elif o.t in [
            WorkflowBranchingType.AndJoinXorSplit,
            WorkflowBranchingType.XorJoinAndSplit,
            WorkflowBranchingType.XorJoinSplit,
            WorkflowBranchingType.AndJoinSplit,
        ]:
            handle_combined_operator(net, o)

