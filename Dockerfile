# syntax=docker/dockerfile:1

# Lightweight Python base
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    WORKERS=2 \
    PYTHONPATH=/app/backend

WORKDIR /app

# System deps required to build uvicorn[standard] optional speedups (uvloop, httptools)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       python3-tk tk tcl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first (better layer caching)
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy app source
COPY backend ./backend

# Expose the HTTP port (informational)
EXPOSE 8000

# Do not bake secrets (.env) into the image; configure env vars in Azure App Service

# Start the API using uvicorn CLI so we can scale workers without code changes
# App Service for Containers sets PORT; default to 8000 for local use
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WORKERS:-2}"]
