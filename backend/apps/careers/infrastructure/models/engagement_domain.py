"""案件×支援領域 中間 ORM モデル。"""

from __future__ import annotations

from django.db import models


class EngagementDomain(models.Model):
    """r_engagement_domains — 案件と支援領域の中間テーブル（寄与度つき）。"""

    engagement = models.ForeignKey(
        "careers.Engagement",
        on_delete=models.CASCADE,
        related_name="domain_links",
    )
    support_domain = models.ForeignKey(
        "careers.SupportDomain",
        on_delete=models.CASCADE,
        related_name="engagement_links",
    )
    relevance = models.IntegerField(default=3)  # 1-5
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "r_engagement_domains"
        unique_together = ("engagement", "support_domain")

    def __str__(self) -> str:
        return f"{self.engagement_id}-{self.support_domain_id} (rel={self.relevance})"
