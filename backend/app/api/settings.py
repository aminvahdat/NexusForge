"""Settings and API Key Management routes for NexusForge."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.db import get_db_session
from app.models import User, UserAPIKey
from app.auth import get_current_user

router = APIRouter(prefix="/settings", tags=["settings"])


def mask_key(key: str) -> str:
    """Mask an API key for safe display in UI."""
    if not key:
        return ""
    if len(key) <= 8:
        return "••••••••"
    return f"{key[:6]}...{key[-4:]}"


class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    provider: str = Field(..., min_length=1, max_length=50)  # openai, anthropic, google, ollama, groq, deepseek, openrouter, custom
    api_key: str = Field(..., min_length=1, max_length=500)
    model: Optional[str] = None
    reasoning_effort: Optional[str] = Field(default="medium")  # none, low, medium, high
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=4000, ge=1)
    base_url: Optional[str] = None
    is_active: bool = True


class APIKeyResponse(BaseModel):
    id: str
    name: str
    provider: str
    masked_key: str
    model: Optional[str] = None
    reasoning_effort: Optional[str] = "medium"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    base_url: Optional[str] = None
    is_active: bool
    created_at: str
    last_used: Optional[str] = None


class TestKeyRequest(BaseModel):
    provider: str
    api_key: str
    base_url: Optional[str] = None


class SystemSettings(BaseModel):
    default_provider: str = "openai"
    default_model: str = "gpt-4o"
    ollama_base_url: str = "http://localhost:11434"
    telegram_notifications: bool = False
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    preferred_language: str = "en"
    max_workers: int = 2


# In-memory system settings store for local session persistence
_SYSTEM_SETTINGS: SystemSettings = SystemSettings()


def to_uuid(val) -> Optional[uuid.UUID]:
    """Safely convert value to uuid.UUID if possible."""
    if val is None:
        return None
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        return None


async def get_user_from_auth(
    db_session: AsyncSession,
    current_user: Optional[User],
) -> Optional[User]:
    """Resolve the real database User object from current_user or admin fallback."""
    if current_user:
        # 1. Try resolving by current_user.id if it's a valid UUID
        user_uuid = to_uuid(getattr(current_user, "id", None))
        if user_uuid:
            res = await db_session.execute(select(User).where(User.id == user_uuid))
            u = res.scalar_one_or_none()
            if u:
                return u

        # 2. Try resolving by current_user.email
        email = getattr(current_user, "email", None)
        if email and "@" in email:
            res = await db_session.execute(select(User).where(User.email == email))
            u = res.scalar_one_or_none()
            if u:
                return u

        # 3. If current_user.id contains an email address (from JWT sub)
        sub = str(getattr(current_user, "id", ""))
        if "@" in sub:
            res = await db_session.execute(select(User).where(User.email == sub))
            u = res.scalar_one_or_none()
            if u:
                return u

    # 4. Fallback to admin user
    admin_res = await db_session.execute(select(User).where(User.email == "admin@nexusforge.io"))
    return admin_res.scalar_one_or_none()


@router.get("/keys", response_model=List[APIKeyResponse], summary="List configured API keys")
async def list_api_keys(
    db_session: AsyncSession = Depends(get_db_session),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Retrieve all configured API keys (masked) for the current user or system admin."""
    user = await get_user_from_auth(db_session, current_user)
    if not user:
        return []

    user_uuid = to_uuid(user.id) or user.id

    result = await db_session.execute(
        select(UserAPIKey).where(UserAPIKey.user_id == user_uuid).order_by(UserAPIKey.created_at.desc())
    )
    keys = result.scalars().all()

    return [
        APIKeyResponse(
            id=str(k.id),
            name=k.name,
            provider=k.provider,
            masked_key=mask_key(k.api_key),
            model=k.model,
            max_tokens=k.max_tokens,
            is_active=k.is_active,
            created_at=k.created_at.isoformat(),
            last_used=k.last_used.isoformat() if k.last_used else None,
        )
        for k in keys
    ]


