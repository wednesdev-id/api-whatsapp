# WAHA FastAPI - WhatsApp HTTP API Automation System

Complete WhatsApp API automation system built with FastAPI, deployed on Vercel with advanced features including auto-response, message handling, template system, and comprehensive monitoring.

## 🚀 What's New

### Latest Updates (December 2024)
- **Complete Python Migration**: Fully converted from JavaScript to Python FastAPI
- **Simplified Architecture**: Streamlined codebase with improved performance
- **WAHA Automator Integration**: Real WhatsApp functionality via `waha_automator.py`
- **🆕 Chat Management**: New `/api/waba/chats` endpoint with sorting and pagination
- **Enhanced Development**: Better DX with FastAPI CLI support and hot reload
- **Modern Python Stack**: Updated to latest FastAPI 0.104+ with async support

## Features

### Core Functionality
- **WAHA API Integration** - Seamless connection to WAHA WhatsApp Gateway
- **Real WAHA Automation** - Automatically triggers WAHA automator on endpoint calls
- **🆕 Chat Management** - Get chats list with sorting, filtering, and pagination
- **Message Management** - Send/receive messages, manage contacts, and chat history
- **Auto-Response Engine** - Intelligent keyword-based and rule-based automation
- **Smart Webhook Processing** - Real WhatsApp message sending via WAHA server
- **Fallback Mode** - Mock responses when WAHA server is unavailable
- **Analytics & Monitoring** - Comprehensive logging and performance metrics

### Advanced Features
- **FastAPI Framework** - Modern async Python web framework with automatic docs
- **CORS Support** - Cross-origin resource sharing enabled
- **Auto Documentation** - Interactive API documentation with Swagger/OpenAPI
- **Pydantic Validation** - Type-safe request/response validation
- **Async Support** - Non-blocking request handling for better performance

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend/UI   │────│  FastAPI App    │────│   WAHA Server   │
│                 │    │                 │    │                 │
│ - Dashboard     │    │ - Async Endpoints│   │ - WhatsApp API  │
│ - Monitoring    │    │ - Pydantic Models│   │ - Session Mgmt  │
│ - Analytics     │    │ - Auto-Response │   │ - Message Queue │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                    ┌─────────────────┐
                    │ WAHA Automator │
                    │                 │
                    │ - Real WhatsApp │
                    │ - Fallback Mode │
                    │ - HTTP Client   │
                    └─────────────────┘
```

## Project Structure

```
test_waha/
├── api/                            # FastAPI application modules
│   ├── core/                       # Core functionality
│   │   ├── config.py              # Configuration management
│   │   ├── exceptions.py          # Custom exception handling
│   │   └── waha_client.py         # WAHA API client with HTTP requests
│   └── routes/                    # API route handlers
│       ├── contacts.py            # Contact management endpoints
│       ├── health.py              # Health check and monitoring
│       ├── messages.py            # Message retrieval endpoints
│       ├── send.py                # Message sending endpoints
│       └── webhook.py             # Webhook event handling
├── main.py                        # FastAPI application entry point
├── waha_automator.py              # WAHA automation script (real WhatsApp integration)
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Python project configuration
├── vercel.json                    # Vercel deployment settings
├── README.md                      # This documentation file
├── .gitignore                     # Git ignore rules
├── .claude/                       # Claude Code configuration
└── .env.example                   # Environment variables template (create if needed)
```

### Key Files Description

- **[`main.py`](main.py)**: Main FastAPI application with all endpoints and auto-response logic
- **[`waha_automator.py`](waha_automator.py)**: WAHA API client for real WhatsApp integration
- **[`pyproject.toml`](pyproject.toml)**: Modern Python project configuration with dependencies
- **[`vercel.json`](vercel.json)**: Vercel deployment configuration for serverless hosting

## Installation & Setup

### Prerequisites
- Python >= 3.8 (recommended 3.9+)
- WAHA Server running (local or remote) - optional, has fallback mode
- Vercel account (for deployment)

### Local Development Setup

1. **Navigate to the project directory**
```bash
cd "d:\MY WORK\Study Case\test_waha"
```

2. **Install Python dependencies**
```bash
# Install all required packages from requirements.txt
pip install -r requirements.txt

