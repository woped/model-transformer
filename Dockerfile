FROM python:3.12-slim

ENV APP_HOME=/app
WORKDIR ${APP_HOME}

# Set the environment variable FORCE_STD_XML
ENV FORCE_STD_XML=true
ENV APP_ENV=production

# Copying complete source code
COPY . ${APP_HOME}/
# Copying requirements
COPY requirements/ ${APP_HOME}/requirements/

# installing all production dependencies
RUN pip install -r requirements/docker.txt

ENV PYTHONPATH=${APP_HOME}

# Make boot script executable
RUN chmod +x ${APP_HOME}/boot.sh

# Run the application with gunicorn
CMD ["./boot.sh"]
