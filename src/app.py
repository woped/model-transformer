"""App file for cloudfunctions when deploying inside a docker container."""

import os
from flask import Flask, request, jsonify
from health.main import get_health
from transform.main import post_transform
from flask_cors import CORS
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
from pythonjsonlogger import jsonlogger
import logging


# Prometheus Metriken
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])
TRANSFORM_DURATION = Histogram('transform_duration_seconds', 'Transform processing duration')


def get_log_level() -> int:
    """Get log level from environment variable LOG_LEVEL.
    
    Supported values: DEBUG, INFO, WARNING, ERROR, CRITICAL
    Default: INFO
    """
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return log_levels.get(log_level_str, logging.INFO)


class MetricsFilter(logging.Filter):
    def filter(self, record):
        if record.name == "werkzeug":
            return "/metrics" not in record.getMessage()
        try:
            return not request.path.startswith('/metrics')
        except RuntimeError:
            return True


# Configure logging
log_level = get_log_level()

logger = logging.getLogger()
logger.setLevel(log_level)

werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(log_level)

metrics_filter = MetricsFilter()

console_handler = logging.StreamHandler()
console_handler.addFilter(metrics_filter)

console_formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(levelname)s %(name)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(console_formatter)

logger.addHandler(console_handler)
werkzeug_logger.addHandler(console_handler)

logger.info("Application starting", extra={"log_level": logging.getLevelName(log_level)})

app = Flask(__name__)
CORS(app)

@app.route('/metrics')
def metrics():
    """Expose Prometheus metrics."""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/health', methods=['GET'])
def health_route():
    """Mapping route for health endpoint."""
    start_time = time.time()
    try:
        logger.debug("Health check endpoint called", extra={
            "method": request.method,
            "remote_addr": request.remote_addr,
        })
        result = get_health(request)
        elapsed_ms = (time.time() - start_time) * 1000
        logger.info("Health check completed", extra={"duration_ms": round(elapsed_ms, 2)})
        REQUEST_COUNT.labels(method='GET', endpoint='/health', status='200').inc()
        return result
    except Exception as e:
        logger.error("Health check failed", extra={"error": str(e), "error_type": type(e).__name__})
        REQUEST_COUNT.labels(method='GET', endpoint='/health', status='500').inc()
        return jsonify({"error": str(e)}), 500
    finally:
        REQUEST_LATENCY.labels(method='GET', endpoint='/health').observe(time.time() - start_time)

@app.route('/transform', methods=['POST'])
def transform_route():
    """Mapping route for transform endpoint."""
    start_time = time.time()
    try:
        direction = request.args.get("direction", "unknown")
        content_length = request.content_length or 0
        
        logger.info("Transform request received", extra={
            "direction": direction,
            "content_length_bytes": content_length,
            "remote_addr": request.remote_addr,
        })
        logger.debug("Transform request details", extra={
            "content_type": request.content_type,
            "form_keys": list(request.form.keys()) if request.form else [],
        })
        
        transform_start_time = time.time()
        result = post_transform(request)
        transform_duration_ms = (time.time() - transform_start_time) * 1000
        TRANSFORM_DURATION.observe(time.time() - transform_start_time)

        logger.info("Transform request completed", extra={
            "direction": direction,
            "duration_ms": round(transform_duration_ms, 2),
        })
        REQUEST_COUNT.labels(method='POST', endpoint='/transform', status='200').inc()
        return result
    except Exception as e:
        logger.error("Transform request failed", extra={
            "error": str(e),
            "error_type": type(e).__name__,
            "direction": request.args.get("direction", "unknown"),
        })
        REQUEST_COUNT.labels(method='POST', endpoint='/transform', status='500').inc()
        return jsonify({"error": str(e)}), 500
    finally:
        REQUEST_LATENCY.labels(method='POST', endpoint='/transform').observe(time.time() - start_time)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