# Or install using pyproject.toml (modern approach)
pip install -e .

# Core packages manually (minimum required)
pip install fastapi uvicorn[standard] httpx requests pydantic pydantic-settings
```

3. **Configure environment variables (optional)**
```bash
# Create .env file for local configuration
# Note: The app works without .env file with default settings
echo "WAHA_API_URL=http://localhost:3000" > .env
echo "DEBUG=true" >> .env
echo "AUTO_RESPONSE_ENABLED=true" >> .env
```

### 🚀 Running the Application

#### Method 1: FastAPI CLI (Recommended)
```bash
# Start development server with hot reload
fastapi dev main.py

# Or with custom host/port
fastapi dev main.py --host 0.0.0.0 --port 8000
```

#### Method 2: Uvicorn Server (Traditional)
```bash
# Start development server with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start production server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Method 3: Direct Python Execution
```bash
# Run the main application directly
python main.py
```

#### Method 4: Python Module
```bash
# Run as module
python -m main
```

### Access Points

Once running, access the application at:

- **Main Application**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **Alternative Documentation (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Deployment to Vercel

1. **Install Vercel CLI**
```bash
npm install -g vercel
```

2. **Login to Vercel**
```bash
vercel login
```

3. **Deploy to production**
```bash
vercel --prod
```

4. **Set environment variables in Vercel dashboard**:
   - `WAHA_API_URL`
   - `WAHA_USERNAME`
   - `WAHA_PASSWORD`
   - `WAHA_API_KEY`
   - `JWT_SECRET`
   - `API_SECRET_KEY`

## 🔄 WAHA Automation Integration

### How It Works

The system integrates with `waha_automator.py` to provide real WhatsApp functionality:

```
WhatsApp Message
        ↓
Webhook Event
        ↓
FastAPI Endpoint
        ↓
WAHA Automator (waha_automator.py)
        ↓
Real WAHA Server
        ↓
Message Sent
```

### Smart Fallback System

#### **With WAHA Server Running:**
- **Send Message**: Real WhatsApp delivery via WAHA API
- **Webhook Processing**: Automatic responses sent to WhatsApp
- **Get Messages/Contacts**: Real data from WAHA server

#### **Without WAHA Server (Fallback Mode):**
- **Mock Data**: Returns realistic sample responses
- **Auto-Response**: Generated and displayed (not sent)
- **Development Friendly**: App works immediately without setup

### Integration Status

Check current WAHA automator status:
```bash
curl http://localhost:8000/api/waba/health
```

Response shows integration status:
```json
{
  "services": {
    "waha_automator": {
      "status": "available" | "unavailable",
      "enabled": true
    }
  },
  "features": {
    "real_waha_integration": true | false
  }
}
```

### 🧪 Test WAHA Integration

```bash
# Test sending message (real if WAHA available, mock otherwise)
curl -X POST http://localhost:8000/api/waba/send \
  -H "Content-Type: application/json" \
  -d '{"chatId": "628123456789@c.us", "message": "Test WAHA"}'

# Test webhook with auto-response
curl -X POST http://localhost:8000/api/waba/webhook \
  -H "Content-Type: application/json" \
  -d '{"event": "message", "data": {"from": "628123456789@c.us", "body": "Hello"}}'
```

## 🚀 Quick Start Guide

### 1. **Test in 2 Minutes**
```bash
# 1. Navigate to project
cd "d:\MY WORK\Study Case\test_waha"

# 2. Install dependencies
pip install fastapi uvicorn

# 3. Run the server (choose one method)
# FastAPI CLI (recommended):
fastapi dev main.py
# Or traditional uvicorn:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. **Test Auto-Response**
```bash
# Test auto-response (using curl or any API client)
curl -X POST http://localhost:8000/api/waba/test-auto-response \
  -H "Content-Type: application/json" \
  -d '{"message": "Halo, saya ingin bertanya"}'
```

### 3. **Explore API Documentation**
Open your browser and navigate to:
- **Swagger Docs**: http://localhost:8000/docs (interactive!)
- **Health Check**: http://localhost:8000/api/waba/health
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Base URL
```
Local: http://localhost:8000
Production: https://your-vercel-app.vercel.app
```

### 📋 Complete Endpoint List

#### 1. **Application Information**
- `GET /` - Root endpoint with app info and documentation links
- `GET /health` - Simple health check with basic status
- `GET /api/waba/health` - Comprehensive WAHA health check with service status

#### 2. **Message Management**
- `GET /api/waba/messages` - Get messages with pagination and filtering
- `POST /api/waba/send` - Send message to WhatsApp (real or mock mode)

#### 3. **Contact Management**
- `GET /api/waba/contacts` - Get contacts list with pagination

#### 4. **Chat Management** 🆕
- `GET /api/waba/chats` - Get chats list with sorting and pagination

#### 5. **Auto-Response System**
- `POST /api/waba/test-auto-response` - Test auto-response functionality without sending

#### 6. **Webhook Handling**
- `POST /api/waba/webhook` - Handle WhatsApp webhook events with auto-response

#### 7. **Documentation**
- `GET /docs` - Interactive Swagger documentation (try it out!)
- `GET /redoc` - Alternative ReDoc documentation
- `GET /openapi.json` - OpenAPI schema for integration

### 🧪 Quick Testing Examples

```bash
# Test health check
curl http://localhost:8000/api/waba/health

# Test auto-response
curl -X POST http://localhost:8000/api/waba/test-auto-response \
  -H "Content-Type: application/json" \
  -d '{"message": "Halo, saya ingin bertanya"}'

# Send a message (will use WAHA if available, otherwise mock)
curl -X POST http://localhost:8000/api/waba/send \
  -H "Content-Type: application/json" \
  -d '{"chatId": "628123456789@c.us", "message": "Test message"}'

# Get messages
curl "http://localhost:8000/api/waba/messages?chatId=628123456789@c.us&limit=10"

# Get chats (NEW!) - with sorting and pagination
curl "http://localhost:8000/api/waba/chats?sortBy=name&sortOrder=desc&limit=100&offset=0"

# Get contacts
curl "http://localhost:8000/api/waba/contacts?limit=10"
```

### 🔐 Authentication
Currently, all endpoints work without authentication for easy testing. The system supports:
- API Key Authentication (can be enabled in production)
- JWT Authentication (planned feature)
- Webhook signature verification (for security)

**Note**: In development mode, authentication is disabled for convenience.

### Health Check Endpoints

#### Root Endpoint
```http
GET /
```

**Response:**
```json
{
  "message": "WAHA FastAPI - WhatsApp HTTP API Automation System",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

#### Simple Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-15T11:00:00.000Z",
  "version": "1.0.0"
}
```

#### WABA Health Check
```http
GET /api/waba/health
```

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2025-12-15T11:00:00.000Z",
    "responseTime": "45ms",
    "version": "1.0.0",
    "services": {
      "waha_api": {
        "status": "connected",
        "url": "http://localhost:3000"
      },
      "environment": {
        "status": "configured"
      }
    },
    "features": {
      "authentication": true,
      "rate_limiting": true,
      "auto_response": true,
      "webhook": true
    }
  }
}
```

### Message Endpoints

#### Get Messages
```http
GET /api/waba/messages?chatId=628123456789@c.us&limit=100&offset=0
```

**Query Parameters:**
- `chatId` (string): WhatsApp chat ID (default: "default@c.us")
- `limit` (int): Number of messages to return (default: 100)
- `offset` (int): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": "msg_001",
        "from": "628123456789@c.us",
        "to": "628987654321@c.us",
        "body": "Sample message",
        "timestamp": "2025-12-15T04:00:00.000Z",
        "fromMe": false
      }
    ],
    "total": 1,
    "limit": 100,
    "offset": 0
  }
}
```

### Chat Endpoints 🆕

#### Get Chats
```http
GET /api/waba/chats?session=default&sortBy=name&sortOrder=desc&limit=100&offset=0
```

**Query Parameters:**
- `session` (string): WhatsApp session ID (default: "default")
- `sortBy` (string): Field to sort by (name, timestamp, lastMessage) (default: "name")
- `sortOrder` (string): Sort order (asc, desc) (default: "desc")
- `limit` (int): Number of chats to return (default: 100)
- `offset` (int): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "chats": [
      {
        "id": "628123456789@c.us",
        "name": "John Doe",
        "lastMessage": "Hello, how are you?",
        "timestamp": 1704240000,
        "unreadCount": 2,
        "isGroup": false,
        "isOnline": true
      },
      {
        "id": "120363419906557011@g.us",
        "name": "Family Group",
        "lastMessage": "Shared a photo",
        "timestamp": 1704236400,
        "unreadCount": 5,
        "isGroup": true,
        "participants": 25
      }
    ],
    "total": 2,
    "limit": 100,
    "offset": 0,
    "hasMore": false,
    "page": 1,
    "total_pages": 1,
    "sortBy": "name",
    "sortOrder": "desc",
    "session": "default"
  }
}
```

