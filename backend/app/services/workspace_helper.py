"""Workspace directory management for NexusForge.

Ensures clean, human-readable, and predictable folder names based on project titles
instead of raw UUIDs or obscure hashes.
"""

import re
import unicodedata
from pathlib import Path
from typing import Optional


def slugify_name(text: str) -> str:
    """Generate a clean, readable ASCII / Latin / transliterated slug from project name."""
    if not text:
        return "project"

    text = text.lower().strip()

    # Domain-specific transliterations and replacements for common Persian tech keywords
    replacements = {
        "فروشگاه": "ecommerce_store",
        "فروشگاهی": "ecommerce_store",
        "سایت": "website",
        "وبسایت": "website",
        "ادمین": "admin",
        "پیامک": "sms",
        "رزرو": "booking",
        "انبار": "warehouse",
        "پرداخت": "payment",
        "چت": "chat",
        "پیام": "messaging",
        "مدیریت": "management",
        "سیستم": "system",
        "سامانه": "system",
        "تس": "task",
        "تسک": "task",
        "هوشمند": "smart",
        "داشبورد": "dashboard",
        "پایتون": "python",
        "سی شارپ": "csharp",
        "سی‌شارپ": "csharp",
        "نود": "node",
    }

    words = text.split()
    translated_parts = []
    for w in words:
        clean_w = re.sub(r"[^\w\s]", "", w)
        matched = False
        for k, v in replacements.items():
            if k in clean_w:
                translated_parts.append(v)
                matched = True
                break
        if not matched and clean_w:
            # Check if Latin
            if re.match(r"^[a-zA-Z0-9_-]+$", clean_w):
                translated_parts.append(clean_w)

    if translated_parts:
        slug = "_".join(translated_parts)
    else:
        # Fallback: remove non-alphanumeric
        slug = re.sub(r"[^\w\s-]", "", text)
        slug = re.sub(r"[-\s]+", "_", slug).strip("_")
        if not slug:
            slug = "nexus_project"

    # Deduplicate underscores
    slug = re.sub(r"_+", "_", slug).strip("_")
    # Limit length
    return slug[:40] or "nexus_app"


def get_project_workspace_path(project_name: str, project_id: str, custom_path: Optional[str] = None) -> Path:
    """Resolve a clean, readable workspace path."""
    if custom_path and custom_path.strip():
        p = Path(custom_path.strip())
        if not p.is_absolute():
            p = (Path("workspaces") / p).resolve()
        return p

    slug = slugify_name(project_name)
    # Append short 6-char id if needed to ensure uniqueness without clutter
    short_id = str(project_id).replace("-", "")[:6]
    clean_dir_name = f"{slug}_{short_id}"
    
    return (Path("workspaces") / clean_dir_name).resolve()
