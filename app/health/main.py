"""Implements the 'get_health' HTTP Cloud Function.

This module defines a Google Cloud Function for responding to HTTP requests
with the health status of the service, indicating if it's operational.
"""

import logging

from flask import jsonify, make_response

logger = logging.getLogger(__name__)


def get_health(request):
    """HTTP Cloud Function.

    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    if request.method == "OPTIONS":
        # Handle CORS preflight request
        response = make_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET,OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        return response

    health_status = {"healthy": True}

    if request and request.args:
        if "message" in request.args:
            health_status["message"] = request.args["message"]
        else:
            error = {
                "code": 400,
                "message": "Invalid parameter provided.",
            }
            logger.warning("Invalid parameter provided for health check")
            response = jsonify(error)
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response, error["code"]

    logger.info("Health check successful")
    response = jsonify(health_status)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response
