"""
Configuration router for the Blob Service.
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.security_config import security_config
from app.utils.auth import get_current_admin
from app.config import config_manager
from pydantic import BaseModel

router = APIRouter()

class ConfigUpdateRequest(BaseModel):
    """Configuration update request model."""
    auth: Optional[Dict[str, Any]] = None
    storage: Optional[Dict[str, Any]] = None
    features: Optional[Dict[str, Any]] = None
    limits: Optional[Dict[str, Any]] = None
    server: Optional[Dict[str, Any]] = None
    processing: Optional[Dict[str, Any]] = None

@router.get("/config")
async def get_config(
    request: Request,
    current_admin = Depends(get_current_admin)
):
    """Get current configuration.
    
    Args:
        request: Request object
        current_admin: Current admin user (from auth dependency)
        
    Returns:
        Current configuration
    """
    try:
        config = config_manager.get_config()
        return {
            "success": True,
            "data": config_manager._config_to_dict(config)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get configuration: {str(e)}"
        )

@router.post("/config")
async def update_config(
    request: Request,
    config_update: ConfigUpdateRequest,
    current_admin = Depends(get_current_admin)
):
    """Update configuration.
    
    Args:
        request: Request object
        config_update: Configuration update request
        current_admin: Current admin user (from auth dependency)
        
    Returns:
        Updated configuration
    """
    try:
        # Get current config
        current_config = config_manager.get_config()
        
        # Update auth config if provided
        if config_update.auth:
            current_config.auth = current_config.auth.copy(
                update=config_update.auth
            )
            
        # Update storage config if provided 
        if config_update.storage:
            current_config.storage = current_config.storage.copy(
                update=config_update.storage
            )
            
        # Update features config if provided
        if config_update.features:
            current_config.features = current_config.features.copy(
                update=config_update.features
            )
            
        # Update limits config if provided
        if config_update.limits:
            current_config.limits = current_config.limits.copy(
                update=config_update.limits
            )
            
        # Update server config if provided
        if config_update.server:
            current_config.server = current_config.server.copy(
                update=config_update.server
            )
            
        # Update processing config if provided
        if config_update.processing:
            current_config.processing = current_config.processing.copy(
                update=config_update.processing
            )
            
        # Save updated config
        config_manager.save_config(current_config)
        
        return {
            "success": True,
            "message": "Configuration updated successfully",
            "data": config_manager._config_to_dict(current_config)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update configuration: {str(e)}"
        )

@router.post("/config/reset")
async def reset_config(
    request: Request,
    current_admin = Depends(get_current_admin)
):
    """Reset configuration to defaults.
    
    Args:
        request: Request object
        current_admin: Current admin user (from auth dependency)
        
    Returns:
        Default configuration
    """
    try:
        # Load default config
        config = config_manager.load_default_config()
        
        # Save default config
        config_manager.save_config(config)
        
        return {
            "success": True,
            "message": "Configuration reset to defaults",
            "data": config_manager._config_to_dict(config)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset configuration: {str(e)}"
        )
