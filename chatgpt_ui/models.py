# chatgpt_ui/models.py
from django.db import models
from accounts.models import CustomUser


class ChatSession(models.Model):
    """
    Состояние диалога для каждого Telegram-пользователя.
    """
    telegram_id = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    last_prompt = models.TextField(null=True, blank=True)

    pending_action = models.CharField(max_length=100, blank=True, default="")
    pending_step = models.CharField(max_length=100, blank=True, default="")

    dialog_mode = models.CharField(max_length=100, blank=True, default="idle")
    user_lang = models.CharField(max_length=20, blank=True, default="ru")

    bridge_active = models.BooleanField(default=False)
    bridge_started_at = models.DateTimeField(null=True, blank=True)
    bridge_closed_at = models.DateTimeField(null=True, blank=True)
    bridge_thread_key = models.CharField(max_length=100, blank=True, default="")

    last_user_message_at = models.DateTimeField(null=True, blank=True)
    last_bot_message_at = models.DateTimeField(null=True, blank=True)

    last_entry_point = models.CharField(max_length=50, blank=True, default="")

    context_json = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Session {self.telegram_id}"


class ChatMessage(models.Model):
    """
    История переписки — все запросы и ответы.
    """
    ROLE = [
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE)
    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role}: {self.content[:40]}"
