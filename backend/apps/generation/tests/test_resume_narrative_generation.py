"""職務経歴書の作文生成（プロフィール/案件実績文）のユースケース・プロンプトのテスト。

LLM 呼び出しは build_llm_client をモックして差し替える。
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from django.contrib.auth.models import User

from apps.careers.infrastructure.repositories.django_engagement_repository import (
    DjangoEngagementRepository,
)
from apps.careers.infrastructure.repositories.django_user_profile_repository import (
    DjangoUserProfileRepository,
)
from apps.careers.presentation.serializers import EngagementSerializer, UserProfileSerializer
from apps.generation.application.dto import EngagementContext
from apps.generation.application.services.resume_prompt_builder import ResumePromptBuilderService
from apps.generation.domain.exceptions import AiConfigNotFoundError
from apps.generation.infrastructure.models import AiConfig
from apps.generation.infrastructure.repositories.django_ai_config_repository import (
    DjangoAiConfigRepository,
)
from apps.generation.infrastructure.repositories.django_ai_generation_log_repository import (
    DjangoAiGenerationLogRepository,
)


@dataclass
class _FakeResponse:
    content: str
    model: str


class _FakeClient:
    def __init__(self, text: str) -> None:
        self._text = text
        self.system_prompt = ""
        self.user_prompt = ""

    def chat(self, system_prompt: str, user_prompt: str) -> _FakeResponse:
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        return _FakeResponse(content=self._text, model="gemini-2.5-flash")


# ----- プロンプトビルダー（純粋ロジック、DB不要） -----


class TestResumePromptBuilder:
    def _ctx(self) -> EngagementContext:
        return EngagementContext(
            company_name="秘密株式会社",
            industry="人材サービス業",
            company_scale="開発30名",
            period="2025-07〜現在",
            position="Backend engineer",
            overview="勤怠システムのリビルド",
            responsibilities="API実装",
            tech_stack=["PHP", "Laravel"],
        )

    def test_profile_prompt_hides_company_name(self) -> None:
        b = ResumePromptBuilderService()
        prompt = b.build_profile_user_prompt("summary", [self._ctx()])
        assert "秘密株式会社" not in prompt  # 企業名は出さない
        assert "人材サービス業" in prompt  # 業界で表現

    def test_engagement_prompt_hides_company_name(self) -> None:
        b = ResumePromptBuilderService()
        prompt = b.build_engagement_user_prompt(self._ctx())
        assert "秘密株式会社" not in prompt
        assert "人材サービス業" in prompt
        assert "PHP, Laravel" in prompt

    def test_system_prompt_has_anonymize_rule(self) -> None:
        b = ResumePromptBuilderService()
        assert "企業名は出さず" in b.build_profile_system_prompt("summary")


# ----- 生成ユースケース（DB + LLM モック） -----


@pytest.mark.django_db
class TestGenerateNarrativeUseCases:
    def _user_with_engagement(self, *, ai_enabled: bool = True) -> tuple[User, int]:
        user = User.objects.create(username="tester")
        if ai_enabled:
            AiConfig.objects.create(
                user=user, provider="gemini", api_key="key", model="gemini-2.5-flash", is_enabled=True
            )
        ser = EngagementSerializer(
            data={
                "title": "勤怠システム",
                "industry": "人材サービス業",
                "period_start": "2025-07",
                "responsibilities": "API実装",
            }
        )
        assert ser.is_valid(), ser.errors
        saved = DjangoEngagementRepository().save(ser.to_entity(user.id))
        assert saved.id is not None
        return user, saved.id

    def _profile_usecase(self, monkeypatch: pytest.MonkeyPatch, text: str) -> object:
        from apps.generation.application.usecases import generate_profile_narrative_usecase as mod

        fake = _FakeClient(text)
        monkeypatch.setattr(mod, "build_llm_client", lambda *a, **k: fake)
        return mod.GenerateProfileNarrativeUseCase(
            engagement_repository=DjangoEngagementRepository(),
            user_profile_repository=DjangoUserProfileRepository(),
            ai_config_repository=DjangoAiConfigRepository(),
            generation_log_repository=DjangoAiGenerationLogRepository(),
        )

    def test_profile_narrative_generates_and_persists(self, monkeypatch: pytest.MonkeyPatch) -> None:
        user, _ = self._user_with_engagement()
        # プロフィール行を先に作る（persist 先）
        pser = UserProfileSerializer(data={"display_name": "テスト"})
        assert pser.is_valid()
        DjangoUserProfileRepository().save(pser.to_entity(user.id))

        usecase = self._profile_usecase(monkeypatch, "生成された職務要約です。")
        text = usecase.execute(user.id, "summary", persist=True)  # type: ignore[attr-defined]
        assert text == "生成された職務要約です。"
        profile = DjangoUserProfileRepository().find_by_user(user.id)
        assert profile is not None
        assert profile.summary == "生成された職務要約です。"

    def test_profile_narrative_requires_ai_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        user, _ = self._user_with_engagement(ai_enabled=False)
        usecase = self._profile_usecase(monkeypatch, "x")
        with pytest.raises(AiConfigNotFoundError):
            usecase.execute(user.id, "summary")  # type: ignore[attr-defined]

    def test_engagement_narrative_generates_and_persists(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from apps.generation.application.usecases import generate_engagement_narrative_usecase as mod

        user, eng_id = self._user_with_engagement()
        fake = _FakeClient("生成された実績文です。")
        monkeypatch.setattr(mod, "build_llm_client", lambda *a, **k: fake)
        usecase = mod.GenerateEngagementNarrativeUseCase(
            engagement_repository=DjangoEngagementRepository(),
            ai_config_repository=DjangoAiConfigRepository(),
            generation_log_repository=DjangoAiGenerationLogRepository(),
        )
        text = usecase.execute(user.id, eng_id, persist=True)
        assert text == "生成された実績文です。"
        fetched = DjangoEngagementRepository().find_by_id(eng_id, user.id)
        assert fetched is not None
        assert fetched.narrative == "生成された実績文です。"

    def _field_usecase(self, monkeypatch: pytest.MonkeyPatch, text: str) -> object:
        from apps.generation.application.usecases import generate_engagement_field_usecase as mod

        monkeypatch.setattr(mod, "build_llm_client", lambda *a, **k: _FakeClient(text))
        return mod.GenerateEngagementFieldUseCase(
            engagement_repository=DjangoEngagementRepository(),
            ai_config_repository=DjangoAiConfigRepository(),
            generation_log_repository=DjangoAiGenerationLogRepository(),
        )

    def test_field_generation_industry_persists(self, monkeypatch: pytest.MonkeyPatch) -> None:
        user, eng_id = self._user_with_engagement()
        usecase = self._field_usecase(monkeypatch, "人材・労務 SaaS")
        text = usecase.execute(user.id, eng_id, "industry", persist=True)  # type: ignore[attr-defined]
        assert text == "人材・労務 SaaS"
        fetched = DjangoEngagementRepository().find_by_id(eng_id, user.id)
        assert fetched is not None
        assert fetched.industry == "人材・労務 SaaS"

    def test_field_generation_only_if_empty_skips_existing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # industry に既存値がある案件は only_if_empty=True でスキップし既存値を返す
        user = User.objects.create(username="tester")
        AiConfig.objects.create(
            user=user, provider="gemini", api_key="key", model="gemini-2.5-flash", is_enabled=True
        )
        ser = EngagementSerializer(data={"title": "A", "industry": "既存の業界"})
        assert ser.is_valid(), ser.errors
        saved = DjangoEngagementRepository().save(ser.to_entity(user.id))
        assert saved.id is not None

        usecase = self._field_usecase(monkeypatch, "新しい業界")
        text = usecase.execute(user.id, saved.id, "industry", persist=True, only_if_empty=True)  # type: ignore[attr-defined]
        assert text == "既存の業界"  # 生成せず既存を維持
        fetched = DjangoEngagementRepository().find_by_id(saved.id, user.id)
        assert fetched is not None
        assert fetched.industry == "既存の業界"

    def test_field_generation_rejects_unknown_field(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from apps.generation.domain.exceptions import StatementSourceNotFoundError

        user, eng_id = self._user_with_engagement()
        usecase = self._field_usecase(monkeypatch, "x")
        with pytest.raises(StatementSourceNotFoundError):
            usecase.execute(user.id, eng_id, "unknown_field")  # type: ignore[attr-defined]
