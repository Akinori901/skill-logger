"""skill-inventory 供給JSON（skilllogger-feed/v1）を取り込むユースケース。

技術メタデータ（言語・FW・期間・規模）を Engagement の下書きとして登録する。
業界・成果・支援領域・担当は空のまま残し、人間が後で補う前提。

management command と DRF View の両方から利用する（ロジックの一元化）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from apps.careers.domain.entities import EngagementEntity

if TYPE_CHECKING:
    from apps.careers.domain.repositories import EngagementRepository

# 取り込んだ案件のタイトルに付ける接頭辞（冪等な照合キーにも使う）
TITLE_PREFIX = "[inv] "


@dataclass
class ImportResult:
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "created_count": len(self.created),
            "updated_count": len(self.updated),
            "skipped_count": len(self.skipped),
        }


class ImportFromInventoryUseCase:
    def __init__(self, engagement_repository: EngagementRepository) -> None:
        self._repo = engagement_repository

    def execute(
        self,
        user_id: int,
        feed: dict[str, Any],
        *,
        only_decision: str | None = None,
        dry_run: bool = False,
    ) -> ImportResult:
        """feed（skilllogger-feed/v1）から案件を取り込む。

        - only_decision: 指定した decision の案件のみ取り込む（例: "as_is"）
        - dry_run: 保存せず、対象だけを result に積む
        """
        result = ImportResult()
        engagements = feed.get("engagements", [])
        existing = {e.title: e for e in self._repo.find_by_user(user_id)}

        for item in engagements:
            name = item.get("display_name") or item.get("source_key") or "?"

            if only_decision and item.get("decision") != only_decision:
                result.skipped.append(name)
                continue
            if item.get("repo_count", 0) == 0 and not item.get("languages"):
                # 手元にリポが無く技術データも空 → 取り込む意味が薄い
                result.skipped.append(name)
                continue

            entity = self._to_entity(item, user_id)
            prior = existing.get(entity.title)
            if prior is not None:
                entity.id = prior.id

            if not dry_run:
                self._repo.save(entity)

            if prior is not None:
                result.updated.append(name)
            else:
                result.created.append(name)

        return result

    # ------------------------------------------------------------------

    def _to_entity(self, item: dict[str, Any], user_id: int) -> EngagementEntity:
        langs = [x["language"] for x in item.get("languages", [])]
        fws = item.get("frameworks", [])
        tech: list[str] = []
        for t in [*langs, *fws]:
            if t and t not in tech:
                tech.append(t)

        title = f"{TITLE_PREFIX}{item.get('display_name') or item.get('source_key')}"
        return EngagementEntity(
            user_id=user_id,
            title=title,
            period_start=self._to_year_month(item.get("period_start", "")),
            period_end=self._to_year_month(item.get("period_end", "")),
            tech_stack=tech,
            overview=self._build_overview(item),
        )

    @staticmethod
    def _to_year_month(date_str: str) -> str:
        """YYYY-MM-DD / YYYY-MM / YYYY を YYYY-MM（最大7文字）に正規化する。"""
        return date_str[:7] if date_str else ""

    @staticmethod
    def _build_overview(item: dict[str, Any]) -> str:
        parts = []
        top_langs = [x["language"] for x in item.get("languages", [])[:3]]
        if top_langs:
            parts.append(f"主要言語: {', '.join(top_langs)}")
        if item.get("frameworks"):
            parts.append(f"FW: {', '.join(item['frameworks'][:5])}")
        parts.append(
            f"規模: {item.get('repo_count', 0)}リポ / {item.get('file_count', 0)}ファイル / "
            f"{item.get('total_commits', 0)}コミット"
        )
        if item.get("my_commits"):
            parts.append(f"関与コミット: {item['my_commits']}")
        parts.append("（skill-inventory から自動取り込み。業界・成果・支援領域は要記入）")
        return "\n".join(parts)
