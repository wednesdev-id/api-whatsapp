"""
Configuration Settings for WAHA FastAPI Application
"""

import os
import secrets
from datetime import datetime
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings as PydanticBaseSettings


class Settings(PydanticBaseSettings):
    """Application settings"""

    # WAHA API Configuration
    WAHA_API_URL: str = "http://localhost:3000"
    WAHA_USERNAME: str = "admin"
    WAHA_PASSWORD: str = "e44213b43dc349709991dbb1a6343e47"
    WAHA_API_KEY: str = "c79b6529186c44aa9d536657ffea710b"

    # Application Configuration
    APP_NAME: str = "WAHA FastAPI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_SECRET: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # API Authentication
    API_SECRET_KEY: str = "your-api-secret-key-change-this"

    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["*"]
    ALLOWED_HOSTS: List[str] = ["*"]

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 900  # 15 minutes

    # Auto-Response Configuration
    AUTO_RESPONSE_ENABLED: bool = True
    RESPONSE_DELAY_MS: int = 1000
    DEFAULT_SESSION: str = "default"

    # Webhook Configuration
    WEBHOOK_SECRET: str = "webhook-secret-key"
    WEBHOOK_VERIFY_TOKEN: str = "webhook-verify-token"

    # Cache Configuration
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 300

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "waha-fastapi.log"

    # Monitoring
    METRICS_ENABLED: bool = True
    HEALTH_CHECK_INTERVAL: int = 30

    # Pagination Defaults
    DEFAULT_LIMIT: int = 100
    MAX_LIMIT: int = 1000
    DEFAULT_OFFSET: int = 0

    # Timeout Configuration
    REQUEST_TIMEOUT: int = 30
    WAHA_TIMEOUT: int = 30

    @field_validator("DEBUG", mode="before")
    @classmethod
    def set_debug_mode(cls, v):
        """Set debug mode based on environment"""
        if os.getenv("DEBUG_MODE") == "true":
            return True
        return v

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def set_environment(cls, v):
        """Set environment from NODE_ENV or ENVIRONMENT"""
        return os.getenv("NODE_ENV", os.getenv("ENVIRONMENT", "development"))

    @field_validator("WAHA_API_URL", mode="before")
    @classmethod
    def validate_waha_url(cls, v):
        """Validate WAHA API URL"""
        if not v:
            raise ValueError("WAHA_API_URL is required")
        return v.rstrip("/")

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse allowed origins from comma-separated string"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        """Parse allowed hosts from comma-separated string"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",") if host.strip()]
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True
    }

    def get_current_time(self) -> str:
        """Get current time in ISO format"""
        return datetime.utcnow().isoformat() + "Z"

    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT.lower() == "development"

    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT.lower() == "production"

    def get_cors_origins(self) -> List[str]:
        """Get CORS origins based on environment"""
        if self.is_development():
            return ["*"]
        return self.ALLOWED_ORIGINS


# Create settings instance
settings = Settings()