from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, internships, competencies, companies

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Stage Monitoring Tool API",
    description="Backend API for the internship/stage monitoring system for Erasmus Hogeschool Brussel",
    version="1.0.0"
)

# CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(internships.router)
app.include_router(competencies.router)


@app.get("/")
def root():
    return {
        "message": "Stage Monitoring Tool API",
        "docs": "/docs",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/auth",
            "companies": "/companies",
            "internships": "/internships",
            "competencies": "/competencies"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
