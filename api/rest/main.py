#!/usr/bin/env python3
"""
Enterprise NGFW - FastAPI REST API
Production-ready REST API with authentication, rate limiting, and comprehensive endpoints
"""

import logging
import os
import secrets
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

import bcrypt
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import jwt
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Prometheus metrics
from telemetry.prometheus_metrics import metrics_endpoint

# Core routers
from api.rest.routers import system, ai, certificates, qos, vpn, firewall, traffic, interfaces, logs

# Database
from core.database import User
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# JWT Configuration
_env_secret = os.getenv("NGFW_SECRET_KEY", "")
if _env_secret:
    SECRET_KEY = _env_secret
else:
    SECRET_KEY = secrets.token_hex(32)
    logger.warning(
        "⚠️ NGFW_SECRET_KEY not set! Using auto-generated key. "
        "Set NGFW_SECRET_KEY environment variable for production."
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


# ==================== Pydantic Models ====================
class ConfigUpdate(BaseModel):
    category: str = Field(..., description="Configuration category (e.g. system, network, ai)")
    key: str = Field(..., description="The exact YAML key to update")
    value: Any = Field(..., description="The new value for the key")

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class SystemStatus(BaseModel):
    status: str
    uptime_seconds: float
    cpu_usage: float
    memory_usage: float
    active_connections: int
    rules_count: int
    ml_models_loaded: bool
    ha_state: str = Field("UNKNOWN", description="Current node HA state")
    ha_peer: Optional[str] = Field(None, description="IP of the HA peer node")
    ha_priority: int = Field(0, description="Priority of the current node")


class PolicyEvaluation(BaseModel):
    action: str
    confidence: float
    reason: str
    matched_rules: List[str]


class VPNPeerRequest(BaseModel):
    public_key: str = Field(..., description="WireGuard Public Key")
    allowed_ips: List[str] = Field(..., description="List of allowed IP addresses/CIDRs")
    endpoint: Optional[str] = Field(None, description="Optional peer endpoint IP:PORT")
    preshared_key: Optional[str] = Field(None, description="Optional preshared key")
    persistent_keepalive: Optional[int] = Field(25, description="Keepalive interval in seconds")


class QoSConfigRequest(BaseModel):
    enabled: bool = Field(..., description="Enable or disable QoS shaping")
    default_user_rate_bytes: int = Field(..., description="Default rate limit per user in bytes/sec")
    default_user_burst_bytes: int = Field(..., description="Default burst limit per user in bytes")


# ==================== Authentication ====================

security = HTTPBearer()

# ==================== Password Hashing ====================

def _hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


# User database configuration handled by core.database.DatabaseManager
# Default users are created on startup if they don't exist.


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
    allow_origins=os.getenv("NGFW_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8888").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router)
app.include_router(ai.router)
app.include_router(certificates.router)
app.include_router(qos.router)
app.include_router(vpn.router)
app.include_router(firewall.router)
app.include_router(traffic.router)
app.include_router(interfaces.router)
app.include_router(logs.router)

# ==================== API Endpoints ====================

@app.post("/api/v1/auth/login", response_model=Token)
@limiter.limit("5/minute")
async def login_for_access_token(
    request: Request,
    login_data: LoginRequest
):
    # Get DB session from app state
    if not hasattr(request.app.state, 'ngfw') or not request.app.state.ngfw:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="NGFW not initialized"
        )
    
    db = request.app.state.ngfw.db
    
    with db.session() as session:
        user = session.query(User).filter(User.username == login_data.username).first()
        
        if not user or not _verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role},
            expires_delta=access_token_expires
        )
        
        # Update last login
        user.last_login = datetime.utcnow()
        session.commit()
        
        logger.info(f"User {login_data.username} logged in")
        
        return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/v1/status", response_model=SystemStatus)
@limiter.limit("60/minute")
async def get_system_status(request: Request, token: dict = Depends(verify_token)):
    """
    Get system status and health metrics
    
    Rate limit: 60 requests per minute
    Requires: Valid authentication token
    """
    import psutil
    
    ha_state = "MASTER" # Default fallback
    ha_peer = "192.168.1.2"
    ha_priority = 100
    uptime = 3600.0
    active_conn = 0
    rules = 0

    try:
        # If running inside the unified Enterprise NGFW context, extract dynamic variables
        if hasattr(request.app.state, 'ngfw_app'):
            ngfw = request.app.state.ngfw_app
            if ngfw.ha_manager:
                ha_state = ngfw.ha_manager.state.name
                ha_peer = ngfw.ha_manager.peer_ip
                ha_priority = ngfw.ha_manager.priority
            uptime = ngfw.get_uptime() if hasattr(ngfw, 'get_uptime') else 3600.0
    except Exception as e:
        logger.error(f"Error fetching extended HA status: {e}")

    return SystemStatus(
        status="operational",
        uptime_seconds=uptime,  
        cpu_usage=psutil.cpu_percent(),
        memory_usage=psutil.virtual_memory().percent,
        active_connections=active_conn, 
        rules_count=rules, 
        ml_models_loaded=True,
        ha_state=ha_state,
        ha_peer=ha_peer,
        ha_priority=ha_priority
    )


