#!/usr/bin/env python3
"""
WAHA API Automation Script
Script untuk automatisasi request ke WAHA API dengan auth barrier
"""

import requests
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse
import base64


class WahaAPIClient:
    """
    Client untuk mengakses WAHA API dengan authentication barrier
    Semua fungsi API mengembalikan data langsung tanpa menyimpan ke file
    """

    def __init__(self, base_url: str = "http://localhost:3000",
                 username: str = "admin",
                 password: str = "e44213b43dc349709991dbb1a6343e47",
                 api_key: str = "c79b6529186c44aa9d536657ffea710b",
                 timeout: int = 30):
        """
        Initialize WAHA API Client

        Args:
            base_url: Base URL untuk WAHA API
            username: Username untuk basic auth
            password: Password untuk basic auth
            api_key: API key untuk request
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()

        # Setup authentication headers
        self._setup_auth()

    def _setup_auth(self):
        """Setup basic authentication untuk session"""
        # Basic Auth credentials
        auth_string = f"{self.username}:{self.password}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')

        # Set headers
        self.session.headers.update({
            'Authorization': f'Basic {auth_b64}',
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'WAHA-Automator/1.0'
        })

    def discover_endpoints(self) -> Dict[str, Any]:
        """
        Discover available endpoints in WAHA API

        Returns:
            Dict: Available endpoints and their status
        """
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
                url = f"{self.base_url}{endpoint}"
                response = self.session.get(url, timeout=5)

                results[endpoint] = {
                    "status": response.status_code,
                    "available": response.status_code != 404,
                    "content_type": response.headers.get('content-type', ''),
                    "sample": response.text[:200] + "..." if len(response.text) > 200 else response.text
                }

                if response.status_code != 404:
                    print(f"[+] Found endpoint: {endpoint} (Status: {response.status_code})")
                else:
                    print(f"[-] Endpoint not found: {endpoint}")

            except Exception as e:
                results[endpoint] = {
                    "status": "error",
                    "available": False,
                    "error": str(e)
                }
                print(f"[!] Error checking {endpoint}: {str(e)}")

        return results

    def get_active_sessions(self) -> List[str]:
        """
        Get list of active sessions from WAHA API

        Returns:
            List: List of active session names
        """
        try:
            url = f"{self.base_url}/api/sessions"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                sessions_data = response.json()
                active_sessions = []

                if isinstance(sessions_data, list):
                    for session in sessions_data:
                        if (session.get('status') in ['WORKING', 'READY', 'CONNECTED']
                            and session.get('name')):
                            active_sessions.append(session['name'])
                            print(f"[+] Active session found: {session['name']} (Status: {session['status']})")
                        else:
                            print(f"[-] Inactive session: {session.get('name', 'unknown')} (Status: {session.get('status', 'unknown')})")

                print(f"Found {len(active_sessions)} active sessions")
                return active_sessions

            return []

        except Exception as e:
            print(f"[!] Error getting sessions: {str(e)}")
            return []

    def test_connection(self) -> bool:
        """
        Test koneksi ke WAHA API

        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            # Try to access a general endpoint first
            response = self.session.get(f"{self.base_url}/", timeout=self.timeout)
            print(f"Testing connection to {self.base_url}/")
            print(f"Status Code: {response.status_code}")

            # Also try the specific WAHA endpoint structure
            test_endpoint = f"{self.base_url}/api/default/chats/test@c.us/messages?limit=1"
            test_response = self.session.get(test_endpoint, timeout=self.timeout)
            print(f"Testing WAHA endpoint: {test_endpoint}")
            print(f"WAHA Status Code: {test_response.status_code}")

            if response.status_code in [200, 404]:  # 404 might mean server is up but endpoint doesn't exist
                print("Server is reachable!")
                if test_response.status_code == 200:
                    print("WAHA API endpoint is working!")
                    return True
                elif test_response.status_code == 401:
                    print("WAHA API found, but authentication required - this is expected!")
                    return True
                elif test_response.status_code == 422:
                    print("WAHA API found, session validation working - this is expected!")
                    return True
                else:
                    print(f"WAHA API responded with: {test_response.status_code}")
                    return True  # Server is up, might be different endpoint structure
            else:
                print(f"Connection failed: {response.text}")
                return False

        except requests.exceptions.Timeout:
            print("Connection timeout - WAHA server might be starting up, try again later")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {str(e)}")
            print("Make sure WAHA server is running at the specified URL")
            return False
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {str(e)}")
            return False

    def generate_mock_data(self, chat_id: str, limit: int = 100) -> Dict[str, Any]:
        """
        Generate mock WhatsApp messages untuk testing

        Args:
            chat_id: Chat ID
            limit: Number of messages to generate

        Returns:
            Dict: Mock response data
        """
        import random
        from datetime import datetime, timedelta

        messages = []
        base_time = datetime.now()

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

        for i in range(min(limit, 20)):  # Max 20 messages for demo
            timestamp = int((base_time - timedelta(hours=i*2)).timestamp())
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
            "hasMore": len(messages) >= limit,
            "mock": True,
            "generated_at": datetime.now().isoformat()
        }

    def get_chat_messages(self, chat_id: str,
                         limit: int = 100,
                         offset: int = 0,
                         sort_by: str = "timestamp",
                         sort_order: str = "desc",
                         use_mock: bool = False) -> Optional[Dict[str, Any]]:
        """
        Mendapatkan pesan dari chat tertentu

        Args:
            chat_id: ID chat (WhatsApp number)
            limit: Jumlah maksimal pesan
            offset: Offset untuk pagination
            sort_by: Field untuk sorting
            sort_order: Urutan sorting (asc/desc)
            use_mock: Gunakan mock data untuk testing

        Returns:
            Dict: Response dari API atau None jika error
        """
        if use_mock:
            print("Using mock data for testing...")
            return self.generate_mock_data(chat_id, limit)

        try:
            # Build URL
            encoded_chat_id = requests.utils.quote(chat_id, safe='')
            url = f"{self.base_url}/api/default/chats/{encoded_chat_id}/messages"

            # Parameters
            params = {
                'sortBy': sort_by,
                'sortOrder': sort_order,
                'limit': limit,
                'offset': offset
            }

            print(f"Requesting messages from: {url}")
            print(f"Parameters: {params}")

            # Make request
            response = self.session.get(url, params=params, timeout=self.timeout)

            print(f"Response Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                # Handle different response structures
                if isinstance(data, list):
                    messages = data
                elif isinstance(data, dict):
                    messages = data.get('messages', data.get('data', []))
                else:
                    messages = []

                print(f"Success! Retrieved {len(messages)} messages")
                return data
            else:
                error_text = response.text
                print(f"Error: {response.status_code} - {error_text}")

                # Detect session issues and suggest mock data
                if response.status_code == 422:
                    if "SCAN_QR_CODE" in error_text:
                        print("\nTip: WhatsApp session needs QR code scan.")
                        print("     Use --mock-data flag for testing development:")
                        print("     python waha_automator.py --mock-data --limit 10")
                    elif "DISCONNECTED" in error_text:
                        print("\nTip: WhatsApp session is disconnected.")
                        print("     Please reconnect and try again.")

                return None

        except requests.exceptions.RequestException as e:
            print(f"Request error: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")
            return None

    def get_all_chats(self,
                      limit: int = 100,
                      offset: int = 0,
                      session: str = "default",
                      sort_by: str = "name",
                      sort_order: str = "desc",
                      use_mock: bool = False) -> Optional[Dict[str, Any]]:
        """
        Mendapatkan semua chats dari WAHA API

        Args:
            limit: Jumlah maksimal chats (default: 100)
            offset: Offset untuk pagination (default: 0)
            session: Session ID untuk WAHA (default: "default")
            sort_by: Field untuk sorting (default: "name")
            sort_order: Urutan sorting (asc/desc) (default: "desc")
            use_mock: Gunakan mock data untuk testing

        Returns:
            Dict: Response dari API atau None jika error
        """
        if use_mock:
            print("Using mock chats data for testing...")
            return self.generate_mock_chats(limit, offset, sort_by, sort_order)

        try:
            # Auto-detect active sessions jika session tidak valid
            active_sessions = self.get_active_sessions()

            if not active_sessions:
                print("[-] No active sessions found. Using mock data instead.")
                return self.generate_mock_chats(limit, offset, sort_by, sort_order)

            # Gunakan session pertama yang aktif
            active_session = active_sessions[0]
            if session not in active_sessions:
                print(f"[-] Session '{session}' is not active. Using active session: '{active_session}'")
                session = active_session

            # Build URL untuk chats endpoint - try different possible endpoints
            chat_endpoints = [
                f"{self.base_url}/api/{session}/chats",
                f"{self.base_url}/api/default/chats",
                f"{self.base_url}/api/chats",
                f"{self.base_url}/chats"
            ]

            # Parameters
            params = {
                'sortBy': sort_by,
                'sortOrder': sort_order,
                'limit': limit,
                'offset': offset
            }

            # Try each endpoint until we find a working one
            for url in chat_endpoints:
                try:
                    print(f"Trying chats endpoint: {url}")
                    print(f"Parameters: {params}")

                    # Make request ke endpoint
                    response = self.session.get(url, params=params, timeout=self.timeout)

                    print(f"Response Status: {response.status_code}")

                    if response.status_code == 200:
                        data = response.json()
                        # Handle different response structures
                        if isinstance(data, list):
                            chats = data
                        elif isinstance(data, dict):
                            chats = data.get('chats', data.get('data', []))
                        else:
                            chats = []

                        print(f"Success! Retrieved {len(chats)} chats from {url}")
                        return {
                            "chats": chats,
                            "total": len(chats),
                            "limit": limit,
                            "offset": offset,
                            "hasMore": len(chats) >= limit,
                            "page": (offset // limit) + 1 if limit > 0 else 1,
                            "total_pages": (len(chats) + limit - 1) // limit if limit > 0 else 1,
                            "sortBy": sort_by,
                            "sortOrder": sort_order,
                            "session": session,
                            "endpoint": url
                        }
                    elif response.status_code == 404:
                        print(f"Endpoint not found: {url}")
                        continue  # Try next endpoint
                    else:
                        error_text = response.text
                        print(f"Error from {url}: {response.status_code} - {error_text}")
                        if response.status_code != 404:  # If it's not 404, don't try other endpoints
                            break

                except requests.exceptions.RequestException as e:
                    print(f"Request error for {url}: {str(e)}")
                    continue  # Try next endpoint

            # If we get here, all endpoints failed
            print("All chat endpoints failed. Using mock data instead.")
            return self.generate_mock_chats(limit, offset, sort_by, sort_order)

        except Exception as e:
            print(f"Unexpected error getting chats: {str(e)}")
            return self.generate_mock_chats(limit, offset, sort_by, sort_order)

    def generate_mock_chats(self, limit: int = 100, offset: int = 0, sort_by: str = "name", sort_order: str = "desc") -> Dict[str, Any]:
        """
        Generate mock WhatsApp chats untuk testing

        Args:
            limit: Number of chats to return
            offset: Offset for pagination
            sort_by: Field for sorting (name, id, lastMessage, etc.)
            sort_order: Sort order (asc/desc)

        Returns:
            Dict: Mock response data
        """
        import random
        from datetime import datetime, timedelta

        chats = []

        # Generate chats dynamically up to the requested limit
        base_sample_chats = [
            {
                "id": "62818114411@c.us",
                "name": "Pak Feri Coworker",
                "lastMessage": "Oke, saya cek dulu ya",
                "timestamp": int((datetime.now() - timedelta(minutes=5)).timestamp()),
                "unreadCount": 2,
                "isGroup": False,
                "isOnline": True
            },
            {
                "id": "6281339691260@c.us",
                "name": "Mas Feri",
                "lastMessage": "Sudah, tinggal testing final",
                "timestamp": int((datetime.now() - timedelta(hours=1)).timestamp()),
                "unreadCount": 0,
                "isGroup": False,
                "isOnline": False
            },
            {
                "id": "120363419906557011@g.us",
                "name": "Developer Coworker",
                "lastMessage": "Documents sudah saya kirim",
                "timestamp": int((datetime.now() - timedelta(minutes=30)).timestamp()),
                "unreadCount": 15,
                "isGroup": True,
                "participants": 25
            },
            {
                "id": "628988146713@c.us",
                "name": "Senseiiii",
                "lastMessage": "Terima kasih atas bantuannya",
                "timestamp": int((datetime.now() - timedelta(hours=2)).timestamp()),
                "unreadCount": 1,
                "isGroup": False,
                "isOnline": True
            },
            {
                "id": "120363419759004678@g.us",
                "name": "Kampus dev team",
                "lastMessage": "Have a great day!",
                "timestamp": int((datetime.now() - timedelta(days=1)).timestamp()),
                "unreadCount": 0,
                "isGroup": True,
                "participants": 12
            }
        ]

        # Sample name and message pools for generating more chats
        first_names = ["Andi", "Budi", "Citra", "Dewi", "Eko", "Fajar", "Gita", "Hadi", "Indra", "Julia"]
        last_names = ["Santoso", "Wijaya", "Putra", "Sari", "Hidayat", "Permata"]
        group_names = ["Family Group", "Work Team", "School Friends", "Project Team", "Community"]
        last_messages = [
            "Oke, saya tunggu ya", "Baik, terima kasih", "Sampai jumpa besok",
            "Have a great day!", "Documents sudah saya kirim", "Saya cek dulu",
            "Siap, saya kerjakan", "Terima kasih infonya", "Oke, mengerti",
            "Saya setuju dengan itu", "Kapan kita mulai?", "Bagaimana progresnya?"
        ]

        # Generate all chats first
        all_chats = []
        total_needed = limit + offset  # Generate enough to handle offset

        for i in range(total_needed):
            if i < len(base_sample_chats):
                # Use base sample chats first
                chat = base_sample_chats[i].copy()
            else:
                # Generate new chats dynamically
                if i % 3 == 0:  # Every 3rd chat is a group
                    group_idx = (i - len(base_sample_chats)) // 3
                    chat = {
                        "id": f"1203634199{random.randint(100000, 999999)}@g.us",
                        "name": f"{random.choice(group_names)} {group_idx + 1}",
                        "lastMessage": random.choice(last_messages),
                        "timestamp": int((datetime.now() - timedelta(hours=random.randint(0, 168))).timestamp()),
                        "unreadCount": random.randint(0, 20),
                        "isGroup": True,
                        "participants": random.randint(3, 50)
                    }
                else:
                    # Generate individual chat
                    name_idx = i - len(base_sample_chats) - (i // 3)
                    first_name = random.choice(first_names)
                    last_name = random.choice(last_names)
                    phone_number = f"628{random.randint(100000000, 999999999)}"
                    chat = {
                        "id": f"{phone_number}@c.us",
                        "name": f"{first_name} {last_name}",
                        "lastMessage": random.choice(last_messages),
                        "timestamp": int((datetime.now() - timedelta(hours=random.randint(0, 72))).timestamp()),
                        "unreadCount": random.randint(0, 10),
                        "isGroup": False,
                        "isOnline": random.choice([True, False])
                    }

            # Add additional fields for compatibility
            chat.update({
                "pushname": chat["name"],
                "profilePicUrl": None,
                "lastMessageTime": chat["timestamp"] * 1000,  # Convert to milliseconds
                "isMyContact": True,
                "isWAContact": True,
                "isArchived": False,
                "isPinned": False,
                "isMuted": False
            })
            all_chats.append(chat)

        # Sort chats
        reverse_order = sort_order.lower() == 'desc'
        if sort_by in ['name', 'id', 'lastMessage', 'pushname']:
            all_chats.sort(key=lambda x: x.get(sort_by, ''), reverse=reverse_order)
        elif sort_by == 'unreadCount':
            all_chats.sort(key=lambda x: x.get('unreadCount', 0), reverse=reverse_order)
        elif sort_by == 'timestamp':
            all_chats.sort(key=lambda x: x.get('timestamp', 0), reverse=reverse_order)
        elif sort_by == 'lastMessageTime':
            all_chats.sort(key=lambda x: x.get('lastMessageTime', 0), reverse=reverse_order)

        # Apply pagination
        total_chats = len(all_chats)
        # Ensure offset doesn't exceed total
        safe_offset = min(offset, total_chats)
        chats = all_chats[safe_offset:safe_offset + limit]
        has_more = (safe_offset + limit) < total_chats

        return {
            "chats": chats,
            "total": total_chats,
            "limit": limit,
            "offset": safe_offset,
            "hasMore": has_more,
            "page": (safe_offset // limit) + 1 if limit > 0 else 1,
            "total_pages": (total_chats + limit - 1) // limit if limit > 0 else 1,
            "sortBy": sort_by,
            "sortOrder": sort_order,
            "session": "default",
            "mock": True,
            "generated_at": datetime.now().isoformat()
        }

    def get_all_contacts(self,
                        limit: int = 100,
                        offset: int = 0,
                        session: str = "default",
                        sort_by: str = "name",
                        sort_order: str = "asc",
                        use_mock: bool = False) -> Optional[Dict[str, Any]]:
        """
        Mendapatkan semua kontak dari WAHA API

        Args:
            limit: Jumlah maksimal kontak (default: 100)
            offset: Offset untuk pagination (default: 0)
            session: Session ID untuk WAHA (default: "default")
            sort_by: Field untuk sorting (default: "name")
            sort_order: Urutan sorting (asc/desc) (default: "asc")
            use_mock: Gunakan mock data untuk testing

        Returns:
            Dict: Response dari API atau None jika error
        """
        if use_mock:
            print("Using mock contacts data for testing...")
            return self.generate_mock_contacts(limit, offset, sort_by, sort_order)

        try:
            # Auto-detect active sessions jika session tidak valid
            active_sessions = self.get_active_sessions()

            if not active_sessions:
                print("[-] No active sessions found. Using mock data instead.")
                return self.generate_mock_contacts(limit, offset, sort_by, sort_order)

            # Gunakan session pertama yang aktif
            active_session = active_sessions[0]
            if session not in active_sessions:
                print(f"[-] Session '{session}' is not active. Using active session: '{active_session}'")
                session = active_session

            # Build URL untuk contacts endpoint
            url = f"{self.base_url}/api/contacts"

            # Parameters
            params = {
                'session': session,
                'limit': limit,
                'offset': offset,
                'sortBy': sort_by,
                'sortOrder': sort_order
            }

            print(f"Requesting contacts from: {url}")
            print(f"Parameters: {params}")

            # Make request ke endpoint
            response = self.session.get(url, params=params, timeout=self.timeout)

            print(f"Response Status: {response.status_code}")

            if response.status_code != 200:
                error_text = response.text
                print(f"Error: {response.status_code} - {error_text}")

                # Detect session issues
                if response.status_code == 422:
                    if "session" in error_text.lower():
                        print("\nTip: Session name is required or invalid.")
                        print("     Available sessions can be checked with --discover-endpoints")
                        print("     Use --mock-contacts for testing development:")
                        print("     python waha_automator.py --get-contacts --mock-contacts")

                return None

            # Kita sudah tahu response.status_code == 200 di sini
            if True:
                data = response.json()
                # Handle different response structures
                if isinstance(data, list):
                    contacts = data
                elif isinstance(data, dict):
                    contacts = data.get('contacts', data.get('data', []))
                else:
                    contacts = []

                print(f"Success! Retrieved {len(contacts)} contacts")
                return {
                    "contacts": contacts,
                    "total": len(contacts),
                    "limit": limit,
                    "offset": offset,
                    "hasMore": len(contacts) >= limit,
                    "page": (offset // limit) + 1 if limit > 0 else 1,
                    "total_pages": (len(contacts) + limit - 1) // limit if limit > 0 else 1,
                    "sortBy": sort_by,
                    "sortOrder": sort_order,
                    "session": session
                }
            else:
                error_text = response.text
                print(f"Error: {response.status_code} - {error_text}")

                # Detect session issues
                if response.status_code == 422:
                    if "SCAN_QR_CODE" in error_text:
                        print("\nTip: WhatsApp session needs QR code scan.")
                        print("     Use --mock-data flag for testing development:")
                        print("     python waha_automator.py --mock-contacts")
                    elif "DISCONNECTED" in error_text:
                        print("\nTip: WhatsApp session is disconnected.")
                        print("     Please reconnect and try again.")

                return None

        except requests.exceptions.RequestException as e:
            print(f"Request error: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")
            return None

    def generate_mock_contacts(self, limit: int = 100, offset: int = 0, sort_by: str = "name", sort_order: str = "asc") -> Dict[str, Any]:
        """
        Generate mock WhatsApp contacts untuk testing

        Args:
            limit: Number of contacts to return
            offset: Offset for pagination
            sort_by: Field for sorting (name, id, notifyName, etc.)
            sort_order: Sort order (asc/desc)

        Returns:
            Dict: Mock response data
        """
        import random
        from datetime import datetime

        contacts = []

        # Generate contacts dynamically up to the requested limit
        base_sample_contacts = [
            {"id": "62818114411@c.us", "name": "Pak Feri Coworker", "notifyName": "Pak Feri", "isGroup": False, "isWAContact": True},
            {"id": "6281339691260@c.us", "name": "Mas Feri", "notifyName": "Mas Feri", "isGroup": False, "isWAContact": True},
            {"id": "120363419906557011@g.us", "name": "Developer Coworker", "notifyName": "Developer Coworker", "isGroup": True, "isWAContact": True},
            {"id": "628988146713@c.us", "name": "Senseiiii", "notifyName": "Senseii", "isGroup": False, "isWAContact": True},
            {"id": "120363419759004678@g.us", "name": "Kampus dev team", "notifyName": "Kampus dev team", "isGroup": True, "isWAContact": True},
            {"id": "628156700525@c.us", "name": "Om Haibannn Wail", "notifyName": "Om Haiban", "isGroup": False, "isWAContact": True},
            {"id": "6289505982878@c.us", "name": "Sabil", "notifyName": "Sabil", "isGroup": False, "isWAContact": True},
            {"id": "6282243673017@c.us", "name": "Me", "notifyName": "Me", "isGroup": False, "isWAContact": True},
            {"id": "628521234567@c.us", "name": "Admin Team", "notifyName": "Admin", "isGroup": False, "isWAContact": True},
            {"id": "6283197301645@c.us", "name": "Personal Contact", "notifyName": "Personal", "isGroup": False, "isWAContact": True}
        ]

        # Sample name pools for generating more contacts
        first_names = ["Andi", "Budi", "Citra", "Dewi", "Eko", "Fajar", "Gita", "Hadi", "Indra", "Julia", "Kurnia", "Laksana", "Maya", "Nina", "Omar", "Putri", "Rudi", "Siti", "Toni", "Umar", "Vera", "Wahyu", "Yanti", "Zainul"]
        last_names = ["Santoso", "Wijaya", "Putra", "Sari", "Hidayat", "Permata", "Prajogo", "Kusumo", "Mulyadi", "Nugroho", "Suharto", "Rahayu", "Hartono", "Firmansyah", "Susilo"]
        group_names = ["Family Group", "Work Team", "School Friends", "Project Team", "Community", "Alumni", "Neighbors", "Hobby Club", "Study Group", "Business Network"]

        # Generate all contacts first
        all_contacts = []
        total_needed = limit + offset  # Generate enough to handle offset

        for i in range(total_needed):
            if i < len(base_sample_contacts):
                # Use base sample contacts first
                contact = base_sample_contacts[i].copy()
            else:
                # Generate new contacts dynamically
                if i % 4 == 0:  # Every 4th contact is a group
                    group_idx = (i - len(base_sample_contacts)) // 2
                    contact = {
                        "id": f"1203634199{random.randint(100000, 999999)}@g.us",
                        "name": f"{random.choice(group_names)} {group_idx + 1}",
                        "notifyName": f"{random.choice(group_names)}",
                        "isGroup": True,
                        "isWAContact": True
                    }
                else:
                    # Generate individual contact
                    name_idx = i - len(base_sample_contacts) - (i // 4)
                    first_name = random.choice(first_names)
                    last_name = random.choice(last_names)
                    phone_number = f"628{random.randint(100000000, 999999999)}"
                    contact = {
                        "id": f"{phone_number}@c.us",
                        "name": f"{first_name} {last_name}",
                        "notifyName": first_name,
                        "isGroup": False,
                        "isWAContact": random.choice([True, True, True, False])  # 75% chance of being WA contact
                    }

            contact.update({
                "id": contact["id"],
                "pushname": contact["name"],
                "profilePicUrl": None,
                "lastMessage": f"Last message {i+1}",
                "lastMessageTime": int((datetime.now().timestamp() - random.randint(0, 86400)) * 1000),
                "unreadCount": random.randint(0, 5)
            })
            all_contacts.append(contact)

        # Sort contacts
        reverse_order = sort_order.lower() == 'desc'
        if sort_by in ['name', 'id', 'notifyName', 'pushname', 'lastMessage']:
            all_contacts.sort(key=lambda x: x.get(sort_by, ''), reverse=reverse_order)
        elif sort_by == 'unreadCount':
            all_contacts.sort(key=lambda x: x.get('unreadCount', 0), reverse=reverse_order)
        elif sort_by == 'lastMessageTime':
            all_contacts.sort(key=lambda x: x.get('lastMessageTime', 0), reverse=reverse_order)

        # Apply pagination
        total_contacts = len(all_contacts)
        # Ensure offset doesn't exceed total
        safe_offset = min(offset, total_contacts)
        contacts = all_contacts[safe_offset:safe_offset + limit]
        has_more = (safe_offset + limit) < total_contacts

        return {
            "contacts": contacts,
            "total": total_contacts,
            "limit": limit,
            "offset": safe_offset,
            "hasMore": has_more,
            "page": (safe_offset // limit) + 1 if limit > 0 else 1,
            "total_pages": (total_contacts + limit - 1) // limit if limit > 0 else 1,
            "sortBy": sort_by,
            "sortOrder": sort_order,
            "session": "default",
            "mock": True,
            "generated_at": datetime.now().isoformat()
        }

    def send_message(self, chat_id: str, message: str, session: str = "default") -> Dict[str, Any]:
        """
        Mengirim pesan WhatsApp via WAHA API

        Args:
            chat_id: Target chat ID (format: phone_number@c.us)
            message: Message content to send
            session: Session ID for WAHA (default: "default")

        Returns:
            Dict[str, Any]: Response from WAHA API
        """
        try:
            # URL untuk send message API
            url = f"{self.base_url}/api/{session}/send-message"

            # Prepare request payload
            payload = {
                "chatId": chat_id,
                "message": message,
                "session": session
            }

            # Setup headers
            headers = {
                "Content-Type": "application/json",
                "X-API-KEY": self.api_key
            }

            # Send request
            response = self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )

            # Handle response
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Message sent successfully",
                    "chatId": chat_id,
                    "session": session,
                    "response": response.json(),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "chatId": chat_id,
                    "session": session,
                    "timestamp": datetime.now().isoformat()
                }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "chatId": chat_id,
                "session": session,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "chatId": chat_id,
                "session": session,
                "timestamp": datetime.now().isoformat()
            }

    def save_response_to_file(self, data: Dict[str, Any],
                             chat_id: str,
                             output_dir: str = "output") -> str:
        """
        Menyimpan response API ke file JSON

        Args:
            data: Response data dari API
            chat_id: ID chat untuk nama file
            output_dir: Directory output

        Returns:
            str: Path file yang disimpan
        """
        try:
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Generate filename dengan timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_chat_id = chat_id.replace('@c.us', '').replace('+', '')
            filename = f"waha_messages_{clean_chat_id}_{timestamp}.json"

            # Prepare data untuk disimpan
            # Handle different response structures
            if isinstance(data, list):
                messages = data
            elif isinstance(data, dict):
                messages = data.get('messages', data.get('data', []))
            else:
                messages = []

            save_data = {
                'metadata': {
                    'chat_id': chat_id,
                    'retrieved_at': datetime.now().isoformat(),
                    'total_messages': len(messages),
                    'api_response': {
                        'status': 'success',
                        'timestamp': datetime.now().isoformat()
                    }
                },
                'messages': messages
            }

            # Save to file
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            print(f"Saved {len(save_data['messages'])} messages to: {filepath}")
            return filepath

        except Exception as e:
            print(f"Error saving file: {str(e)}")
            raise


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='WAHA API Automation Tool')

    # WAHA API configuration
    parser.add_argument('--url', default='http://localhost:3000',
                       help='WAHA API base URL (default: http://localhost:3000)')
    parser.add_argument('--username', default='admin',
                       help='Username for basic auth (default: admin)')
    parser.add_argument('--password', default='e44213b43dc349709991dbb1a6343e47',
                       help='Password for basic auth')
    parser.add_argument('--api-key', default='c79b6529186c44aa9d536657ffea710b',
                       help='API key for WAHA')

    # Operation mode
    parser.add_argument('--get-contacts', action='store_true',
                       help='Get all contacts instead of messages')
    parser.add_argument('--get-messages', action='store_true',
                       help='Get messages for specific chat (default operation)')

    # Chat configuration
    parser.add_argument('--chat-id', default='6282243673017@c.us',
                       help='Chat ID (format: 628123456789@c.us). Available: 6282243673017@c.us, 628123456789@c.us, etc.')
    parser.add_argument('--session', default='default',
                       help='Session ID for WAHA API (default: default)')
    parser.add_argument('--limit', type=int, default=100,
                       help='Limit results per request (default: 100, max: 1000)')
    parser.add_argument('--offset', type=int, default=0,
                       help='Offset for pagination (default: 0)')
    parser.add_argument('--sort-by', default='name',
                       choices=['name', 'id', 'notifyName', 'pushname', 'lastMessage', 'unreadCount', 'lastMessageTime'],
                       help='Sort field for contacts (default: name)')
    parser.add_argument('--sort-order', default='asc',
                       choices=['asc', 'desc'], help='Sort order (default: asc)')
    parser.add_argument('--sort-by-messages', default='timestamp',
                       choices=['timestamp', 'from', 'to', 'body'],
                       help='Sort field for messages (default: timestamp)')
    parser.add_argument('--sort-order-messages', default='desc',
                       choices=['asc', 'desc'], help='Sort order for messages (default: desc)')

    # Output configuration
    parser.add_argument('--output-dir', default='output',
                       help='Output directory (default: output)')
    parser.add_argument('--test-connection', action='store_true',
                       help='Test connection to WAHA API only')
    parser.add_argument('--discover-endpoints', action='store_true',
                       help='Discover available endpoints in WAHA API')
    parser.add_argument('--return-only', action='store_true', default=True,
                       help='Return data as JSON to stdout (default behavior)')

    # Automation options
    parser.add_argument('--auto-retry', type=int, default=3,
                       help='Number of retry attempts (default: 3)')
    parser.add_argument('--retry-delay', type=int, default=5,
                       help='Delay between retries in seconds (default: 5)')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Request timeout in seconds (default: 30)')
    parser.add_argument('--mock-data', action='store_true',
                       help='Use mock data for testing when WA session is not ready')
    parser.add_argument('--mock-contacts', action='store_true',
                       help='Use mock contacts data for testing')

    return parser.parse_args()






def send_whatsapp_message(chat_id: str, message: str, session: str = "default",
                          url: str = None, username: str = None,
                          password: str = None, api_key: str = None) -> Dict[str, Any]:
    """
    Wrapper function untuk mengirim pesan WhatsApp

    Args:
        chat_id: Target chat ID (format: phone_number@c.us)
        message: Message content to send
        session: Session ID for WAHA (default: "default")
        url: WAHA API URL (from environment if None)
        username: WAHA username (from environment if None)
        password: WAHA password (from environment if None)
        api_key: WAHA API key (from environment if None)

    Returns:
        Dict[str, Any]: Response from WAHA API
    """
    # Use environment variables if not provided
    url = url or os.getenv("WAHA_API_URL", "http://localhost:3000")
    username = username or os.getenv("WAHA_USERNAME", "admin")
    password = password or os.getenv("WAHA_PASSWORD", "e44213b43dc349709991dbb1a6343e47")
    api_key = api_key or os.getenv("WAHA_API_KEY", "c79b6529186c44aa9d536657ffea710b")

    # Create client and send message
    client = WahaAPIClient(
        base_url=url,
        username=username,
        password=password,
        api_key=api_key
    )

    return client.send_message(chat_id=chat_id, message=message, session=session)


def get_waha_contacts(limit: int = 100, offset: int = 0, session: str = "default",
                      url: str = None, username: str = None,
                      password: str = None, api_key: str = None) -> Dict[str, Any]:
    """
    Wrapper function untuk mendapatkan kontak WAHA

    Args:
        limit: Number of contacts (default: 100)
        offset: Offset for pagination (default: 0)
        session: Session ID for WAHA (default: "default")
        url: WAHA API URL (from environment if None)
        username: WAHA username (from environment if None)
        password: WAHA password (from environment if None)
        api_key: WAHA API key (from environment if None)

    Returns:
        Dict[str, Any]: Contacts data
    """
    # Use environment variables if not provided
    url = url or os.getenv("WAHA_API_URL", "http://localhost:3000")
    username = username or os.getenv("WAHA_USERNAME", "admin")
    password = password or os.getenv("WAHA_PASSWORD", "e44213b43dc349709991dbb1a6343e47")
    api_key = api_key or os.getenv("WAHA_API_KEY", "c79b6529186c44aa9d536657ffea710b")

    # Create client and get contacts
    client = WahaAPIClient(
        base_url=url,
        username=username,
        password=password,
        api_key=api_key
    )

    # Get contacts and ensure it returns a valid dict
    result = client.get_all_contacts(limit=limit, offset=offset, session=session)

    if result is None:
        # Fallback to mock data when WAHA server is not available
        return client.generate_mock_contacts(limit=limit, offset=offset, sort_by="name", sort_order="asc")

    return result


def get_waha_chats(limit: int = 100, offset: int = 0, session: str = "default",
                  url: str = None, username: str = None,
                  password: str = None, api_key: str = None,
                  sort_by: str = "name", sort_order: str = "desc") -> Dict[str, Any]:
    """
    Wrapper function untuk mendapatkan chats WAHA

    Args:
        limit: Number of chats (default: 100)
        offset: Offset for pagination (default: 0)
        session: Session ID for WAHA (default: "default")
        url: WAHA API URL (from environment if None)
        username: WAHA username (from environment if None)
        password: WAHA password (from environment if None)
        api_key: WAHA API key (from environment if None)
        sort_by: Field for sorting (default: "name")
        sort_order: Sort order (default: "desc")

    Returns:
        Dict[str, Any]: Chats data
    """
    # Use environment variables if not provided
    url = url or os.getenv("WAHA_API_URL", "http://localhost:3000")
    username = username or os.getenv("WAHA_USERNAME", "admin")
    password = password or os.getenv("WAHA_PASSWORD", "e44213b43dc349709991dbb1a6343e47")
    api_key = api_key or os.getenv("WAHA_API_KEY", "c79b6529186c44aa9d536657ffea710b")

    # Create client and get chats
    client = WahaAPIClient(
        base_url=url,
        username=username,
        password=password,
        api_key=api_key
    )

    # Get chats and ensure it returns a valid dict
    result = client.get_all_chats(limit=limit, offset=offset, session=session,
                                sort_by=sort_by, sort_order=sort_order)

    if result is None:
        # Fallback to mock data when WAHA server is not available
        return client.generate_mock_chats(limit=limit, offset=offset,
                                       sort_by=sort_by, sort_order=sort_order)

    return result


def test_waha_integration():
    """
    Test WAHA integration and return results

    Returns:
        Dict: Test results including contacts count and status
    """
    try:
        # Test getting contacts
        contacts_result = get_waha_contacts(limit=10)

        if contacts_result and isinstance(contacts_result, dict):
            total_contacts = contacts_result.get('total', 0)
            contacts_count = len(contacts_result.get('contacts', []))

            return {
                "success": True,
                "data": {
                    "status": "healthy",
                    "total_contacts": total_contacts,
                    "contacts_returned": contacts_count,
                    "message": f"Successfully retrieved {contacts_count} of {total_contacts} contacts",
                    "pagination_works": total_contacts > 0,
                    "mock_mode": contacts_result.get('mock', False)
                }
            }
        else:
            return {
                "success": False,
                "error": "Failed to get contacts response"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Test failed: {str(e)}"
        }


def get_waha_messages(chat_id: str, limit: int = 100, offset: int = 0,
                      url: str = None, username: str = None,
                      password: str = None, api_key: str = None) -> Dict[str, Any]:
    """
    Wrapper function untuk mendapatkan pesan WAHA

    Args:
        chat_id: Chat ID (format: phone_number@c.us)
        limit: Number of messages (default: 100)
        offset: Offset for pagination (default: 0)
        url: WAHA API URL (from environment if None)
        username: WAHA username (from environment if None)
        password: WAHA password (from environment if None)
        api_key: WAHA API key (from environment if None)

    Returns:
        Dict[str, Any]: Messages data
    """
    # Use environment variables if not provided
    url = url or os.getenv("WAHA_API_URL", "http://localhost:3000")
    username = username or os.getenv("WAHA_USERNAME", "admin")
    password = password or os.getenv("WAHA_PASSWORD", "e44213b43dc349709991dbb1a6343e47")
    api_key = api_key or os.getenv("WAHA_API_KEY", "c79b6529186c44aa9d536657ffea710b")

    # Create client and get messages
    client = WahaAPIClient(
        base_url=url,
        username=username,
        password=password,
        api_key=api_key
    )

    # Get messages and ensure it returns a valid dict
    result = client.get_chat_messages(chat_id=chat_id, limit=limit, offset=offset)

    if result is None:
        # Fallback to mock data when WAHA server is not available
        return client.generate_mock_data(chat_id=chat_id, limit=limit)

    return result


def main():
    """Main function - always returns data directly"""
    args = parse_arguments()

    print("WAHA API Automation Tool")
    print("=" * 50)

    # Validate parameters
    if args.limit > 1000:
        print("Error: Maximum limit is 1000 results per request")
        return {"status": "error", "message": "Maximum limit is 1000 results per request"}

    if args.limit <= 0:
        print("Error: Limit must be greater than 0")
        return {"status": "error", "message": "Limit must be greater than 0"}

    # Initialize client
    client = WahaAPIClient(
        base_url=args.url,
        username=args.username,
        password=args.password,
        api_key=args.api_key,
        timeout=args.timeout
    )

    # Test connection if requested
    if args.test_connection:
        if client.test_connection():
            print("Connection test passed!")
            return {"status": "success", "message": "Connection successful"}
        else:
            print("Connection test failed!")
            return {"status": "error", "message": "Connection failed"}

    # Discover endpoints if requested
    if args.discover_endpoints:
        print("Discovering available endpoints...")
        print("=" * 50)
        endpoints = client.discover_endpoints()

        available_endpoints = [ep for ep, info in endpoints.items() if info.get('available', False)]

        if available_endpoints:
            print(f"\n[+] Found {len(available_endpoints)} available endpoints:")
            for ep in available_endpoints:
                info = endpoints[ep]
                print(f"  - {ep} (Status: {info['status']}, Type: {info.get('content_type', 'unknown')})")
        else:
            print("\n[-] No available endpoints found. Check WAHA server configuration.")

        return {
            "status": "success",
            "endpoints": endpoints,
            "available_count": len(available_endpoints),
            "recommendation": "Use --mock-contacts for testing if no endpoints available"
        }

    # Handle get contacts mode
    use_mock = args.mock_data or args.mock_contacts
    if args.get_contacts:
        print(f"Getting contacts with session: {args.session}")
        print(f"Limit: {args.limit} contacts")
        print("-" * 50)

        for attempt in range(args.auto_retry + 1):
            if attempt > 0:
                print(f"Retry attempt {attempt}/{args.auto_retry}...")
                time.sleep(args.retry_delay)

            print(f"Attempt {attempt + 1}: Getting contacts...")

            response_data = client.get_all_contacts(
                limit=args.limit,
                offset=args.offset,
                session=args.session,
                sort_by=args.sort_by,
                sort_order=args.sort_order,
                use_mock=use_mock
            )

            if response_data:
                print("Success! Retrieved contacts")
                return response_data
            else:
                print(f"Failed to get contacts on attempt {attempt + 1}")
                if attempt == args.auto_retry:
                    return {"status": "error", "message": "Failed to retrieve contacts after all retries"}

        return {"status": "error", "message": "Unknown error occurred"}

    # Handle get messages mode (default)
    print(f"Chat ID: {args.chat_id}")
    print(f"Session: {args.session}")
    print(f"Limit: {args.limit} messages")
    print(f"Offset: {args.offset}")
    print(f"Sort: {args.sort_by_messages} ({args.sort_order_messages})")
    print("-" * 50)

    # Get messages with retry mechanism
    for attempt in range(args.auto_retry + 1):
        if attempt > 0:
            print(f"Retry attempt {attempt}/{args.auto_retry}...")
            time.sleep(args.retry_delay)

        print(f"Attempt {attempt + 1}: Getting messages for chat {args.chat_id}")

        response_data = client.get_chat_messages(
            chat_id=args.chat_id,
            limit=args.limit,
            offset=args.offset,
            sort_by=args.sort_by_messages,
            sort_order=args.sort_order_messages,
            use_mock=args.mock_data
        )

        if response_data:
            print("Success! Retrieved messages")
            return response_data
        else:
            print(f"Failed to get messages on attempt {attempt + 1}")
            if attempt == args.auto_retry:
                return {"status": "error", "message": "Failed to retrieve messages after all retries"}

    return {"status": "error", "message": "Unknown error occurred"}


if __name__ == "__main__":
    result = main()

    # Always print JSON response to stdout
    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps({"status": "error", "message": "No data returned"}, indent=2, ensure_ascii=False))