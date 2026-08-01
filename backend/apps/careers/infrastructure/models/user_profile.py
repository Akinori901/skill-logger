"""ユーザープロフィール ORM モデル（職務経歴書サマリ）。"""

from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """m_user_profiles — 職務経歴書サマリ（ユーザー単位）。

    AiConfig と同じく OneToOne + update_or_create で単一オブジェクトとして扱う。
    Django 標準 User は不可侵に保ち、プロフィール列はこのテーブルへ切り出す。
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    # 事実（手入力）
    display_name = models.CharField(max_length=100, blank=True)
    age_range = models.CharField(max_length=20, blank=True)
    residence = models.CharField(max_length=100, blank=True)
    headline = models.CharField(max_length=200, blank=True)
    # 作文（Gemini 生成 or 手入力）
    summary = models.TextField(blank=True)
    strengths = models.TextField(blank=True)
    good_at = models.TextField(blank=True)
    # 生成AI活用 [{"tool","how","effect"}]
    ai_usage = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "m_user_profiles"

    def __str__(self) -> str:
        return f"{self.user_id}:{self.display_name}"
