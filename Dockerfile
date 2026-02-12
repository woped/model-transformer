# Use an official Python runtime as a base image
FROM python:3.13-slim

ENV FLASK_APP=flasky.py \
    FLASK_CONFIG=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN useradd -m -u 1000 flasky

WORKDIR /home/flasky

# Requirements kopieren + installieren (als root)
COPY --chown=flasky:flasky requirements requirements
RUN apt-get update
RUN apt-get install -y --no-install-recommends \
        gcc \
        libc6-dev \
        libffi-dev \
        cargo \
        rustc
RUN python -m venv .venv
RUN .venv/bin/pip install --upgrade pip
RUN .venv/bin/pip install -r requirements/docker.txt
RUN apt-get purge -y --auto-remove \
        gcc \
        libc6-dev \
        libffi-dev \
        cargo \
        rustc
RUN rm -rf /var/lib/apt/lists/*

# App-Dateien kopieren (mit Ownership direkt setzen)
COPY --chown=flasky:flasky app app
COPY --chown=flasky:flasky flasky.py config.py boot.sh ./

# Fix line endings and set permissions
RUN sed -i 's/\r$//' boot.sh && chmod +x boot.sh
USER flasky

# run-time configuration
EXPOSE 5000
ENTRYPOINT ["./boot.sh"]