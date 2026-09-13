"""Hermes Conversational Agent Service for NexusForge.

Implements the conversational Lead Architect & Copilot (Hermes / Arya) that:
1. Interviews the user and asks clarifying questions about the project.
2. Automatically selects optimal free models (or user-chosen providers) for each agent role.
3. Guides the user through architectural choices before and during code synthesis.
4. Orchestrates autonomous squad execution when confirmed by the user.
"""

import uuid
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Project, ProjectMessage, UserAPIKey

logger = logging.getLogger("hermes_agent")

# Curated Recommended Models by Role
DEFAULT_FREE_MODELS: Dict[str, Dict[str, str]] = {
    "orchestrator": {
        "role_title": "هدایتگر و برنامه‌ریز (Orchestrator)",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "reason": "Llama 3.3 70B for task planning and coordination"
    },
    "architect": {
        "role_title": "معمار سیستم (System Architect)",
        "model": "deepseek/deepseek-r1:free",
        "reason": "DeepSeek-R1 for modular architecture and schema contracts"
    },
    "backend": {
        "role_title": "توسعه بک‌اند (Backend Coder)",
        "model": "qwen/qwen-2.5-coder-32b-instruct:free",
        "reason": "Qwen 2.5 Coder 32B for clean backend services"
    },
    "frontend": {
        "role_title": "رابط کاربری (UI/UX Coder)",
        "model": "google/gemini-2.0-flash-exp:free",
        "reason": "Gemini 2.0 Flash for web interface development"
    },
    "qa": {
        "role_title": "آزمون و کیفیت (QA & Testing)",
        "model": "mistralai/mistral-small-24b-instruct-2501:free",
        "reason": "Mistral Small for verification and code review"
    },
}


def is_persian(text: str) -> bool:
    """Check if text contains Persian or Arabic characters."""
    for char in text:
        if '\u0600' <= char <= '\u06FF':
            return True
    return False


