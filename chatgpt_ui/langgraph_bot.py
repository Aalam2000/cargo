from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, TypedDict
from zoneinfo import ZoneInfo

from autoi18n import Translator
from bs4 import BeautifulSoup
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from langgraph.graph import END, START, StateGraph
from openai import OpenAI

from accounts.models import CustomUser
from accounts.services.client_actions import enqueue_create_client_action
from accounts.services.company_actions import enqueue_create_company_action
from chatgpt_ui.models import ChatMessage, ChatSession
from chatgpt_ui.services.ai.lang_detect import detect_language
from chatgpt_ui.services.ai.prompt_loader import load_prompt


class AdminBotState(TypedDict, total=False):
    ai_action_company_name: str
    telegram_id: str
    username: str
    first_name: str
    last_name: str
    text: str

    session_id: int
    user_id: Optional[int]
    user_role: str

    identified: bool
    actor_level: str
    reply_text: str
    stop: bool

    user_lang: str
    context_json: dict

    session_user_exists: bool
    customuser_lookup_performed: bool
    customuser_found: bool
    matched_by: str

    recent_messages: list[dict[str, str]]
    memory_facts: dict[str, Any]
    help_context: dict[str, Any]

    ai_intent: str
    ai_action: str
    ai_action_email: str
    ai_action_name: str
    memory_update: dict[str, Any]


ALLOWED_BOT_ROLES = {"Admin", "Operator"}
NO_ACCESS_ROLES = {"WarehouseWorker", "Driver", "Client"}

RECENT_MESSAGE_LIMIT = 12
MAX_HELP_TEXT_LEN = 12000
MAX_SUMMARIES = 30
OPENAI_MODEL = (os.getenv("OPENAI_MODEL") or "gpt-4.1-mini").strip()

TRANSLATOR = Translator(
    api_key=os.getenv("OPENAI_API_KEY"),
    cache_dir=os.path.join(settings.BASE_DIR, "translations"),
    source_lang="ru",
    target_langs=getattr(settings, "AUTO_I18N_TARGET_LANGS", []),
)

TRANSLATOR.register_keys(
    {
        "bot.ai_error": "Сейчас не смог нормально разобрать ваш запрос. Напишите чуть конкретнее.",
        "bot.fallback": "Я могу помочь по боту, по платформе и по базовым действиям в Cargo.",
        "bot.client_action_started": "Принял. Запускаю создание клиента.",
        "bot.create_user_not_connected": "Создание пользователя компании в этой ветке пока не подключено. Сейчас реально подключено только создание клиента.",
        "system.request_accepted": "Запрос принят.",
    },
    dict_name="bot",
)

HELP_CACHE: dict[str, dict[str, Any]] = {}


def _clean_text(value: str | None) -> str:
    return (value or "").strip()


def _normalize_lang(lang: str | None) -> str:
    return _clean_text(lang).lower() or "ru"


def _translate_bot_text(key: str, lang: str, default: str, **kwargs) -> str:
    text = TRANSLATOR.translate_key(
        key=key,
        lang=_normalize_lang(lang),
        default=default,
        dict_name="bot",
    )
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return default.format(**kwargs) if kwargs else default
    return text


def _normalize_text_for_compare(text: str | None) -> str:
    value = _clean_text(text).lower()
    for ch in ("!", "?", ".", ",", ";", ":", "-", "_", "(", ")", "[", "]", "{", "}", '"', "'"):
        value = value.replace(ch, " ")
    return " ".join(value.split())


def _tokenize(text: str | None) -> list[str]:
    normalized = _normalize_text_for_compare(text)
    if not normalized:
        return []
    return [item for item in normalized.split() if item]


def _contains_any(text: str, values: set[str]) -> bool:
    return any(value in text for value in values)


def _normalize_telegram_candidates(telegram_id: str, username: str) -> list[str]:
    result: list[str] = []

    cleaned_id = _clean_text(telegram_id)
    cleaned_username = _clean_text(username).lstrip("@")

    if cleaned_id:
        result.append(cleaned_id)

    if cleaned_username:
        result.append(cleaned_username)
        result.append(f"@{cleaned_username}")

    unique_result: list[str] = []
    seen: set[str] = set()

    for value in result:
        lowered = value.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique_result.append(value)

    return unique_result


