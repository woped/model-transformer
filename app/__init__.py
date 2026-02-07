"""Application factory for the Flask app."""

import logging
import os
import time
import uuid

from flask import Flask, g, jsonify, request
from flask_cors import CORS

from app.logging_config import setup_logging
from config import get_config


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application.
    
    Args:
        config_name: Configuration name (development, testing, production, default).
                    If None, uses FLASK_CONFIG or APP_ENV environment variable.
    
    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG') or os.environ.get('APP_ENV') or 'default'

    config_class = get_config(config_name)
    app.config.from_object(config_class)
    config_class.init_app(app)

    log_level_name = app.config.get("LOG_LEVEL", "INFO")
    log_level = getattr(logging, log_level_name.upper(), logging.INFO)
    logger = setup_logging(log_level, __name__)

    # Configure CORS
    CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]}})

    @app.before_request
    def capture_request_context():
        g.request_start_time = time.time()
        g.request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        logger.info(
            "Request received",
            extra={
                "request_id": g.request_id,
                "http_method": request.method,
                "http_path": request.path,
            },
        )

    @app.after_request
    def log_response(response):
        duration_ms = round((time.time() - g.request_start_time) * 1000, 2)
        logger.info(
            "Request completed",
            extra={
                "request_id": getattr(g, "request_id", None),
                "http_method": request.method,
                "http_path": request.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    @app.errorhandler(Exception)
    def handle_unhandled_exception(exception):
        logger.exception(
            "Unhandled exception",
            extra={
                "request_id": getattr(g, "request_id", None),
                "http_method": getattr(request, "method", None),
                "http_path": getattr(request, "path", None),
            },
        )
        return jsonify({"error": "Internal server error"}), 500

    # Register blueprints
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='')

    return app
