FROM python:3.12-slim

ENV APP_HOME=/app
WORKDIR ${APP_HOME}

# Set the environment variable FORCE_STD_XML
ENV FORCE_STD_XML=true

RUN mkdir -p /logs && \
    chmod 777 /logs

# Copying complete source code
COPY src/. ${APP_HOME}/src/.
# Copying the global requirements.txt
COPY requirements.txt global_requirements.txt

# installing all globally required dependencies
RUN pip install -r global_requirements.txt

ENV PYTHONPATH=${APP_HOME}/src/transform:${APP_HOME}/src/health

CMD ["python", "src/app.py"]
