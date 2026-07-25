"""支援領域マスタ ORM モデル。"""

from __future__ import annotations

from django.db import models


class SupportDomain(models.Model):
    """m_support_domains — Expert 申請の支援領域マスタ。"""

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "m_support_domains"
        ordering = ["display_order"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"
