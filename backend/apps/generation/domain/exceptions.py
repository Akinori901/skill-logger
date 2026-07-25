"""AI 生成ドメイン例外。"""

from __future__ import annotations


class AiConfigNotFoundError(Exception):
    """AI設定が未登録 or is_enabled=False"""


class AiApiKeyInvalidError(Exception):
    """API キーが無効"""


class AiRateLimitExceededError(Exception):
    """レート制限超過"""

    def __init__(self, max_per_minute: int, current_count: int) -> None:
        self.max_per_minute = max_per_minute
        self.current_count = current_count
        super().__init__(f"レート制限: {current_count}/{max_per_minute} req/min")


class StatementSourceNotFoundError(Exception):
    """生成対象の領域に紐づく案件が1件もない"""
