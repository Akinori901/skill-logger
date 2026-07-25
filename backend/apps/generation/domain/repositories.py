"""AI 生成リポジトリABC。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .entities import AiConfigEntity, DomainStatementEntity


class AiConfigRepository(ABC):
    @abstractmethod
    def find_by_user(self, user_id: int) -> AiConfigEntity | None: ...

    @abstractmethod
    def save(self, entity: AiConfigEntity) -> AiConfigEntity: ...


class DomainStatementRepository(ABC):
    @abstractmethod
    def find_by_user(self, user_id: int) -> list[DomainStatementEntity]: ...

    @abstractmethod
    def save(self, entity: DomainStatementEntity) -> DomainStatementEntity: ...


class AiGenerationLogRepository(ABC):
    @abstractmethod
    def count_recent(self, user_id: int, within_seconds: int) -> int:
        """直近 within_seconds 秒間の生成回数（レート制限用）。"""
        ...

    @abstractmethod
    def record(self, user_id: int, model: str, success: bool) -> None: ...