@app.get("/health")
async def health_check():
    """
    Basic health check endpoint (no authentication required)
    Used for load balancer health checks
    """
    return {"status": "healthy", "timestamp": datetime.now()}


@app.get("/api/v1/health/liveness")
async def liveness_probe():
    """
    Liveness probe - is the application alive?
    Returns 200 if alive, 503 if dead
    No authentication required
    """
    try:
        ngfw_app = app.state.ngfw_app if hasattr(app.state, 'ngfw_app') else None
        
        if ngfw_app and hasattr(ngfw_app, 'health_checker'):
            is_alive = await ngfw_app.health_checker.liveness_probe()
            
            if is_alive:
                return {"status": "alive", "timestamp": datetime.now()}
            else:
                return JSONResponse(
                    status_code=503,
                    content={"status": "dead", "timestamp": datetime.now().isoformat()}
                )
        else:
            return {"status": "alive", "timestamp": datetime.now()}
            
    except Exception as e:
        logger.error(f"Liveness probe error: {e}")
        return JSONResponse(status_code=503, content={"status": "error", "error": str(e)})


@app.get("/api/v1/health/readiness")
async def readiness_probe():
    """
    Readiness probe - is the application ready to accept traffic?
    Returns 200 if ready, 503 if not ready
    No authentication required
    """
    try:
        ngfw_app = app.state.ngfw_app if hasattr(app.state, 'ngfw_app') else None
        
        if ngfw_app and hasattr(ngfw_app, 'health_checker'):
            is_ready = await ngfw_app.health_checker.readiness_probe()
            
            if is_ready:
                return {"status": "ready", "timestamp": datetime.now()}
            else:
                return JSONResponse(
                    status_code=503,
                    content={"status": "not_ready", "timestamp": datetime.now().isoformat()}
                )
        else:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": "Health checker not initialized"}
            )
            
    except Exception as e:
        logger.error(f"Readiness probe error: {e}")
        return JSONResponse(status_code=503, content={"status": "error", "error": str(e)})


@app.get("/metrics", include_in_schema=False)
async def get_metrics():
    """
    Prometheus metrics endpoint
    """
    return await metrics_endpoint()


@app.get("/api/v1/health/detailed")
@limiter.limit("10/minute")
async def detailed_health_check(request: Request, token: dict = Depends(verify_token)):
    """
    Detailed health check with component statuses
    
    Rate limit: 10 requests per minute
    Requires: Valid authentication token
    """
    try:
        ngfw_app = app.state.ngfw_app if hasattr(app.state, 'ngfw_app') else None
        
        if ngfw_app and hasattr(ngfw_app, 'health_checker'):
            health_status = await ngfw_app.health_checker.check_all_components()
            return health_status
        else:
            return {
                "overall_status": "unknown",
                "message": "Health checker not available",
                "timestamp": datetime.now()
            }
            
    except Exception as e:
        logger.error(f"Detailed health check error: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


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


# ==================== Configuration Endpoints ====================

@app.get("/api/v1/config")
@limiter.limit("30/minute")
async def get_configuration(request: Request, token: dict = Depends(require_admin)):
    """
    Get current system configuration
    Requires: Admin role
    """
    import yaml
    from pathlib import Path
    
    # Try to locate the active config file
    config_path = os.getenv("NGFW_CONFIG", "/etc/ngfw/config.yaml")
    if not os.path.exists(config_path):
        # Fallback to local dev path
        config_path = Path(__file__).parent.parent.parent / "config" / "defaults" / "base.yaml"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        return config_data
    except Exception as e:
        logger.error(f"Failed to read config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read configuration: {str(e)}"
        )

@app.put("/api/v1/config")
@limiter.limit("10/minute")
async def update_configuration(request: Request, update: ConfigUpdate, token: dict = Depends(require_admin)):
    """
    Update a specific configuration value and reload system
    Requires: Admin role
    """
    import yaml
    from pathlib import Path
    
    config_path = os.getenv("NGFW_CONFIG", "/etc/ngfw/config.yaml")
    if not os.path.exists(config_path):
        config_path = Path(__file__).parent.parent.parent / "config" / "defaults" / "base.yaml"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f) or {}
            
        # Update nested dictionary
        if update.category not in config_data:
            config_data[update.category] = {}
        
        config_data[update.category][update.key] = update.value
        
        # Write back
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False)
            
        # Try to hot-reload if running in unified app
        if hasattr(request.app.state, 'ngfw_app'):
            try:
                request.app.state.ngfw_app.reload_config()
            except Exception as e:
                logger.warning(f"Could not hot-reload config: {e}")

        return {"status": "success", "message": f"Updated {update.category}.{update.key}"}
        
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


# ==================== Core Application Instantiation fallback ====================
# Run natively only if not imported by unified system
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