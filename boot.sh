#!/bin/bash
. .venv/bin/activate

# Transformation is CPU-bound XML/graph work (no LLM wait), so favour workers
# over threads, with a generous timeout for pathologically large models. All
# three are env-overridable.
GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
GUNICORN_THREADS="${GUNICORN_THREADS:-2}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-120}"

exec gunicorn \
	-b :5000 \
	--workers "$GUNICORN_WORKERS" \
	--threads "$GUNICORN_THREADS" \
	--timeout "$GUNICORN_TIMEOUT" \
	--access-logfile - \
	--error-logfile - \
	flasky:app
