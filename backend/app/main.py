import os
import time
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect
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

inspector = inspect(engine)
if not inspector.get_table_names():
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Stage Monitoring Tool API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

_origins = os.getenv("FRONTEND_ORIGINS", "*")
allow_origins = (
    ["*"] if _origins == "*" else [o.strip() for o in _origins.split(",") if o.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=_origins != "*",
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,
)

_rate_limit = {}


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    path = request.url.path
    if path in ("/api/auth/login", "/api/auth/register", "/api/health"):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        _rate_limit[ip] = [t for t in _rate_limit.get(ip, []) if now - t < 60]
        if len(_rate_limit[ip]) >= 10:
            return Response("Too many requests", status_code=429)
        _rate_limit[ip].append(now)
    return await call_next(request)


for router in (
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
):
    app.include_router(router, prefix="/api")


@app.on_event("shutdown")
def shutdown_event():
    engine.dispose()


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


@app.get("/robots.txt", include_in_schema=False)
def robots():
    return Response("User-agent: *\nDisallow: /\n", media_type="text/plain")


_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
