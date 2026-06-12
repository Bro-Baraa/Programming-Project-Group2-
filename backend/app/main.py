"""Stage Monitoring Tool API - FastAPI application."""

import os
import logging
import time
from collections import defaultdict
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.routers import (
    auth,
    companies,
    internships,
    proposals,
    agreements,
    logbooks,
    evaluations,
    feedback,
    reports,
    competencies,
    users,
    me,
    notifications,
    audit,
)

# Configure logging so app-level warnings/info are visible in uvicorn console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create database tables only if they don't exist (skip on startup for speed)
from sqlalchemy import inspect

inspector = inspect(engine)
if not inspector.get_table_names():
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Stage Monitoring Tool API",
    description="Backend API for the internship/stage monitoring system for Erasmus Hogeschool Brussel",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# CORS for frontend communication
# FRONTEND_ORIGINS env var: comma-separated list, e.g. "http://localhost:8080,http://framearch-juan:8080"
# Default "*" allows any origin (development only — no credentials, since JWT is in header)
_origins = os.getenv("FRONTEND_ORIGINS", "*")
if _origins == "*":
    allow_origins = ["*"]
    allow_credentials = False
else:
    allow_origins = [o.strip() for o in _origins.split(",") if o.strip()]
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# Simple in-memory rate limiter with hard cap to prevent memory leaks
_MAX_RATE_LIMIT_IPS = 10_000
_rate_limit: dict[str, list] = defaultdict(list)
_last_cleanup = time.time()


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    global _last_cleanup
    path = request.url.path
    if path in ("/api/auth/login", "/api/auth/register", "/api/health"):
        ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Hard cap: evict oldest entries if dict exceeds max size
        if len(_rate_limit) > _MAX_RATE_LIMIT_IPS:
            oldest_keys = sorted(
                _rate_limit.keys(),
                key=lambda k: max(_rate_limit[k]) if _rate_limit[k] else 0,
            )[: _MAX_RATE_LIMIT_IPS // 10]
            for k in oldest_keys:
                del _rate_limit[k]

        # Cleanup verlopen entries elke 5 minuten
        if now - _last_cleanup > 300:
            cutoff = now - 60
            stale = [
                k for k, v in _rate_limit.items() if not [t for t in v if t > cutoff]
            ]
            for k in stale:
                del _rate_limit[k]
            _last_cleanup = now

        _rate_limit[ip] = [t for t in _rate_limit[ip] if now - t < 60]
        if len(_rate_limit[ip]) >= 10:
            return Response("Too many requests", status_code=429)
        _rate_limit[ip].append(now)
    return await call_next(request)


app.include_router(auth, prefix="/api")
app.include_router(companies, prefix="/api")
app.include_router(internships, prefix="/api")
app.include_router(proposals, prefix="/api")
app.include_router(agreements, prefix="/api")
app.include_router(logbooks, prefix="/api")
app.include_router(evaluations, prefix="/api")
app.include_router(feedback, prefix="/api")
app.include_router(reports, prefix="/api")
app.include_router(competencies, prefix="/api")
app.include_router(users, prefix="/api")
app.include_router(notifications, prefix="/api")
app.include_router(me, prefix="/api")
app.include_router(audit, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


@app.get("/robots.txt", include_in_schema=False)
def robots():
    return Response("User-agent: *\nDisallow: /\n", media_type="text/plain")


# ── Static files (frontend) — serveer alleen als frontend dir bestaat ──
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.isdir(_frontend_dir):

    class _CachedStaticFiles(StaticFiles):
        async def get_response(self, path, scope):
            response = await super().get_response(path, scope)
            if response.status_code == 200:
                response.headers["Cache-Control"] = "public, max-age=3600"
            return response

    # Fallback: serveer frontend voor alle niet-API routes
    app.mount(
        "/", _CachedStaticFiles(directory=_frontend_dir, html=True), name="frontend"
    )