def _find_user_by_telegram(telegram_id: str, username: str) -> tuple[Optional[CustomUser], str]:
    candidates = _normalize_telegram_candidates(telegram_id, username)
    if not candidates:
        return None, ""

    query = Q()
    for value in candidates:
        query |= Q(telegram__iexact=value)

    users = list(CustomUser.objects.filter(query).only("id", "role", "telegram")[:50])
    normalized_map = {value.lower(): value for value in candidates}

    for candidate_lower, original_value in normalized_map.items():
        for user in users:
            user_telegram = _clean_text(user.telegram).lower()
            if user_telegram == candidate_lower:
                return user, original_value

    return None, ""


def _resolve_actor_level(user_role: str) -> str:
    cleaned_role = _clean_text(user_role)

    if cleaned_role in ALLOWED_BOT_ROLES:
        return "authorized"

    if cleaned_role in NO_ACCESS_ROLES:
        return "no_access"

    return "no_access"


def _get_authorized_company_name(session: ChatSession) -> str:
    company_name = ""
    placeholder_values = {"", "не указано", "не указан", "not specified", "none", "-"}

    if session.user:
        company_from_fk = _clean_text(getattr(getattr(session.user, "company", None), "name", ""))
        company_from_field = _clean_text(getattr(session.user, "company_name", ""))

        if company_from_fk and company_from_fk.lower() not in placeholder_values:
            company_name = company_from_fk
        elif company_from_field and company_from_field.lower() not in placeholder_values:
            company_name = company_from_field

    return company_name


def _get_user_timezone_name(session: ChatSession) -> str:
    user_tz = _clean_text(getattr(getattr(session, "user", None), "timezone", ""))
    return user_tz or getattr(settings, "TIME_ZONE", "Asia/Baku") or "Asia/Baku"


def _get_local_now(session: ChatSession):
    tz_name = _get_user_timezone_name(session)
    try:
        tz_obj = ZoneInfo(tz_name)
    except Exception:
        tz_name = "Asia/Baku"
        tz_obj = ZoneInfo(tz_name)

    local_now = timezone.now().astimezone(tz_obj)
    return local_now, tz_name


def _get_recent_messages(session: ChatSession, limit: int = RECENT_MESSAGE_LIMIT) -> list[dict[str, str]]:
    messages = list(
        ChatMessage.objects.filter(session=session).order_by("-created_at", "-id")[:limit]
    )
    messages.reverse()

    result: list[dict[str, str]] = []
    for msg in messages:
        result.append(
            {
                "role": _clean_text(getattr(msg, "role", "")),
                "content": _clean_text(getattr(msg, "content", "")),
            }
        )
    return result


def _load_help_doc(help_name: str) -> dict[str, Any]:
    cached = HELP_CACHE.get(help_name)
    if cached is not None:
        return cached

    file_path = Path(settings.BASE_DIR) / "web" / "templates" / "chatgpt_ui" / help_name
    if not file_path.exists():
        data = {"text": "", "chunks": []}
        HELP_CACHE[help_name] = data
        return data

    try:
        raw_html = file_path.read_text(encoding="utf-8")
        soup = BeautifulSoup(raw_html, "html.parser")
    except Exception:
        data = {"text": "", "chunks": []}
        HELP_CACHE[help_name] = data
        return data

    text = " ".join(line.strip() for line in soup.get_text(" ").splitlines() if line.strip())
    text = text[:MAX_HELP_TEXT_LEN]

    chunks: list[str] = []
    for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        chunk_text = " ".join(tag.get_text(" ").split())
        if chunk_text:
            chunks.append(chunk_text)

    data = {"text": text, "chunks": chunks}
    HELP_CACHE[help_name] = data
    return data


