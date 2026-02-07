"""API routes for model transformer."""

import logging
import time

from flask import jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api import bp
from app.health.main import get_health
from app.model_transformer.metrics import (
    TRANSFORM_DURATION,
    REQUEST_COUNT,
    REQUEST_LATENCY,
)
from app.transform.main import post_transform

logger = logging.getLogger(__name__)


@bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    start_time = time.time()
    try:
        logger.info("Health check endpoint called")
        result = get_health(request)
        REQUEST_COUNT.labels(method="GET", endpoint="/health", status="200").inc()
        return result
    except Exception as exc:
        logger.exception("Health check failed")
        REQUEST_COUNT.labels(method="GET", endpoint="/health", status="500").inc()
        return jsonify({"error": str(exc)}), 500
    finally:
        REQUEST_LATENCY.labels(method="GET", endpoint="/health").observe(
            time.time() - start_time
        )


@bp.route("/transform", methods=["POST"])
def transform():
    """Transform endpoint for model transformation."""
    start_time = time.time()
    try:
        logger.info("Transform request received")
        transform_start_time = time.time()
        result = post_transform(request)
        TRANSFORM_DURATION.observe(time.time() - transform_start_time)

        REQUEST_COUNT.labels(method="POST", endpoint="/transform", status="200").inc()
        return result
    except Exception as exc:
        logger.exception("Transform request failed")
        REQUEST_COUNT.labels(method="POST", endpoint="/transform", status="500").inc()
        return jsonify({"error": str(exc)}), 500
    finally:
        REQUEST_LATENCY.labels(method="POST", endpoint="/transform").observe(
            time.time() - start_time
        )


@bp.route("/metrics", methods=["GET"])
def metrics():
    """Expose Prometheus metrics."""
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}
