"""Authorization module for NexusForge.

Phase 6 — Final Migration & Handover
Provides authentication and authorization utilities.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config.settings import get_settings
settings = get_settings()

from app.models.user import User, UserCreate, UserResponse, Token

# ── Constants ────────────────────────────────────────────────────────────────
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ── OAuth2 ───────────────────────────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


# ── Schemas ──────────────────────────────────────────────────────────────────

class RolePermissions(BaseModel):
    """Permission matrix for each role."""
    chief_orchestrator: list[str] = ["admin", "chief_orchestrator"]
    project_planner: list[str] = ["admin", "project_planner"]
    software_architect: list[str] = ["admin", "software_architect"]
    research_agent: list[str] = ["admin", "research_agent"]
    ui_ux_agent: list[str] = ["admin", "ui_ux_agent"]
    frontend_agent: list[str] = ["admin", "frontend_agent"]
    backend_agent: list[str] = ["admin", "backend_agent"]
    mobile_agent: list[str] = ["admin", "mobile_agent"]
    database_agent: list[str] = ["admin", "database_agent"]
    security_agent: list[str] = ["admin", "security_agent"]
    qa_agent: list[str] = ["admin", "qa_agent"]
    devops_agent: list[str] = ["admin", "devops_agent"]


class ResourceOwnership(BaseModel):
    """Defines ownership relationships for resource access control."""
    project: Optional[str] = None
    task: Optional[str] = None
    artifact: Optional[str] = None
    user: Optional[str] = None
    worker: Optional[str] = None


# ── Dependencies ─────────────────────────────────────────────────────────────

def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[User]:
    """Retrieve current user from JWT token."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Extract user_id from token payload
        user_id = payload.get("sub")
        if not user_id:
            return None
        email = payload.get("email") or (user_id if "@" in str(user_id) else "admin@nexusforge.io")
        return User(
            id=user_id,
            email=email,
            password_hash="",
            is_active=True,
            is_superuser=payload.get("is_superuser", False),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    except JWTError:
        return None


def get_resource_permissions(user_id: str) -> dict[str, list[str]]:
    """Return permission matrix for a given user."""
    return {
        "admin": ["*"],
        "chief_orchestrator": ["*"],
        "project_planner": ["*"],
        "software_architect": ["*"],
        "research_agent": ["*"],
        "ui_ux_agent": ["*"],
        "frontend_agent": ["*"],
        "backend_agent": ["*"],
        "mobile_agent": ["*"],
        "database_agent": ["*"],
        "security_agent": ["*"],
        "qa_agent": ["*"],
        "devops_agent": ["*"],
    }


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
