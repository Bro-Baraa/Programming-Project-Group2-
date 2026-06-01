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

# Patch frontend: use same-origin for API calls (Docker mode)
RUN <<'PYEOF'
python3 -c "
with open('frontend/api-client.js', 'r') as f:
    content = f.read()
old = '''const API_BASE_URL = (() => {
  // Use the same host as the frontend page, but port 8001
  // This works for localhost:8080 → localhost:8001
  // and for remote access: framearch-juan:8080 → framearch-juan:8001
  const host = window.location.hostname;
  return \`http://\${host}:8001\`;
})();'''
new = '''const API_BASE_URL = (() => {
  // In Docker: API and frontend share same origin
  return \`\${window.location.protocol}//\${window.location.host}\`;
})();'''
if old in content:
    content = content.replace(old, new)
    with open('frontend/api-client.js', 'w') as f:
        f.write(content)
    print('Frontend patched for Docker mode')
else:
    print('WARNING: could not patch frontend api-client.js')
"
PYEOF

# ── Create a Docker-specific main that serves static files ──
RUN cat > backend/docker_main.py << 'PYEOF'
"""Docker entrypoint: FastAPI app with static frontend files."""
import os
from app.main import app
from fastapi.staticfiles import StaticFiles
from starlette.routing import Mount

# Remove the root API route (/) so StaticFiles can serve index.html at root
# app.router.routes is the actual list; we filter out the root route
app.router.routes = [
    r for r in app.router.routes
    if not (getattr(r, 'path', None) == '/' and 'GET' in getattr(r, 'methods', set()))
]

frontend_dir = "/app/frontend"
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
PYEOF

# Environment defaults
ENV DATABASE_PATH=/app/data/stage_monitoring.db
ENV SECRET_KEY=docker-default-secret-key-change-me
ENV FRONTEND_ORIGINS=*
ENV PYTHONPATH=/app/backend

# Create data directory
RUN mkdir -p /app/data

# ── Entrypoint ──
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uvicorn", "docker_main:app", "--host", "0.0.0.0", "--port", "8080"]
