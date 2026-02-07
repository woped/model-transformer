"""Prometheus metrics used by the Flask app."""

from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
)
TRANSFORM_DURATION = Histogram(
    "transform_duration_seconds",
    "Transform processing duration",
)
