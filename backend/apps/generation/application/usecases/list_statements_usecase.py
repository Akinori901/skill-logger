"""生成済み申請文の一覧取得ユースケース。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.generation.domain.entities import DomainStatementEntity
    from apps.generation.domain.repositories import DomainStatementRepository


class ListStatementsUseCase:
    def __init__(self, statement_repository: DomainStatementRepository) -> None:
        self._repo = statement_repository

    def execute(self, user_id: int) -> list[DomainStatementEntity]:
        return self._repo.find_by_user(user_id)
