"""成果 ORM モデル。"""

from __future__ import annotations

from django.db import models


class Achievement(models.Model):
    """t_achievements — 案件の成果（数字付き）。"""

    CATEGORY_CHOICES = [
        ("speed", "速度改善"),
        ("cost", "コスト削減"),
        ("quality", "品質向上"),
        ("ops", "運用改善"),
        ("incident", "障害削減"),
        ("release", "リリース改善"),
        ("review", "レビュー体制改善"),
    ]

    engagement = models.ForeignKey(
        "careers.Engagement",
        on_delete=models.CASCADE,
        related_name="achievements",
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.CharField(max_length=500)
    metric_before = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    metric_after = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    metric_unit = models.CharField(max_length=30, blank=True)
    metric_delta_pct = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "t_achievements"

    def __str__(self) -> str:
        return f"[{self.category}] {self.description[:30]}"
