"""Optional OpenAI-backed assistant provider (used when configured)."""
from __future__ import annotations

from ..config import settings

if settings.assistant_provider == "openai" and settings.openai_api_key:
    from openai import OpenAI as _OpenAI

    _client: _OpenAI | None = _OpenAI(api_key=settings.openai_api_key)
else:
    _client = None


def llm_available() -> bool:
    return _client is not None


def ask(system: str, user: str, max_tokens: int = 700) -> str:
    if _client is None:
        raise RuntimeError("OpenAI not configured (set OPENAI_API_KEY + ASSISTANT_PROVIDER=openai)")
    resp = _client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()