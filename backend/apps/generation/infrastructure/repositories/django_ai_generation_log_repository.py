"""AI生成ログリポジトリ ORM 実装。"""

from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from apps.generation.domain.repositories import AiGenerationLogRepository
from apps.generation.infrastructure.models import AiGenerationLog


class DjangoAiGenerationLogRepository(AiGenerationLogRepository):
    def count_recent(self, user_id: int, within_seconds: int) -> int:
        threshold = timezone.now() - timedelta(seconds=within_seconds)
        return AiGenerationLog.objects.filter(user_id=user_id, created_at__gte=threshold).count()

    def record(self, user_id: int, model: str, success: bool) -> None:
        AiGenerationLog.objects.create(user_id=user_id, model=model, success=success)
