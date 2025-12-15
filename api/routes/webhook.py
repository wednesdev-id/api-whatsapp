"""
Webhook Routes
"""

import time
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException, Depends, Query, Body, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from api.core.config import settings
from api.core.waha_client import WahaClient
from api.core.exceptions import WAHAException

router = APIRouter()


class WebhookMessageData(BaseModel):
    """Webhook message data model"""
    id: str
    from: str
    to: str
    body: str
    timestamp: int
    fromMe: bool
    hasMedia: bool = False
    mediaType: Optional[str] = None
    mediaCaption: Optional[str] = None
    ack: Optional[int] = None


class WebhookEvent(BaseModel):
    """Webhook event model"""
    event: str = Field(..., regex="^(message|messageAck|sessionStatus|qrCode|disconnected)$")
    session: str = "default"
    data: WebhookMessageData

    @validator('data')
    def validate_data_for_event(cls, v, values):
        event = values.get('event')
        if event == 'message' and not isinstance(v, dict):
            raise ValueError('Message event requires valid message data')
        return v


class WebhookVerifyRequest(BaseModel):
    """Webhook verification request"""
    mode: str = "subscribe"
    challenge: str
    verify_token: str


@router.get("/webhook", summary="Webhook Verification")
async def webhook_verify(
    request: Request,
    mode: str = Query(None),
    challenge: str = Query(None),
    verify_token: str = Query(None)
) -> JSONResponse:
    """
    Handle webhook verification (GET request)

    Used for initial webhook setup with WAHA
    """
    try:
        logger.info(f"Webhook verification request: mode={mode}")

        if mode == "subscribe" and verify_token == settings.WEBHOOK_VERIFY_TOKEN:
            logger.info("Webhook verification successful")
            return JSONResponse(
                status_code=200,
                content=challenge
            )

        raise HTTPException(
            status_code=403,
            detail={
                "success": False,
                "error": "Webhook verification failed",
                "code": "WEBHOOK_VERIFICATION_FAILED",
                "details": {
                    "mode": mode,
                    "expected_token": settings.WEBHOOK_VERIFY_TOKEN,
                    "received_token": verify_token
                } if settings.DEBUG else None
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Webhook verification error",
                "code": "WEBHOOK_VERIFY_ERROR",
                "details": {
                    "error": str(e)
                } if settings.DEBUG else None
            }
        )


@router.post("/webhook", summary="Handle Webhook Events")
async def webhook_handler(
    request: Request,
    x_waha_signature: Optional[str] = Header(None, description="WAHA signature for security"),
    webhook_event: WebhookEvent = Body(...)
) -> Dict[str, Any]:
    """
    Handle incoming webhook events from WAHA

    Processes different types of webhook events:
    - message: New incoming message
    - messageAck: Message acknowledgment
    - sessionStatus: Session status change
    - qrCode: QR code available
    - disconnected: Session disconnected
    """
    start_time = time.time()

    try:
        event_type = webhook_event.event
        session = webhook_event.session
        event_data = webhook_event.data

        logger.info(f"Processing webhook event: {event_type} for session: {session}")

        # Verify webhook signature if configured
        if settings.WEBHOOK_SECRET and x_waha_signature:
            if not _verify_webhook_signature(
                await request.body(),
                x_waha_signature,
                settings.WEBHOOK_SECRET
            ):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "success": False,
                        "error": "Invalid webhook signature",
                        "code": "INVALID_WEBHOOK_SIGNATURE"
                    }
                )

        # Process different event types
        response_data = None

        if event_type == "message":
            response_data = await _handle_message_event(session, event_data)
        elif event_type == "messageAck":
            response_data = await _handle_message_ack_event(session, event_data)
        elif event_type == "sessionStatus":
            response_data = await _handle_session_status_event(session, event_data)
        elif event_type == "qrCode":
            response_data = await _handle_qr_code_event(session, event_data)
        elif event_type == "disconnected":
            response_data = await _handle_disconnected_event(session, event_data)
        else:
            logger.warning(f"Unknown webhook event: {event_type}")
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "Unknown webhook event",
                    "code": "UNKNOWN_EVENT",
                    "details": {
                        "event": event_type,
                        "supported_events": ["message", "messageAck", "sessionStatus", "qrCode", "disconnected"]
                    }
                }
            )

        response_time = int((time.time() - start_time) * 1000)

        # Log successful processing
        logger.info(f"Webhook event {event_type} processed successfully in {response_time}ms")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "event": event_type,
                    "session": session,
                    "processed": True,
                    "response": response_data,
                    "timestamp": settings.get_current_time()
                },
                "metadata": {
                    "response_time_ms": response_time,
                    "request_id": getattr(request.state, "request_id", None),
                    "signature_verified": bool(settings.WEBHOOK_SECRET and x_waha_signature)
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        # Always return 200 for webhooks to prevent retries from WAHA
        # but include error details in the response
        response_time = int((time.time() - start_time) * 1000)

        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "error": "Webhook processing failed",
                "code": "WEBHOOK_PROCESSING_ERROR",
                "details": {
                    "error": str(e)
                } if settings.DEBUG else None
            },
            metadata={
                "response_time_ms": response_time,
                "timestamp": settings.get_current_time(),
                "request_id": getattr(request.state, "request_id", None)
            }
        )


