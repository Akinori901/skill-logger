"""AI設定取得ユースケース。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from apps.generation.domain.entities import AiConfigEntity

if TYPE_CHECKING:
    from apps.generation.domain.repositories import AiConfigRepository


class GetAiConfigUseCase:
    def __init__(self, ai_config_repository: AiConfigRepository) -> None:
        self._repo = ai_config_repository

    def execute(self, user_id: int) -> AiConfigEntity:
        config = self._repo.find_by_user(user_id)
        if config is None:
            # 未登録なら空の既定を返す（フロントで初期表示に使う）
            return AiConfigEntity(user_id=user_id)
        return config
