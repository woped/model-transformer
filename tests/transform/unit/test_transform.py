"""Unit tests for transforming BPMN models to Petri nets/Workflows and vice versa.

Includes tests for supported, unsupported, and ignored cases to handle transformations.
"""

import shutil
import unittest
from pathlib import Path

from tests.transform.testgeneration.testcases.bpmn_to_pnml.ignored_cases import (
    all_cases as ignored_cases_bpmn,
)
from tests.transform.testgeneration.testcases.bpmn_to_pnml.supported_cases import (
    all_cases as supported_cases_bpmn,
)
from tests.transform.testgeneration.testcases.bpmn_to_pnml.supported_cases_workflow\
import (
    supported_cases_workflow_bpmn,
)
from tests.transform.testgeneration.testcases.bpmn_to_pnml.unsupported_cases import (
    all_cases as unsupported_cases_bpmn,
)
from tests.transform.testgeneration.testcases.pnml_to_bpmn.supported_cases import (
    all_cases as supported_cases_pnml,
)
from tests.transform.testgeneration.testcases.pnml_to_bpmn.supported_cases_workflow\
import (
    supported_cases_workflow_pnml,
)
from tests.transform.testgeneration.utility import clear

from app.transform.exceptions import NotSupportedBPMNElement
from app.transform.transformer.equality.bpmn import compare_bpmn
from app.transform.transformer.equality.petrinet import compare_pnml
from app.transform.transformer.models.bpmn.bpmn import BPMN
from app.transform.transformer.models.pnml.pnml import Pnml
from app.transform.transformer.transform_bpmn_to_petrinet.transform import (
    bpmn_to_wf_net_from_xml,
    bpmn_to_workflow_net,
)
from app.transform.transformer.transform_petrinet_to_bpmn.transform import pnml_to_bpmn

LOG_PATH = "test_log"


def save_failed_bpmn_to_pnml_transformation(
    pn_expected: Pnml, pn_transformed: Pnml, bpmn: BPMN, case: str
):
    """Saves files for failed BPMN to Petri net transformations for debugging purposes.

    Creates necessary directories and saves the expected and transformed Petri nets,
    the original BPMN model, and visual representations of all three.

    Args:
        pn_expected: The expected Petri net model.
        pn_transformed: The transformed Petri net model from the BPMN.
        bpmn: The original BPMN model.
        case: A string identifier for the test case.
    """

    def create_path(file_name: str = ""):
        p = f"{LOG_PATH}/{case}/{file_name}"
        return p

    Path(create_path()).mkdir(parents=True, exist_ok=True)

    pn_expected.write_to_file(create_path("expected.pnml"))
    pn_transformed.write_to_file(create_path("transformed.pnml"))
    bpmn.write_to_file(create_path("source.bpmn"))


def save_failed_pnml_to_bpmn_transformation(
    bpmn_expected: BPMN, bpmn_transformed: BPMN, net: Pnml, case: str
):
    """Saves files for failed pnml to bpmn transformations for debugging purposes.

    Creates necessary directories and saves the expected and transformed bpmn,
    the original pnml model, and visual representations of all three.

    Args:
        bpmn_expected: The expected BPMN model.
        bpmn_transformed: The transformed BPMN model from the BPMN.
        net: The original PNML model.
        case: A string identifier for the test case.
    """

    def create_path(file_name: str = ""):
        return f"{LOG_PATH}/{case}/{file_name}"

    Path(create_path()).mkdir(parents=True, exist_ok=True)

    bpmn_expected.write_to_file(create_path("expected.bpmn"))
    bpmn_transformed.write_to_file(create_path("transformed.bpmn"))
    net.write_to_file(create_path("source.pnml"))


