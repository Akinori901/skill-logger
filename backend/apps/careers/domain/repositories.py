"""棚卸しリポジトリABC。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .entities import EngagementEntity, SupportDomainEntity


class EngagementRepository(ABC):
    @abstractmethod
    def find_by_user(self, user_id: int) -> list[EngagementEntity]: ...

    @abstractmethod
    def find_by_id(self, engagement_id: int, user_id: int) -> EngagementEntity | None: ...

    @abstractmethod
    def find_by_domain(self, user_id: int, support_domain_id: int) -> list[EngagementEntity]:
        """指定支援領域に紐づく案件を relevance 降順で返す。"""
        ...

    @abstractmethod
    def save(self, entity: EngagementEntity) -> EngagementEntity:
        """案件＋成果＋URL＋領域リンクを一括保存する（@transaction.atomic）。"""
        ...

    @abstractmethod
    def delete(self, engagement_id: int, user_id: int) -> None: ...


class SupportDomainRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[SupportDomainEntity]: ...

    @abstractmethod
    def find_by_code(self, code: str) -> SupportDomainEntity | None: ...
