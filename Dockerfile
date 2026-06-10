# syntax=docker/dockerfile:1.4
# Stage Monitoring Tool — Single-container build
# Usage:
#   docker build -t stage-app .
#   docker run -p 8080:8080 stage-app
#   docker run -p 8080:8080 -v stage-data:/app/data stage-app  (persist DB)

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Backend ──
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Pin bcrypt to avoid passlib incompatibility with bcrypt 5.0
RUN pip install --no-cache-dir 'bcrypt<5.0'

COPY backend/ ./backend/

# ── Frontend ──
COPY frontend/ ./frontend/

# ── Create a Docker-specific main that serves static files ──
COPY backend/docker_main.py backend/docker_main.py

# Environment defaults
ENV DATABASE_PATH=/app/data/stage_monitoring.db
ENV SECRET_KEY=docker-default-secret-key-change-me
ENV FRONTEND_ORIGINS=*
ENV PYTHONPATH=/app/backend

# Create data directory
RUN mkdir -p /app/data

# Create a non-root user and group
RUN useradd -u 1001 -U -m appuser

# Change ownership of the app directory to the non-root user
RUN chown -R appuser:appuser /app

# ── Entrypoint ──
COPY --chown=appuser:appuser docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Switch to non-root user
USER appuser

EXPOSE 8080

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uvicorn", "docker_main:app", "--host", "0.0.0.0", "--port", "8080"]