**Usage Examples:**
```bash
# Get all chats sorted by name (descending)
curl "http://localhost:8000/api/waba/chats?sortBy=name&sortOrder=desc&limit=100&offset=0"

# Get chats sorted by most recent message
curl "http://localhost:8000/api/waba/chats?sortBy=timestamp&sortOrder=desc&limit=20"

# Get chats with pagination (page 2)
curl "http://localhost:8000/api/waba/chats?sortBy=name&limit=50&offset=50"

# Get chats for specific session
curl "http://localhost:8000/api/waba/chats?session=mySession&sortBy=name&sortOrder=asc"
```

### Contact Endpoints

#### Get Contacts
```http
GET /api/waba/contacts?limit=100&offset=0
```

**Query Parameters:**
- `limit` (int): Number of contacts to return (default: 100)
- `offset` (int): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "contacts": [
      {
        "id": "628123456789@c.us",
        "name": "John Doe",
        "phone": "+62 812-3456-7890",
        "isMyContact": true,
        "isWaContact": true
      }
    ],
    "total": 1,
    "limit": 100,
    "offset": 0
  }
}
```

### Send Message Endpoints

#### Send Single Message
```http
POST /api/waba/send
Content-Type: application/json

{
  "chatId": "628123456789@c.us",
  "message": "Hello, World!",
  "type": "text",
  "session": "default"
}
```

**Request Body:**
- `chatId` (string, required): WhatsApp chat ID
- `message` (string, required): Message content
- `type` (string, optional): Message type (default: "text")
- `session` (string, optional): WhatsApp session (default: "default")

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Message sent successfully",
    "chatId": "628123456789@c.us",
    "session": "default",
    "auto_response": "Halo! Terima kasih telah menghubungi kami.",
    "timestamp": "2025-12-15T11:00:00.000Z"
  }
}
```

