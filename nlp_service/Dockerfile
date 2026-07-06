FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Phase 3.8: nlp_service 改为 HTTP 透传到主后端，默认 http://web:5000
# docker-compose 会通过 environment 覆盖此值
ENV NLP_BACKEND_URL=http://web:5000 \
    NLP_BACKEND_TIMEOUT=20

# Run Celery worker by default
CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info"]
