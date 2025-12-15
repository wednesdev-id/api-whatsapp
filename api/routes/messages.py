"""
Messages Routes
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator

from api.core.config import settings
from api.core.waha_client import WahaClient
from api.core.exceptions import WAHAException, WAHASessionException

router = APIRouter()


class MessageRequest(BaseModel):
    """Request model for getting messages"""
    chat_id: str
    limit: int = 100
    offset: int = 0
    sort_by: str = "timestamp"
    sort_order: str = "desc"
    session: str = "default"
    use_mock: bool = False

    @validator('chat_id')
    def validate_chat_id(cls, v):
        if not v.endswith('@c.us'):
            raise ValueError('Chat ID must end with @c.us')
        return v

    @validator('limit')
    def validate_limit(cls, v):
        if v <= 0 or v > settings.MAX_LIMIT:
            raise ValueError(f'Limit must be between 1 and {settings.MAX_LIMIT}')
        return v

    @validator('offset')
    def validate_offset(cls, v):
        if v < 0:
            raise ValueError('Offset must be non-negative')
        return v

    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed = ['timestamp', 'from', 'to', 'body']
        if v not in allowed:
            raise ValueError(f'Sort by must be one of: {", ".join(allowed)}')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('Sort order must be asc or desc')
        return v


@router.get("/messages", summary="Get Chat Messages")
async def get_chat_messages(
    request: Request,
    chat_id: str = Query(..., description="Chat ID (format: 628123456789@c.us)"),
    limit: int = Query(100, ge=1, le=settings.MAX_LIMIT, description="Number of messages to retrieve"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    sort_by: str = Query("timestamp", regex="^(timestamp|from|to|body)$", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    session: str = Query("default", description="WAHA session name"),
    use_mock: bool = Query(False, description="Use mock data for testing")
) -> Dict[str, Any]:
    """
    Retrieve messages from a specific WhatsApp chat

    - **chat_id**: WhatsApp chat ID in format 628123456789@c.us
    - **limit**: Number of messages to retrieve (max 1000)
    - **offset**: Pagination offset
    - **sort_by**: Field to sort messages by
    - **sort_order**: Sort direction (asc/desc)
    - **session**: WAHA session name
    - **use_mock**: Use mock data for testing
    """
    start_time = time.time()

    try:
        # Validate chat ID format
        if not chat_id.endswith('@c.us'):
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "Invalid chat ID format",
                    "code": "INVALID_CHAT_ID",
                    "details": {
                        "required_format": "628123456789@c.us",
                        "provided": chat_id
                    }
                }
            )

        logger.info(f"Getting messages for chat: {chat_id}, limit: {limit}, offset: {offset}")

        # Initialize WAHA client
        waha_client = WahaClient()

        # Get messages
        waha_response = await waha_client.get_chat_messages(
            chat_id=chat_id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            session=session,
            use_mock=use_mock
        )

        response_time = int((time.time() - start_time) * 1000)

        if not waha_response.success:
            # Handle specific WAHA errors
            error_code = waha_response.code
            if error_code == "SCAN_QR_REQUIRED":
                raise HTTPException(
                    status_code=422,
                    detail={
                        "success": False,
                        "error": "WhatsApp session needs QR code scan",
                        "code": "SCAN_QR_REQUIRED",
                        "details": {
                            "message": "Please scan QR code in WAHA dashboard",
                            "waha_url": f"{settings.WAHA_API_URL}/"
                        }
                    }
                )
            elif error_code == "SESSION_DISCONNECTED":
                raise HTTPException(
                    status_code=422,
                    detail={
                        "success": False,
                        "error": "WhatsApp session is disconnected",
                        "code": "SESSION_DISCONNECTED",
                        "details": {
                            "message": "Please reconnect WhatsApp session",
                            "session": session
                        }
                    }
                )
            else:
                raise HTTPException(
                    status_code=500 if not error_code else 503,
                    detail={
                        "success": False,
                        "error": waha_response.error or "Failed to retrieve messages",
                        "code": error_code or "MESSAGES_ERROR",
                        "metadata": {
                            "response_time_ms": response_time,
                            "timestamp": settings.get_current_time()
                        }
                    }
                )

        # Format successful response
        messages_data = waha_response.data
        messages = messages_data.get("messages", [])

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "chat_id": chat_id,
                    "messages": messages,
                    "pagination": messages_data.get("pagination", {
                        "limit": limit,
                        "offset": offset,
                        "has_more": len(messages) >= limit,
                        "page": (offset // limit) + 1,
                        "total_pages": (len(messages) + limit - 1) // limit
                    }),
                    "sorting": {
                        "sort_by": sort_by,
                        "sort_order": sort_order
                    },
                    "session": session,
                    "mock": messages_data.get("mock", False),
                    "total": len(messages)
                },
                "metadata": {
                    "response_time_ms": response_time,
                    "timestamp": settings.get_current_time(),
                    "request_id": getattr(request.state, "request_id", None)
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Internal server error",
                "code": "INTERNAL_ERROR",
                "details": {
                    "error": str(e)
                } if settings.DEBUG else None,
                "metadata": {
                    "response_time_ms": int((time.time() - start_time) * 1000),
                    "timestamp": settings.get_current_time(),
                    "request_id": getattr(request.state, "request_id", None)
                }
            }
        )


@router.get("/messages/mock", summary="Get Mock Messages")
async def get_mock_messages(
    request: Request,
    chat_id: str = Query(..., description="Chat ID"),
    limit: int = Query(100, ge=1, le=settings.MAX_LIMIT)
) -> Dict[str, Any]:
    """
    Get mock messages for testing purposes
    """
    start_time = time.time()

    try:
        waha_client = WahaClient()
        mock_data = waha_client._generate_mock_messages(chat_id, limit)

        response_time = int((time.time() - start_time) * 1000)

        return {
            "success": True,
            "data": {
                "chat_id": chat_id,
                "messages": mock_data["messages"],
                "total": mock_data["total"],
                "has_more": mock_data["has_more"],
                "mock": True,
                "generated_at": mock_data["generated_at"]
            },
            "metadata": {
                "response_time_ms": response_time,
                "timestamp": settings.get_current_time(),
                "request_id": getattr(request.state, "request_id", None)
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to generate mock messages",
                "code": "MOCK_GENERATION_ERROR",
                "details": {
                    "error": str(e)
                } if settings.DEBUG else None
            }
        )


@router.post("/messages", summary="Get Messages with POST")
async def get_messages_post(
    request: Request,
    message_request: MessageRequest
) -> Dict[str, Any]:
    """
    Get messages using POST method for complex queries
    """
    return await get_chat_messages(
        request=request,
        chat_id=message_request.chat_id,
        limit=message_request.limit,
        offset=message_request.offset,
        sort_by=message_request.sort_by,
        sort_order=message_request.sort_order,
        session=message_request.session,
        use_mock=message_request.use_mock
    )