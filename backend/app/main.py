"""Stage Monitoring Tool API - FastAPI application."""
from fastapi import FastAPI
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

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Stage Monitoring Tool API",
    description="Backend API for the internship/stage monitoring system for Erasmus Hogeschool Brussel",
    version="1.0.0",
)

# CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
