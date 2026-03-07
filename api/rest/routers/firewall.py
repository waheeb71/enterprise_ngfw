from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
import logging
from api.rest.main import require_admin, verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["firewall"])

class FirewallRule(BaseModel):
    rule_id: Optional[str] = None
    src_ip: Optional[str] = Field(None, description="Source IP (CIDR notation)")
    dst_ip: Optional[str] = Field(None, description="Destination IP (CIDR notation)")
    dst_port: Optional[int] = Field(None, ge=1, le=65535)
    protocol: Optional[str] = Field(None, pattern="^(TCP|UDP|ICMP|ALL)$")
    zone_src: str = Field("ANY", description="Source Zone (e.g. LAN, WAN)")
    zone_dst: str = Field("ANY", description="Destination Zone (e.g. DMZ, WAN)")
    app_category: str = Field("ANY", description="Application Category (e.g. Social Media)")
    file_type: str = Field("ANY", description="File Type Extension (e.g. EXE, PDF)")
    schedule: str = Field("ALWAYS", description="Schedule Name (e.g. WorkHours)")
    action: str = Field(..., pattern="^(ALLOW|BLOCK|THROTTLE)$")
    priority: int = Field(100, ge=1, le=1000)
    enabled: bool = True

class PolicyEvaluation(BaseModel):
    action: str
    confidence: float
    reason: str
    matched_rules: List[str]

@router.get("/rules", response_model=List[FirewallRule])
async def list_rules(request: Request, token: dict = Depends(verify_token)):
    """List all firewall rules"""
    # Replace with actual rules from policy engine
    return []

@router.post("/rules", response_model=FirewallRule, status_code=status.HTTP_201_CREATED)
async def create_rule(
    request: Request,
    rule: FirewallRule,
    token: dict = Depends(require_admin)
):
    """Create a new firewall rule"""
    if not any([rule.src_ip, rule.dst_ip, rule.dst_port]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of src_ip, dst_ip, or dst_port must be specified"
        )
    
    rule.rule_id = f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"Created rule {rule.rule_id}: {rule.dict()}")
    return rule

@router.get("/rules/{rule_id}", response_model=FirewallRule)
async def get_rule(request: Request, rule_id: str, token: dict = Depends(verify_token)):
    raise HTTPException(status_code=404, detail="Rule not found")

@router.put("/rules/{rule_id}", response_model=FirewallRule)
async def update_rule(
    request: Request,
    rule_id: str,
    rule: FirewallRule,
    token: dict = Depends(require_admin)
):
    rule.rule_id = rule_id
    logger.info(f"Updated rule {rule_id}: {rule.dict()}")
    return rule

@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(request: Request, rule_id: str, token: dict = Depends(require_admin)):
    logger.info(f"Deleted rule {rule_id}")
    return None

@router.post("/policy/evaluate", response_model=PolicyEvaluation)
async def evaluate_policy(
    request: Request,
    src_ip: str,
    dst_ip: str,
    dst_port: int,
    protocol: str,
    token: dict = Depends(verify_token)
):
    return PolicyEvaluation(action="ALLOW", confidence=0.95, reason="No threats detected", matched_rules=[])

@router.post("/block/{ip_address}", status_code=status.HTTP_200_OK)
async def block_ip(
    request: Request,
    ip_address: str,
    duration: int = 3600,
    token: dict = Depends(require_admin)
):
    logger.info(f"Blocking IP {ip_address} for {duration} seconds")
    return {
        "status": "success",
        "ip_address": ip_address,
        "blocked_until": datetime.now() + timedelta(seconds=duration)
    }

@router.delete("/block/{ip_address}", status_code=status.HTTP_204_NO_CONTENT)
async def unblock_ip(request: Request, ip_address: str, token: dict = Depends(require_admin)):
    logger.info(f"Unblocking IP {ip_address}")
    return None
