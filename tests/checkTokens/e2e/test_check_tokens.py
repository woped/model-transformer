"""E2E tests for the checkTokens endpoint of the application."""

import requests
import unittest

import os

class TestE2ECheckTokens(unittest.TestCase):
    """A e2e test class for testing the CheckTokens Endpoint of the application."""
 
    REQUEST_TIMEOUT = 50

    def setUp(self):
        """Performs setup before each test case."""
        self.url = os.getenv("E2E_URL")
        if self.url is None:
            raise ValueError("E2E_URL environment variable not set.")
        self.token = os.getenv("E2E_IDENTITY_TOKEN")
        if self.token is None:
            raise ValueError("E2E_IDENTITY_TOKEN environment variable not set.")
        self.shared_haeaders = {
            "Authorization": f"Bearer {self.token}"
        }

    def test_checkToken_statusCode_contentType(self):
        """Tests the statuscode and contentType of the check Token endpoint."""
        response = requests.get(
            self.url,
            timeout=self.REQUEST_TIMEOUT,
            headers=self.shared_haeaders,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")
    

    def test_checkToken_token_value_valid(self):
        """Tests the response body of the health endpoint with a provided parameter."""
        response = requests.get(
            self.url, 
            timeout=self.REQUEST_TIMEOUT,
            headers=self.shared_haeaders,
        )
        tokens = response.json()["tokens"]
        self.assertTrue(0 <= tokens <= 100,
                        f"Tokens value {tokens} is not between 0 and 100")
