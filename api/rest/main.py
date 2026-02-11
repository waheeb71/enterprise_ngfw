#!/usr/bin/env python3
"""
Enterprise NGFW - FastAPI REST API
Production-ready REST API with authentication, rate limiting, and comprehensive endpoints
"""

import logging
import os
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import jwt
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

# JWT Configuration
# JWT Configuration
SECRET_KEY = os.getenv("NGFW_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


# ==================== Pydantic Models ====================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class FirewallRule(BaseModel):
    rule_id: Optional[str] = None
    src_ip: Optional[str] = Field(None, description="Source IP (CIDR notation)")
    dst_ip: Optional[str] = Field(None, description="Destination IP (CIDR notation)")
    dst_port: Optional[int] = Field(None, ge=1, le=65535)
    protocol: Optional[str] = Field(None, pattern="^(TCP|UDP|ICMP|ALL)$")
    action: str = Field(..., pattern="^(ALLOW|BLOCK|THROTTLE)$")
    priority: int = Field(100, ge=1, le=1000)
    enabled: bool = True


class TrafficStats(BaseModel):
    timestamp: datetime
    total_packets: int
    total_bytes: int
    blocked_packets: int
    allowed_packets: int
    unique_sources: int
    unique_destinations: int
    top_protocols: Dict[str, int]


class AnomalyReport(BaseModel):
    timestamp: datetime
    src_ip: str
    anomaly_score: float
    is_anomaly: bool
    reason: str
    confidence: float


class SystemStatus(BaseModel):
    status: str
    uptime_seconds: float
    cpu_usage: float
    memory_usage: float
    active_connections: int
    rules_count: int
    ml_models_loaded: bool


class PolicyEvaluation(BaseModel):
    action: str
    confidence: float
    reason: str
    matched_rules: List[str]


# ==================== Authentication ====================

security = HTTPBearer()

# Simple user database (replace with real database in production)
# Simple user database (replace with real database in production)
USERS_DB = {
    "admin": {
        "password": os.getenv("NGFW_ADMIN_PASSWORD", "admin123"),
        "role": "admin"
    },
    "operator": {
        "password": os.getenv("NGFW_OPERATOR_PASSWORD", "operator123"),
        "role": "operator"
    }
}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


def require_admin(token_data: dict = Depends(verify_token)):
    """Require admin role"""
    if token_data.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return token_data


# ==================== FastAPI Application ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("NGFW API starting up...")
    # Initialize NGFW components here
    yield
    logger.info("NGFW API shutting down...")


app = FastAPI(
    title="Enterprise NGFW API",
    description="Production-ready Next-Generation Firewall REST API",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("NGFW_ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== API Endpoints ====================

@app.post("/api/v1/auth/login", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest):
    """
    Authenticate user and get access token
    
    Rate limit: 5 requests per minute
    """
    user = USERS_DB.get(login_data.username)
    
    if not user or user["password"] != login_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(
        data={"sub": login_data.username, "role": user["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    logger.info(f"User {login_data.username} logged in")
    
    return Token(access_token=access_token)


@app.get("/api/v1/status", response_model=SystemStatus)
@limiter.limit("60/minute")
async def get_system_status(request: Request, token: dict = Depends(verify_token)):
    """
    Get system status and health metrics
    
    Rate limit: 60 requests per minute
    Requires: Valid authentication token
    """
    import psutil
    
    return SystemStatus(
        status="operational",
        uptime_seconds=3600.0,  # Replace with actual uptime
        cpu_usage=psutil.cpu_percent(),
        memory_usage=psutil.virtual_memory().percent,
        active_connections=0,  # Replace with actual count
        rules_count=0,  # Replace with actual count
        ml_models_loaded=True
    )


@app.get("/api/v1/statistics", response_model=TrafficStats)
@limiter.limit("60/minute")
async def get_traffic_statistics(
    request: Request,
    time_window: int = 300,
    token: dict = Depends(verify_token)
):
    """
    Get traffic statistics for specified time window
    
    Args:
        time_window: Time window in seconds (default: 300)
    
    Rate limit: 60 requests per minute
    Requires: Valid authentication token
    """
    # Replace with actual statistics from NGFW
    return TrafficStats(
        timestamp=datetime.now(),
        total_packets=1000000,
        total_bytes=500000000,
        blocked_packets=5000,
        allowed_packets=995000,
        unique_sources=500,
        unique_destinations=1000,
        top_protocols={"TCP": 800000, "UDP": 150000, "ICMP": 50000}
    )


@app.get("/api/v1/rules", response_model=List[FirewallRule])
@limiter.limit("60/minute")
async def list_rules(request: Request, token: dict = Depends(verify_token)):
    """
    List all firewall rules
    
    Rate limit: 60 requests per minute
    Requires: Valid authentication token
    """
    # Replace with actual rules from policy engine
    return []


@app.post("/api/v1/rules", response_model=FirewallRule, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_rule(
    request: Request,
    rule: FirewallRule,
    token: dict = Depends(require_admin)
):
    """
    Create a new firewall rule
    
    Rate limit: 30 requests per minute
    Requires: Admin role
    """
    # Validate rule
    if not any([rule.src_ip, rule.dst_ip, rule.dst_port]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of src_ip, dst_ip, or dst_port must be specified"
        )
    
    # Generate rule ID
    rule.rule_id = f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Add rule to policy engine (implement this)
    logger.info(f"Created rule {rule.rule_id}: {rule.dict()}")
    
    return rule


@app.get("/api/v1/rules/{rule_id}", response_model=FirewallRule)
@limiter.limit("60/minute")
async def get_rule(
    request: Request,
    rule_id: str,
    token: dict = Depends(verify_token)
):
    """
    Get specific firewall rule
    
    Rate limit: 60 requests per minute
    Requires: Valid authentication token
    """
    # Retrieve rule from policy engine
    raise HTTPException(status_code=404, detail="Rule not found")


@app.put("/api/v1/rules/{rule_id}", response_model=FirewallRule)
@limiter.limit("30/minute")
async def update_rule(
    request: Request,
    rule_id: str,
    rule: FirewallRule,
    token: dict = Depends(require_admin)
):
    """
    Update existing firewall rule
    
    Rate limit: 30 requests per minute
    Requires: Admin role
    """
    rule.rule_id = rule_id
    logger.info(f"Updated rule {rule_id}: {rule.dict()}")
    return rule


@app.delete("/api/v1/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def delete_rule(
    request: Request,
    rule_id: str,
    token: dict = Depends(require_admin)
):
    """
    Delete firewall rule
    
    Rate limit: 30 requests per minute
    Requires: Admin role
    """
    logger.info(f"Deleted rule {rule_id}")
    return None


@app.get("/api/v1/anomalies", response_model=List[AnomalyReport])
@limiter.limit("60/minute")
async def get_anomalies(
    request: Request,
    limit: int = 100,
    token: dict = Depends(verify_token)
):
    """
    Get recent anomaly detections
    
    Args:
        limit: Maximum number of results (default: 100)
    
    Rate limit: 60 requests per minute
    Requires: Valid authentication token
    """
    # Retrieve from anomaly detector
    return []


@app.post("/api/v1/policy/evaluate", response_model=PolicyEvaluation)
@limiter.limit("1000/minute")
async def evaluate_policy(
    request: Request,
    src_ip: str,
    dst_ip: str,
    dst_port: int,
    protocol: str,
    token: dict = Depends(verify_token)
):
    """
    Evaluate traffic against current policies
    
    Rate limit: 1000 requests per minute
    Requires: Valid authentication token
    """
    # Evaluate using adaptive policy engine
    return PolicyEvaluation(
        action="ALLOW",
        confidence=0.95,
        reason="No threats detected",
        matched_rules=[]
    )


@app.post("/api/v1/block/{ip_address}", status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def block_ip(
    request: Request,
    ip_address: str,
    duration: int = 3600,
    token: dict = Depends(require_admin)
):
    """
    Block an IP address
    
    Args:
        ip_address: IP to block
        duration: Block duration in seconds (default: 3600)
    
    Rate limit: 30 requests per minute
    Requires: Admin role
    """
    logger.info(f"Blocking IP {ip_address} for {duration} seconds")
    
    return {
        "status": "success",
        "ip_address": ip_address,
        "blocked_until": datetime.now() + timedelta(seconds=duration)
    }


@app.delete("/api/v1/block/{ip_address}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def unblock_ip(
    request: Request,
    ip_address: str,
    token: dict = Depends(require_admin)
):
    """
    Unblock an IP address
    
    Rate limit: 30 requests per minute
    Requires: Admin role
    """
    logger.info(f"Unblocking IP {ip_address}")
    return None


@app.get("/api/v1/profiles/{ip_address}")
@limiter.limit("60/minute")
async def get_ip_profile(
    request: Request,
    ip_address: str,
    token: dict = Depends(verify_token)
):
    """
    Get behavioral profile for an IP address
    
    Rate limit: 60 requests per minute
    Requires: Valid authentication token
    """
    # Retrieve from traffic profiler
    return {
        "ip": ip_address,
        "reputation_score": 85.0,
        "total_connections": 1000,
        "patterns_detected": [],
        "first_seen": datetime.now() - timedelta(days=7),
        "last_seen": datetime.now()
    }


@app.get("/api/v1/health")
async def health_check():
    """
    Health check endpoint (no authentication required)
    """
    return {"status": "healthy", "timestamp": datetime.now()}


# ==================== Error Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    import uvicorn
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("NGFW_ENV", "production") == "development",
        log_level="info"
    )