# chatgpt_ui/langgraph_bot.py
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional, TypedDict

from django.db.models import Q
from langgraph.graph import END, START, StateGraph
from openai import OpenAI

from accounts.models import CustomUser
from accounts.services.company_actions import enqueue_create_company_action
from chatgpt_ui.models import ChatMessage, ChatSession
from chatgpt_ui.services.ai.lang_detect import detect_language
from chatgpt_ui.services.ai.prompt_loader import load_intent_prompt
from chatgpt_ui.services.knowledge.loader import load_help_pages


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
    request_level: str
    info_level: str
    safety_level: str

    reply_text: str
    stop: bool

    onboarding_mode: str
    pending_action: str
    dialog_mode: str
    debug_note: str

    ai_intent: str
    ai_params: dict


def _clean_text(value: str | None) -> str:
    return (value or "").strip()


def _normalize_text(value: str | None) -> str:
    return _clean_text(value).lower()


def _build_unidentified_reply(state: AdminBotState) -> str:
    username = _clean_text(state.get("username"))
    telegram_id = _clean_text(state.get("telegram_id"))
    first_name = _clean_text(state.get("first_name"))
    last_name = _clean_text(state.get("last_name"))

    show_username = f"@{username}" if username else "нет"

    return (
        "Ваш Telegram ещё не привязан к системе.\n"
        "Откройте CargoAdmin и заполните поле Telegram в карточке пользователя.\n\n"
        f"ID: {telegram_id}\n"
        f"Username: {show_username}\n"
        f"Имя: {first_name or 'нет'}\n"
        f"Фамилия: {last_name or 'нет'}"
    )


def _build_identified_reply(state: AdminBotState) -> str:
    first_name = _clean_text(state.get("first_name"))
    username = _clean_text(state.get("username"))
    role = _clean_text(state.get("user_role"))

    name_block = first_name or (f"@{username}" if username else "коллега")

    return (
        f"Принято, {name_block}.\n"
        f"Роль: {role}.\n\n"
        "Доступно:\n"
        "1. Создание компании\n"
        "2. Создание пользователя компании\n"
        "3. Создание клиента\n"
        "4. Инструкции"
    )


def _build_instruction_reply() -> str:
    return (
        "Инструкция:\n"
        "1. Для создания компании напиши название и email главного админа.\n"
        "2. Можно сразу добавить Telegram админа.\n\n"
        "Пример:\n"
        'Создать компанию "Ромашка", admin email: boss@example.com, telegram: @boss'
    )


def _is_smalltalk(text: str) -> bool:
    lowered = _normalize_text(text)
    return any(
        phrase in lowered
        for phrase in (
            "привет",
            "здрав",
            "даров",
            "дароф",
            "салам",
            "чего молчишь",
            "давай поговорим",
            "поговорим",
        )
    )


def _is_help_request(text: str) -> bool:
    lowered = _normalize_text(text)
    return any(
        phrase in lowered
        for phrase in (
            "что умеешь",
            "помощь",
            "help",
            "инструкц",
            "дай инструкц",
            "инструкция",
            "что ты умеешь",
            "меню",
        )
    )


def _is_complaint(text: str) -> bool:
    lowered = _normalize_text(text)
    return any(
        phrase in lowered
        for phrase in (
            "не сделал",
            "ни хера не сделал",
            "ничего не сделал",
            "ты сделал",
            "что сделал",
        )
    )


