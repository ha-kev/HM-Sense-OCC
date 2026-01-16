# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system-level dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better layer caching
COPY services/feature_producer/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the services package (and any shared resources)
COPY services ./services

EXPOSE 8000

CMD ["uvicorn", "services.feature_producer.app:app", "--host", "0.0.0.0", "--port", "8000"]