def _expand_question_keywords(question: str) -> set[str]:
    normalized = _normalize_text_for_compare(question)
    tokens = set(_tokenize(normalized))

    if _contains_any(normalized, {"цена", "стоимость", "сколько стоит", "price", "pricing", "бесплатно"}):
        tokens.update({"цена", "стоимость", "сколько", "стоит", "бесплатно", "текущий", "функционал"})
    if _contains_any(normalized, {"бот", "telegram", "телеграм"}):
        tokens.update({"бот", "telegram", "телеграм", "инструкция"})
    if _contains_any(normalized, {"система", "платформа", "cargo"}):
        tokens.update({"система", "платформа", "cargo", "справочники", "грузы", "товары", "оплаты"})
    if _contains_any(normalized, {"возможности", "умеет", "полезно", "клиент", "пользователь"}):
        tokens.update({"возможности", "умеет", "помогает", "работа", "платформа", "бот", "клиент", "пользователь"})

    return tokens


def _score_help_chunk(chunk: str, keywords: set[str]) -> int:
    normalized_chunk = _normalize_text_for_compare(chunk)
    if not normalized_chunk:
        return 0

    score = 0
    for keyword in keywords:
        if keyword and keyword in normalized_chunk:
            score += 3

    if "бесплатно" in keywords and "бесплатно" in normalized_chunk:
        score += 10
    if "цена" in keywords and ("цена" in normalized_chunk or "стоимость" in normalized_chunk):
        score += 10

    return score


def _find_help_chunks(question: str, help_name: str, max_chunks: int = 5) -> list[str]:
    doc = _load_help_doc(help_name)
    chunks = list(doc.get("chunks") or [])
    if not chunks:
        return []

    keywords = _expand_question_keywords(question)
    scored: list[tuple[int, str]] = []

    for chunk in chunks:
        score = _score_help_chunk(chunk, keywords)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)

    result: list[str] = []
    seen: set[str] = set()
    for _, chunk in scored:
        if chunk in seen:
            continue
        seen.add(chunk)
        result.append(chunk)
        if len(result) >= max_chunks:
            break

    return result


def _build_help_fallback(question: str, help_names: list[str], fallback: str) -> str:
    selected_chunks: list[str] = []
    seen: set[str] = set()

    for help_name in help_names:
        for chunk in _find_help_chunks(question=question, help_name=help_name, max_chunks=3):
            if chunk in seen:
                continue
            seen.add(chunk)
            selected_chunks.append(chunk)
            if len(selected_chunks) >= 3:
                break
        if len(selected_chunks) >= 3:
            break

    if not selected_chunks:
        return fallback

    return " ".join(selected_chunks)


def _extract_json_object(raw_text: str) -> dict[str, Any]:
    cleaned = _clean_text(raw_text)
    if not cleaned:
        return {}

    fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.DOTALL)
    if fenced_match:
        cleaned = fenced_match.group(1).strip()

    try:
        value = json.loads(cleaned)
        return value if isinstance(value, dict) else {}
    except Exception:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = cleaned[start:end + 1]
        try:
            value = json.loads(snippet)
            return value if isinstance(value, dict) else {}
        except Exception:
            return {}

    return {}


def _get_openai_client() -> Optional[OpenAI]:
    api_key = _clean_text(os.getenv("OPENAI_API_KEY"))
    if not api_key:
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception:
        return None


def _call_openai_json(
    *,
    system_prompt: str,
    user_payload: dict[str, Any],
    model: str = OPENAI_MODEL,
) -> dict[str, Any]:
    client = _get_openai_client()
    if client is None:
        return {}

    try:
        completion = client.chat.completions.create(
            model=model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
        )
        content = completion.choices[0].message.content or ""
        return _extract_json_object(content)
    except Exception:
        return {}


def _merge_memory_facts(old_facts: dict[str, Any], new_facts: dict[str, Any]) -> dict[str, Any]:
    result = dict(old_facts or {})

    for key, value in (new_facts or {}).items():
        if value is None:
            continue

        if isinstance(value, str):
            cleaned = _clean_text(value)
            if cleaned:
                result[key] = cleaned
            continue

        if isinstance(value, list):
            existing = list(result.get(key) or [])
            for item in value:
                if item not in existing:
                    existing.append(item)
            result[key] = existing[:20]
            continue

        if isinstance(value, dict):
            existing_dict = dict(result.get(key) or {})
            existing_dict.update(value)
            result[key] = existing_dict
            continue

        result[key] = value

    return result


