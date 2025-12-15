"""
Send Message Routes
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, Depends, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from api.core.config import settings
from api.core.waha_client import WahaClient
from api.core.exceptions import WAHAException

router = APIRouter()


class SendMessageRequest(BaseModel):
    """Request model for sending messages"""
    chat_id: str = Field(..., description="Chat ID (format: 628123456789@c.us)")
    message: str = Field(..., min_length=1, max_length=4096, description="Message content")
    session: str = Field("default", description="WAHA session name")
    type: str = Field("text", regex="^(text|image|document|audio|video)$", description="Message type")
    media_url: Optional[str] = Field(None, description="Media URL for media messages")
    media_caption: Optional[str] = Field(None, max_length=1024, description="Media caption")

    @validator('chat_id')
    def validate_chat_id(cls, v):
        if not v.endswith('@c.us'):
            raise ValueError('Chat ID must end with @c.us')
        return v

    @validator('media_url')
    def validate_media_url(cls, v, values):
        if v is None:
            return v

        # Check if media type requires media URL
        message_type = values.get('type', 'text')
        if message_type != 'text' and not v:
            raise ValueError('Media URL is required for media messages')

        return v


class SendMessageResponse(BaseModel):
    """Response model for sent message"""
    message_id: str
    chat_id: str
    message: str
    type: str
    session: str
    status: str
    timestamp: str


@router.post("/send", summary="Send WhatsApp Message")
async def send_message(
    request: Request,
    message_request: SendMessageRequest = Body(...)
) -> Dict[str, Any]:
    """
    Send a message via WhatsApp using WAHA API

    - **chat_id**: WhatsApp chat ID in format 628123456789@c.us
    - **message**: Message content (max 4096 characters)
    - **session**: WAHA session name
    - **type**: Message type (text, image, document, audio, video)
    - **media_url**: URL for media files (required for non-text messages)
    - **media_caption**: Caption for media files
    """
    start_time = time.time()

    try:
        chat_id = message_request.chat_id
        message = message_request.message
        session = message_request.session
        message_type = message_request.type
        media_url = message_request.media_url
        media_caption = message_request.media_caption

        logger.info(f"Sending {message_type} message to chat: {chat_id}")

        # Check if auto-response is enabled
        auto_response_enabled = settings.AUTO_RESPONSE_ENABLED

        # Initialize WAHA client
        waha_client = WahaClient()

        # Validate media URL for media messages
        if message_type != 'text' and media_url:
            try:
                from urllib.parse import urlparse
                parsed_url = urlparse(media_url)
                if not parsed_url.scheme or not parsed_url.netloc:
                    raise ValueError("Invalid URL format")
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error": "Invalid media URL format",
                        "code": "INVALID_MEDIA_URL",
                        "details": {
                            "provided_url": media_url,
                            "required_format": "Valid URL (http:// or https://)"
                        }
                    }
                )

        # Send message
        waha_response = await waha_client.send_message(
            chat_id=chat_id,
            message=message,
            session=session,
            message_type=message_type,
            media_url=media_url,
            media_caption=media_caption
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
                        "error": waha_response.error or "Failed to send message",
                        "code": error_code or "SEND_MESSAGE_ERROR",
                        "metadata": {
                            "response_time_ms": response_time,
                            "timestamp": settings.get_current_time()
                        }
                    }
                )

        # Format successful response
        message_data = waha_response.data
        message_id = message_data.get("message_id", f"msg_{int(time.time())}_{chat_id}")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "message_id": message_id,
                    "chat_id": chat_id,
                    "message": message if message_type == 'text' else (media_caption or 'Media message'),
                    "type": message_type,
                    "session": session,
                    "status": "sent",
                    "timestamp": settings.get_current_time(),
                    "media": {
                        "url": media_url,
                        "caption": media_caption,
                        "type": message_type
                    } if message_type != 'text' else None,
                    "auto_response": {
                        "enabled": auto_response_enabled,
                        "delay_ms": settings.RESPONSE_DELAY_MS,
                        "scheduled": auto_response_enabled
                    }
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


@router.post("/send/batch", summary="Send Batch Messages")
async def send_batch_messages(
    request: Request,
    messages: list[SendMessageRequest] = Body(...)
) -> Dict[str, Any]:
    """
    Send multiple messages in batch

    - **messages**: List of message objects to send
    """
    start_time = time.time()
    results = []
    errors = []

    try:
        if len(messages) > 100:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "Batch size exceeds limit",
                    "code": "BATCH_SIZE_EXCEEDED",
                    "details": {
                        "max_batch_size": 100,
                        "provided_size": len(messages)
                    }
                }
            )

        logger.info(f"Sending batch of {len(messages)} messages")

        waha_client = WahaClient()

        for i, message_request in enumerate(messages):
            try:
                # Send individual message
                waha_response = await waha_client.send_message(
                    chat_id=message_request.chat_id,
                    message=message_request.message,
                    session=message_request.session,
                    message_type=message_request.type,
                    media_url=message_request.media_url,
                    media_caption=message_request.media_caption
                )

                if waha_response.success:
                    results.append({
                        "index": i,
                        "chat_id": message_request.chat_id,
                        "success": True,
                        "message_id": waha_response.data.get("message_id"),
                        "status": "sent"
                    })
                else:
                    errors.append({
                        "index": i,
                        "chat_id": message_request.chat_id,
                        "success": False,
                        "error": waha_response.error,
                        "code": waha_response.code
                    })

            except Exception as e:
                errors.append({
                    "index": i,
                    "chat_id": message_request.chat_id,
                    "success": False,
                    "error": str(e),
                    "code": "MESSAGE_SEND_ERROR"
                })

        response_time = int((time.time() - start_time) * 1000)

        return {
            "success": True,
            "data": {
                "batch_id": f"batch_{int(time.time())}",
                "total_messages": len(messages),
                "successful": len(results),
                "failed": len(errors),
                "results": results,
                "errors": errors,
                "success_rate": f"{(len(results) / len(messages) * 100):.1f}%" if messages else "0%"
            },
            "metadata": {
                "response_time_ms": response_time,
                "timestamp": settings.get_current_time(),
                "request_id": getattr(request.state, "request_id", None)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to send batch messages",
                "code": "BATCH_SEND_ERROR",
                "details": {
                    "error": str(e)
                } if settings.DEBUG else None
            }
        )


@router.post("/send/mock", summary="Mock Send Message")
async def send_mock_message(
    request: Request,
    message_request: SendMessageRequest = Body(...)
) -> Dict[str, Any]:
    """
    Mock send message for testing purposes (doesn't actually send)
    """
    start_time = time.time()

    try:
        response_time = int((time.time() - start_time) * 1000)
        message_id = f"mock_msg_{int(time.time())}_{message_request.chat_id}"

        return {
            "success": True,
            "data": {
                "message_id": message_id,
                "chat_id": message_request.chat_id,
                "message": message_request.message,
                "type": message_request.type,
                "session": message_request.session,
                "status": "mocked",
                "timestamp": settings.get_current_time(),
                "mock": True,
                "media": {
                    "url": message_request.media_url,
                    "caption": message_request.media_caption,
                    "type": message_request.type
                } if message_request.type != 'text' else None
            },
            "metadata": {
                "response_time_ms": response_time,
                "timestamp": settings.get_current_time(),
                "request_id": getattr(request.state, "request_id", None),
                "note": "This is a mock response - no message was actually sent"
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to create mock message",
                "code": "MOCK_SEND_ERROR",
                "details": {
                    "error": str(e)
                } if settings.DEBUG else None
            }
        )