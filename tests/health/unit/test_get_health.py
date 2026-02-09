"""This module contains unit tests for the get_health function."""
from unittest.mock import Mock
import unittest
from app.health import main
from flask import Flask

class TestIntegrationGetHealth(unittest.TestCase):
    """A unit test class for testing the health endpoint of the application."""

    def setUp(self):
        """Performs setup before each test case."""
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()


    def tearDown(self):
        """Performs cleanup after each test case."""
        self.app_context.pop()


    def test_status_code(self):
        """Tests the status code of the health endpoint."""
        data = {}
        req = Mock(get_json=Mock(return_value=data), args=data)
        res = main.get_health(req)
        
        self.assertEqual(res.status_code, 200)


    def test_content_type(self):
        """Tests the content type of the health endpoint."""
        data = {}
        req = Mock(get_json=Mock(return_value=data), args=data)
        res = main.get_health(req)
        
        self.assertEqual(res.content_type, 'application/json')


    def test_res_body(self):
        """Tests the response body of the health endpoint."""
        data = {}
        req = Mock(get_json=Mock(return_value=data), args=data)
        res = main.get_health(req)

        self.assertEqual(res.get_json(), {"healthy": True})


    def test_res_body_with_param(self):
        """Tests the response body of the health endpoint with a provided parameter."""
        message = "unitTestMessage"
        data = {"message": message}
        req = Mock(get_json=Mock(return_value=data), args=data)
        res = main.get_health(req)

        self.assertEqual(res.get_json(), {"healthy": True, "message": message})


    def test_res_body_with_unkown_param(self):
        """Tests the response body of the health endpoint with an unknown parameter."""
        message = "unitTestMessage"
        data = {"unkownParameter": message}
        req = Mock(get_json=Mock(return_value=data), args=data)
        res, status_code = main.get_health(req)
        expected_res_body = {"code": 400, "message": "Invalid parameter provided."}
        
        self.assertEqual(status_code, 400)
        self.assertEqual(res.get_json(), expected_res_body)


if __name__ == '__main__':
    unittest.main()