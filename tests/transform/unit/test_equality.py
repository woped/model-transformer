"""Unit tests for the detection of subelements.

Includes tests to check whether all PNML and BPMN subelemts are identified correctly.
"""

import unittest

from tests.transform.testgeneration.pnml.utility import create_petri_net

from app.transform.transformer.equality.bpmn import get_all_processes_by_id
from app.transform.transformer.equality.petrinet import compare_pnml, get_all_nets_by_id
from app.transform.transformer.models.bpmn.bpmn import BPMN
from app.transform.transformer.models.pnml.pnml import Place, Pnml, Transition


class TestSubelements(unittest.TestCase):
    """This class tests whether all subprocesses are identified."""

    def test_pnml_eqaulity_subprocess(self):
        """Tests whether all pnml subprocesses are identified."""
        pnml = Pnml.from_file("tests/transform/assets/multiplesubprocesses.pnml")
        subnets = {}
        get_all_nets_by_id(pnml.net, subnets)
        self.assertEqual(len(subnets), 8)

    def test_bpmn_eqaulity_subprocess(self):
        """Tests whether all bpmn subprocesses are identified."""
        bpmn = BPMN.from_file("tests/transform/assets/multiplesubprocesses.bpmn")
        subnets = {}
        get_all_processes_by_id(bpmn.process, subnets)
        self.assertEqual(len(subnets), 5)


class TestEqualityOracle(unittest.TestCase):
    """``compare_pnml`` is the oracle every BPMN<->PNML transform test relies on:
    the transform is asserted correct by comparing its output against an
    expected net. The existing tests only ever feed it nets that *should* be
    equal, so a bug that made it return ``True`` for unequal nets would make the
    whole transform suite pass vacuously. These tests pin the other direction --
    genuinely different nets must compare unequal -- using hand-built nets as
    independent ground truth.
    """

    @staticmethod
    def _line_net(middle_id):
        """place 'p_in' -> transition <middle_id> -> place 'p_out'."""
        return create_petri_net(
            "oracle_net",
            [[Place(id="p_in"), Transition(id=middle_id), Place(id="p_out")]],
        )

    def test_identical_net_compares_equal(self):
        """Sanity floor: a net must compare equal to itself."""
        net = self._line_net("t1")
        equal, error = compare_pnml(net.net, net.net)
        self.assertTrue(equal)
        self.assertIsNone(error)

    def test_renamed_node_compares_unequal(self):
        """Two nets of identical shape but a differently-identified transition
        are not equal -- otherwise transform output could diverge undetected."""
        equal, error = compare_pnml(
            self._line_net("t1").net, self._line_net("t_renamed").net
        )
        self.assertFalse(equal)
        self.assertTrue(error)

    def test_extra_node_compares_unequal(self):
        """A net with extra elements is not equal to a smaller one."""
        small = self._line_net("t1")
        larger = create_petri_net(
            "oracle_net",
            [
                [
                    Place(id="p_in"),
                    Transition(id="t1"),
                    Place(id="p_mid"),
                    Transition(id="t2"),
                    Place(id="p_out"),
                ]
            ],
        )
        equal, error = compare_pnml(small.net, larger.net)
        self.assertFalse(equal)
        self.assertTrue(error)
