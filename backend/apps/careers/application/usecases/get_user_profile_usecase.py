"""ユーザープロフィール取得ユースケース。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from apps.careers.domain.entities import UserProfileEntity

if TYPE_CHECKING:
    from apps.careers.domain.repositories import UserProfileRepository


class GetUserProfileUseCase:
    def __init__(self, user_profile_repository: UserProfileRepository) -> None:
        self._repo = user_profile_repository

    def execute(self, user_id: int) -> UserProfileEntity:
        profile = self._repo.find_by_user(user_id)
        if profile is None:
            # 未登録なら空の既定を返す（フロントの初期表示に使う）
            return UserProfileEntity(user_id=user_id)
        return profile
