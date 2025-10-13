import logging
from typing import Dict, List

from openai import APIError, OpenAI, OpenAIError

from character_settings import get_character
from config import Config

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    # สร้างไคลเอนต์เพียงครั้งเดียวและตรวจสอบคีย์ก่อนเรียกใช้งาน
    global _client
    if _client is None:
        if not Config.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        _client = OpenAI(api_key=Config.OPENAI_API_KEY)
    return _client


def _normalise_history(history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    # เก็บเฉพาะบทสนทนาที่จำเป็น (user/assistant) เพื่อป้องกัน prompt leakage
    cleaned: List[Dict[str, str]] = []
    for item in history[-10:]:
        role = item.get("role")
        text = (item.get("content") or item.get("text") or "").strip()
        if role in {"user", "assistant"} and text:
            cleaned.append({"role": role, "content": text})
    return cleaned


def chat_complete(character_key: str, history: List[Dict[str, str]], user_message: str) -> str:
    """เรียก OpenAI เพื่อให้ตอบกลับโดยยึด persona ของตัวละครที่เลือก"""
    character = get_character(character_key)
    if not character:
        raise ValueError(f"Unknown character key: {character_key}")

    client = _get_client()

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": character["system"]},
        *_normalise_history(history),
        {"role": "user", "content": user_message},
    ]

    model = character.get("model") or "gpt-4o-mini"
    temperature = character.get("temperature", 0.7)
    max_tokens = character.get("max_tokens")

    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "timeout": 30,
    }
    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    try:
        response = client.chat.completions.create(**kwargs)
    except APIError as exc:
        status = getattr(exc, "status_code", getattr(exc, "http_status", "unknown"))
        detail = str(exc)[:400]
        logger.warning("OpenAI API error status=%s detail=%s", status, detail)
        raise RuntimeError(f"OpenAI call failed: {status}") from exc
    except OpenAIError as exc:
        logger.warning("OpenAI client error: %s", str(exc)[:400])
        raise RuntimeError("OpenAI call failed") from exc
    except Exception as exc:
        logger.warning("OpenAI request exception: %s", str(exc)[:400])
        raise RuntimeError("OpenAI call failed") from exc

    content = response.choices[0].message.content
    if isinstance(content, list):
        content = "".join(part.get("text", "") for part in content)
    return (content or "").strip()
