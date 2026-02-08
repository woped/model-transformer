# PNML-BPMN-TRANSFORMER

A simple FaaS-API application designed to convert Business Processes in BPMN notation to PNML and vice versa. 

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

# Run development server
flask run
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
   flask run
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

```bash
gunicorn wsgi:app
```

---

## Project Setup

After cloning this repository, it's essential to [set up git hooks](https://github.com/woped/woped-git-hooks/blob/main/README.md#activating-git-hooks-after-cloning-a-repository) to ensure project standards.

---

## Architecture Overview

### Project Structure

```
model-transformer/
├── config.py                    # Root-level configuration
├── wsgi.py                      # WSGI entry point
├── app/
│   ├── __init__.py             # Application factory (create_app)
│   ├── logging_config.py       # JSON logging configuration
│   ├── api/
│   │   ├── __init__.py         # API blueprint definition
│   │   └── routes.py           # Consolidated API routes
│   ├── model_transformer/
│   │   ├── __init__.py
│   │   └── metrics.py          # Prometheus metrics
│   ├── health/                 # Health check logic
│   ├── transform/              # Model transformation logic
│   ├── checkTokens/            # Token validation logic
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

Centralized configuration management with environment-based loading:

```python
class Config:
    """Base configuration"""
    ENV_NAME = "default"
    DEBUG = False
    TESTING = False
    LOG_LEVEL = "INFO"

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True

class ProductionConfig(Config):
    pass

def get_config(config_name=None):
    """Get config class by name, auto-detects from environment variables"""
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

#### Entry Points

**`wsgi.py`** - Main entry point for WSGI servers and CLI:
```python
app = create_app()

@app.cli.command("test")
@click.option('--cov', is_flag=True, help="Show test coverage report.")
def test_command(cov):
    """Run all tests in the 'tests/' directory."""
```

**`app/__init__.py`** - Contains `create_app()` factory function

---

## API Endpoints

### GET `/health`
Health check endpoint for monitoring application status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-07T12:00:00Z"
}
```

### POST `/transform`
Transform models between BPMN and PNML formats.

**Request Body:**
```json
{
  "data": "...",
  "format": "bpmn|pnml"
}
```

**Response:**
The transformed model in the requested format.

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

flask run --reload
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

gunicorn wsgi:app \
  --workers 4 \
  --threads 2 \
  --bind 0.0.0.0:8080
```

### Docker Configuration

```dockerfile
FROM python:3.13

WORKDIR /app

COPY requirements/docker.txt .
RUN pip install -r docker.txt

COPY . .

ENV FORCE_STD_XML=true
ENV FLASK_CONFIG=production

CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:8080"]
```

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

# Run via CLI command
python wsgi.py test              # Run all tests
python wsgi.py test --cov        # Run with coverage
```

### Test Coverage

The project uses pytest with coverage reporting:

```bash
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

---

## Recent Refactoring (February 2026)

### What Changed

The Flask application has been refactored to follow the well-structured pattern used in reference projects (`t2p-2.0` and `t2p-llm-api-connector`):

1. **Application Factory Pattern**
   - Single `create_app()` function in `app/__init__.py`
   - Centralized Flask configuration and initialization
   - Enables easy testing with different configurations

2. **Root-Level Configuration**
   - `config.py` contains all configuration classes
   - Environment-based configuration resolution
   - Supports multiple deployment environments

3. **Unified API Blueprint**
   - All routes in `app/api/` package
   - Single `routes.py` file with all endpoints
   - Cleaner, more maintainable structure

4. **Test Consolidation**
   - All tests moved to `tests/` directory at project root
   - Tests organized by module (checkTokens, health, transform)
   - Proper Python package structure with `__init__.py` files

5. **Entry Point Simplification**
   - `wsgi.py` is main entry point (removed redundant `app/app.py`)
   - Cleaner WSGI configuration
   - CLI test commands available

### Before vs After

| Aspect | Before | After |
|--------|--------|-------|
| Configuration | Scattered across modules | Centralized in `config.py` |
| Factory Logic | In `app/model_transformer/__init__.py` | In `app/__init__.py` |
| Routes | Multiple files in `app/model_transformer/routes/` | Single blueprint in `app/api/routes.py` |
| Tests | Distributed in each module | Consolidated in `tests/` directory |
| Entry Point | `wsgi.py` → `app/app.py` → factory | Direct `wsgi.py` → factory |

### Verification

The refactored structure has been verified:
- ✅ Application loads successfully
- ✅ All 3 API routes registered
- ✅ 22 unit and integration tests pass
- ✅ Prometheus metrics working
- ✅ Backward compatibility maintained

### Benefits

- **Consistency**: Matches proven patterns from reference projects
- **Maintainability**: Centralized configuration and clear module organization
- **Testability**: Factory pattern enables comprehensive testing
- **Scalability**: Blueprint structure easy to extend
- **Code Quality**: Better separation of concerns

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

- **Flask 3.0+** - Web framework
- **flask-cors** - CORS support
- **prometheus-client** - Metrics collection
- **python-json-logger** - Structured JSON logging
- **pydantic** - Data validation
- **lxml** - XML processing
- **requests** - HTTP client

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

---

*Last Updated: February 7, 2026*
