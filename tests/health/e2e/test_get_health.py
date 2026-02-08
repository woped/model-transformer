"""e2e test cases for testing the health endpoint of the application."""

import requests
import unittest
import pytest

import os

@pytest.mark.e2e
class TestE2EGetHealth(unittest.TestCase):
    """A e2e test class for testing the health endpoint of the application."""
    
    REQUEST_TIMEOUT = 50

    def setUp(self):
        """Performs setup before each test case."""
        self.url = os.getenv("E2E_URL")
        if self.url is None:
            raise ValueError("E2E_URL environment variable not set.")
    
    def test_health_without_param(self):
        """Tests the status code of the health endpoint."""
        response = requests.get(
            self.url,
            timeout=self.REQUEST_TIMEOUT,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertEqual(response.json(), {"healthy": True})
    
    def test_health_with_param(self):
        """Tests the response body of the health endpoint with a provided parameter."""
        message = "e2eTestMessage"
        response = requests.get(
            f'{self.url}?message={message}', 
            timeout=self.REQUEST_TIMEOUT,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertEqual(response.json(), {"healthy": True, "message": message})
    
    def test_health_with_unkown_param(self):
        """Tests the response body of the health endpoint with an unknown parameter."""
        message = "e2eTestMessage"
        response = requests.get(
            f'{self.url}?unkownParameter={message}',
            timeout=self.REQUEST_TIMEOUT,
        )
        expected_res_body = {"code": 400, "message": "Invalid parameter provided."} 
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), expected_res_body)    
