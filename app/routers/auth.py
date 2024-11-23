"""
Authentication router for the Blob Service.
"""
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime
from app.core.security_config import security_config
from app.utils.auth import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    verify_token,
    blacklist_token
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Token data model."""
    username: str
    exp: datetime

@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Authenticate user and return access and refresh tokens.
    """
    # Verify credentials
    if not (
        form_data.username == security_config.auth.admin_user and
        verify_password(form_data.password, security_config.auth.admin_password)
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )

    # Create tokens
    access_token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=security_config.auth.token_expiry
    )
    refresh_token = create_refresh_token(
        data={"sub": form_data.username},
        expires_delta=security_config.auth.refresh_token_expiry
    )

    # Set secure cookie with refresh token
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=security_config.auth.refresh_token_expiry.total_seconds()
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(request: Request, response: Response):
    """
    Refresh access token using refresh token.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Refresh token missing"
        )

    # Verify refresh token
    try:
        token_data = verify_token(refresh_token)
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

    # Create new tokens
    access_token = create_access_token(
        data={"sub": token_data.username},
        expires_delta=security_config.auth.token_expiry
    )
    new_refresh_token = create_refresh_token(
        data={"sub": token_data.username},
        expires_delta=security_config.auth.refresh_token_expiry
    )

    # Set new refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=security_config.auth.refresh_token_expiry.total_seconds()
    )

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(
    response: Response,
    token: str = Depends(oauth2_scheme)
):
    """
    Logout user and blacklist current token.
    """
    try:
        # Blacklist current token
        blacklist_token(token)
        # Clear refresh token cookie
        response.delete_cookie(
            key="refresh_token",
            secure=True,
            httponly=True
        )
        return {"detail": "Successfully logged out"}
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Logout failed"
        )
