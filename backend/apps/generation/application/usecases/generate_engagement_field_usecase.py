"""案件の単一フィールド（業界/概要/実績）を Gemini で生成するユースケース。

generate_engagement_narrative_usecase の骨格を汎用化し、field を指定して
industry / overview / narrative のいずれかを生成する。下書き用途。
persist 時は「空フィールドのみ埋める」ガードで既存の手入力を保護する。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from apps.generation.application.dto import AchievementContext, EngagementContext
from apps.generation.application.services.llm_client_service import build_llm_client
from apps.generation.application.services.resume_prompt_builder import (
    ENGAGEMENT_FIELD_KINDS,
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
    from apps.careers.domain.repositories import EngagementRepository
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


class GenerateEngagementFieldUseCase:
    def __init__(
        self,
        engagement_repository: EngagementRepository,
        ai_config_repository: AiConfigRepository,
        generation_log_repository: AiGenerationLogRepository,
    ) -> None:
        self._engagement_repo = engagement_repository
        self._config_repo = ai_config_repository
        self._log_repo = generation_log_repository
        self._prompt_builder = ResumePromptBuilderService()

    def execute(
        self,
        user_id: int,
        engagement_id: int,
        field: str,
        *,
        persist: bool = False,
        only_if_empty: bool = False,
    ) -> str:
        if field not in ENGAGEMENT_FIELD_KINDS:
            raise StatementSourceNotFoundError(
                f"未知のフィールドです: {field}（許可: {', '.join(ENGAGEMENT_FIELD_KINDS)}）"
            )

        # 1. AI設定
        config = self._config_repo.find_by_user(user_id)
        if config is None or not config.is_enabled or not config.api_key:
            raise AiConfigNotFoundError("AI設定が未登録または無効です。設定ページで API キーを登録してください。")

        # 2. レート制限
        recent = self._log_repo.count_recent(user_id, within_seconds=60)
        if recent >= _RATE_LIMIT_PER_MINUTE:
            raise AiRateLimitExceededError(_RATE_LIMIT_PER_MINUTE, recent)

        # 3. 対象案件
        engagement = self._engagement_repo.find_by_id(engagement_id, user_id)
        if engagement is None:
            raise StatementSourceNotFoundError(f"案件が見つかりません: id={engagement_id}")

        # only_if_empty: 既に値があるフィールドはスキップ（一括自動埋めで手入力を守る）
        if only_if_empty and self._field_value(engagement, field):
            return self._field_value(engagement, field)

        context = self._to_engagement_context(engagement)

        # 4. プロンプト → LLM
        system_prompt = self._prompt_builder.build_engagement_system_prompt(field)
        user_prompt = self._prompt_builder.build_engagement_user_prompt(context, field)
        client = build_llm_client(config.provider, config.api_key, config.model)
        try:
            response = client.chat(system_prompt, user_prompt)
        except Exception:
            self._log_repo.record(user_id, config.model, success=False)
            raise

        # 5. ログ + 反映
        self._log_repo.record(user_id, config.model, success=True)
        body = response.content.strip()
        if persist:
            self._set_field(engagement, field, body)
            self._engagement_repo.save(engagement)
        return body

    @staticmethod
    def _field_value(e: EngagementEntity, field: str) -> str:
        return str(getattr(e, field, "") or "")

    @staticmethod
    def _set_field(e: EngagementEntity, field: str, value: str) -> None:
        setattr(e, field, value)

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
