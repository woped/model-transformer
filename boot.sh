#!/bin/bash
set -e

echo "Starting application with gunicorn..."

# Use gunicorn to run the WSGI app
gunicorn \
    --bind 0.0.0.0:8080 \
    --workers 4 \
    --worker-class sync \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    wsgi:app