### Auto-Response Endpoints

#### Test Auto-Response
```http
POST /api/waba/test-auto-response
Content-Type: application/json

{
  "message": "Halo, selamat pagi",
  "chatId": "628123456789@c.us",
  "session": "default",
  "type": "text"
}
```

**Request Body:**
- `message` (string, required): Message to test auto-response
- `chatId` (string, optional): Chat ID (default: "default@c.us")
- `session` (string, optional): Session ID (default: "default")
- `type` (string, optional): Message type (default: "text")

**Response:**
```json
{
  "success": true,
  "data": {
    "original_message": "Halo, selamat pagi",
    "auto_response": "Halo! Terima kasih telah menghubungi kami. Ada yang bisa kami bantu?",
    "response_generated": true,
    "timestamp": "2025-12-15T11:00:00.000Z"
  }
}
```

### Webhook Endpoints

#### Handle WhatsApp Events
```http
POST /api/waba/webhook
Content-Type: application/json
X-Waha-Signature: sha256=...

{
  "event": "message",
  "session": "default",
  "data": {
    "id": "msg_123",
    "from": "628123456789@c.us",
    "to": "628987654321@c.us",
    "body": "Hello",
    "timestamp": 1234567890,
    "fromMe": false
  }
}
```

**Request Body:**
- `event` (string): Event type ("message", "messageAck", "sessionStatus")
- `session` (string): WhatsApp session ID
- `data` (object): Event data

