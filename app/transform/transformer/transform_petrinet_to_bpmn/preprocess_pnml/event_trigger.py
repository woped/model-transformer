"""Module to preprocess workflow event triggers.

A event trigger is a message or time.
A resource will be handled by another preprocessing function.
"""

from app.transform.exceptions import InternalTransformationException
from app.transform.transformer.models.pnml.base import NetElement
from app.transform.transformer.models.pnml.pnml import Net
from app.transform.transformer.models.pnml.transform_helper import (
    MessageHelperPNML,
    TimeHelperPNML,
)
from app.transform.transformer.transform_petrinet_to_bpmn.preprocess_pnml.split_dispatch import (
    split_by_degree,
)
from app.transform.transformer.utility.pnml import (
    find_triggers,
    generate_explicit_trigger_id,
)


def handle_trigger_creation(trigger: NetElement):
    """Create a trigger helper element."""
    if not trigger.toolspecific:
        raise InternalTransformationException("Not possible.")
    if trigger.toolspecific.is_workflow_message():
        return MessageHelperPNML(
            id=generate_explicit_trigger_id(trigger.id), name=trigger.name
        )
    elif trigger.toolspecific.is_workflow_time():
        return TimeHelperPNML(
            id=generate_explicit_trigger_id(trigger.id), name=trigger.name
        )
    else:
        raise InternalTransformationException("Should not happen.")


def split_event_triggers(net: Net):
    """Split the event triggers into a net and helper element."""
    for trigger in find_triggers(net):
        split_by_degree(net, trigger, handle_trigger_creation, split_on_sequence=True)
