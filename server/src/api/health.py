import time
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlmodel import text
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.dependencies.session import get_session
from src.config.celery import celery_app
from src.core.cache_manager import cache_manager

router = APIRouter(tags=["Health"])


class HealthCheck(BaseModel):
    status: str
    timestamp: str
    checks: Optional[Dict[str, Any]] = None


async def check_redis() -> Dict[str, Any]:
    """Check Redis cache connectivity"""
    try:
        start = time.time()
        await cache_manager.ping()
        response_time = (time.time() - start) * 1000
        return {"status": "healthy", "response_time_ms": round(response_time, 2)}
    except Exception as e:
        return {"status": "unhealthy", "response_time_ms": 0, "error": str(e)}


async def check_database(session: AsyncSession) -> Dict[str, Any]:
    """Check database connectivity"""
    try:
        start = time.time()
        await session.execute(text("SELECT 1"))
        response_time = (time.time() - start) * 1000
        return {"status": "healthy", "response_time_ms": round(response_time, 2)}
    except Exception as e:
        return {"status": "unhealthy", "response_time_ms": 0, "error": str(e)}


async def check_celery() -> Dict[str, Any]:
    """Check Celery worker connectivity"""
    try:
        start = time.time()
        celery_app.control.inspect().active()  # ping active workers
        response_time = (time.time() - start) * 1000
        return {"status": "healthy", "response_time_ms": round(response_time, 2)}
    except Exception as e:
        return {"status": "unhealthy", "response_time_ms": 0, "error": str(e)}


@router.head("/health/server")
async def health_server():
    """Server health check (lightweight)"""
    return Response(status_code=200)


@router.head("/health/redis")
async def health_redis():
    """Redis cache health check"""
    result = await check_redis()
    status_code = 200 if result["status"] == "healthy" else 503
    return Response(status_code=status_code)


@router.head("/health/db")
async def health_db(session: AsyncSession = Depends(get_session)):
    """Database health check"""
    result = await check_database(session)
    status_code = 200 if result["status"] == "healthy" else 503
    return Response(status_code=status_code)


@router.head("/health/celery")
async def health_celery():
    """Celery worker health check"""
    result = await check_celery()
    status_code = 200 if result["status"] == "healthy" else 503
    return Response(status_code=status_code)


@router.get("/health", response_model=HealthCheck)
async def health_full(session: AsyncSession = Depends(get_session)):
    """Full health check with detailed response"""
    redis_check = await check_redis()
    db_check = await check_database(session)
    celery_check = await check_celery()

    # Determine overall status
    overall_status = "healthy"
    checks_list = [redis_check["status"], db_check["status"], celery_check["status"]]

    if "unhealthy" in checks_list:
        overall_status = "unhealthy"
    elif "degraded" in checks_list or checks_list.count("unhealthy") == 1:
        overall_status = "degraded"

    health = HealthCheck(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        checks={
            "server": {"status": "healthy", "response_time_ms": 0},
            "redis": redis_check,
            "database": db_check,
            "celery": celery_check,
        },
    )

    return health
