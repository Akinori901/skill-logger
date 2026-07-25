"""Django 互換 re-export（実体は infrastructure/models/）。

Django の migration / admin は `apps.careers.models` からモデルを解決するため、
infrastructure 層の ORM モデルをここで re-export する。
"""

from apps.careers.infrastructure.models import (
    Achievement,
    Engagement,
    EngagementDomain,
    EngagementUrl,
    SupportDomain,
)

__all__ = [
    "Achievement",
    "Engagement",
    "EngagementDomain",
    "EngagementUrl",
    "SupportDomain",
]
