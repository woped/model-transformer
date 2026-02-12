"""WSGI entry point for the application."""

import logging
import click

from app import create_app

logger = logging.getLogger(__name__)

# Create Flask app instance for WSGI
app = create_app()


@app.cli.command("test")
@click.option("--cov", is_flag=True, help="Show test coverage report.")
def test_command(cov):
    """Run all tests in the 'tests/' directory."""
    import pytest

    logger.info("Running test suite via CLI", extra={"coverage": bool(cov)})
    args = ["tests"]
    if cov:
        args += ["--cov=app", "--cov-report=term-missing"]
    result = pytest.main(args)
    logger.info("Test suite finished", extra={"exit_code": result})
    raise SystemExit(result)
