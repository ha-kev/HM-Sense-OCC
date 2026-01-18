# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system app && adduser --system --ingroup app app

COPY services/model_consumer/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services ./services

ENV FEATURE_PRODUCER_FEATURE_ENDPOINT_BASE_URL=http://feature-producer:8000/api

USER app

EXPOSE 8002

CMD ["uvicorn", "services.model_consumer.app:app", "--host", "0.0.0.0", "--port", "8002"]
