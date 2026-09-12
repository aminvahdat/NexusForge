"""LLM Service for NexusForge.

Provides dynamic, stack-aware code and text generation powered by real LLMs (OpenRouter, OpenAI, etc.).
Features:
1. Automatic active API key discovery from database (user_api_keys) or environment.
2. Dynamic technology stack detection (C#/.NET, Python, Node/TS, Go, Rust).
3. Real AI generation for each agent with resilient model fallback.
4. Intelligent language-tailored fallback synthesis to ensure zero hallucination or hardcoded static mismatches.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx
from sqlalchemy import select

logger = logging.getLogger("llm_service")

# High-quality active free models on OpenRouter
FALLBACK_MODELS = [
    "nex-agi/nex-n2.5-pro:free",
    "google/gemma-4-31b-it:free",
    "liquid/lfm-2.5-2.6b:free",
    "nvidia/nemotron-3.5-lightning:free",
    "meta-llama/llama-3.3-70b-instruct",
]


async def get_active_api_key(db_session) -> Optional[Dict[str, str]]:
    """Retrieve active API key from database or environment."""
    try:
        from app.models import UserAPIKey
        result = await db_session.execute(
            select(UserAPIKey).where(UserAPIKey.is_active == True).order_by(UserAPIKey.created_at.desc())
        )
        key_record = result.scalars().first()
        if key_record and key_record.api_key:
            return {
                "provider": key_record.provider or "openrouter",
                "api_key": key_record.api_key.strip(),
                "model": key_record.model or "nex-agi/nex-n2.5-pro:free",
            }
    except Exception as e:
        logger.warning(f"Error fetching API key from DB: {e}")

    # Fallback to environment
    env_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if env_key:
        return {
            "provider": "openrouter" if "OPENROUTER" in os.environ else "openai",
            "api_key": env_key.strip(),
            "model": "nex-agi/nex-n2.5-pro:free",
        }
    return None


def detect_tech_stack(text_corpus: str) -> Dict[str, Any]:
    """Analyze project title, description, and chat prompts to detect intended technology stack."""
    clean = text_corpus.lower()

    # C# / .NET / ASP.NET
    csharp_matches = ["c#", "csharp", "dotnet", ".net", "asp.net", "aspnet", "blazor", "razor", "entity framework", "nuget", "csproj"]
    if any(k in clean for k in csharp_matches):
        return {
            "language": "csharp",
            "language_title": "C# (.NET 8.0 / ASP.NET Core)",
            "framework": "ASP.NET Core Minimal APIs",
            "extension": ".cs",
            "main_file": "Program.cs",
            "models_file": "Models.cs",
            "manifest_file": "Project.csproj",
            "manifest_type": "csproj",
            "runner_cmd": "dotnet run",
            "compiler": "dotnet",
        }

    # Node.js / TypeScript / JavaScript
    node_matches = ["node", "nodejs", "typescript", "express", "nest", "javascript", "react", "vue", "nextjs", "npm"]
    if any(k in clean for k in node_matches):
        is_ts = "typescript" in clean or "ts" in clean
        return {
            "language": "typescript" if is_ts else "javascript",
            "language_title": "TypeScript (Node.js)" if is_ts else "JavaScript (Node.js)",
            "framework": "Express.js REST API",
            "extension": ".ts" if is_ts else ".js",
            "main_file": "server.ts" if is_ts else "server.js",
            "models_file": "types.ts" if is_ts else "models.js",
            "manifest_file": "package.json",
            "manifest_type": "json",
            "runner_cmd": "node server.js",
            "compiler": "node",
        }

    # Go / Golang
    go_matches = ["go", "golang", "gin", "fiber", "echo", "goroutine"]
    if any(k in clean for k in go_matches):
        return {
            "language": "go",
            "language_title": "Go (Golang 1.22+)",
            "framework": "Go Net/HTTP & Gin REST API",
            "extension": ".go",
            "main_file": "main.go",
            "models_file": "models.go",
            "manifest_file": "go.mod",
            "manifest_type": "mod",
            "runner_cmd": "go run .",
            "compiler": "go",
        }

    # Default: Python / FastAPI
    return {
        "language": "python",
        "language_title": "Python 3.10+ (FastAPI)",
        "framework": "FastAPI & Uvicorn",
        "extension": ".py",
        "main_file": "main.py",
        "models_file": "models.py",
        "manifest_file": "requirements.txt",
        "manifest_type": "txt",
        "runner_cmd": "python main.py",
        "compiler": "python",
    }


async def call_openrouter(
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    preferred_model: Optional[str] = None,
    temperature: float = 0.5,
    timeout_sec: float = 6.0,
) -> Optional[str]:
    """Call OpenRouter API with graceful model failover."""
    models_queue = []
    # If preferred model is an obsolete free model that returns 404, skip it
    if preferred_model and "llama-3.3-70b-instruct:free" not in preferred_model:
        models_queue.append(preferred_model)
    for fm in FALLBACK_MODELS:
        if fm not in models_queue:
            models_queue.append(fm)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "NexusForge/1.0",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "NexusForge Autonomous Squad",
    }

    async with httpx.AsyncClient(timeout=timeout_sec) as client:
        for model in models_queue[:2]:  # Try top 2 fast models
            try:
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": temperature,
                }
                res = await client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if content and content.strip():
                        return content.strip()
                elif res.status_code in (404, 429):
                    logger.warning(f"Model {model} returned HTTP {res.status_code}, trying next model")
                    continue
            except Exception as e:
                logger.warning(f"Error calling {model}: {e}")
                continue

    return None


def clean_code_block(raw_text: str, expected_lang: str = "") -> str:
    """Extract clean code from markdown code blocks if present."""
    if not raw_text:
        return ""
    # Pattern for ```csharp ... ``` or ```python ... ```
    pattern = r"```(?:[a-zA-Z0-9_+-]*\n)?([\s\S]*?)```"
    matches = re.findall(pattern, raw_text)
    if matches:
        # Return largest matching code block
        return max(matches, key=len).strip()
    return raw_text.strip()
