"""案件 ORM モデル。"""

from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class Engagement(models.Model):
    """t_engagements — 棚卸しの主テーブル。"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="engagements")
    title = models.CharField(max_length=200)
    industry = models.CharField(max_length=100, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    company_size_employees = models.IntegerField(null=True, blank=True)
    dev_org_size = models.IntegerField(null=True, blank=True)
    period_start = models.CharField(max_length=7, blank=True)  # YYYY-MM
    period_end = models.CharField(max_length=7, blank=True)  # YYYY-MM（空=現在）
    position = models.CharField(max_length=100, blank=True)
    overview = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    tech_stack = models.JSONField(default=list, blank=True)
    challenges = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "t_engagements"
        ordering = ["display_order", "-created_at"]

    def __str__(self) -> str:
        return self.title
