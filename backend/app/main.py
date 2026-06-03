"""Stage Monitoring Tool API - FastAPI application."""
import os
import logging
import time
from collections import defaultdict
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
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
)

# Configure logging so app-level warnings/info are visible in uvicorn console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create database tables
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

# Simple in-memory rate limiter
_rate_limit = defaultdict(list)

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    path = request.url.path
    if path in ("/auth/login", "/auth/register", "/health"):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        _rate_limit[ip] = [t for t in _rate_limit[ip] if now - t < 60]
        if len(_rate_limit[ip]) > 10:
            return Response("Too many requests", status_code=429)
        _rate_limit[ip].append(now)
    return await call_next(request)


app.include_router(auth)
app.include_router(companies)
app.include_router(internships)
app.include_router(proposals)
app.include_router(agreements)
app.include_router(logbooks)
app.include_router(evaluations)
app.include_router(feedback)
app.include_router(reports)
app.include_router(competencies)
app.include_router(users)
app.include_router(me)


@app.get("/")
def root():
    return {
        "message": "Stage Monitoring Tool API",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/robots.txt", include_in_schema=False)
def robots():
    return Response("User-agent: *\nDisallow: /\n", media_type="text/plain")
