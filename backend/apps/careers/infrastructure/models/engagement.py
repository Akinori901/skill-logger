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
    phases = models.JSONField(default=list, blank=True)  # 担当工程コード配列
    contract_type = models.CharField(max_length=20, blank=True)  # 雇用形態
    tech_categorized = models.JSONField(default=dict, blank=True)  # 技術の種別分離
    # 技術ごとの関与度の重み（技術名→0.0〜1.0）。言語比率(pct)やFW主要度から算出。
    # スキル経験年数の集計で案件期間に掛ける。空=全技術を重み1.0扱い（前方互換）。
    tech_weights = models.JSONField(default=dict, blank=True)
    # git集計に出ない実務技術の手動補完（技術名→年数）。ライブラリ的利用の最小保証。
    manual_skills = models.JSONField(default=dict, blank=True)
    # 案件で使った技術のバージョン（技術名→版）。案件詳細に「Laravel 8.12」等を表示。
    tech_versions = models.JSONField(default=dict, blank=True)
    # 採用したアーキテクチャ構造（案件詳細に層図を出す）。{"name": str, "layers": [str, ...]}
    architecture = models.JSONField(default=dict, blank=True)
    narrative = models.TextField(blank=True)  # 実績・取り組みの作文
    is_public = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "t_engagements"
        ordering = ["display_order", "-created_at"]

    def __str__(self) -> str:
        return self.title
