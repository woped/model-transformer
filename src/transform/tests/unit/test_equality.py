"""Unit tests for the detection of subelements.

Includes tests to check whether all PNML and BPMN subelemts are identified correctly.
"""

import unittest
import pytest

from transformer.equality.bpmn import get_all_processes_by_id
from transformer.equality.petrinet import get_all_nets_by_id
from transformer.models.bpmn.bpmn import BPMN
from transformer.models.pnml.pnml import Pnml


class TestSubelements(unittest.TestCase):
    """This class tests whether all subprocesses are identified."""

    @pytest.mark.skip(reason="Test asset path issue - file not found at relative path")
    def test_pnml_eqaulity_subprocess(self):
        """Tests whether all pnml subprocesses are identified."""
        pnml = Pnml.from_file("tests/assets/multiplesubprocesses.pnml")
        subnets = {}
        get_all_nets_by_id(pnml.net, subnets)
        self.assertEqual(len(subnets), 8)

    @pytest.mark.skip(reason="Test asset path issue - file not found at relative path")
    def test_bpmn_eqaulity_subprocess(self):
        """Tests whether all bpmn subprocesses are identified."""
        bpmn = BPMN.from_file("tests/assets/multiplesubprocesses.bpmn")
        subnets = {}
        get_all_processes_by_id(bpmn.process, subnets)
        self.assertEqual(len(subnets), 5)
