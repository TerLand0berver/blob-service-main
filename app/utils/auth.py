"""
Authentication utility functions.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from app.core.security_config import security_config
import redis
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Redis client for token blacklist
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

class TokenData(BaseModel):
    """Token data model."""
    username: str
    exp: datetime
    token_type: str

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash using constant-time comparison.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification failed: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    """
    Generate password hash using bcrypt.
    """
    return pwd_context.hash(password)

def create_token(
    data: Dict[str, Any],
    expires_delta: timedelta,
    token_type: str = "access"
) -> str:
    """
    Create a JWT token with expiration.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({
        "exp": expire,
        "type": token_type,
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        security_config.auth.jwt_secret_key,
        algorithm=security_config.auth.jwt_algorithm
    )
    
    return encoded_jwt

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create access token.
    """
    if expires_delta is None:
        expires_delta = security_config.auth.token_expiry
    return create_token(data, expires_delta, "access")

def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create refresh token.
    """
    if expires_delta is None:
        expires_delta = security_config.auth.refresh_token_expiry
    return create_token(data, expires_delta, "refresh")

def verify_token(token: str) -> TokenData:
    """
    Verify and decode a JWT token.
    """
    try:
        # Check if token is blacklisted
        if is_token_blacklisted(token):
            raise jwt.InvalidTokenError("Token is blacklisted")

        # Decode and verify token
        payload = jwt.decode(
            token,
            security_config.auth.jwt_secret_key,
            algorithms=[security_config.auth.jwt_algorithm]
        )

        username: str = payload.get("sub")
        if username is None:
            raise jwt.InvalidTokenError("Token missing username claim")

        token_data = TokenData(
            username=username,
            exp=datetime.fromtimestamp(payload["exp"]),
            token_type=payload.get("type", "access")
        )
        return token_data

    except jwt.ExpiredSignatureError:
        raise jwt.InvalidTokenError("Token has expired")
    except jwt.JWTError as e:
        raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise jwt.InvalidTokenError("Token verification failed")

def blacklist_token(token: str) -> None:
    """
    Add a token to the blacklist.
    """
    try:
        # Decode token without verification to get expiration
        payload = jwt.decode(
            token,
            options={"verify_signature": False}
        )
        exp = payload.get("exp")
        
        if exp:
            # Calculate TTL (time until token expires)
            ttl = exp - datetime.utcnow().timestamp()
            if ttl > 0:
                # Add token to blacklist with expiration
                redis_client.setex(
                    f"blacklist:{token}",
                    int(ttl),
                    "1"
                )
    except Exception as e:
        logger.error(f"Failed to blacklist token: {str(e)}")
        raise

def is_token_blacklisted(token: str) -> bool:
    """
    Check if a token is blacklisted.
    """
    try:
        return bool(redis_client.exists(f"blacklist:{token}"))
    except Exception as e:
        logger.error(f"Failed to check token blacklist: {str(e)}")
        return True  # Fail secure

def get_current_user(token: str) -> str:
    """
    Get current user from token.
    """
    token_data = verify_token(token)
    return token_data.username