async def _handle_message_event(session: str, data: WebhookMessageData) -> Dict[str, Any]:
    """Handle incoming message events"""
    message_id = data.id
    from_chat = data.from
    to_chat = data.to
    body = data.body
    timestamp = data.timestamp
    from_me = data.fromMe

    logger.info(f"New message: {from_chat} -> {to_chat} ({'from me' if from_me else 'to me'})")

    # Only process messages from others (not our own messages)
    if from_me:
        return {
            "action": "ignored",
            "reason": "own_message",
            "message_id": message_id
        }

    # Check if auto-response is enabled
    if settings.AUTO_RESPONSE_ENABLED:
        try:
            # Get auto-response based on message content
            auto_response = _get_auto_response(body, from_chat)

            if auto_response:
                # Schedule auto-response with delay
                delay = settings.RESPONSE_DELAY_MS

                # In production, you'd use a task queue like Celery
                # For now, we'll simulate with a comment
                logger.info(f"Auto-response scheduled for {from_chat}: {auto_response}")

                # Send response immediately (in production, add delay)
                waha_client = WahaClient()
                send_response = await waha_client.send_message(
                    chat_id=from_chat,
                    message=auto_response,
                    session=session
                )

                if send_response.success:
                    logger.info(f"Auto-response sent to {from_chat}")
                    return {
                        "action": "auto_response_sent",
                        "message": auto_response,
                        "message_id": send_response.data.get("message_id"),
                        "delay_ms": delay
                    }
                else:
                    logger.warn(f"Failed to send auto-response to {from_chat}")
                    return {
                        "action": "auto_response_failed",
                        "error": send_response.error
                    }

        except Exception as e:
            logger.error(f"Error processing auto-response: {str(e)}")
            return {
                "action": "auto_response_error",
                "error": str(e)
            }

    # Store message for analytics (in production, use database)
    _store_message_analytics({
        "message_id": message_id,
        "from": from_chat,
        "to": to_chat,
        "body": body,
        "timestamp": timestamp,
        "from_me": from_me,
        "has_media": data.hasMedia,
        "media_type": data.mediaType,
        "session": session,
        "processed_at": settings.get_current_time()
    })

    return {
        "action": "processed",
        "type": "message_logged"
    }


async def _handle_message_ack_event(session: str, data: WebhookMessageData) -> Dict[str, Any]:
    """Handle message acknowledgment events"""
    message_id = data.id
    ack = data.ack

    logger.info(f"Message acknowledgment: {message_id} - ack: {ack}")

    # Update message status in database (in production)
    _update_message_status(message_id, ack)

    return {
        "action": "acknowledgment_processed",
        "message_id": message_id,
        "status": _convert_ack_status(ack)
    }


async def _handle_session_status_event(session: str, data: WebhookMessageData) -> Dict[str, Any]:
    """Handle session status events"""
    status = data.body  # Status is often in body field for session events

    logger.info(f"Session status changed: {session} - {status}")

    # Update session status in database (in production)
    _update_session_status(session, status)

    # Send notification for important status changes
    if status in ['DISCONNECTED', 'CONFLICT']:
        await _send_session_alert(session, status)

    return {
        "action": "status_updated",
        "session": session,
        "status": status
    }


async def _handle_qr_code_event(session: str, data: WebhookMessageData) -> Dict[str, Any]:
    """Handle QR code events"""
    qr_code = data.body  # QR code is often in body field

    logger.info(f"QR code received for session: {session}")

    # Store QR code for scanning (in production, use secure storage)
    _store_qr_code(session, qr_code)

    return {
        "action": "qr_code_received",
        "session": session,
        "qr_available": True
    }