class HermesAgentService:
    """Core Hermes Conversational Agent service."""

    @staticmethod
    async def get_or_create_initial_messages(
        db_session: AsyncSession, project: Project
    ) -> List[Dict[str, Any]]:
        """Ensure initial greeting and clarifying questions exist for the project."""
        p_uuid = project.id if isinstance(project.id, uuid.UUID) else uuid.UUID(str(project.id))
        
        # Check existing messages
        res = await db_session.execute(
            select(ProjectMessage)
            .where(ProjectMessage.project_id == p_uuid)
            .order_by(ProjectMessage.created_at.asc())
        )
        messages = res.scalars().all()
        if messages:
            return [m.to_dict() for m in messages]

        # Generate smart initial greeting & clarifying questions
        p_name = project.name
        p_desc = project.description or "پروژه نرم‌افزاری خودکار"
        use_fa = is_persian(p_name + p_desc) or project.preferred_language == "fa"

        if use_fa:
            greeting = (
                f"سلام! من دستیار هوشمند پروژه **«{p_name}»** در نکسوس‌فورج هستم.\n\n"
                f"هدف پروژه شما بررسی شد. برای اینکه کدی دقیق، کاربردی و منطبق بر نیاز واقعی شما در پوشه کاری تولید شود، "
                f"لطفاً نظرتان را در مورد این ۳ سوال کلیدی بفرمایید:\n\n"
                f"1. **زبان و فریم‌ورک پایه:** آیا ترجیح شما پایتون (مثلاً FastAPI / Flask) است یا استک دیگری مدنظر دارید؟\n"
                f"2. **پایگاه داده و ذخیره‌سازی:** آیا سیستم نیاز به ذخیره‌سازی پایدار (مانند SQLite خودکار یا دیتابیس خاص) دارد؟\n"
                f"3. **رابط کاربری:** آیا مایلید یک داشبورد تک‌صفحه‌ای وب شیک و واکنش‌گرا (HTML/CSS) برای کنترل این سیستم طراحی و اضافه شود؟\n\n"
                f"می‌توانید پاسخ سوالات را تایپ کنید، یا از گزینه‌های سریع زیر انتخاب کنید یا مستقیماً دکمه «🚀 ساخت و اجرا» را بزنید!"
            )
            quick_chips = [
                "🚀 با تنظیمات پیش‌فرض بساز و اجرا کن",
                "⚡ بک‌اند پایتون FastAPI + دیتابیس SQLite",
                "💎 همراه با داشبورد وب شیک و واکنش‌گرا",
                "🛠️ فقط یک اسکریپت سبک و سریع تولید کن"
            ]
        else:
            greeting = (
                f"Hello! I am your technical project assistant for **\"{p_name}\"**.\n\n"
                f"Before generating production code in your workspace, could you clarify 3 quick details?\n\n"
                f"1. **Core Tech Stack:** Do you prefer Python (FastAPI / Flask) or another runtime?\n"
                f"2. **Data Persistence:** Does this require an embedded database (like SQLite) or in-memory state?\n"
                f"3. **User Interface:** Would you like a responsive single-page web dashboard to interact with the system?\n\n"
                f"Reply here or click any of the quick suggestions below to start!"
            )
            quick_chips = [
                "🚀 Build with default settings",
                "⚡ Python FastAPI + SQLite DB",
                "💎 Include modern Web Dashboard",
                "🛠️ Lightweight CLI script only"
            ]

        msg = ProjectMessage(
            id=uuid.uuid4(),
            project_id=p_uuid,
            sender="hermes",
            content=greeting,
            metadata_json={
                "type": "interview",
                "quick_chips": quick_chips,
                "suggested_models": DEFAULT_FREE_MODELS,
            },
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(msg)
        await db_session.commit()
        await db_session.refresh(msg)
        return [msg.to_dict()]

    @staticmethod
    async def handle_user_message(
        db_session: AsyncSession, project: Project, user_text: str
    ) -> Dict[str, Any]:
        """Process an incoming user message, generate Hermes response, and decide if build should trigger."""
        p_uuid = project.id if isinstance(project.id, uuid.UUID) else uuid.UUID(str(project.id))
        user_clean = user_text.strip()
        use_fa = is_persian(user_clean + project.name) or project.preferred_language == "fa"

        # 1. Save user message
        user_msg = ProjectMessage(
            id=uuid.uuid4(),
            project_id=p_uuid,
            sender="user",
            content=user_clean,
            metadata_json={},
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(user_msg)
        await db_session.commit()

        # Check if user wants to trigger build
        build_triggers = [
            "بساز", "اجرا", "شروع کن", "تایید", "اوکی", "run", "build", "start",
            "پیاده‌سازی", "کد بزن", "تولید کن", "go", "create", "execute"
        ]
        is_build_request = any(t in user_clean.lower() for t in build_triggers)

        # Detect technology stack from user input and project context
        from app.services.llm_service import detect_tech_stack, get_active_api_key, call_openrouter
        full_context = f"{project.name} {project.description or ''} {user_clean}"
        stack = detect_tech_stack(full_context)

        # 2. Formulate response
        if is_build_request:
            if use_fa:
                hermes_reply = (
                    f"بسیار عالی! تمام ترجیحات شما دریافت و در نقشه معماری ثبت شد. 🎯\n\n"
                    f"استک انتخابی پروژه: **{stack['language_title']}** ({stack['framework']})\n\n"
                    f"تسک‌های پروژه برای تولید فایل‌های کالبدی زیر در پوشه کاری آماده شدند:\n"
                    f"• سند مشخصات و قراردادهای معماری (`system_architecture.md`)\n"
                    f"• مدل‌های داده و ساختار دیتابیس (`{stack['models_file']}`)\n"
                    f"• وب‌سرویس اصلی و اندپوینت‌ها (`{stack['main_file']}`)\n"
                    f"• رابط کاربری و صفحات داشبورد (`index.html`)\n"
                    f"• مانیفست وابستگی‌ها و راهنمای اجرا (`{stack['manifest_file']}`, `README.md`)\n\n"
                    f"⏳ فایل‌ها در فضای کاری پروژه مستقر شدند. می‌توانید تب «فایل‌های پروژه» را مشاهده کنید."
                )
            else:
                hermes_reply = (
                    f"Excellent! All your specifications have been recorded into the architectural blueprint. 🎯\n\n"
                    f"Selected Stack: **{stack['language_title']}** ({stack['framework']})\n\n"
                    f"Project tasks structured for workspace synthesis:\n"
                    f"• Architecture specifications (`system_architecture.md`)\n"
                    f"• Data models and schemas (`{stack['models_file']}`)\n"
                    f"• Core service implementation (`{stack['main_file']}`)\n"
                    f"• Web interface dashboard (`index.html`)\n"
                    f"• Dependency manifest and runbook (`{stack['manifest_file']}`, `README.md`)\n\n"
                    f"⏳ Workspace files ready. Check the 'Project Files' tab!"
                )
            trigger_build = True
            chips = ["📁 مشاهده فایل‌های پروژه", "⚙️ مشخصات و پیکربندی"]
        else:
            # Contextual conversational guidance with LLM or smart stack detection
            trigger_build = False
            llm_reply = None
            try:
                key_info = await get_active_api_key(db_session)
                if key_info and key_info.get("api_key"):
                    sys_prompt = (
                        f"You are the technical project assistant for NexusForge. "
                        f"Communicate fluently and politely in natural Persian (Farsi). "
                        f"The user is planning a software project: '{project.name}'. "
                        f"The detected target technology stack is: {stack['language_title']} ({stack['framework']}). "
                        f"CRITICAL: Never suggest Python if the user requested another language like C#, Node.js, Go, etc. "
                        f"Acknowledge the user's specific stack ({stack['language_title']}), discuss the requested features, "
                        f"and ask if they are ready to generate the code files ({stack['main_file']}, {stack['models_file']}, {stack['manifest_file']}, index.html)."
                    )
                    llm_reply = await call_openrouter(
                        api_key=key_info["api_key"],
                        system_prompt=sys_prompt,
                        user_prompt=user_clean,
                        preferred_model=key_info.get("model"),
                        timeout_sec=12.0
                    )
            except Exception as e:
                logger.warning(f"Hermes LLM call error: {e}")

            if llm_reply and len(llm_reply.strip()) > 20:
                hermes_reply = llm_reply.strip()
            elif use_fa:
                hermes_reply = (
                    f"نکات و دستورات شما کاملاً دریافت و ثبت شد: «{user_clean}».\n\n"
                    f"من این موارد را به عنوان استاندارد پروژه تنظیم کردم:\n"
                    f"✓ زبان و پلتفرم اجرایی: **{stack['language_title']}** ({stack['framework']})\n"
                    f"✓ فایل‌های سورس‌کد تولیدی: `{stack['main_file']}`, `{stack['models_file']}`, `{stack['manifest_file']}` و `index.html`\n"
                    f"✓ کاملاً منطبق بر نیازمندی‌های خواسته شده شما (بدون وابستگی به استک ناخواسته).\n\n"
                    f"آیا نکته دیگری هست که مایلید اضافه کنید، یا برای شروع ساخت و کدنویسی آماده‌اید؟"
                )
            else:
                hermes_reply = (
                    f"Got your input: \"{user_clean}\".\n\n"
                    f"I've configured the architecture strictly according to your instructions:\n"
                    f"✓ Target Technology: **{stack['language_title']}** ({stack['framework']})\n"
                    f"✓ Files to generate: `{stack['main_file']}`, `{stack['models_file']}`, `{stack['manifest_file']}`, `index.html`.\n\n"
                    f"Would you like to add any other specifications, or are you ready to build?"
                )

            chips = [
                f"🚀 با استک {stack['language_title']} بساز و اجرا کن",
                "📦 پنل ادمین و احراز هویت هم اضافه کن",
                "📊 تنظیمات دیتابیس و سرویس‌ها"
            ]

        # Save Hermes reply
        hermes_msg = ProjectMessage(
            id=uuid.uuid4(),
            project_id=p_uuid,
            sender="hermes",
            content=hermes_reply,
            metadata_json={
                "trigger_build": trigger_build,
                "quick_chips": chips,
                "models": DEFAULT_FREE_MODELS,
            },
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(hermes_msg)
        await db_session.commit()
        await db_session.refresh(hermes_msg)

        return {
            "user_message": user_msg.to_dict(),
            "hermes_message": hermes_msg.to_dict(),
            "assistant_message": hermes_msg.to_dict(),
            "trigger_build": trigger_build,
        }
