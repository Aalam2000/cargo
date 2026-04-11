from __future__ import annotations

import os
from typing import Any, Dict, Optional, TypedDict

from autoi18n import Translator
from django.conf import settings
from django.db.models import Q
from langgraph.graph import END, START, StateGraph

from accounts.models import CustomUser
from chatgpt_ui.models import ChatMessage, ChatSession
from chatgpt_ui.services.ai.lang_detect import detect_language


class AdminBotState(TypedDict, total=False):
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


ALLOWED_BOT_ROLES = {"Admin", "Operator"}
NO_ACCESS_ROLES = {"WarehouseWorker", "Driver", "Client"}

TRANSLATOR = Translator(
    api_key=os.getenv("OPENAI_API_KEY"),
    cache_dir=os.path.join(settings.BASE_DIR, "translations"),
    source_lang="ru",
    target_langs=getattr(settings, "AUTO_I18N_TARGET_LANGS", []),
)

TRANSLATOR.register_keys(
    {
        "bot.no_access": "У вас нет доступа к функционалу бота. Я могу соединить вас с администратором.",
        "bot.anonymous_welcome": "Здравствуйте. Я могу помочь создать вашу компанию в системе. Напишите название компании и email главного администратора.",
        "bot.authorized_welcome_with_company": "Здравствуйте. Вы работаете в компании {company_name}. Могу помочь создать клиента, пользователя или подготовить отчет.",
        "bot.authorized_welcome_no_company": "Здравствуйте. Могу помочь создать клиента, пользователя или подготовить отчет.",
        "system.request_accepted": "Запрос принят.",
    },
    dict_name="bot",
)


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

    users = list(
        CustomUser.objects.filter(query).only("id", "role", "telegram")[:50]
    )

    normalized_map = {value.lower(): value for value in candidates}

    for candidate_lower, original_value in normalized_map.items():
        for user in users:
            user_telegram = _clean_text(user.telegram).lower()
            if user_telegram == candidate_lower:
                return user, original_value

    return None, ""


def _get_last_assistant_message(session: ChatSession) -> str:
    last_msg = (
        ChatMessage.objects.filter(session=session, role="assistant")
        .order_by("-created_at", "-id")
        .first()
    )
    return _clean_text(last_msg.content if last_msg else "")


def _resolve_actor_level(user_role: str) -> str:
    cleaned_role = _clean_text(user_role)

    if cleaned_role in ALLOWED_BOT_ROLES:
        return "authorized"

    if cleaned_role in NO_ACCESS_ROLES:
        return "no_access"

    return "no_access"


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

    matched_user, matched_by = _find_user_by_telegram(
        telegram_id=telegram_id,
        username=username,
    )

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


def node_anonymous(state: AdminBotState) -> AdminBotState:
    user_lang = _normalize_lang(state.get("user_lang"))
    return {
        "reply_text": _translate_bot_text(
            key="bot.anonymous_welcome",
            lang=user_lang,
            default="Здравствуйте. Я могу помочь создать вашу компанию в системе. Напишите название компании и email главного администратора.",
        ),
    }


def node_no_access(state: AdminBotState) -> AdminBotState:
    user_lang = _normalize_lang(state.get("user_lang"))
    return {
        "reply_text": _translate_bot_text(
            key="bot.no_access",
            lang=user_lang,
            default="У вас нет доступа к функционалу бота. Я могу соединить вас с администратором.",
        ),
    }


def node_authorized(state: AdminBotState) -> AdminBotState:
    session = ChatSession.objects.select_related("user", "user__company").get(id=state["session_id"])
    user_lang = _normalize_lang(state.get("user_lang"))

    company_name = ""
    placeholder_values = {
        "",
        "не указано",
        "не указан",
        "not specified",
        "none",
        "-",
    }

    if session.user:
        company_from_fk = _clean_text(getattr(getattr(session.user, "company", None), "name", ""))
        company_from_field = _clean_text(getattr(session.user, "company_name", ""))

        if company_from_fk and company_from_fk.lower() not in placeholder_values:
            company_name = company_from_fk
        elif company_from_field and company_from_field.lower() not in placeholder_values:
            company_name = company_from_field

    if company_name:
        return {
            "reply_text": _translate_bot_text(
                key="bot.authorized_welcome_with_company",
                lang=user_lang,
                default="Здравствуйте. Вы работаете в компании {company_name}. Могу помочь создать клиента, пользователя или подготовить отчет.",
                company_name=company_name,
            ),
        }

    return {
        "reply_text": _translate_bot_text(
            key="bot.authorized_welcome_no_company",
            lang=user_lang,
            default="Здравствуйте. Могу помочь создать клиента, пользователя или подготовить отчет.",
        ),
    }

def node_finalize(state: AdminBotState) -> AdminBotState:
    session = ChatSession.objects.get(id=state["session_id"])
    text = _clean_text(state.get("text"))
    reply_text = _clean_text(state.get("reply_text"))
    user_lang = _normalize_lang(state.get("user_lang"))
    context_json = state.get("context_json") or {}

    if hasattr(session, "user_lang"):
        session.user_lang = user_lang
    if hasattr(session, "context_json"):
        session.context_json = context_json

    update_fields = []
    if hasattr(session, "user_lang"):
        update_fields.append("user_lang")
    if hasattr(session, "context_json"):
        update_fields.append("context_json")
    if update_fields:
        session.save(update_fields=update_fields)

    last_assistant_text = _get_last_assistant_message(session)

    if text:
        ChatMessage.objects.create(
            session=session,
            role="user",
            content=text,
        )

    if reply_text and reply_text != last_assistant_text:
        ChatMessage.objects.create(
            session=session,
            role="assistant",
            content=reply_text,
        )

    return {}


def build_admin_bot_graph():
    graph = StateGraph(AdminBotState)

    graph.add_node("load_context", node_load_context)
    graph.add_node("identify_telegram_user", node_identify_telegram_user)
    graph.add_node("anonymous", node_anonymous)
    graph.add_node("no_access", node_no_access)
    graph.add_node("authorized", node_authorized)
    graph.add_node("finalize", node_finalize)

    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "identify_telegram_user")

    graph.add_conditional_edges(
        "identify_telegram_user",
        route_after_identify,
        {
            "anonymous": "anonymous",
            "no_access": "no_access",
            "authorized": "authorized",
        },
    )

    graph.add_edge("anonymous", "finalize")
    graph.add_edge("no_access", "finalize")
    graph.add_edge("authorized", "finalize")
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