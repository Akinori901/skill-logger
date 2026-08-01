"""Phase 2 で追加した案件詳細フィールド（担当工程/雇用形態/技術種別/実績文）の
serializer ⇔ entity ⇔ repository ラウンドトリップを検証する。
"""

from __future__ import annotations

import pytest
from django.contrib.auth.models import User

from apps.careers.infrastructure.repositories.django_engagement_repository import (
    DjangoEngagementRepository,
)
from apps.careers.presentation.serializers import EngagementSerializer


@pytest.mark.django_db
class TestEngagementDetailFields:
    def _user(self) -> User:
        return User.objects.create(username="tester")

    def test_serializer_roundtrip_persists_new_fields(self) -> None:
        user = self._user()
        payload = {
            "title": "勤怠システム",
            "period_start": "2025-07",
            "phases": ["req", "basic", "backend", "test"],
            "contract_type": "quasi",
            "tech_categorized": {
                "language": ["PHP", "JavaScript"],
                "db": ["MySQL"],
                "framework": ["Laravel"],
                "cloud": [],
                "tool": ["Docker"],
            },
            "narrative": "法務要件の取りまとめから顔認証連携まで担当。",
        }
        ser = EngagementSerializer(data=payload)
        assert ser.is_valid(), ser.errors
        entity = ser.to_entity(user.id)

        repo = DjangoEngagementRepository()
        saved = repo.save(entity)
        assert saved.id is not None

        # 保存後に再取得しても4フィールドが保持される
        fetched = repo.find_by_id(saved.id, user.id)
        assert fetched is not None
        assert fetched.phases == ["req", "basic", "backend", "test"]
        assert fetched.contract_type == "quasi"
        assert fetched.tech_categorized["language"] == ["PHP", "JavaScript"]
        assert fetched.tech_categorized["db"] == ["MySQL"]
        assert fetched.narrative == "法務要件の取りまとめから顔認証連携まで担当。"

    def test_defaults_are_backward_compatible(self) -> None:
        # 新フィールド未指定でも従来通り作成でき、既定は空
        user = self._user()
        ser = EngagementSerializer(data={"title": "旧来案件"})
        assert ser.is_valid(), ser.errors
        entity = ser.to_entity(user.id)
        saved = DjangoEngagementRepository().save(entity)
        assert saved.phases == []
        assert saved.contract_type == ""
        assert saved.tech_categorized == {}
        assert saved.narrative == ""

    def test_invalid_phase_rejected(self) -> None:
        ser = EngagementSerializer(data={"title": "A", "phases": ["req", "unknown_phase"]})
        assert not ser.is_valid()
        assert "phases" in ser.errors

    def test_invalid_contract_type_rejected(self) -> None:
        ser = EngagementSerializer(data={"title": "A", "contract_type": "freelance"})
        assert not ser.is_valid()
        assert "contract_type" in ser.errors

    def test_unknown_tech_category_key_rejected(self) -> None:
        ser = EngagementSerializer(data={"title": "A", "tech_categorized": {"unknown": ["X"]}})
        assert not ser.is_valid()
        assert "tech_categorized" in ser.errors

    def test_entity_to_dict_includes_new_fields(self) -> None:
        user = self._user()
        ser = EngagementSerializer(
            data={"title": "A", "phases": ["backend"], "contract_type": "contract", "narrative": "n"}
        )
        assert ser.is_valid(), ser.errors
        saved = DjangoEngagementRepository().save(ser.to_entity(user.id))
        out = EngagementSerializer.entity_to_dict(saved)
        assert out["phases"] == ["backend"]
        assert out["contract_type"] == "contract"
        assert out["narrative"] == "n"
        assert out["tech_categorized"] == {}
