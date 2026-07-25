"""AI 生成ドメインエンティティ。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass
class AiConfigEntity:
    """LLM API 設定（ユーザー単位）。"""

    user_id: int
    provider: str = "gemini"  # "gemini" | "claude" | "openai"
    api_key: str = ""
    model: str = "gemini-2.5-flash"
    is_enabled: bool = False
    id: int | None = None


@dataclass
class DomainStatementEntity:
    """生成/編集済みの領域別申請文。"""

    user_id: int
    support_domain_id: int
    body: str
    priority: int = 0  # 申請フォームの優先順位 1-5（0=未設定）
    char_count: int = 0
    source_engagement_ids: list[int] = field(default_factory=list)
    ai_model: str = ""
    id: int | None = None
    generated_at: datetime | None = None
    updated_at: datetime | None = None
