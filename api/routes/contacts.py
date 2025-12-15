"""
Contacts Routes
"""

import time
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator

from api.core.config import settings
from api.core.waha_client import WahaClient
from api.core.exceptions import WAHAException, WAHASessionException

router = APIRouter()


class ContactRequest(BaseModel):
    """Request model for getting contacts"""
    limit: int = 100
    offset: int = 0
    sort_by: str = "name"
    sort_order: str = "asc"
    session: str = "default"
    use_mock: bool = False

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
        allowed = ['name', 'id', 'notifyName', 'pushname', 'lastMessage', 'unreadCount', 'lastMessageTime']
        if v not in allowed:
            raise ValueError(f'Sort by must be one of: {", ".join(allowed)}')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('Sort order must be asc or desc')
        return v


@router.get("/contacts", summary="Get WhatsApp Contacts")
async def get_contacts(
    request: Request,
    limit: int = Query(100, ge=1, le=settings.MAX_LIMIT, description="Number of contacts to retrieve"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    sort_by: str = Query("name", regex="^(name|id|notifyName|pushname|lastMessage|unreadCount|lastMessageTime)$", description="Field to sort by"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    session: str = Query("default", description="WAHA session name"),
    use_mock: bool = Query(False, description="Use mock data for testing")
) -> Dict[str, Any]:
    """
    Retrieve WhatsApp contacts from WAHA API

    - **limit**: Number of contacts to retrieve (max 1000)
    - **offset**: Pagination offset
    - **sort_by**: Field to sort contacts by
    - **sort_order**: Sort direction (asc/desc)
    - **session**: WAHA session name
    - **use_mock**: Use mock data for testing
    """
    start_time = time.time()

    try:
        logger.info(f"Getting contacts - limit: {limit}, offset: {offset}, sort_by: {sort_by}")

        # Initialize WAHA client
        waha_client = WahaClient()

        # Get contacts
        waha_response = await waha_client.get_all_contacts(
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
                        "error": waha_response.error or "Failed to retrieve contacts",
                        "code": error_code or "CONTACTS_ERROR",
                        "metadata": {
                            "response_time_ms": response_time,
                            "timestamp": settings.get_current_time()
                        }
                    }
                )

        # Process contacts data
        contacts_data = waha_response.data
        contacts = contacts_data.get("contacts", [])

        # Process and enrich contacts
        processed_contacts = []
        for contact in contacts:
            processed_contact = {
                "id": contact.get("id"),
                "name": contact.get("name") or contact.get("pushname") or contact.get("notifyName") or "Unknown",
                "display_name": contact.get("pushname") or contact.get("notifyName") or contact.get("name") or "Unknown",
                "is_group": contact.get("isGroup", False),
                "is_wa_contact": contact.get("isWAContact", False),
                "last_message": contact.get("lastMessage"),
                "last_message_time": contact.get("lastMessageTime"),
                "unread_count": contact.get("unreadCount", 0),
                "profile_pic_url": contact.get("profilePicUrl"),
                "phone": contact.get("id", "").replace("@c.us", "").replace("@g.us", ""),
                "type": "group" if contact.get("isGroup") else "individual",
                "notify_name": contact.get("notifyName"),
                "pushname": contact.get("pushname")
            }
            processed_contacts.append(processed_contact)

        # Calculate statistics
        stats = {
            "total": len(processed_contacts),
            "individuals": len([c for c in processed_contacts if c["type"] == "individual"]),
            "groups": len([c for c in processed_contacts if c["type"] == "group"]),
            "wa_contacts": len([c for c in processed_contacts if c["is_wa_contact"]]),
            "with_unread": len([c for c in processed_contacts if c["unread_count"] > 0]),
            "total_unread": sum(c["unread_count"] for c in processed_contacts)
        }

        # Get pagination data
        pagination_data = contacts_data.get("pagination", {})
        pagination = {
            "limit": limit,
            "offset": offset,
            "total": contacts_data.get("total", len(processed_contacts)),
            "has_more": contacts_data.get("has_more", len(processed_contacts) >= limit),
            "page": (offset // limit) + 1,
            "total_pages": pagination_data.get("total_pages", (len(processed_contacts) + limit - 1) // limit)
        }

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "contacts": processed_contacts,
                    "pagination": pagination,
                    "sorting": {
                        "sort_by": sort_by,
                        "sort_order": sort_order
                    },
                    "session": session,
                    "statistics": stats,
                    "mock": contacts_data.get("mock", False),
                    "generated_at": contacts_data.get("generated_at", settings.get_current_time())
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


@router.get("/contacts/statistics", summary="Get Contact Statistics")
async def get_contact_statistics(request: Request) -> Dict[str, Any]:
    """
    Get statistics about WhatsApp contacts
    """
    try:
        # Get all contacts with higher limit
        waha_client = WahaClient()
        waha_response = await waha_client.get_all_contacts(
            limit=1000,
            offset=0,
            sort_by="name",
            sort_order="asc",
            session="default",
            use_mock=False
        )

        if not waha_response.success:
            raise HTTPException(
                status_code=503,
                detail={
                    "success": False,
                    "error": "Unable to retrieve contacts for statistics",
                    "code": "STATISTICS_ERROR"
                }
            )

        contacts = waha_response.data.get("contacts", [])

        # Calculate detailed statistics
        stats = {
            "total_contacts": len(contacts),
            "individual_contacts": len([c for c in contacts if not c.get("isGroup", False)]),
            "group_chats": len([c for c in contacts if c.get("isGroup", False)]),
            "wa_contacts": len([c for c in contacts if c.get("isWAContact", False)]),
            "non_wa_contacts": len([c for c in contacts if not c.get("isWAContact", False)]),
            "contacts_with_unread": len([c for c in contacts if c.get("unreadCount", 0) > 0]),
            "total_unread_messages": sum(c.get("unreadCount", 0) for c in contacts),
            "contacts_with_profile_pic": len([c for c in contacts if c.get("profilePicUrl")]),
            "average_unread_per_contact": 0
        }

        # Calculate average unread per contact
        if stats["total_contacts"] > 0:
            stats["average_unread_per_contact"] = stats["total_unread_messages"] / stats["total_contacts"]

        # Get unread distribution
        unread_distribution = {
            "zero_unread": 0,
            "1_to_5_unread": 0,
            "6_to_10_unread": 0,
            "11_to_50_unread": 0,
            "more_than_50_unread": 0
        }

        for contact in contacts:
            unread_count = contact.get("unreadCount", 0)
            if unread_count == 0:
                unread_distribution["zero_unread"] += 1
            elif unread_count <= 5:
                unread_distribution["1_to_5_unread"] += 1
            elif unread_count <= 10:
                unread_distribution["6_to_10_unread"] += 1
            elif unread_count <= 50:
                unread_distribution["11_to_50_unread"] += 1
            else:
                unread_distribution["more_than_50_unread"] += 1

        return {
            "success": True,
            "data": {
                "statistics": stats,
                "unread_distribution": unread_distribution,
                "last_updated": settings.get_current_time(),
                "session": "default"
            },
            "metadata": {
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
                "error": "Failed to generate contact statistics",
                "code": "STATISTICS_GENERATION_ERROR",
                "details": {
                    "error": str(e)
                } if settings.DEBUG else None
            }
        )


@router.get("/contacts/mock", summary="Get Mock Contacts")
async def get_mock_contacts(
    request: Request,
    limit: int = Query(100, ge=1, le=settings.MAX_LIMIT),
    sort_by: str = Query("name", regex="^(name|id|notifyName|pushname|lastMessage|unreadCount|lastMessageTime)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$")
) -> Dict[str, Any]:
    """
    Get mock contacts for testing purposes
    """
    start_time = time.time()

    try:
        waha_client = WahaClient()
        mock_data = waha_client._generate_mock_contacts(limit, 0, sort_by, sort_order)

        response_time = int((time.time() - start_time) * 1000)

        return {
            "success": True,
            "data": {
                "contacts": mock_data["contacts"],
                "total": mock_data["total"],
                "limit": limit,
                "has_more": mock_data["has_more"],
                "mock": True,
                "generated_at": mock_data["generated_at"],
                "statistics": {
                    "total": mock_data["total"],
                    "individuals": len([c for c in mock_data["contacts"] if not c.get("isGroup", False)]),
                    "groups": len([c for c in mock_data["contacts"] if c.get("isGroup", False)])
                }
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
                "error": "Failed to generate mock contacts",
                "code": "MOCK_GENERATION_ERROR",
                "details": {
                    "error": str(e)
                } if settings.DEBUG else None
            }
        )


@router.post("/contacts", summary="Get Contacts with POST")
async def get_contacts_post(
    request: Request,
    contact_request: ContactRequest
) -> Dict[str, Any]:
    """
    Get contacts using POST method for complex queries
    """
    return await get_contacts(
        request=request,
        limit=contact_request.limit,
        offset=contact_request.offset,
        sort_by=contact_request.sort_by,
        sort_order=contact_request.sort_order,
        session=contact_request.session,
        use_mock=contact_request.use_mock
    )