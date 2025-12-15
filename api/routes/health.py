"""
Health Check Routes
"""

import time
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse

from api.core.config import settings
from api.core.waha_client import WahaClient, WahaResponse
from api.core.exceptions import WAHAException

router = APIRouter()


@router.get("/health", summary="Health Check Endpoint")
async def health_check(request: Request) -> Dict[str, Any]:
    """
    Comprehensive health check for the WAHA FastAPI service

    Returns system status, WAHA API connection, and configuration details.
    """
    start_time = time.time()
    timestamp = settings.get_current_time()

    try:
        # Initialize WAHA client
        waha_client = WahaClient()

        # Test WAHA connection
        waha_response = await waha_client.test_connection()

        # Get environment variables check
        required_env_vars = ['WAHA_API_URL', 'WAHA_USERNAME', 'WAHA_PASSWORD', 'WAHA_API_KEY']
        missing_env_vars = [var for var in required_env_vars if not getattr(settings, var, None)]

        # Calculate response time
        response_time = int((time.time() - start_time) * 1000)

        # Determine overall health status
        is_healthy = (
            waha_response.success and
            len(missing_env_vars) == 0
        )

        health_data = {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": timestamp,
            "response_time_ms": response_time,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "services": {
                "waha_api": {
                    "status": "connected" if waha_response.success else "disconnected",
                    "url": settings.WAHA_API_URL,
                    "error": None if waha_response.success else waha_response.error,
                    "response_time_ms": response_time
                },
                "environment": {
                    "status": "configured" if len(missing_env_vars) == 0 else "misconfigured",
                    "missing": missing_env_vars,
                    "configured": [var for var in required_env_vars if getattr(settings, var, None)]
                }
            },
            "features": {
                "authentication": bool(settings.JWT_SECRET and settings.API_SECRET_KEY),
                "rate_limiting": settings.RATE_LIMIT_ENABLED,
                "auto_response": settings.AUTO_RESPONSE_ENABLED,
                "webhook": bool(settings.WEBHOOK_SECRET),
                "logging": True,
                "cache": settings.CACHE_ENABLED,
                "metrics": settings.METRICS_ENABLED
            },
            "endpoints": {
                "health": "/api/waba/health",
                "messages": "/api/waba/messages",
                "contacts": "/api/waba/contacts",
                "send": "/api/waba/send",
                "webhook": "/api/waba/webhook"
            },
            "metadata": {
                "request_id": getattr(request.state, "request_id", None),
                "user_agent": request.headers.get("user-agent"),
                "remote_addr": request.client.host if request.client else None
            }
        }

        # Set appropriate status code
        status_code = 200 if is_healthy else 503

        return JSONResponse(
            status_code=status_code,
            content={
                "success": is_healthy,
                "data": health_data,
                "message": "All systems operational" if is_healthy else "Some services are down"
            }
        )

    except WAHAException as e:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Health check failed",
                "code": "HEALTH_CHECK_FAILED",
                "details": {
                    "error": e.message,
                    "code": e.code
                } if settings.DEBUG else None,
                "timestamp": timestamp,
                "response_time_ms": int((time.time() - start_time) * 1000)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Health check failed",
                "code": "HEALTH_CHECK_ERROR",
                "details": {
                    "error": str(e)
                } if settings.DEBUG else None,
                "timestamp": timestamp,
                "response_time_ms": int((time.time() - start_time) * 1000)
            }
        )


@router.get("/health/waha", summary="WAHA API Health Check")
async def waha_health_check() -> Dict[str, Any]:
    """
    Specific health check for WAHA API connection only
    """
    try:
        waha_client = WahaClient()
        waha_response = await waha_client.test_connection()

        return {
            "success": True,
            "data": {
                "waha_api": {
                    "status": "connected" if waha_response.success else "disconnected",
                    "url": settings.WAHA_API_URL,
                    "response": waha_response.data if waha_response.success else None,
                    "error": waha_response.error if not waha_response.success else None,
                    "timestamp": settings.get_current_time()
                }
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "WAHA health check failed",
                "code": "WAHA_HEALTH_ERROR",
                "details": {
                    "error": str(e)
                } if settings.DEBUG else None
            }
        )


@router.get("/status", summary="Service Status")
async def service_status(request: Request) -> Dict[str, Any]:
    """
    Simple service status endpoint
    """
    return {
        "success": True,
        "data": {
            "status": "running",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": settings.get_current_time(),
            "uptime": time.time() - getattr(request.app.state, "start_time", time.time()),
            "request_id": getattr(request.state, "request_id", None)
        }
    }


@router.get("/ping", summary="Ping Endpoint")
async def ping() -> Dict[str, Any]:
    """
    Simple ping endpoint for connectivity testing
    """
    return {
        "success": True,
        "data": {
            "message": "pong",
            "timestamp": settings.get_current_time(),
            "service": settings.APP_NAME
        }
    }