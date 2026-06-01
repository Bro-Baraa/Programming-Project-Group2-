"""Stage Monitoring Tool API - FastAPI application."""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base

# Configure logging so app-level warnings/info are visible in uvicorn console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

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

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Stage Monitoring Tool API",
    description="Backend API for the internship/stage monitoring system for Erasmus Hogeschool Brussel",
    version="1.0.0",
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
        "docs": "/docs",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
