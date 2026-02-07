"""Module for creating operator places and transitions in a workflow using PNML."""

from app.transform.transformer.models.pnml.pnml import (
    Place,
    Transition,
)
from app.transform.transformer.models.pnml.workflow import WorkflowBranchingType


def create_operator_place(id: str, branching_type: WorkflowBranchingType):
    """Returns an operator place for a workflow operator."""
    place = Place.create(id=f"P_CENTER_{id}")
    place.mark_as_workflow_operator(branching_type, id)
    return place


def create_operator_transition(
    id: str, index: int, branching_type: WorkflowBranchingType, name: str | None = None
):
    """Returns an operator transition for a workflow operator."""
    new_id = f"{id}_op_{index}"
    transition = Transition.create(id=new_id, name=name)
    transition.mark_as_workflow_operator(branching_type, id)
    return transition

