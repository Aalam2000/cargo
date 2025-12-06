# chatgpt_ui/models.py
from django.db import models
from accounts.models import CustomUser


class ChatSession(models.Model):
    """
    Состояние диалога для каждого Telegram-пользователя.
    """
    telegram_id = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(CustomUser, null=True, blank=True,
                             on_delete=models.SET_NULL)

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    # последний системный промпт, чтобы бот знал режим (создание клиента, компании и т.д.)
    last_prompt = models.TextField(null=True, blank=True)

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