**Response:**
```json
{
  "success": true,
  "data": {
    "event_processed": "message",
    "auto_response_generated": true,
    "auto_response": "Halo! Terima kasih telah menghubungi kami.",
    "timestamp": "2025-12-15T11:00:00.000Z"
  }
}
```

## Auto-Response System

### Built-in Response Templates

The system includes intelligent auto-responders for common scenarios:

#### Greetings
**Keywords:** "Halo", "Hi", "Assalamualaikum", "Hello"
**Response:** "Halo! Terima kasih telah menghubungi kami. Ada yang bisa kami bantu?"

#### Thanks
**Keywords:** "Thank you", "Terima kasih", "Makasih"
**Response:** "Sama-sama! Senang bisa membantu Anda."

#### Help
**Keywords:** "Help", "Bantuan", "Tolong"
**Response:** "Bantuan tersedia! Silakan jelaskan masalah Anda dan kami akan segera membantu."

#### Business
**Keywords:** "Harga", "Produk", "Layanan"
**Response:**
```
Informasi bisnis:
• Produk: Tersedia berbagai pilihan
• Harga: Kompetitif dan terjangkau
• Layanan: 24/7 support

Untuk info detail, silakan hubungi admin kami.
```

#### Location
**Keywords:** "Lokasi", "Alamat"
**Response:**
```
Lokasi kami:
Jl. Contoh No. 123, Jakarta

Jam operasional: 08:00 - 22:00 WIB
```

#### Contact
**Keywords:** "Kontak", "Hubungi"
**Response:**
```
Kontak kami:
• WhatsApp: +62 812-3456-7890
• Email: info@contoh.com
• Website: www.contoh.com
```

## Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```env
# WAHA API Configuration
WAHA_API_URL=http://localhost:3000
WAHA_USERNAME=admin
WAHA_PASSWORD=e44213b43dc349709991dbb1a6343e47
WAHA_API_KEY=c79b6529186c44aa9d536657ffea710b

# Application Configuration
APP_NAME=WAHA FastAPI
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true

# Authentication
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
API_SECRET_KEY=your-api-secret-key-change-this

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=900

# Auto-Response Configuration
AUTO_RESPONSE_ENABLED=true
RESPONSE_DELAY_MS=1000
DEFAULT_SESSION=default

# Webhook Configuration
WEBHOOK_SECRET=webhook-secret-key
WEBHOOK_VERIFY_TOKEN=webhook-verify-token

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=waha-fastapi.log

# Monitoring
METRICS_ENABLED=true
HEALTH_CHECK_INTERVAL=30

# Pagination Defaults
DEFAULT_LIMIT=100
MAX_LIMIT=1000
DEFAULT_OFFSET=0

# Timeout Configuration
REQUEST_TIMEOUT=30
WAHA_TIMEOUT=30
```

## WAHA Server Setup

### Docker Setup (Recommended)
```bash
docker run -d \
  --name waha \
  -p 3000:3000 \
  -e WAHA_API_KEY=your-api-key \
  -e WAHA_USERNAME=admin \
  -e WAHA_PASSWORD=your-password \
  devlikeapro/waha
```

### Local Setup
1. Install WAHA following [official documentation](https://waha.devlike.pro/docs/)
2. Configure WAHA with your credentials
3. Start WAHA server
4. Scan QR code to connect WhatsApp

### Webhook Configuration
```bash
# Set webhook in WAHA
curl -X POST http://localhost:3000/api/sessions/default/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-vercel-app.vercel.app/api/waba/webhook",
    "events": ["message", "messageAck", "sessionStatus"],
    "secret": "webhook-secret-key"
  }'