def _summarize_old_messages_with_ai(
    *,
    old_messages: list[dict[str, str]],
    existing_memory: dict[str, Any],
    user_lang: str,
) -> dict[str, Any]:
    if not old_messages:
        return {}

    payload = {
        "task": "Summarize old dialog messages for long-term memory.",
        "rules": {
            "keep_only_long_lived_information": True,
            "drop_noise_repeats_emotions_smalltalk": True,
            "languages_are_mixed_possible": True,
        },
        "existing_memory": existing_memory,
        "messages": old_messages,
        "user_lang": user_lang,
        "expected_json": {
            "facts": {
                "name": "",
                "business": "",
                "topics": [],
                "knowledge_level": "",
                "important_facts": [],
            },
            "summary": "",
        },
    }

    system_prompt = load_prompt("memory_summary.txt")
    return _call_openai_json(system_prompt=system_prompt, user_payload=payload)


def _compact_old_messages_with_memory(
    *,
    session: ChatSession,
    context_json: dict[str, Any],
    user_lang: str,
) -> dict[str, Any]:
    result = dict(context_json or {})
    memory_block = dict(result.get("memory") or {})
    memory_facts = dict(memory_block.get("facts") or {})
    summaries = list(memory_block.get("summaries") or [])

    local_now, tz_name = _get_local_now(session)
    local_today = local_now.date()

    all_messages = list(ChatMessage.objects.filter(session=session).order_by("created_at", "id"))

    old_messages_for_ai: list[dict[str, str]] = []
    message_ids_to_delete: list[int] = []

    tz_obj = ZoneInfo(tz_name)
    for msg in all_messages:
        try:
            msg_local_date = msg.created_at.astimezone(tz_obj).date()
        except Exception:
            msg_local_date = msg.created_at.date()

        if msg_local_date >= local_today:
            continue

        old_messages_for_ai.append(
            {
                "role": _clean_text(msg.role),
                "content": _clean_text(msg.content),
            }
        )
        message_ids_to_delete.append(msg.id)

    if not old_messages_for_ai:
        memory_block["facts"] = memory_facts
        memory_block["summaries"] = summaries[-MAX_SUMMARIES:]
        result["memory"] = memory_block
        return result

    ai_summary = _summarize_old_messages_with_ai(
        old_messages=old_messages_for_ai,
        existing_memory=memory_facts,
        user_lang=user_lang,
    )

    summary_facts = dict(ai_summary.get("facts") or {})
    summary_text = _clean_text(ai_summary.get("summary"))
    merged_facts = _merge_memory_facts(memory_facts, summary_facts)

    summaries.append(
        {
            "date": str(local_today),
            "timezone": tz_name,
            "message_count": len(old_messages_for_ai),
            "summary": summary_text,
        }
    )

    ChatMessage.objects.filter(id__in=message_ids_to_delete).delete()

    memory_block["facts"] = merged_facts
    memory_block["summaries"] = summaries[-MAX_SUMMARIES:]
    result["memory"] = memory_block
    result["last_memory_compaction_at"] = timezone.now().isoformat()

    return result