class TestPetriNetToBPMN(unittest.TestCase):
    """Tests for verifying Petri net to BPMN model transformations.

    This class tests the transformation of Petri nets to BPMN models using
    predefined test cases.
    """

    def test_supported_elements(self):
        """Tests the transformation of supported Petri net elements into BPMN.

        Transforms Test Petri nets to BPMN and verifies if the resulting BPMN
        matches the expected outcome.
        """
        for bpmn_expected, net, case in supported_cases_pnml:
            bpmn_transformed = pnml_to_bpmn(net)
            equal, error = compare_bpmn(bpmn_expected, bpmn_transformed)
            if not equal:
                save_failed_pnml_to_bpmn_transformation(
                    bpmn_expected, bpmn_transformed, net, case
                )
            with self.subTest(case):
                self.assertTrue(equal, f"{case} should be equal\n{error}")


class TestWorkflowNetToBPMN(unittest.TestCase):
    """Tests for verifying Workflows to BPMN model transformations.

    This class tests the transformation of Workflows to BPMN models using
    predefined test cases.
    """

    def test_supported_workflow_elements(self):
        """Tests the transformation of supported Workflow elements into BPMN.

        Transforms Test Workflows to BPMN and verifies if the resulting BPMN
        matches the expected outcome.
        """
        for bpmn_expected, net, case in supported_cases_workflow_pnml:
            bpmn_transformed = pnml_to_bpmn(net)
            equal, error = compare_bpmn(bpmn_expected, bpmn_transformed)
            if not equal:
                save_failed_pnml_to_bpmn_transformation(
                    bpmn_expected, bpmn_transformed, net, case
                )
            with self.subTest(case):
                self.assertTrue(equal, f"{case} should be equal\n{error}")


class TestBPMNToPetriNet(unittest.TestCase):
    """Tests for verifying BPMN to Petri net transformations.

    This class tests the transformation of BPMN to Petri net using
    predefined test cases.
    """

    def test_supported_elements(self):
        """Tests the handling of supported BPMN elements.

        Transforms supported BPMN elements to Petri net and verifies if the resulting
        Petri net matches the expected outcome.
        """
        for bpmn, pn_expected, case in supported_cases_bpmn:
            pn_transformed = bpmn_to_workflow_net(bpmn)
            equal, error = compare_pnml(pn_expected.net, pn_transformed.net)
            if not equal:
                save_failed_bpmn_to_pnml_transformation(
                    pn_expected, pn_transformed, bpmn, case
                )
            with self.subTest(case):
                self.assertTrue(equal, f"{case} should be equal\n{error}")

    def test_unsupported_elemnts(self):
        """Tests the handling of unsupported BPMN elements.

        Checks unsupported BPMN elements and raises an exception.
        """
        for bpmn_xml, name in unsupported_cases_bpmn:
            with self.assertRaises(NotSupportedBPMNElement):
                bpmn_to_wf_net_from_xml(bpmn_xml)
        clear()

    def test_ignore_elements(self):
        """Tests the handling of ignored BPMN elements.

        Transforms ignored BPMN elements to Petri net and verifies if the resulting
        Petri net matches the expected outcome.
        """
        for bpmn_xml, pn_truth in ignored_cases_bpmn:
            pn_transformed = bpmn_to_wf_net_from_xml(bpmn_xml)
            equal, error = compare_pnml(pn_truth.net, pn_transformed.net)
            self.assertTrue(equal, f"should be equal\n{error}")
        clear()


class TestBPMNToWorkflowNet(unittest.TestCase):
    """Tests for verifying BPMN to Workflow transformations.

    This class tests the transformation of BPMN to Workflow using
    predefined test cases.
    """

    def test_supported_elements(self):
        """Tests the handling of supported BPMN elements.

        Transforms Test BPMNs to PNML and verifies if the resulting Workflow
        matches the expected outcome.
        """
        for bpmn, pn_expected, case in supported_cases_workflow_bpmn:
            pn_transformed = bpmn_to_workflow_net(bpmn)
            equal, error = compare_pnml(pn_expected.net, pn_transformed.net)
            if not equal:
                save_failed_bpmn_to_pnml_transformation(
                    pn_expected, pn_transformed, bpmn, case
                )
            with self.subTest(case):
                self.assertTrue(equal, f"{case} should be equal\n{error}")


if __name__ == "__main__":
    if Path(LOG_PATH).exists():
        shutil.rmtree(LOG_PATH)
    unittest.main()

