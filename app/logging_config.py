"""Shared logging configuration using pythonjsonlogger."""

import logging
from typing import Optional

from pythonjsonlogger import jsonlogger

try:
    from flask import request, g
except Exception:  # pragma: no cover - flask not available in all contexts
    request = None
    g = None


class RequestContextFilter(logging.Filter):
    """Attach request context fields to log records when available."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "status_code"):
            record.status_code = None
        if not hasattr(record, "duration_ms"):
            record.duration_ms = None

        try:
            record.http_method = request.method if request is not None else None
            record.http_path = request.path if request is not None else None
            record.request_id = getattr(g, "request_id", None) if g is not None else None
        except RuntimeError:
            record.http_method = None
            record.http_path = None
            record.request_id = None
        return True


class MetricsFilter(logging.Filter):
    """Prevent noisy metrics logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name == "werkzeug":
            return "/metrics" not in record.getMessage()
        try:
            if request is None:
                return True
            return not request.path.startswith("/metrics")
        except RuntimeError:
            return True


_LOG_FORMAT = (
    "%(asctime)s %(levelname)s %(name)s %(message)s "
    "%(request_id)s %(http_method)s %(http_path)s %(status_code)s %(duration_ms)s"
)


def setup_logging(level: int = logging.INFO, logger_name: Optional[str] = None) -> logging.Logger:
    """Configure structured JSON logging.

    Args:
        level: Logging level for root and configured loggers.
        logger_name: Optional logger name to return.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if not any(isinstance(handler, logging.StreamHandler) for handler in root_logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.addFilter(MetricsFilter())
        console_handler.addFilter(RequestContextFilter())

        console_formatter = jsonlogger.JsonFormatter(
            _LOG_FORMAT,
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        werkzeug_logger = logging.getLogger("werkzeug")
        werkzeug_logger.setLevel(level)
        werkzeug_logger.addHandler(console_handler)

    return logging.getLogger(logger_name) if logger_name else root_logger
