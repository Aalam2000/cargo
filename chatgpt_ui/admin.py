# chatgpt_ui/admin.py
from django.contrib import admin
from .models import ChatSession, ChatMessage


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "telegram_id", "user", "is_active", "created_at")
    search_fields = ("telegram_id",)
    list_filter = ("is_active",)
    ordering = ("-created_at",)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "role", "short_text", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("content",)

    def short_text(self, obj):
        return obj.content[:50]

