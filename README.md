# PNML-BPMN-TRANSFORMER

A Flask API service that converts business processes between BPMN notation and
PNML (Petri Net Markup Language), in both directions. It is called directly by
the WOPED client.

Please refer to this [repo's wiki](https://github.com/Niyada/bpmn-pnml-transformer-poc/wiki) for more information.
To use the API, refer to its [documentation](https://woped.github.io/model-transformer/).

---

## Quick Start

### Development

```bash
# Install dependencies
pip install -r requirements/dev.txt

# Set required environment variables
export FORCE_STD_XML=true
export FLASK_CONFIG=development

# Run development server (FLASK_APP defaults to flasky.py)
flask --app flasky run
```

### Testing

```bash
export FORCE_STD_XML=true
pytest tests/
# or with coverage
pytest tests/ --cov=app
```

### End-to-End (E2E) Testing

E2E tests require a running server instance and are skipped by default. To run E2E tests:

1. Start the application server:
   ```bash
   export FORCE_STD_XML=true
   export FLASK_CONFIG=development
   flask --app flasky run
   ```

2. In a separate terminal, set E2E environment variable and run tests:
   ```bash
   export E2E_URL=http://localhost:5000    # Base URL for health/checkTokens
   # For transform endpoint: http://localhost:5000/transform

   # Run only E2E tests
   pytest tests/ -m e2e

   # Run all tests including E2E
   pytest tests/
   ```

To exclude E2E tests (default behavior when environment variables are not set):
```bash
pytest tests/ -m "not e2e"
```

### Production

The production entry point is `flasky:app`, launched through `boot.sh`:

```bash
gunicorn -b :5000 flasky:app
```

---

## Project Setup

After cloning this repository, it's essential to [set up git hooks](https://github.com/woped/woped-git-hooks/blob/main/README.md#activating-git-hooks-after-cloning-a-repository) to ensure project standards.

---

## Architecture Overview

### Project Structure

```
model-transformer/
├── config.py                    # Root-level configuration classes
├── flasky.py                    # WSGI entry point (app = create_app()) + CLI test command
├── version.py                   # Version and metadata, used by CI for container tagging
├── boot.sh                      # Container entry point (activates venv, runs gunicorn)
├── Dockerfile                   # Container image definition
├── app/
│   ├── __init__.py             # Application factory (create_app)
│   ├── logging_config.py       # JSON logging configuration
│   ├── api/
│   │   ├── __init__.py         # API blueprint definition
│   │   └── routes.py           # Consolidated API routes (/health, /transform, /metrics)
│   ├── model_transformer/
│   │   ├── __init__.py
│   │   └── metrics.py          # Prometheus metrics
│   ├── health/                 # Health check logic
│   ├── transform/              # Model transformation logic
│   ├── checkTokens/            # Token validation logic (Cloud Function helper)
│   └── ...
├── tests/
│   ├── checkTokens/
│   ├── health/
│   └── transform/
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   ├── docker.txt
│   ├── prod.txt
│   └── test.txt
└── docs/
    └── ...
```

### Key Components

#### Application Factory (`app/__init__.py`)

The Flask app is created using the factory pattern via `create_app()`:

```python
from app import create_app

# Create app with defaults
app = create_app()

# Create app with specific config
app = create_app('development')
app = create_app('testing')
app = create_app('production')
```

The factory handles:
- Configuration loading from `config.py`
- JSON logging setup via `logging_config.py`
- CORS configuration
- Blueprint registration
- Error handlers
- Request/response middleware

#### Configuration (`config.py`)

Centralized configuration management with environment-based loading. The base
`Config` and the per-environment subclasses are resolved by name through
`CONFIG_BY_NAME` / `get_config()`:

```python
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
        return None

class DevelopmentConfig(Config):
    ENV_NAME = "development"
    DEBUG = True

class TestingConfig(Config):
    ENV_NAME = "testing"
    TESTING = True
    LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    ENV_NAME = "production"

def get_config(config_name=None):
    """Resolve a configuration class by name (falls back to FLASK_CONFIG / APP_ENV)."""
```

**Environment Variables:**
```bash
FLASK_CONFIG=development|testing|production  # Explicit config selection
APP_ENV=development|testing|production       # Alternative config selection
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR           # Logging level (default: INFO)
FORCE_STD_XML=true                           # Required for transform module
```

#### API Blueprint (`app/api/`)

All routes are consolidated under a single API blueprint:

```python
# app/api/__init__.py
bp = Blueprint('api', __name__)

# app/api/routes.py
@bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""

@bp.route('/transform', methods=['POST'])
def transform():
    """Model transformation endpoint"""

@bp.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
```

#### Entry Point

**`flasky.py`** — the WSGI entry point. It builds the app via the factory and
registers the CLI test command:

```python
app = create_app()

@app.cli.command("test")
@click.option('--cov', is_flag=True, help="Show test coverage report.")
def test_command(cov):
    """Run all tests in the 'tests/' directory."""
```

`app/__init__.py` contains the `create_app()` factory itself.

---

## API Endpoints

### GET `/health`
Health check endpoint for monitoring application status.

**Response:**
```json
{
  "healthy": true
}
```

An optional `?message=...` query parameter is echoed back as a `message` field.
Any other query parameter returns `400`.

### POST `/transform`
Transform a model between BPMN and PNML. The direction is selected with the
`direction` **query parameter**, and the model XML is sent as **form-data**.

**Request:**

| Direction (`?direction=`) | Form field | Response body |
|---------------------------|------------|---------------|
| `bpmntopnml`              | `bpmn`     | `{ "pnml": "<...>" }` |
| `pnmltobpmn`              | `pnml`     | `{ "bpmn": "<...>" }` |

```bash
curl -X POST "http://localhost:5000/transform?direction=bpmntopnml" \
  --form 'bpmn=<bpmn>...</bpmn>'
```

A missing/unknown `direction` or a missing form field returns `400` with an
error message. When the service runs on Cloud Run (`K_SERVICE` set), requests
are first checked against the token-rate-limiting Cloud Function.

### GET `/metrics`
Prometheus metrics endpoint for monitoring.

**Metrics:**
- `http_requests_total` - Total HTTP requests by method, endpoint, and status
- `http_request_duration_seconds` - HTTP request duration histogram
- `transform_duration_seconds` - Model transformation duration

---

## Configuration & Environment

### Development Configuration

```bash
export FLASK_CONFIG=development
export FORCE_STD_XML=true
export LOG_LEVEL=DEBUG

flask --app flasky run --reload
```

### Testing Configuration

```bash
export FLASK_CONFIG=testing
export FORCE_STD_XML=true

# Run tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=app --cov-report=html
```

### Production Configuration

```bash
export FLASK_CONFIG=production
export FORCE_STD_XML=true
export LOG_LEVEL=INFO

gunicorn -b :5000 \
  --workers 4 \
  --threads 2 \
  flasky:app
```

### Docker

The image is built from the repository `Dockerfile` (`python:3.13-slim`, installs
`requirements/docker.txt` into a virtualenv, runs as a non-root `flasky` user) and
starts through `boot.sh`, which binds gunicorn to port `5000`:

```bash
# Build
docker build -t model-transformer .

# Run (container listens on 5000)
docker run -p 5000:5000 -e FORCE_STD_XML=true model-transformer
```

`FLASK_APP=flasky.py` and `FLASK_CONFIG=production` are set inside the image.

---

## Testing

### Running Tests

All tests are located in the `tests/` directory, organized by module:

```
tests/
├── checkTokens/
│   ├── e2e/
│   └── unit/
├── health/
│   ├── e2e/
│   └── unit/
└── transform/
    ├── e2e/
    ├── unit/
    ├── assets/        # Test fixtures
    └── testgeneration/  # Test case generation
```

### Test Discovery

```bash
# Collect all tests
pytest tests/ --collect-only

# Run all tests
pytest tests/

# Run specific module
pytest tests/transform/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing

# Run via the Flask CLI command
flask --app flasky test          # Run all tests
flask --app flasky test --cov    # Run with coverage
```

### Test Coverage

The project uses pytest with coverage reporting:

```bash
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

---

## Logging

The application uses JSON-formatted structured logging via `python-json-logger`:

### Configuration

Logging is configured in `app/logging_config.py` with:
- JSON formatter for structured logging
- Request context filters (request_id, method, path)
- Metrics filter to exclude noisy `/metrics` endpoint

### Log Format

```json
{
  "asctime": "2026-02-07 12:00:00",
  "levelname": "INFO",
  "name": "app.api.routes",
  "message": "Transform request received",
  "request_id": "abc123def456",
  "http_method": "POST",
  "http_path": "/transform"
}
```

### Environment Variable

```bash
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR  # Default: INFO
```

---

## Metrics

Prometheus metrics are available at the `/metrics` endpoint:

### Available Metrics

- `http_requests_total{method, endpoint, status}` - Total HTTP requests
- `http_request_duration_seconds{method, endpoint}` - Request latency histogram
- `transform_duration_seconds` - Model transformation duration

### Scraping Metrics

```bash
curl http://localhost:5000/metrics
```

---

## Dependencies

### Core Dependencies

- **Flask 3.0.3** - Web framework
- **flask-cors** - CORS support
- **prometheus-client** - Metrics collection
- **python-json-logger** - Structured JSON logging
- **pydantic** / **pydantic_xml** - Data validation and XML (de)serialization
- **defusedxml** - Safe XML parsing
- **requests** - HTTP client
- **firebase_admin** - Used by the token-check integration

### Development Dependencies

- **pytest** - Testing framework
- **pytest-cov** - Coverage reporting
- **python-dotenv** - Environment variables

### See Also

See `requirements/` directory for complete dependency lists:
- `base.txt` - Core dependencies
- `dev.txt` - Development dependencies
- `test.txt` - Testing dependencies
- `prod.txt` - Production dependencies
- `docker.txt` - Docker image dependencies

---

## Troubleshooting

### ImportError: No module named 'flask'

Install dependencies:
```bash
pip install -r requirements/dev.txt
```

### MissingEnvironmentVariable: FORCE_STD_XML

Required environment variable not set:
```bash
export FORCE_STD_XML=true
```

### Test Collection Errors

Ensure all test directories have `__init__.py` files:
```bash
find tests -type d -exec touch {}/__init__.py \;
```

### CORS Errors

CORS is configured in `app/__init__.py` to allow all origins. If issues persist, check `config.py` CORS settings.

---

## Development Workflow

1. **Create a branch** for your feature
2. **Write tests** first (TDD approach)
3. **Implement changes** in `app/` modules
4. **Run tests** locally before pushing
5. **Update documentation** if needed
6. **Submit pull request** with clear description

### Running Tests Locally

```bash
# Set up environment
export FORCE_STD_XML=true
export FLASK_CONFIG=development

# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/transform/unit/test_transform.py::TestBPMNToPetriNet -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing
```

---

## Contributing

Please see [CONTRIBUTING.md](.github/CONTRIBUTING.md) for guidelines on:
- Code style
- Commit messages
- Pull request process
- Issue reporting

---

## Additional Resources

- [Project Wiki](https://github.com/Niyada/bpmn-pnml-transformer-poc/wiki)
- [API Documentation](https://woped.github.io/model-transformer/)
- [BPMN Specification](https://www.omg.org/spec/BPMN/)
- [Petri Net Documentation](https://en.wikipedia.org/wiki/Petri_net)

---

## License

See [LICENSE](license.md) for details.