```

## Monitoring & Analytics

### Health Check Response
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2025-12-15T10:30:00.000Z",
    "responseTime": "45ms",
    "version": "1.0.0",
    "services": {
      "waha_api": {
        "status": "connected",
        "url": "http://localhost:3000"
      },
      "environment": {
        "status": "configured"
      }
    },
    "features": {
      "authentication": true,
      "rate_limiting": true,
      "auto_response": true,
      "webhook": true
    }
  }
}
```

### Built-in Metrics

The system automatically tracks:
- Total requests processed
- Response time statistics
- Error rates
- Active sessions
- Auto-response effectiveness

### Request IDs

Every request gets a unique ID for tracking:
```json
{
  "metadata": {
    "request_id": "req_1234567890_abc123def456",
    "timestamp": "2025-12-15T10:30:00.000Z"
  }
}
```

## Security Features

### Authentication Methods

1. **API Key Authentication**
```http
GET /api/waba/messages
X-API-Key: your-api-secret-key
```

2. **JWT Authentication**
```http
GET /api/waba/messages
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Rate Limiting

- **Authenticated users**: 100 requests per 15 minutes
- **API Keys**: 200 requests per 15 minutes
- **Unauthenticated**: 10 requests per 15 minutes
- **Webhooks**: 1000 requests per minute

### Input Validation

All inputs are automatically:
- Sanitized for HTML/XSS attacks
- Validated for proper format
- Limited to safe lengths
- Rate limited

### Security Headers

Automatic security headers in production:
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` (HTTPS only)
- Content Security Policy

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run tests with coverage
pytest --cov=api --cov-report=html
```

### Code Quality
```bash
# Install development dependencies
pip install black isort flake8 mypy

# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type checking
mypy .
```

### Local Development
```bash
# Enable debug mode
export DEBUG=true
export LOG_LEVEL=debug

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Open API docs
# http://localhost:8000/docs
```

### Mock Data Testing
Enable mock mode for testing without WAHA server:
```bash
# Use mock data
GET /api/waba/messages?useMock=true&chatId=628123456789@c.us

