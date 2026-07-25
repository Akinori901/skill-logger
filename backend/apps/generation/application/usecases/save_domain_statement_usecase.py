"""申請文の手編集保存ユースケース。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.generation.domain.entities import DomainStatementEntity
    from apps.generation.domain.repositories import DomainStatementRepository


class SaveDomainStatementUseCase:
    def __init__(self, statement_repository: DomainStatementRepository) -> None:
        self._repo = statement_repository

    def execute(self, entity: DomainStatementEntity) -> DomainStatementEntity:
        entity.char_count = len(entity.body)
        return self._repo.save(entity)
