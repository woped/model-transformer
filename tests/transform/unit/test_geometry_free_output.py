"""Regression guard for the geometry-free PNML output contract.

The transformer was changed to emit lean, geometry-free PNML: layout
(``<graphics>``/``<position>``/``<dimension>``/``<offset>``), operator
``<orientation>`` and ``<time>``/``<timeUnit>`` fields were deliberately
dropped, because t2p-2.0 owns layout and adds coordinates downstream.

Nothing else in the suite guards this: ``compare_pnml`` compares parsed *model
objects*, not the serialized XML, so a reintroduced field default (or a stray
``graphics`` assignment in the transform) would slip through every existing
test. This asserts directly on the emitted XML string instead.
"""

import unittest

from tests.transform.testgeneration.bpmn.utility import create_bpmn

from app.transform.transformer.models.bpmn.bpmn import EndEvent, StartEvent, Task
from app.transform.transformer.transform_bpmn_to_petrinet.transform import (
    bpmn_to_workflow_net,
)

# Element tags that must never appear in the transformer's PNML output.
FORBIDDEN_TAGS = (
    "graphics",
    "position",
    "dimension",
    "offset",
    "orientation",
    "time",
    "timeUnit",
)


class TestGeometryFreeOutput(unittest.TestCase):
    """The serialized PNML must carry no layout/UI/time fields."""

    def test_transformed_pnml_has_no_layout_or_ui_fields(self):
        bpmn = create_bpmn(
            "geometry_free",
            [[StartEvent(id="s1"), Task(id="t1"), EndEvent(id="e1")]],
        )

        xml = bpmn_to_workflow_net(bpmn).to_string()

        for tag in FORBIDDEN_TAGS:
            self.assertNotIn(
                f"<{tag}",
                xml,
                f"geometry/UI element <{tag}> leaked into geometry-free PNML:\n{xml}",
            )


if __name__ == "__main__":
    unittest.main()
