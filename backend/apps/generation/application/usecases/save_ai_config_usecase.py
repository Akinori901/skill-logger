"""AI設定保存ユースケース。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.generation.domain.entities import AiConfigEntity
    from apps.generation.domain.repositories import AiConfigRepository


class SaveAiConfigUseCase:
    def __init__(self, ai_config_repository: AiConfigRepository) -> None:
        self._repo = ai_config_repository

    def execute(self, entity: AiConfigEntity) -> AiConfigEntity:
        return self._repo.save(entity)
