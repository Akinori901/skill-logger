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
            # 取り込む価値があるか判定。git集計(languages)が無くても、
            # 手動補完技術・マーカー検出技術・経歴書由来プロファイル(役割/責務/成果)の
            # いずれかがあれば「載せる意味のある案件」として取り込む。
            # ※退職済み等でリポを再clone出来ない案件は languages が空になるが、
            #   本人が匿名化して書いたプロファイルは職務経歴の主役なので落とさない。
            has_content = (
                item.get("repo_count", 0) > 0
                or item.get("languages")
                or item.get("manual_skills")
                or item.get("detected_tech")
                or item.get("title_line")
                or item.get("role")
                or item.get("responsibilities")
                or item.get("achievements")
            )
            if not has_content:
                # 技術データもプロファイルも一切無い → 取り込む意味が薄い
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
        languages = item.get("languages", [])
        langs = [x["language"] for x in languages]
        fws = item.get("frameworks", [])
        tech: list[str] = []
        for t in [*langs, *fws]:
            if t and t not in tech:
                tech.append(t)

        # 言語比率(pct)を関与度の重み(0.0〜1.0)に変換。git-local feed は「自分が
        # 参加期間内に書いた行」の比率なので、これがそのまま関与度になる。
        tech_weights: dict[str, float] = {}
        for x in languages:
            pct = x.get("pct")
            if pct is not None:
                tech_weights[x["language"]] = round(float(pct) / 100.0, 4)
        # フレームワーク(React/Vue/Django等)は pct を持たず「使った」事実のみ。
        # 期間フルカウント(重み1.0)にすると案件全期間ぶん計上され過大になるため、
        # 控えめな既定重み(0.3)にする。実態が違う場合は manual_skills で上書き。
        fw_weight = 0.3
        for fw in fws:
            tech_weights.setdefault(fw, fw_weight)

        # マーカー検出した「使った技術」(Docker/Cypress/PHPUnit/Laravel等)を tech_stack に合流。
        # git集計(自分が書いた行)に出ない技術を存在ベースで拾い、案件数を正確にする。
        # detected は「そのプロジェクトで使った」事実なので重み1.0(使った案件の期間フル)を保証。
        # ※git言語側で低い比率(例 cypress 0.0%)が出ていても、存在ベースの1.0で上書きする。
        for t in item.get("detected_tech", []):
            if not t:
                continue
            if t not in tech:
                tech.append(t)
            tech_weights[t] = 1.0

        # 手動補完技術(git集計に出ない実務利用)。tech_stack にも足しつつ年数を保持。
        manual_skills: dict[str, float] = {}
        for ms in item.get("manual_skills", []):
            t = ms.get("tech")
            if not t:
                continue
            if t not in tech:
                tech.append(t)
            years = ms.get("years")
            if years is not None:
                manual_skills[t] = float(years)

        # タイトルは「案件を簡潔に表す一文」(title_line)を優先。無ければ display_name。
        title_line = item.get("title_line") or item.get("display_name") or item.get("source_key")
        title = f"{TITLE_PREFIX}{title_line}"
        # display_name は skill-inventory 側で匿名化済みの「企業名／案件呼称」。
        # 非匿名表示時（企業名を伏せるOFF）の案件見出しに使う。
        company_name = item.get("display_name", "")
        return EngagementEntity(
            user_id=user_id,
            title=title,
            company_name=company_name,
            industry=item.get("industry", ""),
            position=item.get("role", ""),
            period_start=self._to_year_month(item.get("period_start", "")),
            period_end=self._to_year_month(item.get("period_end", "")),
            tech_stack=tech,
            tech_weights=tech_weights,
            manual_skills=manual_skills,
            tech_versions=dict(item.get("tech_versions", {})),
            architecture=dict(item.get("architecture", {})),
            overview=item.get("overview", ""),
            responsibilities=item.get("responsibilities", ""),
            challenges=item.get("achievements", ""),
        )

    @staticmethod
    def _to_year_month(date_str: str) -> str:
        """YYYY-MM-DD / YYYY-MM / YYYY を YYYY-MM（最大7文字）に正規化する。"""
        return date_str[:7] if date_str else ""