def _extract_email(text: str) -> str:
    match = re.search(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", text or "")
    return (match.group(1) if match else "").strip().lower()


def _extract_telegram(text: str) -> str:
    raw = text or ""
    matches = re.findall(r"(?<![A-Za-z0-9._%+-])(@[A-Za-z0-9_]{4,})\b", raw)
    if not matches:
        return ""

    for value in matches:
        if value.lower() not in ("@gmail", "@mail", "@yahoo", "@outlook", "@hotmail", "@icloud"):
            return value.strip()

    return ""


def _extract_company_name(text: str) -> str:
    raw = _clean_text(text)

    quoted = re.search(r'["«“](.+?)["»”]', raw)
    if quoted:
        value = quoted.group(1).strip(" .,:;\"'«»")
        if value:
            return value

    patterns = [
        r"(?:компан(?:ию|ия|ии|ией)|фирм(?:у|а|ы|е)|организац(?:ию|ия|ии))\s+([A-Za-zА-Яа-я0-9 _.\-]+?)(?:,|;|\n|$)",
        r"(?:название|company)\s*[:\-]\s*(.+?)(?:,|;|\n|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, raw, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip(" .,:;\"'«»")
            if value:
                return value

    return ""


def _parse_create_company_request(text: str) -> dict:
    raw = _clean_text(text)
    lowered = raw.lower()

    company_words = ("создай", "создать", "добавь", "добавить", "зарегистрируй", "регистрация", "сделай")
    entity_words = ("компан", "фирм", "организац")

    wants_create = any(word in lowered for word in company_words) and any(word in lowered for word in entity_words)

    company_name = _extract_company_name(raw)
    admin_email = _extract_email(raw)
    admin_telegram = _extract_telegram(raw)

    return {
        "intent": "create_company" if wants_create else "",
        "company_name": company_name,
        "admin_email": admin_email,
        "admin_telegram": admin_telegram,
        "missing_fields": [
            field
            for field, value in (
                ("company_name", company_name),
                ("admin_email", admin_email),
            )
            if not value
        ],
    }


def _parse_company_data_from_followup(text: str) -> dict:
    raw = _clean_text(text)
    company_name = _extract_company_name(raw)
    admin_email = _extract_email(raw)
    admin_telegram = _extract_telegram(raw)

    return {
        "company_name": company_name,
        "admin_email": admin_email,
        "admin_telegram": admin_telegram,
        "missing_fields": [
            field
            for field, value in (
                ("company_name", company_name),
                ("admin_email", admin_email),
            )
            if not value
        ],
    }


def _get_last_assistant_message(session: ChatSession) -> str:
    last_msg = (
        ChatMessage.objects.filter(session=session, role="assistant")
        .order_by("-created_at", "-id")
        .first()
    )
    return _clean_text(last_msg.content if last_msg else "")


def _get_recent_dialog_history_by_telegram(telegram_id: str, limit: int = 20) -> str:
    session = ChatSession.objects.filter(telegram_id=str(telegram_id)).first()
    if not session:
        return ""

    messages = list(
        ChatMessage.objects.filter(session=session)
        .order_by("-created_at", "-id")[:limit]
    )
    messages.reverse()

    parts = []
    for msg in messages:
        role = (msg.role or "").strip().lower()
        content = _clean_text(msg.content)
        if not content:
            continue

        if role == "user":
            parts.append(f"USER: {content}")
        elif role == "assistant":
            parts.append(f"ASSISTANT: {content}")
        elif role == "system":
            parts.append(f"SYSTEM: {content}")

    return "\n".join(parts)


def node_ai(state: AdminBotState) -> AdminBotState:
    import json
    import os
    from openai import OpenAI

    def _strip_html(text: str) -> str:
        cleaned = re.sub(r"<[^>]+>", " ", text or "")
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

    text = _clean_text(state.get("text"))
    telegram_id = str(state.get("telegram_id") or "").strip()
    prompt = load_intent_prompt()
    pages = load_help_pages()

    bot_help = _strip_html(pages.get("bot_help") or "")
    platform_help = _strip_html(pages.get("platform_help") or "")
    history_text = _get_recent_dialog_history_by_telegram(telegram_id, limit=20)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "ai_intent": "clarify",
            "ai_params": {},
            "reply_text": "Ошибка конфигурации AI.",
            "user_lang": state.get("user_lang") or "en",
        }

    client = OpenAI(api_key=api_key)

    user_payload = (
        "BOT_HELP_PAGE:\n"
        f"{bot_help}\n\n"
        "PLATFORM_HELP_PAGE:\n"
        f"{platform_help}\n\n"
        "DIALOG_HISTORY_LAST_20:\n"
        f"{history_text}\n\n"
        "CURRENT_USER_MESSAGE:\n"
        f"{text}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_payload},
            ],
            temperature=0,
        )
        raw = (response.choices[0].message.content or "").strip()

        if raw.startswith("```"):
            raw = re.sub(r"^```[a-zA-Z]*", "", raw)
            raw = raw.rstrip("```").strip()

        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            raw = match.group(0)

        try:
            data = json.loads(raw)
        except Exception:
            data = {
                "intent": "clarify",
                "params": {},
                "reply": "Уточни, пожалуйста, что именно ты хочешь сделать или понять.",
                "lang": state.get("user_lang") or "en",
            }

        return {
            "ai_intent": data.get("intent") or "clarify",
            "ai_params": data.get("params") or {},
            "reply_text": data.get("reply") or "",
            "user_lang": data.get("lang") or state.get("user_lang") or "en",
        }

    except Exception:
        return {
            "ai_intent": "clarify",
            "ai_params": {},
            "reply_text": "Сбой AI. Повтори, пожалуйста, короче.",
            "user_lang": state.get("user_lang") or "en",
        }


