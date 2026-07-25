"""AI設定 ORM モデル。"""

from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class AiConfig(models.Model):
    """m_user_ai_configs — ユーザー単位の LLM API 設定。

    API キーは平文保存（fair-value apps/ai と同方式）。public リポには
    実キーを含めない（DB のみに存在）。
    """

    # 無料枠のある Gemini を既定にする。
    PROVIDER_CHOICES = [("gemini", "Gemini"), ("claude", "Claude"), ("openai", "OpenAI")]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="ai_config")
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default="gemini")
    api_key = models.CharField(max_length=255, blank=True)
    model = models.CharField(max_length=100, default="gemini-2.5-flash")
    is_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "m_user_ai_configs"

    def __str__(self) -> str:
        return f"{self.user_id}:{self.provider}/{self.model}"
