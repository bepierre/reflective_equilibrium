from __future__ import annotations

import json
import os
from typing import Type, TypeVar

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ValidationError

load_dotenv()

DEFAULT_MODEL = os.getenv("RE_MODEL", "deepseek/deepseek-chat")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY not set. Copy .env.example to .env and add your key."
            )
        _client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)
    return _client


T = TypeVar("T", bound=BaseModel)


def chat(
    system: str,
    user: str,
    response_model: Type[T] | None = None,
    model: str | None = None,
    temperature: float = 0.4,
) -> T | str:
    """Call the LLM through OpenRouter.

    If response_model is provided, the LLM is asked to return JSON matching that schema.
    One retry on parse failure.
    """
    model = model or DEFAULT_MODEL
    client = _get_client()

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    if response_model is None:
        resp = client.chat.completions.create(
            model=model, messages=messages, temperature=temperature
        )
        return resp.choices[0].message.content or ""

    schema_str = json.dumps(response_model.model_json_schema(), indent=2)
    structured_system = (
        system
        + "\n\nYou MUST reply with a single JSON object matching this schema. "
        "No prose, no markdown fences, just the JSON.\n\n"
        f"Schema:\n{schema_str}"
    )
    messages[0]["content"] = structured_system

    last_err: Exception | None = None
    for attempt in range(2):
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or ""
        try:
            return response_model.model_validate_json(_strip_fences(raw))
        except (ValidationError, json.JSONDecodeError) as e:
            last_err = e
            messages.append({"role": "assistant", "content": raw})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"Your previous reply could not be parsed: {e}. "
                        "Reply again with valid JSON matching the schema. No prose."
                    ),
                }
            )
    raise RuntimeError(f"LLM failed to produce valid JSON after retry: {last_err}")


def _strip_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s[3:]
        if s.endswith("```"):
            s = s[: -3]
    return s.strip()
