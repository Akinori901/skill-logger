"""プロフィール作文（職務要約/自己PR/AI効果）の生成ユースケース。

generate_domain_statement_usecase の骨格を踏襲:
  1. AI設定取得・有効チェック
  2. レート制限チェック
  3. 全案件をコンテキスト化
  4. プロンプト構築 → LLM 呼び出し
  5. ログ記録し、persist 時は UserProfile の該当フィールドへ反映
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from apps.generation.application.dto import AchievementContext, EngagementContext
from apps.generation.application.services.llm_client_service import build_llm_client
from apps.generation.application.services.resume_prompt_builder import (
    NARRATIVE_KINDS,
    ResumePromptBuilderService,
)
from apps.generation.domain.exceptions import (
    AiConfigNotFoundError,
    AiRateLimitExceededError,
    StatementSourceNotFoundError,
)

if TYPE_CHECKING:
    from decimal import Decimal

    from apps.careers.domain.entities import AchievementEntity, EngagementEntity
    from apps.careers.domain.repositories import EngagementRepository, UserProfileRepository
    from apps.generation.domain.repositories import (
        AiConfigRepository,
        AiGenerationLogRepository,
    )

_RATE_LIMIT_PER_MINUTE = 10

_CATEGORY_LABELS = {
    "speed": "速度改善",
    "cost": "コスト削減",
    "quality": "品質向上",
    "ops": "運用改善",
    "incident": "障害削減",
    "release": "リリース改善",
    "review": "レビュー体制改善",
}

# kind → UserProfile のフィールド名
_KIND_TO_FIELD = {
    "summary": "summary",
    "strengths": "strengths",
    "good_at": "good_at",
    # ai_effect は ai_usage の各 effect を埋めるため個別に扱う（persist は行わない）
}


class GenerateProfileNarrativeUseCase:
    def __init__(
        self,
        engagement_repository: EngagementRepository,
        user_profile_repository: UserProfileRepository,
        ai_config_repository: AiConfigRepository,
        generation_log_repository: AiGenerationLogRepository,
    ) -> None:
        self._engagement_repo = engagement_repository
        self._profile_repo = user_profile_repository
        self._config_repo = ai_config_repository
        self._log_repo = generation_log_repository
        self._prompt_builder = ResumePromptBuilderService()

    def execute(self, user_id: int, kind: str, *, persist: bool = False) -> str:
        if kind not in NARRATIVE_KINDS:
            raise StatementSourceNotFoundError(
                f"未知の作文種別です: {kind}（許可: {', '.join(NARRATIVE_KINDS)}）"
            )

        # 1. AI設定
        config = self._config_repo.find_by_user(user_id)
        if config is None or not config.is_enabled or not config.api_key:
            raise AiConfigNotFoundError("AI設定が未登録または無効です。設定ページで API キーを登録してください。")

        # 2. レート制限
        recent = self._log_repo.count_recent(user_id, within_seconds=60)
        if recent >= _RATE_LIMIT_PER_MINUTE:
            raise AiRateLimitExceededError(_RATE_LIMIT_PER_MINUTE, recent)

        # 3. コンテキスト（全案件）
        engagements = self._engagement_repo.find_by_user(user_id)
        if not engagements:
            raise StatementSourceNotFoundError("案件がありません。案件を登録してから生成してください。")
        contexts = [self._to_engagement_context(e) for e in engagements]

        # 4. プロンプト → LLM
        system_prompt = self._prompt_builder.build_profile_system_prompt(kind)
        user_prompt = self._prompt_builder.build_profile_user_prompt(kind, contexts)
        client = build_llm_client(config.provider, config.api_key, config.model)
        try:
            response = client.chat(system_prompt, user_prompt)
        except Exception:
            self._log_repo.record(user_id, config.model, success=False)
            raise

        # 5. ログ + 反映
        self._log_repo.record(user_id, config.model, success=True)
        body = response.content.strip()
        if persist and kind in _KIND_TO_FIELD:
            profile = self._profile_repo.find_by_user(user_id)
            if profile is not None:
                setattr(profile, _KIND_TO_FIELD[kind], body)
                self._profile_repo.save(profile)
        return body

    def _to_engagement_context(self, e: EngagementEntity) -> EngagementContext:
        return EngagementContext(
            engagement_id=e.id,
            company_name=e.company_name,
            industry=e.industry,
            company_scale=self._scale(e),
            period=self._period(e),
            position=e.position,
            overview=e.overview,
            responsibilities=e.responsibilities,
            tech_stack=self._all_techs(e),
            achievements=[self._to_achievement_context(a) for a in e.achievements],
        )

    def _to_achievement_context(self, a: AchievementEntity) -> AchievementContext:
        return AchievementContext(
            category_label=_CATEGORY_LABELS.get(a.category, a.category),
            description=a.description,
            metric_text=self._metric_text(a),
        )

    @staticmethod
    def _all_techs(e: EngagementEntity) -> list[str]:
        cat = e.tech_categorized
        if cat and any(cat.values()):
            out: list[str] = []
            for vals in cat.values():
                out.extend(str(v) for v in (vals or []))
            return out
        return list(e.tech_stack)

    @staticmethod
    def _scale(e: EngagementEntity) -> str:
        parts = []
        if e.company_size_employees is not None:
            parts.append(f"従業員{e.company_size_employees}名")
        if e.dev_org_size is not None:
            parts.append(f"開発{e.dev_org_size}名")
        return " / ".join(parts)

    @staticmethod
    def _period(e: EngagementEntity) -> str:
        if not e.period_start:
            return ""
        return f"{e.period_start}〜{e.period_end or '現在'}"

    @staticmethod
    def _metric_text(a: AchievementEntity) -> str:
        if a.metric_before is not None and a.metric_after is not None:
            unit = a.metric_unit or ""
            text = f"{_num(a.metric_before)}{unit} → {_num(a.metric_after)}{unit}"
            if a.metric_delta_pct is not None:
                text += f"（{_num(a.metric_delta_pct)}%改善）"
            return text
        if a.metric_delta_pct is not None:
            return f"{_num(a.metric_delta_pct)}%改善"
        return ""


def _num(value: Decimal) -> str:
    s = str(value)
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s
