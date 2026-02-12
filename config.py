"""Flask configuration classes and environment setup."""

import os
import sys
from pathlib import Path

# Load environment variables from .env file (development only)
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv not available in production

# Add the root of the project to sys.path
PROJECT_ROOT = Path(__file__).parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class Config:
    """Base configuration."""

    ENV_NAME = "default"
    DEBUG = False
    TESTING = False
    JSON_SORT_KEYS = False
    PROPAGATE_EXCEPTIONS = False
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @staticmethod
    def init_app(app):
        """Hook for additional initialization."""
        return None


class DevelopmentConfig(Config):
    """Development configuration."""

    ENV_NAME = "development"
    DEBUG = True


class TestingConfig(Config):
    """Testing configuration."""

    ENV_NAME = "testing"
    TESTING = True
    LOG_LEVEL = "DEBUG"  # Enable debug logging for tests
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""

    ENV_NAME = "production"


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": Config,
}


def get_config(config_name: str | None = None):
    """Resolve a configuration class by name."""
    if not config_name:
        config_name = (
            os.environ.get("FLASK_CONFIG") or os.environ.get("APP_ENV") or "default"
        )
    return CONFIG_BY_NAME.get(config_name.lower(), Config)
