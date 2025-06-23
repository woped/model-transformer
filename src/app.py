"""App file for cloudfunctions when deploying inside a docker container."""

from flask import Flask, request, jsonify
from health.main import get_health
from transform.main import post_transform
from flask_cors import CORS
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
from pythonjsonlogger import jsonlogger
import logging
import os

# Prometheus Metriken
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])
TRANSFORM_DURATION = Histogram('transform_duration_seconds', 'Transform processing duration')

# Logging Setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Console handler with JSON format
console_handler = logging.StreamHandler()
console_formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(levelname)s %(name)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

app = Flask(__name__)
CORS(app)

@app.before_request
def suppress_metrics_logging():
    """Suppress logging for /metrics endpoint to avoid log spam."""
    if request.path == '/metrics':
        app.logger.disabled = True

@app.after_request
def restore_logging(response):
    """Restore logging after request is processed."""
    app.logger.disabled = False
    return response

@app.route('/metrics')
def metrics():
    """Expose Prometheus metrics."""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/health', methods=['GET'])
def health_route():
    """Mapping route for health endpoint."""
    start_time = time.time()
    try:
        logger.info("Health check endpoint called")
        result = get_health(request)
        REQUEST_COUNT.labels(method='GET', endpoint='/health', status='200').inc()
        return result
    except Exception as e:
        logger.error("Health check failed", extra={"error": str(e)})
        REQUEST_COUNT.labels(method='GET', endpoint='/health', status='500').inc()
        return jsonify({"error": str(e)}), 500
    finally:
        REQUEST_LATENCY.labels(method='GET', endpoint='/health').observe(time.time() - start_time)

@app.route('/transform', methods=['POST'])
def transform_route():
    """Mapping route for transform endpoint."""
    start_time = time.time()
    try:
        logger.info("Transform request received")
        transform_start_time = time.time()
        result = post_transform(request)
        TRANSFORM_DURATION.observe(time.time() - transform_start_time)
        
        REQUEST_COUNT.labels(method='POST', endpoint='/transform', status='200').inc()
        return result
    except Exception as e:
        logger.error("Transform request failed", extra={"error": str(e)})
        REQUEST_COUNT.labels(method='POST', endpoint='/transform', status='500').inc()
        return jsonify({"error": str(e)}), 500
    finally:
        REQUEST_LATENCY.labels(method='POST', endpoint='/transform').observe(time.time() - start_time)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
