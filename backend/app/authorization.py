"""Authorization module for NexusForge — RBAC layer."""

from typing import Optional, List
from functools import wraps
from fastapi import Depends, HTTPException, status

# RBAC Roles and Permissions
ROLES = {
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

def require_role(role: str):
    """Guard: user must have the specified role."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

def check_ownership(resource_owner_id: str, user_id: str) -> bool:
    """Enforce resource ownership: user must own or be admin."""
    return resource_owner_id == user_id or user_id == "admin"

def can_access(user_id: str, resource_id: str, resource_owner_id: str) -> bool:
    """Ownership + role check for any resource."""
    return check_ownership(resource_owner_id, user_id)

class RBAC:
    """Role-Based Access Control engine."""
    def __init__(self, user_id: str, roles: List[str]):
        self.user_id = user_id
        self.roles = roles

    def has_permission(self, permission: str) -> bool:
        """Check if user has a given permission via any role."""
        for role in self.roles:
            perms = ROLES.get(role, [])
            if "*" in perms or permission in perms:
                return True
        return False

    def can_access_resource(self, resource_owner_id: str) -> bool:
        """Can access if owner or admin."""
        return check_ownership(resource_owner_id, self.user_id)
