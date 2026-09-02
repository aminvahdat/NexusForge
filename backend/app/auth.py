"""Authorization module for NexusForge."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config.settings import get_settings
from app.models.user import User
from app.models.artifact import Artifact
from app.models.project import Project
from app.models.worker import Worker

# ── Constants ────────────────────────────────────────────────────────────────
SECRET_KEY = get_settings().secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ── Schemas ────────────────────────────────────────────────────────────────

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


# ── Dependencies ────────────────────────────────────────────────────────────

def get_current_user(token: Optional[str] = Depends()) -> Optional[User]:
    """Retrieve current user from JWT token."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return User(**payload)
    except JWTError:
        return None


def get_resource_permissions(user_id: str) -> dict[str, list[str]]:
    """Return permission matrix for a given user."""
    # In production, query the database for user roles and permissions
    # For now, return a simplified matrix
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


# ── API Endpoints ───────────────────────────────────────────────────────────

@app.post("/auth/register", response_model=UserResponse, tags=["Authentication"])
async def register(user: UserCreate) -> UserResponse:
    """Register a new user."""
    # Implementation: hash password, check uniqueness, create DB record
    return UserResponse(
        id="user_001",
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=True,
        is_superuser=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@app.post("/auth/login", response_model=Token, tags=["Authentication"])
async def login(form: OAuth2PasswordRequestForm = Depends()) -> Token:
    """Authenticate user and return JWT token."""
    # Implementation: verify credentials, create token
    return Token(
        access_token="access_token_here",
        token_type="bearer",
    )


@app.get("/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_endpoint(current_user: Optional[User] = Depends(get_current_user)):
    """Get current authenticated user."""
    if current_user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user