async def _handle_disconnected_event(session: str, data: WebhookMessageData) -> Dict[str, Any]:
    """Handle disconnection events"""
    logger.info(f"Session disconnected: {session}")

    # Clean up session data
    _cleanup_session_data(session)

    return {
        "action": "disconnection_handled",
        "session": session
    }


def _verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature"""
    if not signature.startswith("sha256="):
        return False

    signature_hash = signature.split("=")[1]
    expected_hash = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature_hash, expected_hash)


def _get_auto_response(incoming_message: str, chat_id: str) -> Optional[str]:
    """Get auto-response based on message content"""
    message = incoming_message.lower()

    # Basic keyword-based auto-responses
    responses = {
        "greeting": ["hello", "hi", "halo", "hai", "assalamualaikum", "selamat pagi", "selamat siang", "selamat sore", "selamat malam"],
        "thanks": ["thank", "thanks", "terima kasih", "makasih"],
        "goodbye": ["bye", "goodbye", "selamat tinggal", "sampai jumpa"],
        "help": ["help", "bantuan", "tolong"],
        "status": ["status", "how are you", "apa kabar"],
        "business": ["price", "harga", "produk", "layanan", "booking"],
        "location": ["lokasi", "alamat", "dimana", "address"],
        "contact": ["contact", "kontak", "hubungi", "telp", "phone"]
    }

    # Check for keywords and return appropriate response
    for category, keywords in responses.items():
        if any(keyword in message for keyword in keywords):
            return _get_response_template(category)

    # Return default response if no keywords matched
    return _get_response_template("default")


def _get_response_template(category: str) -> str:
    """Get response template for category"""
    templates = {
        "greeting": "Halo! Selamat datang di layanan kami. Ada yang bisa kami bantu? 🙏",
        "thanks": "Sama-sama! Senang bisa membantu Anda. 😊",
        "goodbye": "Sampai jumpa! Semoga harimu menyenangkan. 👋",
        "help": "Kami siap membantu! Silakan jelaskan kebutuhan Anda.",
        "status": "Kami baik-baik saja! Bagaimana dengan Anda? 😊",
        "business": "Untuk informasi harga dan layanan, silakan hubungi tim sales kami.",
        "location": "Kantor kami berlokasi di Jl. Contoh No. 123, Jakarta. 📍",
        "contact": "Hubungi kami di: 📞 021-1234567 atau 📱 wa.me/628123456789",
        "default": "Terima kasih atas pesan Anda. Kami akan segera merespons."
    }

    return templates.get(category, templates["default"])


def _convert_ack_status(ack: int) -> str:
    """Convert WhatsApp acknowledgment status to readable format"""
    ack_map = {
        0: "pending",
        1: "sent",
        2: "received",
        3: "read",
        4: "played"
    }

    return ack_map.get(ack, "unknown")


def _store_message_analytics(message_data: dict):
    """Store message analytics (in production, use database)"""
    logger.debug(f"Storing message analytics: {message_data}")


def _update_message_status(message_id: str, ack: int):
    """Update message status in database"""
    logger.debug(f"Updating message {message_id} status to {_convert_ack_status(ack)}")


def _update_session_status(session: str, status: str):
    """Update session status in database"""
    logger.debug(f"Updating session {session} status to {status}")


async def _send_session_alert(session: str, status: str):
    """Send session alert to administrators"""
    logger.warning(f"Session alert: {session} is {status}")


def _store_qr_code(session: str, qr_code: str):
    """Store QR code securely"""
    logger.debug(f"Storing QR code for session {session}")


def _cleanup_session_data(session: str):
    """Clean up session-related data"""
    logger.debug(f"Cleaning up data for session {session}")


@router.get("/webhook/info", summary="Get Webhook Information")
async def webhook_info() -> Dict[str, Any]:
    """
    Get information about webhook configuration
    """
    return {
        "success": True,
        "data": {
            "webhook_url": f"{request.base_url}/webhook",
            "events": ["message", "messageAck", "sessionStatus", "qrCode", "disconnected"],
            "security": {
                "signature_enabled": bool(settings.WEBHOOK_SECRET),
                "verification_token": settings.WEBHOOK_VERIFY_TOKEN
            },
            "auto_response": {
                "enabled": settings.AUTO_RESPONSE_ENABLED,
                "delay_ms": settings.RESPONSE_DELAY_MS
            }
        }
    }