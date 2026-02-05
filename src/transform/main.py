"""API to transform a given model into a selected direction."""

import os
import logging
import time

import flask
import functions_framework
import requests
from flask import jsonify, make_response

from exceptions import (
    KnownException,
    MissingEnvironmentVariable,
    PrivateInternalException,
    TokenCheckUnsuccessful,
    UnexpectedError,
    UnexpectedQueryParameter,
    NoRequestTokensAvailable,
)
from transformer.models.bpmn.bpmn import BPMN
from transformer.models.pnml.pnml import Pnml
from transformer.transform_bpmn_to_petrinet.transform import (
    bpmn_to_workflow_net,
)
from transformer.transform_petrinet_to_bpmn.transform import pnml_to_bpmn
from transformer.utility.utility import clean_xml_string

logger = logging.getLogger(__name__)

CHECK_TOKEN_URL = "https://europe-west3-woped-422510.cloudfunctions.net/checkTokens"

is_force_std_xml_active = os.getenv("FORCE_STD_XML")
if is_force_std_xml_active is None:
    raise MissingEnvironmentVariable("FORCE_STD_XML")


@functions_framework.http
def post_transform(request: flask.Request):
    """HTTP based model transformation API.

    Process parameters to detect the type of posted model and the
    transformation direction.

    Args:
        request: A request with a parameter "direction" as transformation direction
        and a form with the xml model "bpmn" or "pnml".
    """
    try:
        if os.getenv("K_SERVICE") is not None:
            logger.debug("Running in Cloud Function environment, checking tokens")
            response = requests.get(CHECK_TOKEN_URL)
            logger.debug("Token check response", extra={"status_code": response.status_code})
            if response.status_code == 400:
                logger.warning("Token check unsuccessful")
                raise TokenCheckUnsuccessful()
            if response.status_code == 429:
                logger.warning("No request tokens available")
                raise NoRequestTokensAvailable()

        if request.method == "OPTIONS":
            logger.debug("Handling CORS preflight request")
            response = make_response()
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "POST,OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type,Authorization"
            )
            return response

        return handle_transformation(request)
    except KnownException as e:
        logger.warning("Known exception occurred", extra={
            "error": str(e),
            "error_type": type(e).__name__,
        })
        return str(e), 400
    except PrivateInternalException as e:
        logger.error("Internal exception occurred", extra={
            "error": str(e),
            "error_type": type(e).__name__,
        })
        return str(e), 400
    except Exception as e:
        logger.exception("Unexpected exception occurred", extra={
            "error": str(e),
            "error_type": type(e).__name__,
        })
        return str(UnexpectedError()), 400


def get_xml_content(request: flask.Request, field_name: str) -> str:
    """Extract XML content from request - supports both form-data and raw XML body.
    
    Args:
        request: The Flask request object
        field_name: The form field name to look for ('bpmn' or 'pnml')
    
    Returns:
        The XML content as string
    
    Raises:
        ValueError: If no XML content could be extracted
    """
    # Try form data first (multipart/form-data)
    if request.form and field_name in request.form:
        logger.debug("Extracting XML from form field", extra={"field": field_name})
        return request.form[field_name]
    
    # Try raw body (application/xml or text/xml)
    content_type = request.content_type or ""
    if "xml" in content_type.lower() or not request.form:
        raw_data = request.get_data(as_text=True)
        if raw_data:
            logger.debug("Extracting XML from raw body", extra={
                "content_type": content_type,
                "body_length": len(raw_data),
            })
            return raw_data
    
    raise ValueError(f"No XML content found. Expected form field '{field_name}' or XML body.")


def handle_transformation(request: flask.Request):
    """Handle the transformation."""
    transform_direction = request.args.get("direction")
    if transform_direction is None:
        logger.warning("Missing 'direction' query parameter")
        raise UnexpectedQueryParameter("direction")

    logger.info("Starting transformation", extra={"direction": transform_direction})

    if transform_direction == "bpmntopnml":
        bpmn_xml_content = get_xml_content(request, "bpmn")
        input_size = len(bpmn_xml_content)
        logger.debug("Received BPMN input", extra={"input_size_bytes": input_size})
        
        parse_start = time.time()
        bpmn = BPMN.from_xml(bpmn_xml_content)
        logger.debug("BPMN parsed successfully", extra={
            "parse_duration_ms": round((time.time() - parse_start) * 1000, 2),
            "process_id": bpmn.process.id if bpmn.process else None,
        })
        
        transform_start = time.time()
        transformed_pnml = bpmn_to_workflow_net(bpmn)
        logger.debug("BPMN to PNML transformation completed", extra={
            "transform_duration_ms": round((time.time() - transform_start) * 1000, 2),
        })
        
        result_string = clean_xml_string(transformed_pnml.to_string())
        logger.info("Transformation successful", extra={
            "direction": transform_direction,
            "output_size_bytes": len(result_string),
        })
        
        response = jsonify({"pnml": result_string})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    elif transform_direction == "pnmltobpmn":
        pnml_xml_content = get_xml_content(request, "pnml")
        input_size = len(pnml_xml_content)
        logger.debug("Received PNML input", extra={"input_size_bytes": input_size})
        
        parse_start = time.time()
        pnml = Pnml.from_xml_str(pnml_xml_content)
        logger.debug("PNML parsed successfully", extra={
            "parse_duration_ms": round((time.time() - parse_start) * 1000, 2),
            "net_id": pnml.net.id if pnml.net else None,
        })
        
        transform_start = time.time()
        transformed_bpmn = pnml_to_bpmn(pnml)
        logger.debug("PNML to BPMN transformation completed", extra={
            "transform_duration_ms": round((time.time() - transform_start) * 1000, 2),
        })
        
        result_string = clean_xml_string(transformed_bpmn.to_string())
        logger.info("Transformation successful", extra={
            "direction": transform_direction,
            "output_size_bytes": len(result_string),
        })
        
        response = jsonify({"bpmn": result_string})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    else:
        logger.warning("Invalid transformation direction", extra={"direction": transform_direction})
        raise UnexpectedQueryParameter("direction")
