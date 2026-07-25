"""AI生成ログ ORM モデル（レート制限・監査用）。"""

from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class AiGenerationLog(models.Model):
    """t_ai_generation_logs — 申請文生成の実行ログ。"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_generation_logs")
    model = models.CharField(max_length=100, blank=True)
    success = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "t_ai_generation_logs"
        indexes = [models.Index(fields=["user", "created_at"])]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.model}:{self.success}"
