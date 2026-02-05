FROM python:3.12-slim

ENV APP_HOME=/app
WORKDIR ${APP_HOME}

# Environment variables with defaults
# FORCE_STD_XML: Required for XML parsing
# LOG_LEVEL: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
ENV FORCE_STD_XML=true
ENV LOG_LEVEL=DEBUG

# Copying complete source code
COPY src/. ${APP_HOME}/src/.
# Copying the global requirements.txt
COPY requirements.txt global_requirements.txt

# Installing all globally required dependencies
RUN pip install -r global_requirements.txt

ENV PYTHONPATH=${APP_HOME}/src/transform:${APP_HOME}/src/health

CMD ["python", "src/app.py"]
