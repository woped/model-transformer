"""Version and metadata information for the Model Transformer application.

This module provides version information, application metadata, and other
details used by the Docker build and deployment workflows.
"""

__version__ = "2.0.0"
__app_name__ = "model-transformer"
__app_title__ = "BPMN-PNML Model Transformer"
__description__ = (
    "REST API service for transforming between BPMN and PNML process models"
)
__author__ = "woped"
__author_email__ = "contact@woped.de"
__organization__ = "woped"
__repository__ = "https://github.com/woped/model-transformer"
__license__ = "GPL-3.0"
__license_url__ = "https://www.gnu.org/licenses/gpl-3.0.html"
__python_version__ = "3.12"

# Docker image metadata
__docker_registry__ = "docker.io"
__docker_namespace__ = "woped"
__docker_image_name__ = "model-transformer"
__docker_base_image__ = "python:3.12-slim"

# API and application metadata
__api_version__ = "1.0.0"
__api_title__ = "Model Transformer API"
__api_description__ = (
    "Transforms between BPMN (Business Process Model and Notation) and "
    "PNML (Petri Net Markup Language) process models"
)
__api_contact_name__ = "woped Team"
__api_contact_url__ = "https://github.com/woped"
__api_contact_email__ = "contact@woped.de"

# Application features
__features__ = [
    "BPMN to PNML transformation",
    "PNML to BPMN transformation",
    "Token-based rate limiting",
    "Health check endpoint",
    "Prometheus metrics",
    "Structured JSON logging",
]

# Environment configuration
__default_port__ = 8080
__default_host__ = "0.0.0.0"
__default_workers__ = 4
__default_worker_timeout__ = 120

# Build and deployment metadata
__build_info__ = {
    "framework": "Flask",
    "framework_version": "3.0.3",
    "database": "None",
    "cache": "None",
    "message_queue": "None",
}


def get_version() -> str:
    """Return the current application version.
    
    Returns:
        str: The application version string.
    """
    return __version__


def get_full_version() -> str:
    """Return the full version string with app name.
    
    Returns:
        str: Full version string in format: "app-name/version".
    """
    return f"{__app_name__}/{__version__}"


def get_docker_image_uri() -> str:
    """Return the full Docker image URI.
    
    Returns:
        str: Full Docker image URI in format: registry/namespace/image:version.
    """
    return f"{__docker_registry__}/{__docker_namespace__}/{__docker_image_name__}:{__version__}"


def get_user_agent() -> str:
    """Return a user agent string for API requests.
    
    Returns:
        str: User agent string.
    """
    return f"{__app_name__}/{__version__} (+{__repository__})"
