from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
import logging
from api.rest.auth import require_admin, verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/qos", tags=["qos"])

class QoSConfigRequest(BaseModel):
    enabled: bool = Field(..., description="Enable or disable QoS shaping")
    default_user_rate_bytes: int = Field(..., description="Default rate limit per user in bytes/sec")
    default_user_burst_bytes: int = Field(..., description="Default burst limit per user in bytes")

@router.get("/config")
async def get_qos_config(request: Request, token: dict = Depends(require_admin)):
    """Get global Quality of Service (QoS) configurations"""
    ngfw_app = getattr(request.app.state, 'ngfw_app', None)
    
    if not ngfw_app or not hasattr(ngfw_app, 'qos_manager'):
        raise HTTPException(status_code=503, detail="QoS functionality is not available")
        
    qos_manager = ngfw_app.qos_manager
    return {
        "enabled": qos_manager.enabled,
        "default_user_rate_bytes": qos_manager.default_per_ip_rate,
        "default_user_burst_bytes": qos_manager.default_per_ip_burst
    }

@router.put("/config", status_code=status.HTTP_200_OK)
async def update_qos_config(request: Request, config: QoSConfigRequest, token: dict = Depends(require_admin)):
    """Update global Quality of Service (QoS) configurations dynamically"""
    ngfw_app = getattr(request.app.state, 'ngfw_app', None)
    
    if not ngfw_app or not hasattr(ngfw_app, 'qos_manager'):
        raise HTTPException(status_code=503, detail="QoS functionality is not available")
        
    qos_manager = ngfw_app.qos_manager
    qos_manager.update_limits(
        enabled=config.enabled,
        rate_bytes=config.default_user_rate_bytes,
        burst_bytes=config.default_user_burst_bytes
    )
    
    return {
        "message": "QoS limits updated successfully",
        "enabled": qos_manager.enabled,
        "default_user_rate_bytes": qos_manager.default_per_ip_rate,
        "default_user_burst_bytes": qos_manager.default_per_ip_burst
    }
