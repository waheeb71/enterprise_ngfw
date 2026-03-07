from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
from api.rest.main import require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/vpn", tags=["vpn"])

class VPNPeerRequest(BaseModel):
    public_key: str = Field(..., description="WireGuard Public Key")
    allowed_ips: List[str] = Field(..., description="List of allowed IP addresses/CIDRs")
    endpoint: Optional[str] = Field(None, description="Optional peer endpoint IP:PORT")
    preshared_key: Optional[str] = Field(None, description="Optional preshared key")
    persistent_keepalive: int = Field(25, description="Keepalive interval in seconds")

@router.get("/status")
async def get_vpn_status(request: Request, token: dict = Depends(require_admin)):
    """Get WireGuard VPN interface status"""
    ngfw_app = getattr(request.app.state, 'ngfw_app', None)
    
    if not ngfw_app or not ngfw_app.vpn_enabled or not ngfw_app.vpn_manager:
        raise HTTPException(status_code=503, detail="VPN functionality is not enabled or available.")
        
    status_text = ngfw_app.vpn_manager.get_status()
    return {"status": status_text, "interface": ngfw_app.vpn_manager.interface}

@router.get("/peers")
async def list_vpn_peers(request: Request, token: dict = Depends(require_admin)):
    """List all configured VPN peers"""
    ngfw_app = getattr(request.app.state, 'ngfw_app', None)
    
    if not ngfw_app or not ngfw_app.vpn_enabled or not ngfw_app.vpn_manager:
        raise HTTPException(status_code=503, detail="VPN functionality is not enabled")
        
    peers = [
        {
            "public_key": pk,
            "allowed_ips": config.allowed_ips,
            "endpoint": config.endpoint,
            "persistent_keepalive": config.persistent_keepalive
        }
        for pk, config in ngfw_app.vpn_manager.peers.items()
    ]
    return {"peers": peers}

@router.post("/peers", status_code=status.HTTP_201_CREATED)
async def add_vpn_peer(request: Request, peer_data: VPNPeerRequest, token: dict = Depends(require_admin)):
    """Add a new WireGuard VPN peer"""
    from integration.vpn.wireguard import PeerConfig
    
    ngfw_app = getattr(request.app.state, 'ngfw_app', None)
    
    if not ngfw_app or not ngfw_app.vpn_enabled or not ngfw_app.vpn_manager:
        raise HTTPException(status_code=503, detail="VPN functionality is not enabled")
        
    peer_config = PeerConfig(
        public_key=peer_data.public_key,
        allowed_ips=peer_data.allowed_ips,
        endpoint=peer_data.endpoint,
        preshared_key=peer_data.preshared_key,
        persistent_keepalive=peer_data.persistent_keepalive
    )
    
    success = ngfw_app.vpn_manager.add_peer(peer_config)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add VPN peer. Check system logs.")
        
    return {"message": "Peer added successfully", "public_key": peer_data.public_key}

@router.delete("/peers/{public_key:path}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_vpn_peer(request: Request, public_key: str, token: dict = Depends(require_admin)):
    """Remove a WireGuard VPN peer"""
    ngfw_app = getattr(request.app.state, 'ngfw_app', None)
    
    if not ngfw_app or not ngfw_app.vpn_enabled or not ngfw_app.vpn_manager:
        raise HTTPException(status_code=503, detail="VPN functionality is not enabled")
        
    success = ngfw_app.vpn_manager.remove_peer(public_key)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to remove VPN peer. Check system logs.")
        
    return None