def node_load_context(state: AdminBotState) -> AdminBotState:
    telegram_id = state["telegram_id"]
    text = _clean_text(state.get("text"))

    session, _ = ChatSession.objects.get_or_create(telegram_id=telegram_id)

    saved_lang = _clean_text(getattr(session, "user_lang", "")) or "en"
    detected_lang = detect_language(text, fallback=saved_lang)

    return {
        "session_id": session.id,
        "user_id": session.user_id,
        "identified": bool(session.user_id),
        "stop": False,
        "pending_action": _clean_text(getattr(session, "pending_action", "")),
        "dialog_mode": _clean_text(getattr(session, "dialog_mode", "")) or "idle",
        "context_json": getattr(session, "context_json", {}) or {},
        "user_lang": detected_lang,
    }


def node_detect_actor(state: AdminBotState) -> AdminBotState:
    telegram_id = state["telegram_id"]
    username = _clean_text(state.get("username"))

    session = ChatSession.objects.select_related("user").get(id=state["session_id"])
    matched_user = session.user

    if matched_user is None:
        candidates = Q()

        if username:
            candidates |= (
                    Q(telegram__iexact=username)
                    | Q(telegram__iexact=f"@{username}")
                    | Q(telegram__iexact=username.lower())
                    | Q(telegram__iexact=f"@{username.lower()}")
            )

        candidates |= Q(telegram__iexact=str(telegram_id).strip())
        matched_user = CustomUser.objects.filter(candidates).first()

        if matched_user:
            session.user = matched_user
            session.save(update_fields=["user"])

    if matched_user is None:
        return {
            "identified": False,
            "actor_level": "unidentified",
            "user_id": None,
            "user_role": "",
        }

    return {
        "identified": True,
        "actor_level": "identified",
        "user_id": matched_user.id,
        "user_role": matched_user.role or "",
    }


def node_security_guard(state: AdminBotState) -> AdminBotState:
    if not state.get("identified"):
        return {
            "safety_level": "allow_unidentified",
        }

    user_role = _clean_text(state.get("user_role"))

    if user_role not in ("Admin", "Operator"):
        return {
            "safety_level": "forbidden_role",
            "reply_text": "У вас нет прав для работы с административным чат-ботом.",
            "stop": True,
        }

    return {
        "safety_level": "allow_admin",
    }


def node_route_unidentified(state: AdminBotState) -> AdminBotState:
    return {
        "request_level": "unknown",
        "info_level": "link_account",
        "reply_text": _build_unidentified_reply(state),
        "stop": True,
    }


def node_route_identified(state: AdminBotState) -> AdminBotState:
    ai_intent = _clean_text(state.get("ai_intent"))
    reply_text = _clean_text(state.get("reply_text"))

    if ai_intent in ("explain_system", "explain_bot", "clarify", "make_report"):
        return {
            "request_level": ai_intent or "ai_reply",
            "reply_text": reply_text,
            "stop": True,
        }

    return {
        "request_level": ai_intent or "route_main",
        "stop": False,
    }


def node_action_router_stub(state: AdminBotState) -> AdminBotState:
    ai_intent = _clean_text(state.get("ai_intent"))
    reply_text = _clean_text(state.get("reply_text"))

    if ai_intent == "create_user":
        return {
            "pending_action": "create_company_user",
            "reply_text": reply_text or "Создание пользователя компании пока настраивается.",
            "stop": True,
        }

    if ai_intent == "create_client":
        return {
            "pending_action": "create_client",
            "reply_text": reply_text or "Создание клиента пока настраивается.",
            "stop": True,
        }

    return {
        "pending_action": "",
        "reply_text": reply_text or "Уточни, что нужно сделать.",
        "stop": True,
    }


def node_info_router_stub(state: AdminBotState) -> AdminBotState:
    text = _clean_text(state.get("text")).lower()
    pages = load_help_pages()

    if any(word in text for word in ("бот", "bot")):
        return {
            "info_level": "bot_help",
            "reply_text": "Инструкция по боту:\nhttps://crm.bona-plus.ru/bot/bot-help/",
            "stop": True,
        }

    if any(word in text for word in ("платформ", "система", "cargo")):
        return {
            "info_level": "platform_help",
            "reply_text": "Инструкция по платформе:\nhttps://crm.bona-plus.ru/bot/platform-help/",
            "stop": True,
        }

    return {
        "info_level": "general_help",
        "reply_text": (
            "Инструкции:\n"
            "Бот: https://crm.bona-plus.ru/bot/bot-help/\n"
            "Платформа: https://crm.bona-plus.ru/bot/platform-help/"
        ),
        "stop": True,
    }


