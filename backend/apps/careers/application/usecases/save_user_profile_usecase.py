"""ユーザープロフィール保存ユースケース。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.careers.domain.entities import UserProfileEntity
    from apps.careers.domain.repositories import UserProfileRepository


class SaveUserProfileUseCase:
    def __init__(self, user_profile_repository: UserProfileRepository) -> None:
        self._repo = user_profile_repository

    def execute(self, entity: UserProfileEntity) -> UserProfileEntity:
        return self._repo.save(entity)
