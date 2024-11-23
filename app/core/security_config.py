"""
Security configuration and validation.
"""
from typing import List, Optional, Dict, Tuple
from pydantic import BaseModel, Field, validator
import ipaddress
from datetime import timedelta
import re

class AuthConfig(BaseModel):
    """Authentication configuration."""
    require_auth: bool = True
    admin_user: str = "admin"
    admin_password: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    token_expiry: timedelta = timedelta(hours=24)
    refresh_token_expiry: timedelta = timedelta(days=7)
    max_failed_attempts: int = 5
    lockout_duration: timedelta = timedelta(minutes=15)
    password_min_length: int = 12
    password_require_special: bool = True
    password_require_numbers: bool = True
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    session_timeout: int = 3600  # seconds
    max_sessions_per_user: int = 5

    @validator("admin_password")
    def validate_password(cls, v):
        if not v:
            raise ValueError("Admin password must be set")
        return v

    @validator("jwt_secret_key")
    def validate_jwt_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters long")
        return v

class AccessControlConfig(BaseModel):
    """Access control configuration."""
    whitelist_domains: List[str] = Field(default_factory=list)
    whitelist_ips: List[str] = Field(default_factory=list)
    protected_paths: List[str] = Field(default_factory=list)
    public_paths: List[str] = [
        "/static",
        "/favicon.ico",
        "/login",
        "/api/auth/login",
        "/health"
    ]
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
    cors_allow_origins: List[str] = Field(default_factory=list)
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE"]
    cors_allow_headers: List[str] = ["Authorization", "Content-Type"]
    cors_expose_headers: List[str] = ["Content-Length"]
    cors_max_age: int = 3600

    @validator("whitelist_ips")
    def validate_ips(cls, v):
        valid_ips = []
        for ip in v:
            try:
                if "/" in ip:  # CIDR notation
                    ipaddress.ip_network(ip)
                else:
                    ipaddress.ip_address(ip)
                valid_ips.append(ip)
            except ValueError as e:
                raise ValueError(f"Invalid IP address or CIDR: {ip}")
        return valid_ips

    @validator("whitelist_domains")
    def validate_domains(cls, v):
        domain_pattern = re.compile(r'^(\*\.)?([\w\-]+\.)*[\w\-]+$')
        invalid_domains = [d for d in v if not domain_pattern.match(d)]
        if invalid_domains:
            raise ValueError(f"Invalid domain patterns: {invalid_domains}")
        return v

class SecurityConfig(BaseModel):
    """Global security configuration."""
    auth: AuthConfig
    access_control: AccessControlConfig
    enable_audit_log: bool = True
    audit_log_path: str = "logs/audit.log"
    enable_request_validation: bool = True
    enable_response_validation: bool = True
    enable_content_security_policy: bool = True
    content_security_policy: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "default-src": ["'self'"],
            "script-src": ["'self'"],
            "style-src": ["'self'"],
            "img-src": ["'self'", "data:"],
            "font-src": ["'self'"],
            "connect-src": ["'self'"],
        }
    )
    secure_headers: Dict[str, str] = Field(
        default_factory=lambda: {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
    )

    class Config:
        arbitrary_types_allowed = True

def load_security_config() -> SecurityConfig:
    """Load security configuration from environment."""
    from app.config import config
    
    auth_config = AuthConfig(
        require_auth=config.REQUIRE_AUTH,
        admin_user=config.ADMIN_USER,
        admin_password=config.ADMIN_PASSWORD,
        jwt_secret_key=config.JWT_SECRET_KEY,
        session_timeout=config.SESSION_TIMEOUT
    )
    
    access_control = AccessControlConfig(
        whitelist_domains=config.WHITELIST_DOMAINS,
        whitelist_ips=config.WHITELIST_IPS,
        cors_allow_origins=config.CORS_ALLOW_ORIGINS,
        rate_limit_per_minute=config.RATE_LIMIT_PER_MINUTE,
        rate_limit_burst=config.RATE_LIMIT_BURST
    )
    
    return SecurityConfig(
        auth=auth_config,
        access_control=access_control
    )

# Create global security config instance
security_config = load_security_config()
