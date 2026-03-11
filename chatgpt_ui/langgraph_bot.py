# chatgpt_ui/langgraph_bot.py
from __future__ import annotations

from typing import Any, Dict, Optional, TypedDict

from django.db.models import Q

from accounts.models import CustomUser
from chatgpt_ui.models import ChatMessage, ChatSession
from langgraph.graph import END, START, StateGraph


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
    debug_note: str


def _build_unidentified_reply(state: AdminBotState) -> str:
    username = (state.get("username") or "").strip()
    telegram_id = (state.get("telegram_id") or "").strip()
    first_name = (state.get("first_name") or "").strip()
    last_name = (state.get("last_name") or "").strip()

    show_username = f"@{username}" if username else "нет"

    return (
        "Добро пожаловать в CargoAdmin Bot!\n\n"
        "Ваш Telegram ещё не привязан к системе.\n"
        "Откройте CargoAdmin и заполните поле «Telegram» в карточке пользователя.\n\n"
        "Укажите одно из значений:\n"
        f"• {show_username}\n"
        f"• {telegram_id}\n\n"
        "Ссылка на платформу:\nhttps://crm.bona-plus.ru\n\n"
        "Ваши данные:\n"
        f"ID: {telegram_id}\n"
        f"Username: {show_username}\n"
        f"Имя: {first_name or 'нет'}\n"
        f"Фамилия: {last_name or 'нет'}"
    )


def _build_identified_reply(state: AdminBotState) -> str:
    first_name = (state.get("first_name") or "").strip()
    username = (state.get("username") or "").strip()
    role = (state.get("user_role") or "").strip()

    name_block = first_name or (f"@{username}" if username else "коллега")

    return (
        f"Принято, {name_block}.\n"
        f"Роль в системе: {role}.\n\n"
        "Доступные направления:\n"
        "1. Создание компании\n"
        "2. Создание пользователя компании\n"
        "3. Создание клиента\n"
        "4. Инструкции и консультации\n\n"
        "Пока активен базовый режим распознавания.\n"
        "Следующие сценарии будут поэтапно перенесены в LangGraph."
    )


def node_load_context(state: AdminBotState) -> AdminBotState:
    telegram_id = state["telegram_id"]
    session, _ = ChatSession.objects.get_or_create(telegram_id=telegram_id)

    return {
        "session_id": session.id,
        "user_id": session.user_id,
        "identified": bool(session.user_id),
        "stop": False,
    }


def node_detect_actor(state: AdminBotState) -> AdminBotState:
    telegram_id = state["telegram_id"]
    username = (state.get("username") or "").strip()

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

    user_role = (state.get("user_role") or "").strip()

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
    return {
        "request_level": "menu",
        "info_level": "base_menu",
        "reply_text": _build_identified_reply(state),
        "stop": True,
    }


def node_action_router_stub(state: AdminBotState) -> AdminBotState:
    text = (state.get("text") or "").strip().lower()

    if "компан" in text or "фирм" in text or "организац" in text:
        return {
            "pending_action": "create_company",
            "reply_text": "Режим создания компании пока подключён как заглушка.",
            "stop": True,
        }

    if "пользоват" in text or "юзер" in text or "сотрудник" in text:
        return {
            "pending_action": "create_company_user",
            "reply_text": "Режим создания пользователя компании пока подключён как заглушка.",
            "stop": True,
        }

    if "клиент" in text:
        return {
            "pending_action": "create_client",
            "reply_text": "Режим создания клиента будет переведён в LangGraph следующим шагом.",
            "stop": True,
        }

    return {
        "pending_action": "",
        "reply_text": _build_identified_reply(state),
        "stop": True,
    }


def node_info_router_stub(state: AdminBotState) -> AdminBotState:
    return {
        "info_level": "stub",
        "reply_text": "Блок инструкций и консультаций пока подключён как заглушка.",
        "stop": True,
    }


def node_finalize(state: AdminBotState) -> AdminBotState:
    session = ChatSession.objects.get(id=state["session_id"])
    text = (state.get("text") or "").strip()
    reply_text = (state.get("reply_text") or "").strip()

    if text:
        ChatMessage.objects.create(
            session=session,
            role="user",
            content=text,
        )

    if reply_text:
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
    text = (state.get("text") or "").strip().lower()

    if any(word in text for word in ("создать", "добавить", "нов", "компан", "фирм", "организац", "пользоват", "юзер", "сотрудник", "клиент")):
        return "action_router_stub"

    if any(word in text for word in ("как", "что", "инструкц", "помощ", "обуч", "консультац", "cargo", "диалог")):
        return "info_router_stub"

    return "action_router_stub"


def build_admin_bot_graph():
    graph = StateGraph(AdminBotState)

    graph.add_node("load_context", node_load_context)
    graph.add_node("detect_actor", node_detect_actor)
    graph.add_node("security_guard", node_security_guard)
    graph.add_node("route_unidentified", node_route_unidentified)
    graph.add_node("route_identified", node_route_identified)
    graph.add_node("action_router_stub", node_action_router_stub)
    graph.add_node("info_router_stub", node_info_router_stub)
    graph.add_node("finalize", node_finalize)

    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "detect_actor")

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
            "action_router_stub": "action_router_stub",
            "info_router_stub": "info_router_stub",
        },
    )

    graph.add_edge("route_unidentified", "finalize")
    graph.add_edge("action_router_stub", "finalize")
    graph.add_edge("info_router_stub", "finalize")
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