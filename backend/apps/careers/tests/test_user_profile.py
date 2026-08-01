"""UserProfile の serializer ⇔ entity ⇔ repository ラウンドトリップ検証。"""

from __future__ import annotations

import pytest
from django.contrib.auth.models import User

from apps.careers.application.usecases.get_user_profile_usecase import GetUserProfileUseCase
from apps.careers.infrastructure.repositories.django_user_profile_repository import (
    DjangoUserProfileRepository,
)
from apps.careers.presentation.serializers import UserProfileSerializer


@pytest.mark.django_db
class TestUserProfile:
    def _user(self) -> User:
        return User.objects.create(username="tester")

    def test_roundtrip_persists_all_fields(self) -> None:
        user = self._user()
        payload = {
            "display_name": "山田 太郎",
            "age_range": "40代",
            "residence": "東京都",
            "headline": "バックエンドエンジニア",
            "summary": "職務要約テキスト",
            "strengths": "挑戦意欲",
            "good_at": "Backend全般",
            "ai_usage": [
                {"tool": "ClaudeCode", "how": "スキル作成", "effect": "対応言語が広がった"},
            ],
        }
        ser = UserProfileSerializer(data=payload)
        assert ser.is_valid(), ser.errors
        entity = ser.to_entity(user.id)

        repo = DjangoUserProfileRepository()
        repo.save(entity)

        fetched = repo.find_by_user(user.id)
        assert fetched is not None
        assert fetched.display_name == "山田 太郎"
        assert fetched.age_range == "40代"
        assert fetched.summary == "職務要約テキスト"
        assert fetched.ai_usage == [
            {"tool": "ClaudeCode", "how": "スキル作成", "effect": "対応言語が広がった"}
        ]

    def test_save_is_upsert(self) -> None:
        # 2回 save しても行は1つ（OneToOne + update_or_create）
        user = self._user()
        repo = DjangoUserProfileRepository()
        ser1 = UserProfileSerializer(data={"display_name": "初回"})
        assert ser1.is_valid()
        repo.save(ser1.to_entity(user.id))
        ser2 = UserProfileSerializer(data={"display_name": "更新後"})
        assert ser2.is_valid()
        saved = repo.save(ser2.to_entity(user.id))
        assert saved.display_name == "更新後"
        fetched = repo.find_by_user(user.id)
        assert fetched is not None
        assert fetched.display_name == "更新後"

    def test_get_usecase_returns_empty_default_when_unregistered(self) -> None:
        user = self._user()
        usecase = GetUserProfileUseCase(user_profile_repository=DjangoUserProfileRepository())
        entity = usecase.execute(user.id)
        assert entity.user_id == user.id
        assert entity.display_name == ""
        assert entity.ai_usage == []
