"""Docker entrypoint: FastAPI app with static frontend files."""

import os
from app.main import app
from fastapi.staticfiles import StaticFiles

# Remove the root API route (/) so StaticFiles can serve index.html at root
app.router.routes = [
    r
    for r in app.router.routes
    if not (getattr(r, "path", None) == "/" and "GET" in getattr(r, "methods", set()))
]

frontend_dir = "/app/frontend"
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
