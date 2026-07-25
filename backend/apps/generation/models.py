"""Django 互換 re-export（実体は infrastructure/models/）。"""

from apps.generation.infrastructure.models import AiConfig, AiGenerationLog, DomainStatement

__all__ = ["AiConfig", "AiGenerationLog", "DomainStatement"]
