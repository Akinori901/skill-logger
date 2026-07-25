"""申請文 ORM モデル。"""

from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class DomainStatement(models.Model):
    """t_domain_statements — 生成/編集済みの領域別申請文。"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="domain_statements")
    support_domain = models.ForeignKey(
        "careers.SupportDomain",
        on_delete=models.CASCADE,
        related_name="statements",
    )
    priority = models.IntegerField(default=0)  # 1-5、0=未設定
    body = models.TextField(blank=True)
    char_count = models.IntegerField(default=0)
    source_engagement_ids = models.JSONField(default=list, blank=True)
    ai_model = models.CharField(max_length=100, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "t_domain_statements"
        unique_together = ("user", "support_domain")
        ordering = ["priority"]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.support_domain_id} (p={self.priority})"