# Mock contacts
GET /api/waba/contacts?useMock=true
```

## Performance Optimization

### Caching
- Template caching with configurable TTL
- Response caching for frequently accessed data
- Session-based caching for user preferences

### Rate Limiting
- Adaptive rate limiting based on user behavior
- Different limits for different user types
- Automatic penalty for abusive behavior

### Connection Pooling
- HTTPX async client with connection pooling
- Configurable timeouts and retry logic
- Optimized for serverless environments

### Memory Management
- Automatic cleanup of expired sessions
- Efficient message queue processing
- Memory-leak prevention

## API Documentation

### Interactive Documentation
When running locally, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Response Format

All API responses follow consistent format:
```json
{
  "success": true|false,
  "data": { ... }, // Response data (if successful)
  "error": "Error message", // Error message (if failed)
  "code": "ERROR_CODE", // Error code (if failed)
  "metadata": {
    "responseTime": "45ms",
    "timestamp": "2025-12-15T10:30:00.000Z",
    "requestId": "req_1234567890_abc123"
  }
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `AUTH_REQUIRED` | Authentication required |
| `INVALID_TOKEN` | Invalid or expired token |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `VALIDATION_ERROR` | Invalid parameters |
| `SERVICE_UNAVAILABLE` | WAHA service down |
| `SESSION_ERROR` | WhatsApp session issue |
| `INTERNAL_ERROR` | Server error |
| `SCAN_QR_REQUIRED` | WhatsApp needs QR scan |
| `MESSAGE_TOO_LONG` | Message exceeds length limit |

## Deployment

### Vercel Deployment

1. **Install Vercel CLI**
```bash
npm i -g vercel
```

2. **Login to Vercel**
```bash
vercel login
```

3. **Configure Project**
```bash
# Link to your GitHub repository
vercel link

# Set environment variables in Vercel dashboard
# or use .env file
```

4. **Deploy**
```bash
# Deploy to production
vercel --prod

# Deploy to preview
vercel
```

### Environment Variables in Vercel

Set these in your Vercel dashboard:
- `WAHA_API_URL`: Your WAHA server URL
- `WAHA_USERNAME`: WAHA username
- `WAHA_PASSWORD`: WAHA password
- `WAHA_API_KEY`: WAHA API key
- `JWT_SECRET`: Secret for JWT tokens
- `API_SECRET_KEY`: Secret for API key auth
- `WEBHOOK_SECRET`: Secret for webhook security

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t waha-fastapi .
docker run -p 8000:8000 waha-fastapi
```

## Troubleshooting

### Common Issues & Solutions

#### **Server Won't Start**
```bash
# Check if port 8000 is already in use
netstat -ano | findstr :8000

# Kill existing processes (Windows)
taskkill /PID <PID> /F

# Use different port
uvicorn main:app --port 8001
```

#### **Import Errors**
```bash
# Install missing dependencies
pip install -r requirements.txt

# Check Python version (must be 3.8+)
python --version

# Install FastAPI specifically
pip install fastapi uvicorn[standard]
```

#### **Auto-Response Not Working**
```bash
# Check environment variables
echo $AUTO_RESPONSE_ENABLED

# Test with simple endpoint
curl -X POST http://localhost:8000/api/waba/test-auto-response \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

#### **Cannot Access API Documentation**
```bash
# Check if server is running
curl http://localhost:8000/health

# Try different browser or clear cache
# Access: http://localhost:8000/docs
```

### 🔍 Advanced Troubleshooting

#### WAHA Connection Failed
```bash
# Check WAHA server status
curl http://localhost:3000/api/sessions

# Verify credentials
curl -u admin:password http://localhost:3000/api/sessions
```

#### Auto-Response Not Working
1. Check `AUTO_RESPONSE_ENABLED=true`
2. Verify WAHA session is active
3. Check webhook configuration
4. Review logs for errors

#### Rate Limiting Issues
```bash
# Check current rate limit status
curl -H "X-API-Key: your-key" https://your-app.vercel.app/api/waba/health
```

#### Import Errors
```bash
# Check Python version
python --version  # Should be 3.8+

# Install dependencies manually
pip install fastapi uvicorn httpx pydantic pydantic-settings

# Check requirements file
cat requirements.txt
```

### Debug Mode

Enable detailed logging:
```bash
export DEBUG=true
export LOG_LEVEL=debug
python main.py
```

### Health Check Issues

Comprehensive health check:
```bash
# Check application health
curl https://your-app.vercel.app/api/waba/health

# Check WAHA connection
curl https://your-app.vercel.app/api/waba/health/waha
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Guidelines
- Follow existing code style
- Add tests for new features
- Update documentation
- Ensure all tests pass

### Code Structure

```
api/
├── __init__.py
├── core/           # Core functionality
│   ├── config.py      # Configuration management
│   ├── waha_client.py # WAHA API client
│   └── exceptions.py   # Custom exceptions
├── middleware/      # Custom middleware
│   ├── auth_middleware.py       # Authentication
│   ├── rate_limit_middleware.py # Rate limiting
│   ├── logging_middleware.py    # Logging
│   └── validation_middleware.py  # Input validation
├── routes/         # API routes
│   ├── health.py      # Health check endpoints
│   ├── messages.py   # Message endpoints
│   ├── contacts.py   # Contact endpoints
│   ├── send.py       # Send message endpoints
│   └── webhook.py    # Webhook endpoints
└── main.py          # FastAPI application
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [GitHub Wiki](https://github.com/your-username/waha-vercel-api/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-username/waha-vercel-api/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/waha-vercel-api/discussions)

## 🙏 Acknowledgments

- [WAHA](https://github.com/devlikeapro/waha) - WhatsApp HTTP API
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Vercel](https://vercel.com/) - Serverless platform
- [Uvicorn](https://www.uvicorn.org/) - ASGI server
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation

---

**Made with ❤️ and FastAPI for WhatsApp automation**

If this project helps you, please give it a ⭐ on GitHub!