"""実績URL ORM モデル。"""

from __future__ import annotations

from django.db import models


class EngagementUrl(models.Model):
    """t_engagement_urls — 案件の実績URL。"""

    engagement = models.ForeignKey(
        "careers.Engagement",
        on_delete=models.CASCADE,
        related_name="urls",
    )
    url = models.URLField(max_length=500)
    label = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "t_engagement_urls"

    def __str__(self) -> str:
        return self.url
