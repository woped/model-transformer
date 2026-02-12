"""Implements the 'check_Tokens' HTTP Cloud Function.

This module defines a Google Cloud Function for RateLimiting the transform Endpoint.
"""

import logging
import base64
import firebase_admin
import functions_framework
import json
from firebase_admin import credentials, firestore
from flask import jsonify
import os
import pytz
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

GCP_SERVICE_ACCOUNT_CERTIFICATE_BASE64 = os.getenv("GCP_SERVICE_ACCOUNT_CERTIFICATE")
if GCP_SERVICE_ACCOUNT_CERTIFICATE_BASE64 is None:
    raise KeyError("Env var GCP_SERVICE_ACCOUNT_CERTIFICATE not found!")


GCP_SERVICE_ACCOUNT_CERTIFICATE_DECODED_BYTES = base64.b64decode(
    GCP_SERVICE_ACCOUNT_CERTIFICATE_BASE64
)

GCP_SERVICE_ACCOUNT_CERTIFICATE_DECODED_STRING = (
    GCP_SERVICE_ACCOUNT_CERTIFICATE_DECODED_BYTES.decode("utf-8")
)

cred_dict = json.loads(GCP_SERVICE_ACCOUNT_CERTIFICATE_DECODED_STRING, strict=False)
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()


@functions_framework.http
def check_tokens(request):
    """Check if there are tokens available in the Firestore database."""
    if db is None:
        logger.error("Firestore client unavailable")
        return jsonify({"error": "No database available"}), 500

    doc_ref = db.collection("api-tokens").document("token-document")
    doc = doc_ref.get()
    if doc.exists:
        tokens = doc.to_dict().get("tokens", 0)
        timestamp = doc.to_dict().get("tokens_last_replenished", 0)
        current_time = datetime.now(pytz.utc)
        time_difference = current_time - timestamp

        if tokens <= 0:
            if time_difference >= timedelta(hours=1):
                doc_ref.update({"tokens": 99, "tokens_last_replenished": current_time})
                logger.info("Tokens replenished", extra={"tokens": 99})
                return jsonify({"tokens": 99})
            else:
                logger.warning("No tokens available and replenish not due")
                return (
                    jsonify(
                        {
                            "error": "No tokens available, and last replenish"
                            + "was less than an hour ago."
                            + "Please try again later."
                        }
                    ),
                    429,
                )
        else:
            doc_ref.update({"tokens": tokens - 1})
            logger.info("Token consumed", extra={"tokens": tokens - 1})
            return jsonify({"tokens": tokens - 1}), 200
    else:
        logger.error("Token document not found")
        return jsonify({"error": "No document available"}), 404
