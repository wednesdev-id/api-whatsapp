"""
WAHA API Client for FastAPI Application
"""

import base64
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

import httpx
from pydantic import BaseModel

from api.core.config import settings
from api.core.exceptions import WAHAException, WAHAConnectionException


class WahaResponse(BaseModel):
    """WAHA API response model"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    code: Optional[str] = None


class WahaClient:
    """WAHA API client for communicating with WAHA server"""

    def __init__(
        self,
        base_url: str = None,
        username: str = None,
        password: str = None,
        api_key: str = None,
        timeout: int = 30
    ):
        self.base_url = base_url or settings.WAHA_API_URL
        self.username = username or settings.WAHA_USERNAME
        self.password = password or settings.WAHA_PASSWORD
        self.api_key = api_key or settings.WAHA_API_KEY
        self.timeout = timeout

        # Setup HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "WAHA-FastAPI/1.0"
            }
        )

        # Setup authentication
        self._setup_auth()

        # Logger
        self.logger = logging.getLogger(__name__)

    def _setup_auth(self):
        """Setup authentication headers"""
        if self.username and self.password:
            # Basic Authentication
            auth_string = f"{self.username}:{self.password}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            self.client.headers["Authorization"] = f"Basic {auth_b64}"

        if self.api_key:
            self.client.headers["X-API-Key"] = self.api_key

    async def test_connection(self) -> WahaResponse:
        """Test connection to WAHA server"""
        try:
            # Test main endpoint
            response = await self.client.get("/")
            self.logger.info(f"WAHA Main endpoint status: {response.status_code}")

            # Test WAHA-specific endpoint
            test_url = "/api/default/chats/test@c.us/messages?limit=1"
            test_response = await self.client.get(test_url)
            self.logger.info(f"WAHA API endpoint status: {test_response.status_code}")

            if response.status_code in [200, 404]:
                if test_response.status_code == 200:
                    return WahaResponse(
                        success=True,
                        data={
                            "main_endpoint": response.status_code,
                            "waha_endpoint": test_response.status_code,
                            "message": "Connection successful"
                        }
                    )
                elif test_response.status_code in [401, 422]:
                    return WahaResponse(
                        success=True,
                        data={
                            "main_endpoint": response.status_code,
                            "waha_endpoint": test_response.status_code,
                            "message": "WAHA API found, authentication or session required"
                        }
                    )
                else:
                    return WahaResponse(
                        success=True,
                        data={
                            "main_endpoint": response.status_code,
                            "waha_endpoint": test_response.status_code,
                            "message": "Server reachable"
                        }
                    )
            else:
                return WahaResponse(
                    success=False,
                    error=f"Connection failed with status {response.status_code}",
                    code="CONNECTION_FAILED"
                )

        except httpx.RequestError as e:
            self.logger.error(f"Connection error: {str(e)}")
            return WahaResponse(
                success=False,
                error=f"Connection error: {str(e)}",
                code="CONNECTION_ERROR"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return WahaResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                code="UNKNOWN_ERROR"
            )

    async def discover_endpoints(self) -> WahaResponse:
        """Discover available WAHA endpoints"""
        common_endpoints = [
            "/api/contacts",
            "/api/default/contacts",
            "/contacts",
            "/api/sessions/default/contacts",
            "/api/sessions",
            "/api/chats",
            "/chats"
        ]

        results = {}

        for endpoint in common_endpoints:
            try:
                response = await self.client.get(endpoint, timeout=5)
                results[endpoint] = {
                    "status": response.status_code,
                    "available": response.status_code != 404,
                    "content_type": response.headers.get('content-type', ''),
                    "sample": response.text[:200] + "..." if len(response.text) > 200 else response.text
                }

                if response.status_code != 404:
                    self.logger.info(f"Found endpoint: {endpoint} (Status: {response.status_code})")

            except Exception as e:
                results[endpoint] = {
                    "status": "error",
                    "available": False,
                    "error": str(e)
                }
                self.logger.error(f"Error checking {endpoint}: {str(e)}")

        return WahaResponse(
            success=True,
            data={"endpoints": results}
        )

    async def get_active_sessions(self) -> WahaResponse:
        """Get list of active WAHA sessions"""
        try:
            response = await self.client.get("/api/sessions")

            if response.status_code == 200:
                sessions_data = response.json()
                active_sessions = []

                if isinstance(sessions_data, list):
                    for session in sessions_data:
                        if (session.get('status') in ['WORKING', 'READY', 'CONNECTED']
                            and session.get('name')):
                            active_sessions.append(session['name'])
                            self.logger.info(f"Active session: {session['name']} ({session['status']})")

                return WahaResponse(
                    success=True,
                    data={"active_sessions": active_sessions, "count": len(active_sessions)}
                )
            else:
                return WahaResponse(
                    success=False,
                    error=f"Failed to get sessions: {response.status_code}",
                    code="SESSIONS_ERROR"
                )

        except Exception as e:
            self.logger.error(f"Error getting sessions: {str(e)}")
            return WahaResponse(
                success=False,
                error=f"Error getting sessions: {str(e)}",
                code="SESSIONS_REQUEST_ERROR"
            )

    async def get_chat_messages(
        self,
        chat_id: str,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        session: str = "default",
        use_mock: bool = False
    ) -> WahaResponse:
        """Get messages from a specific chat"""
        if use_mock:
            return WahaResponse(
                success=True,
                data=self._generate_mock_messages(chat_id, limit)
            )

        try:
            encoded_chat_id = httpx._utils.quote(chat_id, safe='')
            url = f"/api/default/chats/{encoded_chat_id}/messages"

            params = {
                "sortBy": sort_by,
                "sortOrder": sort_order,
                "limit": limit,
                "offset": offset
            }

            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()

                # Return the raw response from WAHA API
                return WahaResponse(
                    success=True,
                    data=data
                )
            else:
                error_text = response.text
                if response.status_code == 422:
                    if "SCAN_QR_CODE" in error_text:
                        return WahaResponse(
                            success=False,
                            error="WhatsApp session needs QR code scan",
                            code="SCAN_QR_REQUIRED"
                        )
                    elif "DISCONNECTED" in error_text:
                        return WahaResponse(
                            success=False,
                            error="WhatsApp session is disconnected",
                            code="SESSION_DISCONNECTED"
                        )

                return WahaResponse(
                    success=False,
                    error=f"Failed to get messages: {response.status_code} - {error_text}",
                    code="MESSAGES_ERROR"
                )

        except Exception as e:
            self.logger.error(f"Error getting messages: {str(e)}")
            return WahaResponse(
                success=False,
                error=f"Error getting messages: {str(e)}",
                code="MESSAGES_REQUEST_ERROR"
            )

    async def get_all_contacts(
        self,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "name",
        sort_order: str = "asc",
        session: str = "default",
        use_mock: bool = False
    ) -> WahaResponse:
        """Get all contacts from WAHA"""
        if use_mock:
            return WahaResponse(
                success=True,
                data=self._generate_mock_contacts(limit, offset, sort_by, sort_order)
            )

        try:
            # Get active sessions first
            sessions_response = await self.get_active_sessions()
            if not sessions_response.success:
                return WahaResponse(
                    success=False,
                    error="Unable to get active sessions",
                    code="SESSIONS_UNAVAILABLE"
                )

            active_sessions = sessions_response.data.get("active_sessions", [])
            if not active_sessions:
                return WahaResponse(
                    success=True,
                    data=self._generate_mock_contacts(limit, offset, sort_by, sort_order)
                )

            active_session = active_sessions[0]
            if session not in active_sessions:
                session = active_session

            url = "/api/contacts"
            params = {
                "session": session,
                "limit": limit,
                "offset": offset,
                "sortBy": sort_by,
                "sortOrder": sort_order
            }

            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()

                # Return the raw response from WAHA API
                return WahaResponse(
                    success=True,
                    data=data  # Return raw response from WAHA API
                )
            else:
                return WahaResponse(
                    success=False,
                    error=f"Failed to get contacts: {response.status_code}",
                    code="CONTACTS_ERROR"
                )

        except Exception as e:
            self.logger.error(f"Error getting contacts: {str(e)}")
            return WahaResponse(
                success=False,
                error=f"Error getting contacts: {str(e)}",
                code="CONTACTS_REQUEST_ERROR"
            )

    async def send_message(
        self,
        chat_id: str,
        message: str,
        session: str = "default",
        message_type: str = "text",
        media_url: str = None,
        media_caption: str = None
    ) -> WahaResponse:
        """Send message via WAHA"""
        try:
            url = f"/api/{session}/send-message"

            payload = {
                "chatId": chat_id,
                "type": message_type,
                "message": message
            }

            if media_url:
                payload["mediaUrl"] = media_url

            if media_caption:
                payload["mediaCaption"] = media_caption

            response = await self.client.post(url, json=payload)

            if response.status_code == 200:
                result = response.json()
                return WahaResponse(
                    success=True,
                    data={
                        "message_id": result.get("id"),
                        "chat_id": chat_id,
                        "message": message,
                        "type": message_type,
                        "session": session,
                        "status": "sent",
                        "timestamp": settings.get_current_time()
                    }
                )
            else:
                return WahaResponse(
                    success=False,
                    error=f"Failed to send message: {response.status_code} - {response.text}",
                    code="SEND_MESSAGE_ERROR"
                )

        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}")
            return WahaResponse(
                success=False,
                error=f"Error sending message: {str(e)}",
                code="SEND_MESSAGE_REQUEST_ERROR"
            )

    def _generate_mock_messages(self, chat_id: str, limit: int) -> Dict[str, Any]:
        """Generate mock message data for testing"""
        import random
        from datetime import datetime, timedelta

        messages = []
        base_time = datetime.utcnow()

        sample_messages = [
            "Halo, bagaimana kabarnya?",
            "Baik-baik saja, terima kasih!",
            "Apakah project sudah selesai?",
            "Sudah, tinggal testing final",
            "Oke, saya cek dulu ya",
            "Siap, saya tunggu update nya",
            "Documents sudah saya kirim",
            "Terima kasih atas bantuannya",
            "Sampai jumpa besok!",
            "Have a great day!"
        ]

        for i in range(min(limit, 20)):
            timestamp = int((base_time - timedelta(hours=i * 2)).timestamp())
            is_from_me = random.choice([True, False])

            message = {
                "id": f"mock_msg_{i}_{timestamp}",
                "timestamp": timestamp,
                "from": chat_id if not is_from_me else "6282243673017@c.us",
                "to": "6282243673017@c.us" if not is_from_me else chat_id,
                "body": random.choice(sample_messages),
                "fromMe": is_from_me,
                "hasMedia": False,
                "mediaType": None,
                "mediaCaption": None,
                "ack": random.randint(1, 3)
            }
            messages.append(message)

        return {
            "messages": messages,
            "total": len(messages),
            "has_more": len(messages) >= limit,
            "mock": True,
            "generated_at": settings.get_current_time()
        }

    def _generate_mock_contacts(
        self, limit: int, offset: int, sort_by: str, sort_order: str
    ) -> Dict[str, Any]:
        """Generate mock contact data for testing"""
        import random

        sample_contacts = [
            {"id": "62818114411@c.us", "name": "Pak Feri Coworker", "notifyName": "Pak Feri", "isGroup": False, "isWAContact": True},
            {"id": "6281339691260@c.us", "name": "Mas Feri", "notifyName": "Mas Feri", "isGroup": False, "isWAContact": True},
            {"id": "120363419906557011@g.us", "name": "Developer Coworker", "notifyName": "Developer Coworker", "isGroup": True, "isWAContact": True},
            {"id": "628988146713@c.us", "name": "Senseiiii", "notifyName": "Senseii", "isGroup": False, "isWAContact": True},
            {"id": "120363419759004678@g.us", "name": "Kampus dev team", "notifyName": "Kampus dev team", "isGroup": True, "isWAContact": True},
            {"id": "628156700525@c.us", "name": "Om Haibannn Wail", "notifyName": "Om Haiban", "isGroup": False, "isWAContact": True},
            {"id": "6289505982878@c.us", "name": "Sabil", "notifyName": "Sabil", "isGroup": False, "isWAContact": True},
            {"id": "6282243673017@c.us", "name": "Me", "notifyName": "Me", "isGroup": False, "isWAContact": True},
        ]

        all_contacts = []
        for contact in sample_contacts:
            contact_copy = contact.copy()
            contact_copy.update({
                "pushname": contact["name"],
                "profilePicUrl": None,
                "lastMessage": f"Last message",
                "lastMessageTime": int((datetime.utcnow().timestamp() - random.randint(0, 86400)) * 1000),
                "unreadCount": random.randint(0, 5)
            })
            all_contacts.append(contact_copy)

        # Sort contacts
        reverse_order = sort_order.lower() == 'desc'
        if sort_by in ['name', 'id', 'notifyName', 'pushname', 'lastMessage']:
            all_contacts.sort(key=lambda x: x.get(sort_by, ''), reverse=reverse_order)
        elif sort_by == 'unreadCount':
            all_contacts.sort(key=lambda x: x.get('unreadCount', 0), reverse=reverse_order)

        # Apply pagination
        total_contacts = len(all_contacts)
        safe_offset = min(offset, total_contacts)
        contacts = all_contacts[safe_offset:safe_offset + limit]
        has_more = (safe_offset + limit) < total_contacts

        return {
            "contacts": contacts,
            "total": total_contacts,
            "limit": limit,
            "offset": safe_offset,
            "hasMore": has_more,
            "mock": True,
            "generated_at": settings.get_current_time()
        }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()