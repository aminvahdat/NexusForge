"""Agent Configuration & Management API for NexusForge.

Allows dynamic configuration of agent roles, custom system prompts,
AI provider/model selection, reasoning effort, and team composition.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/agents", tags=["agents"])

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
CONFIG_FILE = CONFIG_DIR / "agents_config.json"


class AgentConfig(BaseModel):
    id: str
    role: str
    name: str
    codename: str = ""
    codename_fa: str = ""
    avatar_badge: str = "🤖"
    description: str
    system_prompt: str
    provider: str = "anthropic"
    model: str = "claude-3-5-sonnet-20241022"
    reasoning_effort: str = "medium"  # none, low, medium, high
    temperature: float = 0.7
    max_tokens: int = 4000
    skills: List[str] = Field(default_factory=list)
    is_active: bool = True
    is_builtin: bool = True
    created_at: str
    updated_at: str


class AgentCreate(BaseModel):
    role: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=100)
    codename: str = ""
    codename_fa: str = ""
    avatar_badge: str = "🤖"
    description: str = Field(..., min_length=5, max_length=500)
    system_prompt: str = Field(..., min_length=10)
    provider: str = "anthropic"
    model: str = "claude-3-5-sonnet-20241022"
    reasoning_effort: str = "medium"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000, ge=100, le=128000)
    skills: List[str] = Field(default_factory=list)
    is_active: bool = True


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    codename: Optional[str] = None
    codename_fa: Optional[str] = None
    avatar_badge: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    reasoning_effort: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    skills: Optional[List[str]] = None
    is_active: Optional[bool] = None


def _load_initial_agents() -> List[dict]:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


DEFAULT_AGENTS: List[dict] = _load_initial_agents()


def load_agents() -> List[AgentConfig]:
    """Load agents from persistent storage or initialize defaults."""
    now_iso = datetime.now(timezone.utc).isoformat()
    if not CONFIG_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        agents = []
        for a in DEFAULT_AGENTS:
            item = a.copy()
            item["created_at"] = now_iso
            item["updated_at"] = now_iso
            agents.append(AgentConfig(**item))
        save_agents(agents)
        return agents

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [AgentConfig(**item) for item in data]
    except Exception:
        return [AgentConfig(**a, created_at=now_iso, updated_at=now_iso) for a in DEFAULT_AGENTS]


def save_agents(agents: List[AgentConfig]):
    """Save agents list to persistent JSON file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump([a.model_dump() for a in agents], f, indent=2, ensure_ascii=False)


@router.get("", response_model=List[AgentConfig], summary="List all configured agents")
async def list_agents():
    """Retrieve all active and customized agents."""
    return load_agents()


@router.get("/{agent_id}", response_model=AgentConfig, summary="Get agent details")
async def get_agent(agent_id: str):
    """Retrieve a single agent configuration by ID."""
    agents = load_agents()
    for a in agents:
        if a.id == agent_id:
            return a
    raise HTTPException(status_code=404, detail="Agent not found")


@router.post("", response_model=AgentConfig, status_code=status.HTTP_201_CREATED, summary="Create custom agent")
async def create_agent(agent_in: AgentCreate):
    """Create a new custom specialized agent."""
    agents = load_agents()
    now_iso = datetime.now(timezone.utc).isoformat()
    new_id = f"agent-{uuid.uuid4().hex[:8]}"

    new_agent = AgentConfig(
        id=new_id,
        role=agent_in.role.lower().strip().replace(" ", "_"),
        name=agent_in.name.strip(),
        description=agent_in.description.strip(),
        system_prompt=agent_in.system_prompt.strip(),
        provider=agent_in.provider,
        model=agent_in.model,
        reasoning_effort=agent_in.reasoning_effort,
        temperature=agent_in.temperature,
        max_tokens=agent_in.max_tokens,
        skills=agent_in.skills or ["custom_skill"],
        is_active=agent_in.is_active,
        is_builtin=False,
        created_at=now_iso,
        updated_at=now_iso,
    )
    agents.append(new_agent)
    save_agents(agents)
    return new_agent


@router.put("/{agent_id}", response_model=AgentConfig, summary="Update agent configuration")
async def update_agent(agent_id: str, agent_in: AgentUpdate):
    """Update prompt, role, model, reasoning effort, or skills of an existing agent."""
    agents = load_agents()
    now_iso = datetime.now(timezone.utc).isoformat()

    found_idx = None
    for idx, a in enumerate(agents):
        if a.id == agent_id:
            found_idx = idx
            break

    if found_idx is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    target = agents[found_idx]
    update_data = agent_in.model_dump(exclude_unset=True)

    for field, val in update_data.items():
        if val is not None:
            setattr(target, field, val)

    target.updated_at = now_iso
    agents[found_idx] = target
    save_agents(agents)
    return target


@router.delete("/{agent_id}", status_code=status.HTTP_200_OK, summary="Delete an agent")
async def delete_agent(agent_id: str):
    """Delete an agent from the active team."""
    agents = load_agents()
    target = None
    for a in agents:
        if a.id == agent_id:
            target = a
            break

    if not target:
        raise HTTPException(status_code=404, detail="Agent not found")

    if target.role == "chief_orchestrator":
        raise HTTPException(status_code=400, detail="Cannot delete the primary Chief Orchestrator agent")

    agents = [a for a in agents if a.id != agent_id]
    save_agents(agents)
    return {"message": f"Agent '{target.name}' deleted successfully", "id": agent_id}


@router.post("/reset", response_model=List[AgentConfig], summary="Reset agents to defaults")
async def reset_agents():
    """Reset all agent configurations to factory defaults."""
    now_iso = datetime.now(timezone.utc).isoformat()
    agents = [AgentConfig(**a, created_at=now_iso, updated_at=now_iso) for a in DEFAULT_AGENTS]
    save_agents(agents)
    return agents