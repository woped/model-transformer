"""API to transform a given model into a selected direction."""

import os
import time
import logging

import flask
import functions_framework
import requests
from flask import jsonify, make_response

from app.transform.exceptions import (
    KnownException,
    MissingEnvironmentVariable,
    PrivateInternalException,
    TokenCheckUnsuccessful,
    UnexpectedError,
    UnexpectedQueryParameter,
    NoRequestTokensAvailable,
)
from app.transform.transformer.models.bpmn.bpmn import BPMN
from app.transform.transformer.models.pnml.pnml import Pnml
from app.transform.transformer.transform_bpmn_to_petrinet.transform import (
    bpmn_to_workflow_net,
)
from app.transform.transformer.transform_petrinet_to_bpmn.transform import pnml_to_bpmn
from app.transform.transformer.utility.utility import clean_xml_string

CHECK_TOKEN_URL = "https://europe-west3-woped-422510.cloudfunctions.net/checkTokens"

logger = logging.getLogger(__name__)

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
    start_time = time.time()
    try:
        if os.getenv("K_SERVICE") is not None:
            logger.info("Checking request tokens")
            response = requests.get(CHECK_TOKEN_URL)
            if response.status_code == 400:
                raise TokenCheckUnsuccessful()
            if response.status_code == 429:
                raise NoRequestTokensAvailable()

        if request.method == "OPTIONS":
            # Handle CORS preflight request
            response = make_response()
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "POST,OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type,Authorization"
            )
            return response

        response = handle_transformation(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info("Transformation completed", extra={"duration_ms": duration_ms})
        return response
    except KnownException as e:
        # Exception with description for the end user.
        logger.warning("Known exception during transform", exc_info=True)
        return str(e), 400
    except PrivateInternalException as e:
        # Internal exception with a generic description to the end user.
        logger.error("Internal exception during transform", exc_info=True)
        return str(e), 400
    except Exception as e:
        # Not handled exception should be handled in the future.
        logger.exception("Unexpected exception during transform")
        return str(UnexpectedError()), 400


def handle_transformation(request: flask.Request):
    """Handle the transformation."""
    transform_direction = request.args.get("direction")
    if transform_direction is None:
        raise UnexpectedQueryParameter("direction")

    if transform_direction == "bpmntopnml":
        logger.info("Transform direction bpmntopnml")
        bpmn_xml_content = request.form["bpmn"]
        logger.debug(f"Received BPMN XML content with length: {len(bpmn_xml_content)} characters")
        
        logger.debug("Starting BPMN XML parsing")
        bpmn = BPMN.from_xml(bpmn_xml_content)
        logger.debug(f"BPMN parsed successfully - Process ID: {bpmn.process.id if bpmn.process else 'N/A'}")
        
        logger.debug("Starting BPMN to workflow net transformation")
        transformed_pnml = bpmn_to_workflow_net(bpmn)
        logger.debug(f"Transformation completed - Net contains {len(transformed_pnml.net.places)} places and {len(transformed_pnml.net.transitions)} transitions")
        
        logger.debug("Generating PNML XML string")
        pnml_string = transformed_pnml.to_string()
        logger.debug(f"PNML XML generated with length: {len(pnml_string)} characters")
        
        response = jsonify({"pnml": clean_xml_string(pnml_string)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    elif transform_direction == "pnmltobpmn":
        logger.info("Transform direction pnmltobpmn")
        pnml_xml_content = request.form["pnml"]
        pnml = Pnml.from_xml_str(pnml_xml_content)
        transformed_bpmn = pnml_to_bpmn(pnml)
        response = jsonify({"bpmn": clean_xml_string(transformed_bpmn.to_string())})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    else:
        raise UnexpectedQueryParameter("direction")
