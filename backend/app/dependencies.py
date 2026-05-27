"""Shared FastAPI dependencies for pagination and common query params."""

from fastapi import Query
from typing import Optional, Annotated
from datetime import date


def pagination(
    skip: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=200, description="Max items per page (max 200)")] = 50,
):
    return {"skip": skip, "limit": limit}


def date_range_filter(
    date_from: Annotated[Optional[date], Query(description="Filter from this date (inclusive)")] = None,
    date_to: Annotated[Optional[date], Query(description="Filter to this date (inclusive)")] = None,
):
    return {"date_from": date_from, "date_to": date_to}


def search_query(
    q: Annotated[Optional[str], Query(min_length=1, max_length=100, description="Search keyword")] = None,
):
    return q