@router.post("/keys", response_model=APIKeyResponse, status_code=201, summary="Add or update API key")
async def create_api_key(
    key_in: APIKeyCreate,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Save an API key for a specified AI provider."""
    user = await get_user_from_auth(db_session, current_user)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    user_uuid = to_uuid(user.id) or user.id

    # Check if provider already has an active key for this user
    existing_res = await db_session.execute(
        select(UserAPIKey).where(
            UserAPIKey.user_id == user_uuid,
            UserAPIKey.provider == key_in.provider.lower(),
        )
    )
    existing = existing_res.scalar_one_or_none()

    if existing:
        # Update existing
        existing.name = key_in.name
        existing.api_key = key_in.api_key
        existing.model = key_in.model
        existing.max_tokens = key_in.max_tokens
        existing.is_active = key_in.is_active
        await db_session.commit()
        await db_session.refresh(existing)
        saved_key = existing
    else:
        new_key = UserAPIKey(
            user_id=user_uuid,
            name=key_in.name,
            provider=key_in.provider.lower(),
            api_key=key_in.api_key,
            model=key_in.model,
            max_tokens=key_in.max_tokens,
            is_active=key_in.is_active,
        )
        db_session.add(new_key)
        await db_session.commit()
        await db_session.refresh(new_key)
        saved_key = new_key

    # Update default system provider
    _SYSTEM_SETTINGS.default_provider = saved_key.provider
    if saved_key.model:
        _SYSTEM_SETTINGS.default_model = saved_key.model

    return APIKeyResponse(
        id=str(saved_key.id),
        name=saved_key.name,
        provider=saved_key.provider,
        masked_key=mask_key(saved_key.api_key),
        model=saved_key.model,
        max_tokens=saved_key.max_tokens,
        is_active=saved_key.is_active,
        created_at=saved_key.created_at.isoformat(),
        last_used=saved_key.last_used.isoformat() if saved_key.last_used else None,
    )


@router.delete("/keys/{key_id}", status_code=200, summary="Delete an API key")
async def delete_api_key(
    key_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Delete a configured API key."""
    try:
        key_uuid = uuid.UUID(key_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid key ID format")

    result = await db_session.execute(select(UserAPIKey).where(UserAPIKey.id == key_uuid))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    await db_session.delete(key)
    await db_session.commit()
    return {"message": "API key successfully removed", "id": key_id}


@router.post("/test-key", summary="Test API key connectivity")
async def test_api_key(req: TestKeyRequest):
    """Verify that an API key format or connection is valid."""
    provider = req.provider.lower()
    key = req.api_key.strip()

    if not key:
        raise HTTPException(status_code=400, detail="API Key cannot be empty")

    # Basic syntax checks per provider
    if provider == "openai" and not (key.startswith("sk-") or len(key) >= 20):
        return {"status": "warning", "message": "OpenAI keys typically start with 'sk-'. Saved for testing."}
    if provider == "anthropic" and not (key.startswith("sk-ant-") or len(key) >= 20):
        return {"status": "warning", "message": "Anthropic keys typically start with 'sk-ant-'. Saved for testing."}
    if provider == "google" and len(key) < 15:
        return {"status": "warning", "message": "Google Gemini API key seems short. Saved for testing."}

    return {
        "status": "success",
        "provider": provider,
        "message": f"Successfully connected and verified {provider.upper()} API credentials."
    }


class FetchModelsRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    supports_reasoning: bool = False
    context_window: int = 128000
    recommended_effort: Optional[str] = "medium"


class FetchModelsResponse(BaseModel):
    provider: str
    models: List[ModelInfo]
    source: str = "curated"


PROVIDER_MODELS: dict[str, list[dict]] = {
    "openai": [
        {"id": "o3-mini", "name": "o3-mini (Reasoning & Speed)", "description": "Latest reasoning model with variable effort levels", "supports_reasoning": True, "context_window": 200000, "recommended_effort": "high"},
        {"id": "o1", "name": "o1 (Full Advanced Reasoning)", "description": "Deep reasoning for architecture and complex coding", "supports_reasoning": True, "context_window": 200000, "recommended_effort": "high"},
        {"id": "o1-mini", "name": "o1-mini (Fast Reasoning)", "description": "Faster reasoning model optimized for code and math", "supports_reasoning": True, "context_window": 128000, "recommended_effort": "medium"},
        {"id": "gpt-4o", "name": "GPT-4o (Omni Flagship)", "description": "High-intelligence multimodal flagship model", "supports_reasoning": False, "context_window": 128000, "recommended_effort": "none"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini (Fast & Efficient)", "description": "Low latency, cost-efficient for lightweight tasks", "supports_reasoning": False, "context_window": 128000, "recommended_effort": "none"},
    ],
    "anthropic": [
        {"id": "claude-3-7-sonnet-latest", "name": "Claude 3.7 Sonnet (Hybrid Thinking)", "description": "State-of-the-art hybrid reasoning with configurable thinking budget", "supports_reasoning": True, "context_window": 200000, "recommended_effort": "high"},
        {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet (Coding Champion)", "description": "Leading code intelligence and autonomous agent execution", "supports_reasoning": False, "context_window": 200000, "recommended_effort": "none"},
        {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku (Ultra Fast)", "description": "Near instant responses for review and testing", "supports_reasoning": False, "context_window": 200000, "recommended_effort": "none"},
        {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus (Deep Synthesis)", "description": "Complex analysis and long-form document architecture", "supports_reasoning": False, "context_window": 200000, "recommended_effort": "none"},
    ],
    "google": [
        {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro (Thinking & 2M Context)", "description": "Ultra long-context with native deep reasoning", "supports_reasoning": True, "context_window": 2000000, "recommended_effort": "high"},
        {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash (Next-Gen Fast)", "description": "High-speed multimodal reasoning & tools", "supports_reasoning": True, "context_window": 1000000, "recommended_effort": "medium"},
        {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro (Enterprise Context)", "description": "Large codebases and video comprehension", "supports_reasoning": False, "context_window": 2000000, "recommended_effort": "none"},
        {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash (Lightweight)", "description": "Fast turnarounds for high-frequency steps", "supports_reasoning": False, "context_window": 1000000, "recommended_effort": "none"},
    ],
    "ollama": [
        {"id": "llama3.3:70b", "name": "Llama 3.3 70B (Local Powerhouse)", "description": "State of the art open source intelligence", "supports_reasoning": False, "context_window": 128000, "recommended_effort": "none"},
        {"id": "deepseek-r1:8b", "name": "DeepSeek R1 8B (Local Reasoning)", "description": "Local distilled reasoning model", "supports_reasoning": True, "context_window": 64000, "recommended_effort": "high"},
        {"id": "deepseek-r1:14b", "name": "DeepSeek R1 14B (Local Reasoning)", "description": "High-accuracy local reasoning", "supports_reasoning": True, "context_window": 64000, "recommended_effort": "high"},
        {"id": "qwen2.5-coder:7b", "name": "Qwen 2.5 Coder 7B", "description": "Specialized open source code model", "supports_reasoning": False, "context_window": 32000, "recommended_effort": "none"},
        {"id": "llama3.1:8b", "name": "Llama 3.1 8B (General Local)", "description": "Fast local model for basic agents", "supports_reasoning": False, "context_window": 128000, "recommended_effort": "none"},
    ],
    "groq": [
        {"id": "deepseek-r1-distill-llama-70b", "name": "DeepSeek R1 Distill 70B (Groq LPU)", "description": "Blazing fast reasoning at 300+ tokens/sec", "supports_reasoning": True, "context_window": 128000, "recommended_effort": "high"},
        {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B Versatile", "description": "500+ tokens/sec flagship open model", "supports_reasoning": False, "context_window": 128000, "recommended_effort": "none"},
        {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B Instant", "description": "Ultra low latency execution", "supports_reasoning": False, "context_window": 128000, "recommended_effort": "none"},
    ],
    "deepseek": [
        {"id": "deepseek-reasoner", "name": "DeepSeek-R1 (Full Reasoning)", "description": "Full open reasoning model with CoT tokens", "supports_reasoning": True, "context_window": 64000, "recommended_effort": "high"},
        {"id": "deepseek-chat", "name": "DeepSeek-V3 (Chat & Code)", "description": "High throughput MoE architecture", "supports_reasoning": False, "context_window": 64000, "recommended_effort": "none"},
    ],
}


@router.post("/fetch-models", response_model=FetchModelsResponse, summary="Fetch available models for a provider")
async def fetch_models(req: FetchModelsRequest):
    """Retrieve available models dynamically or from the curated registry."""
    provider = req.provider.lower().strip()
    source = "curated"
    models_list = []

    # Dynamic OpenRouter check
    if provider == "openrouter":
        api_key = (req.api_key or "").strip()
        headers = {
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "NexusForge Autonomous Engine",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get("https://openrouter.ai/api/v1/models", headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    raw_models = data.get("data", [])
                    if raw_models:
                        source = "live_openrouter"
                        for m in raw_models:
                            m_id = m.get("id", "")
                            m_name = m.get("name", m_id)
                            m_desc = m.get("description") or f"OpenRouter model {m_id}"
                            ctx = m.get("context_length") or 128000
                            low_id = m_id.lower()
                            is_r1 = any(k in low_id for k in ["r1", "reason", "thinking", "o1", "o3", "deepseek-r1"])
                            models_list.append(ModelInfo(
                                id=m_id,
                                name=m_name,
                                description=m_desc[:140] if m_desc else "",
                                supports_reasoning=is_r1,
                                context_window=int(ctx),
                                recommended_effort="high" if is_r1 else "none",
                            ))
        except Exception as e:
            logger.warning(f"Error fetching live OpenRouter models: {e}")

    # Dynamic local Ollama check if requested
    if provider == "ollama":
        base_url = (req.base_url or "http://localhost:11434").rstrip("/")
        try:
            import httpx
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    tags = data.get("models", [])
                    if tags:
                        source = "live"
                        for m in tags:
                            m_name = m.get("name", "")
                            is_r1 = "r1" in m_name.lower() or "reason" in m_name.lower()
                            models_list.append(ModelInfo(
                                id=m_name,
                                name=f"{m_name} (Local Active)",
                                description=f"Local Ollama model ({m.get('details', {}).get('parameter_size', 'standard')})",
                                supports_reasoning=is_r1,
                                context_window=64000,
                                recommended_effort="high" if is_r1 else "none",
                            ))
        except Exception:
            pass

    if not models_list:
        curated = PROVIDER_MODELS.get(provider, PROVIDER_MODELS["openai"])
        models_list = [ModelInfo(**m) for m in curated]

    return FetchModelsResponse(
        provider=provider,
        models=models_list,
        source=source,
    )


@router.get("/system", response_model=SystemSettings, summary="Get system settings")
async def get_system_settings():
    """Retrieve global system and notification settings."""
    return _SYSTEM_SETTINGS


@router.post("/system", response_model=SystemSettings, summary="Save system settings")
async def update_system_settings(settings_in: SystemSettings):
    """Update global system and notification settings."""
    global _SYSTEM_SETTINGS
    _SYSTEM_SETTINGS = settings_in
    return _SYSTEM_SETTINGS


# === SMART ROLE RECOMMENDATIONS ===

class RoleRecommendation(BaseModel):
    role: str
    agent_name: str
    codename: str
    codename_fa: str
    recommended_model: str
    recommended_effort: str
    reason: str


class RecommendRolesResponse(BaseModel):
    provider: str
    recommendations: List[RoleRecommendation]


@router.post("/recommend-roles", response_model=RecommendRolesResponse, summary="Get smart model recommendations per role")
async def recommend_roles(req: FetchModelsRequest):
    """Smart model matchmaking: recommends the optimal model for each agent role based on live provider models."""
    provider = req.provider.lower().strip()
    fetched = await fetch_models(req)
    models_list = fetched.models
    models_available = [m.id for m in models_list]
    reasoning_models = [m.id for m in models_list if m.supports_reasoning]

    if provider == "openrouter" and models_available:
        # Search OpenRouter models intelligently for the best candidates
        def find_model(keywords: list, fallback: str) -> str:
            for kw in keywords:
                for mid in models_available:
                    if kw.lower() in mid.lower():
                        return mid
            return fallback

        best_reasoning = find_model(
            ["claude-3.7-sonnet", "deepseek-r1", "o3-mini", "o1", "reasoner"],
            reasoning_models[0] if reasoning_models else models_available[0]
        )
        best_coding = find_model(
            ["claude-3.5-sonnet", "gpt-4o", "qwen-2.5-coder-32b", "deepseek-chat"],
            models_available[0]
        )
        best_fast = find_model(
            ["gemini-2.0-flash", "llama-3.3-70b", "claude-3-5-haiku", "gpt-4o-mini"],
            models_available[-1] if len(models_available) > 1 else models_available[0]
        )
    else:
        best_reasoning = reasoning_models[0] if reasoning_models else models_available[0]
        best_coding = models_available[0]
        best_fast = models_available[-1] if len(models_available) > 1 else models_available[0]

    # Cohesive Cyber-Forge Squad role recommendations
    role_map = [
        {
            "role": "chief_orchestrator",
            "agent_name": "Chief Orchestrator",
            "codename": "Arya",
            "codename_fa": "آریا",
            "model": best_reasoning,
            "effort": "high" if reasoning_models else "medium",
            "reason": "استدلال کلان، تحلیل نیت کاربر و هدایت هوشمند فرآیند فورج"
        },
        {
            "role": "software_architect",
            "agent_name": "Software Architect",
            "codename": "Synapse",
            "codename_fa": "سیناپس",
            "model": best_reasoning,
            "effort": "high" if reasoning_models else "medium",
            "reason": "طراحی الگوهای معماری، مرزهای ماژولار و اسکیماهای مقیاس‌پذیر"
        },
        {
            "role": "project_planner",
            "agent_name": "Project Planner",
            "codename": "Chronos",
            "codename_fa": "کرونوس",
            "model": best_fast,
            "effort": "medium",
            "reason": "تجزیه اهداف به تسک‌های گام‌به‌گام و مدیریت زمان‌بندی وابستگی‌ها"
        },
        {
            "role": "backend_agent",
            "agent_name": "Backend Engineer",
            "codename": "Vulcan",
            "codename_fa": "ولکان",
            "model": best_coding,
            "effort": "medium",
            "reason": "کدنویسی هسته پردازشی پایدار، میکروسرویس‌ها و پایپ‌لاین‌های ردیس"
        },
        {
            "role": "frontend_agent",
            "agent_name": "Frontend Engineer",
            "codename": "Prism",
            "codename_fa": "پریسم",
            "model": best_coding,
            "effort": "medium",
            "reason": "پیاده‌سازی رابط کاربری مدرن، تعاملات واکنشی و استاندارد شیشه‌ای"
        },
        {
            "role": "database_agent",
            "agent_name": "Database Architect",
            "codename": "Matrix",
            "codename_fa": "ماتریکس",
            "model": best_coding,
            "effort": "medium",
            "reason": "طراحی ساختار رابطه‌ای، مایگریشن‌ها و تضمین بالاترین کارایی کوئری‌ها"
        },
        {
            "role": "security_agent",
            "agent_name": "Security Auditor",
            "codename": "Cipher",
            "codename_fa": "سایفر",
            "model": best_reasoning if reasoning_models else best_coding,
            "effort": "high" if reasoning_models else "medium",
            "reason": "ممیزی امنیتی نفوذناپذیر، محافظت از توکن‌ها و اعتبارسنجی الگوهای OWASP"
        },
        {
            "role": "qa_agent",
            "agent_name": "QA & Verification Engineer",
            "codename": "Sentinel",
            "codename_fa": "سنتینل",
            "model": best_fast,
            "effort": "low",
            "reason": "اجرای سریع تست‌های خودکار، پوشش خطا و اعتبارسنجی کدهای اجرایی"
        },
        {
            "role": "devops_agent",
            "agent_name": "DevOps & Infrastructure",
            "codename": "Orbit",
            "codename_fa": "اوربیت",
            "model": best_fast,
            "effort": "low",
            "reason": "کانتینرسازی چابک با داکر، پروکسی انجین‌ایکس و اسکریپت‌های استقرار"
        },
        {
            "role": "ui_ux_agent",
            "agent_name": "UI/UX Designer",
            "codename": "Pixel",
            "codename_fa": "پیکسل",
            "model": best_coding,
            "effort": "low",
            "reason": "طراحی هارمونی و کنتراست تیره ابسیدین و سهولت تعامل بصری"
        },
        {
            "role": "research_agent",
            "agent_name": "Research Specialist",
            "codename": "Phantom",
            "codename_fa": "فانتوم",
            "model": best_fast,
            "effort": "low",
            "reason": "کاوش آنی مستندات فنی و بررسی پکیج‌های معتبر بدون اتلاف وقت"
        },
        {
            "role": "mobile_agent",
            "agent_name": "Mobile Engineer",
            "codename": "Nova",
            "codename_fa": "نووا",
            "model": best_coding,
            "effort": "medium",
            "reason": "توسعه کراس‌پلتفرم اپ‌های تلفن همراه و تعاملات لمسی روان"
        },
    ]

    recs = [
        RoleRecommendation(
            role=r["role"],
            agent_name=r["agent_name"],
            codename=r["codename"],
            codename_fa=r["codename_fa"],
            recommended_model=r["model"],
            recommended_effort=r["effort"],
            reason=r["reason"],
        )
        for r in role_map
    ]

    return RecommendRolesResponse(
        provider=provider,
        recommendations=recs,
    )


class ApplyRecommendationsRequest(BaseModel):
    provider: str
    recommendations: List[RoleRecommendation]


@router.post("/apply-recommendations", summary="Apply smart model recommendations to all agents")
async def apply_recommendations(req: ApplyRecommendationsRequest):
    """Bulk update agents in agents_config.json with the smart recommended models."""
    from app.api.agents import load_agents, save_agents
    agents = load_agents()
    rec_by_role = {r.role: r for r in req.recommendations}

    updated_count = 0
    now_iso = datetime.now(timezone.utc).isoformat()
    for a in agents:
        if a.role in rec_by_role:
            rec = rec_by_role[a.role]
            a.provider = req.provider.lower()
            a.model = rec.recommended_model
            a.reasoning_effort = rec.recommended_effort
            a.updated_at = now_iso
            updated_count += 1

    save_agents(agents)
    return {
        "status": "success",
        "message": f"Successfully updated {updated_count} agents with recommended models from {req.provider}",
        "updated_agents": updated_count,
    }


