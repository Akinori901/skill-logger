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
    # 参加ルート3軸（skill-inventory の client/agent/sier と揃える）。
    # 実名を格納し、public 出力時の匿名化は is_public で制御する。
    client = models.CharField(max_length=200, blank=True, default="")  # 案件先（実際の発注元）
    agent = models.CharField(max_length=200, blank=True, default="")   # 紹介元エージェント
    sier = models.CharField(max_length=200, blank=True, default="")    # 実装元SIer
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
    # 案件レジストリ共通キー(skill-inventory ledger/projects.yaml の key)。
    # Publicity の projects.yaml / redaction / jobs.projectKey と同一語彙。空=記事化対象外。
    project_key = models.CharField(max_length=50, blank=True, default="")
    # 稼働中フラグ。週次ネタ収穫が is_active な案件だけを対象にする。
    is_active = models.BooleanField(default=False)
    # 記事化で読むローカルのコード配置パス(利用者のPC/SSD)。worker が収穫対象にする。
    local_path = models.CharField(max_length=500, blank=True, default="")
    # 記事化・スキャンで読むローカルパスの複数版。空list=単一 local_path を見る(後方互換)。
    local_paths = models.JSONField(default=list, blank=True)
    is_public = models.BooleanField(default=False)
    # 自社プロダクトか受託案件かの区別。"own"/"client"/""(未分類)。
    # is_public(匿名化制御)とは別概念。真実は skill-inventory ledger の decision(as_is→own)。
    engagement_type = models.CharField(max_length=20, blank=True, default="")
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "t_engagements"
        ordering = ["display_order", "-created_at"]

    def __str__(self) -> str:
        return self.title
