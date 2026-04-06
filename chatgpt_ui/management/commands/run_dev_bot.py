import os
import time

import requests
from django.core.management.base import BaseCommand

from chatgpt_ui.langgraph_bot import run_admin_bot_graph

BOT_TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()


class Command(BaseCommand):
    help = "Run DEV Telegram bot (polling)"

    def handle(self, *args, **options):
        if not BOT_TOKEN:
            print("ERROR: TELEGRAM_BOT_TOKEN is missing!")
            return

        api_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
        offset = None

        print("DEV BOT STARTED")

        while True:
            try:
                resp = requests.get(
                    f"{api_url}/getUpdates",
                    params={"timeout": 30, "offset": offset},
                    timeout=35,
                ).json()

                print("RAW:", resp)

                for update in resp.get("result", []):
                    offset = update["update_id"] + 1

                    message = update.get("message")
                    if not message:
                        continue

                    chat = message.get("chat", {}) or {}
                    from_user = message.get("from", {}) or {}

                    chat_id = chat.get("id")
                    text = (message.get("text") or "").strip()
                    username = (from_user.get("username") or chat.get("username") or "").strip()
                    first_name = (from_user.get("first_name") or chat.get("first_name") or "").strip()
                    last_name = (from_user.get("last_name") or chat.get("last_name") or "").strip()

                    if not chat_id or not text:
                        continue

                    result = run_admin_bot_graph(
                        telegram_id=str(chat_id),
                        username=username,
                        first_name=first_name,
                        last_name=last_name,
                        text=text,
                    )

                    reply_text = (result.get("reply_text") or "").strip() or "Запрос принят."

                    send_resp = requests.post(
                        f"{api_url}/sendMessage",
                        json={"chat_id": chat_id, "text": reply_text},
                        timeout=10,
                    )
                    print("SEND RESPONSE:", send_resp.status_code, send_resp.text)

            except Exception as e:
                print("ERROR:", e)
                time.sleep(3)