def node_execute_company_action(state: AdminBotState) -> AdminBotState:
    session = ChatSession.objects.select_related("user").get(id=state["session_id"])
    operator_user = session.user
    text = _clean_text(state.get("text"))
    dialog_mode = _clean_text(state.get("dialog_mode"))

    if not operator_user:
        return {
            "reply_text": "❗ Оператор не определён.",
            "stop": True,
        }

    if dialog_mode == "await_company_data":
        parsed = _parse_company_data_from_followup(text)
    else:
        parsed = _parse_create_company_request(text)

    missing_fields = parsed.get("missing_fields") or []
    if missing_fields:
        hints = []
        if "company_name" in missing_fields:
            hints.append("название компании")
        if "admin_email" in missing_fields:
            hints.append("email главного админа")

        return {
            "pending_action": "create_company",
            "dialog_mode": "await_company_data",
            "reply_text": (
                "Для создания компании не хватает данных.\n"
                f"Нужно прислать: {', '.join(hints)}.\n\n"
                "Пример:\n"
                'Создать компанию "Ромашка", admin email: boss@example.com, telegram: @boss'
            ),
            "stop": True,
        }

    enqueue_create_company_action(
        telegram_id=state["telegram_id"],
        operator_user_id=operator_user.id,
        company_name=parsed["company_name"],
        admin_email=parsed["admin_email"],
        admin_telegram=parsed["admin_telegram"],
        admin_name="",
    )

    return {
        "pending_action": "",
        "dialog_mode": "idle",
        "reply_text": (
            "Команда принята.\n"
            f"Создаю компанию: {parsed['company_name']}\n"
            f"Главный админ: {parsed['admin_email']}\n"
            f"Telegram: {parsed['admin_telegram'] or '—'}"
        ),
        "stop": True,
    }


def node_finalize(state: AdminBotState) -> AdminBotState:
    session = ChatSession.objects.get(id=state["session_id"])
    text = _clean_text(state.get("text"))
    reply_text = _clean_text(state.get("reply_text"))
    pending_action = _clean_text(state.get("pending_action"))
    dialog_mode = _clean_text(state.get("dialog_mode")) or "idle"
    user_lang = _clean_text(state.get("user_lang")) or "ru"
    context_json = state.get("context_json") or {}

    if hasattr(session, "pending_action"):
        session.pending_action = pending_action
    if hasattr(session, "dialog_mode"):
        session.dialog_mode = dialog_mode
    if hasattr(session, "user_lang"):
        session.user_lang = user_lang
    if hasattr(session, "context_json"):
        session.context_json = context_json

    update_fields = []
    if hasattr(session, "pending_action"):
        update_fields.append("pending_action")
    if hasattr(session, "dialog_mode"):
        update_fields.append("dialog_mode")
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


def route_after_detect_actor(state: AdminBotState) -> str:
    if state.get("identified"):
        return "security_guard"
    return "route_unidentified"


def route_after_security(state: AdminBotState) -> str:
    if state.get("stop"):
        return "finalize"
    return "route_identified"


def route_after_identified(state: AdminBotState) -> str:
    intent = state.get("ai_intent")

    if intent == "create_company":
        return "execute_company_action"

    if intent == "create_client":
        return "action_router_stub"

    if intent == "create_user":
        return "action_router_stub"

    if intent in ("explain_system", "explain_bot", "clarify"):
        return "finalize"

    return "finalize"


def build_admin_bot_graph():
    graph = StateGraph(AdminBotState)

    graph.add_node("load_context", node_load_context)
    graph.add_node("detect_actor", node_detect_actor)
    graph.add_node("security_guard", node_security_guard)
    graph.add_node("route_unidentified", node_route_unidentified)
    graph.add_node("route_identified", node_route_identified)
    graph.add_node("action_router_stub", node_action_router_stub)
    graph.add_node("info_router_stub", node_info_router_stub)
    graph.add_node("execute_company_action", node_execute_company_action)
    graph.add_node("finalize", node_finalize)
    graph.add_node("node_ai", node_ai)
    graph.add_edge("load_context", "detect_actor")

    graph.add_edge(START, "node_ai")
    graph.add_edge("node_ai", "load_context")

    graph.add_conditional_edges(
        "detect_actor",
        route_after_detect_actor,
        {
            "security_guard": "security_guard",
            "route_unidentified": "route_unidentified",
        },
    )

    graph.add_conditional_edges(
        "security_guard",
        route_after_security,
        {
            "route_identified": "route_identified",
            "finalize": "finalize",
        },
    )

    graph.add_conditional_edges(
        "route_identified",
        route_after_identified,
        {
            "execute_company_action": "execute_company_action",
            "action_router_stub": "action_router_stub",
            "info_router_stub": "info_router_stub",
            "finalize": "finalize",
        },
    )

    graph.add_edge("route_unidentified", "finalize")
    graph.add_edge("action_router_stub", "finalize")
    graph.add_edge("info_router_stub", "finalize")
    graph.add_edge("execute_company_action", "finalize")
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