def _is_valid_email(value: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", _clean_text(value)))


def _analyze_branch_with_ai(
    *,
    branch_type: str,
    text: str,
    user_lang: str,
    recent_messages: list[dict[str, str]],
    last_bot_reply: str,
    memory_facts: dict[str, Any],
    context_json: dict[str, Any],
    bot_help_text: str,
    platform_help_text: str,
    company_name: str,
    greeted_today: bool,
    bot_help_chunks: list[str],
    platform_help_chunks: list[str],
    pricing_chunks: list[str],
) -> dict[str, Any]:
    payload = {
        "branch_type": branch_type,
        "user_lang": user_lang,
        "company_name": company_name,
        "greeted_today": greeted_today,
        "current_message": text,
        "recent_messages": recent_messages,
        "last_bot_reply": last_bot_reply,
        "memory_facts": memory_facts,
        "session_context": context_json,
        "knowledge": {
            "bot_help_full": bot_help_text,
            "platform_help_full": platform_help_text,
            "bot_help_relevant_chunks": bot_help_chunks,
            "platform_help_relevant_chunks": platform_help_chunks,
            "pricing_relevant_chunks": pricing_chunks,
        },
        "expected_json": {
            "intent": "clarify",
            "reply": "",
            "memory_update": {
                "name": "",
                "business": "",
                "topics": [],
                "knowledge_level": "",
                "important_facts": [],
            },
            "should_greet": False,
            "action": {
                "name": "none",
                "email": "",
                "person_name": "",
                "company_name": "",
            },
        },
    }

    prompt_map = {
        "authorized": "dialog_authorized.txt",
        "anonymous": "dialog_anonymous.txt",
        "no_access": "dialog_no_access.txt",
    }

    system_prompt = load_prompt(prompt_map[branch_type])
    return _call_openai_json(system_prompt=system_prompt, user_payload=payload)


def _get_last_assistant_message(session: ChatSession) -> str:
    last_msg = (
        ChatMessage.objects.filter(session=session, role="assistant")
        .order_by("-created_at", "-id")
        .first()
    )
    return _clean_text(last_msg.content if last_msg else "")


def node_load_context(state: AdminBotState) -> AdminBotState:
    telegram_id = _clean_text(state.get("telegram_id"))
    text = _clean_text(state.get("text"))

    session, _ = ChatSession.objects.get_or_create(telegram_id=telegram_id)

    saved_lang = _clean_text(getattr(session, "user_lang", "")) or "ru"
    detected_lang = detect_language(text, fallback=saved_lang)

    session_role = _clean_text(session.user.role if session.user else "")
    actor_level = _resolve_actor_level(session_role) if session.user_id else "anonymous"

    return {
        "session_id": session.id,
        "user_id": session.user_id,
        "user_role": session_role,
        "identified": bool(session.user_id),
        "actor_level": actor_level,
        "stop": False,
        "context_json": getattr(session, "context_json", {}) or {},
        "user_lang": detected_lang,
        "session_user_exists": bool(session.user_id),
        "customuser_lookup_performed": False,
        "customuser_found": bool(session.user_id),
        "matched_by": "session.user" if session.user_id else "",
    }


def node_identify_telegram_user(state: AdminBotState) -> AdminBotState:
    session = ChatSession.objects.select_related("user").get(id=state["session_id"])

    telegram_id = _clean_text(state.get("telegram_id"))
    username = _clean_text(state.get("username"))

    if session.user_id:
        user_role = _clean_text(session.user.role if session.user else "")
        return {
            "identified": True,
            "user_id": session.user_id,
            "user_role": user_role,
            "actor_level": _resolve_actor_level(user_role),
            "session_user_exists": True,
            "customuser_lookup_performed": False,
            "customuser_found": True,
            "matched_by": "session.user",
        }

    matched_user, matched_by = _find_user_by_telegram(telegram_id=telegram_id, username=username)

    if matched_user:
        session.user = matched_user
        session.save(update_fields=["user"])

        user_role = _clean_text(matched_user.role)
        return {
            "identified": True,
            "user_id": matched_user.id,
            "user_role": user_role,
            "actor_level": _resolve_actor_level(user_role),
            "session_user_exists": False,
            "customuser_lookup_performed": True,
            "customuser_found": True,
            "matched_by": matched_by,
        }

    return {
        "identified": False,
        "user_id": None,
        "user_role": "",
        "actor_level": "anonymous",
        "session_user_exists": False,
        "customuser_lookup_performed": True,
        "customuser_found": False,
        "matched_by": "",
    }


def route_after_identify(state: AdminBotState) -> str:
    actor_level = _clean_text(state.get("actor_level"))
    if actor_level == "authorized":
        return "authorized"
    if actor_level == "no_access":
        return "no_access"
    return "anonymous"


def _prepare_branch_common(state: AdminBotState) -> AdminBotState:
    session = ChatSession.objects.select_related("user", "user__company").get(id=state["session_id"])
    user_lang = _normalize_lang(state.get("user_lang"))

    context_json = _compact_old_messages_with_memory(
        session=session,
        context_json=dict(state.get("context_json") or {}),
        user_lang=user_lang,
    )
    recent_messages = _get_recent_messages(session=session, limit=RECENT_MESSAGE_LIMIT)
    memory_facts = dict((context_json.get("memory") or {}).get("facts") or {})

    bot_help_doc = _load_help_doc("bot_help.html")
    platform_help_doc = _load_help_doc("platform_help.html")
    text = _clean_text(state.get("text"))

    return {
        "context_json": context_json,
        "recent_messages": recent_messages,
        "memory_facts": memory_facts,
        "help_context": {
            "bot_help": _clean_text(bot_help_doc.get("text") or ""),
            "platform_help": _clean_text(platform_help_doc.get("text") or ""),
            "bot_help_chunks": _find_help_chunks(question=text, help_name="bot_help.html", max_chunks=5),
            "platform_help_chunks": _find_help_chunks(question=text, help_name="platform_help.html", max_chunks=5),
            "pricing_chunks": _find_help_chunks(
                question=f"{text} цена стоимость сколько стоит бесплатно текущий функционал",
                help_name="platform_help.html",
                max_chunks=5,
            ),
        },
    }


def node_anonymous_prepare(state: AdminBotState) -> AdminBotState:
    return _prepare_branch_common(state)


def node_no_access_prepare(state: AdminBotState) -> AdminBotState:
    return _prepare_branch_common(state)


def node_authorized_prepare(state: AdminBotState) -> AdminBotState:
    return _prepare_branch_common(state)


def _run_ai_for_branch(state: AdminBotState, branch_type: str) -> AdminBotState:
    session = ChatSession.objects.select_related("user", "user__company").get(id=state["session_id"])
    user_lang = _normalize_lang(state.get("user_lang"))
    text = _clean_text(state.get("text"))
    context_json = dict(state.get("context_json") or {})
    recent_messages = list(state.get("recent_messages") or [])
    memory_facts = dict(state.get("memory_facts") or {})
    help_context = dict(state.get("help_context") or {})

    local_now, _ = _get_local_now(session)
    greeted_today = _clean_text(context_json.get("last_greeting_date")) == str(local_now.date())
    last_bot_reply = _get_last_assistant_message(session)
    company_name = _get_authorized_company_name(session)

    ai_result = _analyze_branch_with_ai(
        branch_type=branch_type,
        text=text,
        user_lang=user_lang,
        recent_messages=recent_messages,
        last_bot_reply=last_bot_reply,
        memory_facts=memory_facts,
        context_json=context_json,
        bot_help_text=help_context.get("bot_help", ""),
        platform_help_text=help_context.get("platform_help", ""),
        company_name=company_name,
        greeted_today=greeted_today,
        bot_help_chunks=list(help_context.get("bot_help_chunks") or []),
        platform_help_chunks=list(help_context.get("platform_help_chunks") or []),
        pricing_chunks=list(help_context.get("pricing_chunks") or []),
    )

    reply_text = _clean_text(ai_result.get("reply"))
    memory_update = dict(ai_result.get("memory_update") or {})
    should_greet = bool(ai_result.get("should_greet"))
    intent = _clean_text(ai_result.get("intent")) or "clarify"

    action_data = dict(ai_result.get("action") or {})
    ai_action = _clean_text(action_data.get("name")) or "none"
    ai_action_email = _clean_text(action_data.get("email"))
    ai_action_name = _clean_text(action_data.get("person_name"))
    ai_action_company_name = _clean_text(action_data.get("company_name"))

    merged_memory = _merge_memory_facts(memory_facts, memory_update)
    context_json["memory"] = dict(context_json.get("memory") or {})
    context_json["memory"]["facts"] = merged_memory

    if should_greet and not greeted_today:
        context_json["last_greeting_date"] = str(local_now.date())

    if not reply_text:
        fallback = _translate_bot_text(
            key="bot.ai_error",
            lang=user_lang,
            default="Сейчас не смог нормально разобрать ваш запрос. Напишите чуть конкретнее.",
        )
        reply_text = _build_help_fallback(
            question=text,
            help_names=["bot_help.html", "platform_help.html"],
            fallback=fallback,
        )
        intent = "clarify"

    return {
        "ai_intent": intent,
        "reply_text": reply_text,
        "memory_update": memory_update,
        "memory_facts": merged_memory,
        "context_json": context_json,
        "ai_action": ai_action,
        "ai_action_email": ai_action_email,
        "ai_action_name": ai_action_name,
        "ai_action_company_name": ai_action_company_name,
        "stop": False,
    }

def node_anonymous_ai_analyze(state: AdminBotState) -> AdminBotState:
    return _run_ai_for_branch(state, "anonymous")


def node_no_access_ai_analyze(state: AdminBotState) -> AdminBotState:
    return _run_ai_for_branch(state, "no_access")


def node_authorized_ai_analyze(state: AdminBotState) -> AdminBotState:
    return _run_ai_for_branch(state, "authorized")


def route_after_ai(state: AdminBotState) -> str:
    return "reply"


def node_reply(state: AdminBotState) -> AdminBotState:
    session = ChatSession.objects.select_related("user").get(id=state["session_id"])
    user_lang = _normalize_lang(state.get("user_lang"))
    reply_text = _clean_text(state.get("reply_text"))
    ai_action = _clean_text(state.get("ai_action"))
    ai_action_email = _clean_text(state.get("ai_action_email"))
    ai_action_name = _clean_text(state.get("ai_action_name"))
    ai_action_company_name = _clean_text(state.get("ai_action_company_name"))

    if ai_action == "create_company":
        if _is_valid_email(ai_action_email) and ai_action_company_name:
            enqueue_create_company_action(
                telegram_id=_clean_text(state.get("telegram_id")),
                company_name=ai_action_company_name,
                admin_email=ai_action_email,
                admin_telegram=_clean_text(state.get("username")),
                admin_name=ai_action_name,
            )
            if not reply_text:
                reply_text = "Принял. Запускаю создание компании."
        else:
            if not reply_text:
                if not ai_action_company_name:
                    reply_text = "Для создания компании нужно название компании."
                else:
                    reply_text = "Для создания компании нужен корректный email."

    elif ai_action == "create_client" and session.user_id:
        if _is_valid_email(ai_action_email):
            enqueue_create_client_action(
                telegram_id=_clean_text(state.get("telegram_id")),
                operator_user_id=session.user_id,
                email=ai_action_email,
                name=ai_action_name,
                lang=user_lang,
            )
            if not reply_text:
                reply_text = _translate_bot_text(
                    key="bot.client_action_started",
                    lang=user_lang,
                    default="Принял. Запускаю создание клиента.",
                )
        else:
            if not reply_text:
                reply_text = "Для создания клиента нужен корректный email."

    elif ai_action == "create_user":
        if not reply_text:
            reply_text = _translate_bot_text(
                key="bot.create_user_not_connected",
                lang=user_lang,
                default="Создание пользователя компании в этой ветке пока не подключено. Сейчас реально подключено только создание клиента.",
            )

    if not reply_text:
        reply_text = _translate_bot_text(
            key="bot.fallback",
            lang=user_lang,
            default="Я могу помочь по боту, по платформе и по базовым действиям в Cargo.",
        )

    return {
        "reply_text": reply_text,
        "context_json": dict(state.get("context_json") or {}),
        "stop": False,
    }


def node_finalize(state: AdminBotState) -> AdminBotState:
    session = ChatSession.objects.get(id=state["session_id"])

    text = _clean_text(state.get("text"))
    reply_text = _clean_text(state.get("reply_text"))
    user_lang = _normalize_lang(state.get("user_lang"))
    context_json = state.get("context_json") or {}
    stop = bool(state.get("stop"))

    now = timezone.now()

    if hasattr(session, "user_lang"):
        session.user_lang = user_lang
    if hasattr(session, "context_json"):
        session.context_json = context_json

    last_user_msg = (
        ChatMessage.objects.filter(session=session, role="user").order_by("-created_at", "-id").first()
    )
    last_bot_msg = (
        ChatMessage.objects.filter(session=session, role="assistant").order_by("-created_at", "-id").first()
    )

    same_user_text = bool(last_user_msg and _clean_text(last_user_msg.content) == text)
    same_bot_reply = bool(last_bot_msg and _clean_text(last_bot_msg.content) == reply_text)

    if same_user_text and ((not reply_text) or same_bot_reply):
        update_fields = []
        if hasattr(session, "user_lang"):
            update_fields.append("user_lang")
        if hasattr(session, "context_json"):
            update_fields.append("context_json")
        if update_fields:
            session.save(update_fields=update_fields)
        return {}

    if text:
        ChatMessage.objects.create(session=session, role="user", content=text)
        if hasattr(session, "last_user_message_at"):
            session.last_user_message_at = now

    if reply_text and not stop:
        ChatMessage.objects.create(session=session, role="assistant", content=reply_text)
        if hasattr(session, "last_bot_message_at"):
            session.last_bot_message_at = now

    update_fields = []
    if hasattr(session, "user_lang"):
        update_fields.append("user_lang")
    if hasattr(session, "context_json"):
        update_fields.append("context_json")
    if hasattr(session, "last_user_message_at") and text:
        update_fields.append("last_user_message_at")
    if hasattr(session, "last_bot_message_at") and reply_text and not stop:
        update_fields.append("last_bot_message_at")

    if update_fields:
        session.save(update_fields=update_fields)

    return {}


def build_admin_bot_graph():
    graph = StateGraph(AdminBotState)

    graph.add_node("load_context", node_load_context)
    graph.add_node("identify_telegram_user", node_identify_telegram_user)

    graph.add_node("anonymous_prepare", node_anonymous_prepare)
    graph.add_node("anonymous_ai_analyze", node_anonymous_ai_analyze)

    graph.add_node("no_access_prepare", node_no_access_prepare)
    graph.add_node("no_access_ai_analyze", node_no_access_ai_analyze)

    graph.add_node("authorized_prepare", node_authorized_prepare)
    graph.add_node("authorized_ai_analyze", node_authorized_ai_analyze)

    graph.add_node("reply", node_reply)
    graph.add_node("finalize", node_finalize)

    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "identify_telegram_user")

    graph.add_conditional_edges(
        "identify_telegram_user",
        route_after_identify,
        {
            "anonymous": "anonymous_prepare",
            "no_access": "no_access_prepare",
            "authorized": "authorized_prepare",
        },
    )

    graph.add_edge("anonymous_prepare", "anonymous_ai_analyze")
    graph.add_edge("no_access_prepare", "no_access_ai_analyze")
    graph.add_edge("authorized_prepare", "authorized_ai_analyze")

    graph.add_conditional_edges(
        "anonymous_ai_analyze",
        route_after_ai,
        {"reply": "reply"},
    )
    graph.add_conditional_edges(
        "no_access_ai_analyze",
        route_after_ai,
        {"reply": "reply"},
    )
    graph.add_conditional_edges(
        "authorized_ai_analyze",
        route_after_ai,
        {"reply": "reply"},
    )

    graph.add_edge("reply", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()


ADMIN_BOT_GRAPH = build_admin_bot_graph()


def run_admin_bot_graph(
    *,
    telegram_id: str,
    username: str = "",
    first_name: str = "",
    last_name: str = "",
    text: str = "",
) -> Dict[str, Any]:
    initial_state: AdminBotState = {
        "telegram_id": str(telegram_id),
        "username": username or "",
        "first_name": first_name or "",
        "last_name": last_name or "",
        "text": text or "",
    }
    result = ADMIN_BOT_GRAPH.invoke(initial_state)
    return dict(result)