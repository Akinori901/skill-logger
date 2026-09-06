"""自社の公開リポ（OSS/スターター）を自社プロダクト案件として登録する。

Akinori901 の公開リポのうち、案件レジストリに未登録のもの（fair-value-calculator-privacy
除く）を engagement_type="own" + 公開リポ URL(kind="repo") 付きで登録する。

- project_key で既存案件と照合し、冪等に動く（既存は engagement_type / repo_url だけ補完、
  未登録は新規作成）。手動で入れた他フィールドは壊さない。
- Lambda 経由でも使える:
    aws lambda invoke --function-name <worker> \
      --payload '{"command": "register_own_repos"}' --cli-binary-format raw-in-base64-out out.json

使い方: python manage.py register_own_repos [--user <name>] [--dry-run]
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.careers.domain.entities import EngagementEntity, EngagementUrlEntity
from config import container

User = get_user_model()

COMPANY = "QOL株式会社"

# 登録する自社公開リポ。period は public リポの初〜最新コミット（= 開発実体）。
OWN_REPOS: list[dict[str, Any]] = [
    {
        "project_key": "clean_arch_starter",
        "title": "アーキテクチャ規約をCIで機械検証するスターター（6言語・DDD/クリーンアーキ）",
        "repo_url": "https://github.com/Akinori901/clean-arch-starter",
        "period_start": "2026-08",
        "period_end": "2026-08",
        "tech_stack": ["Python", "Go", "PHP", "Ruby", "C#", "TypeScript", "Docker", "Terraform"],
        "industry": "開発ツール / OSS",
        "overview": "Django=DDD、Laravel・Go・Hanami・.NET=クリーンアーキ、React=feature-sliced。"
        ".claude/rules と各層検証ツール（import-linter/deptrac/go-arch-lint 等）で構造を機械強制する。",
    },
    {
        "project_key": "modular_monolith_starter",
        "title": "層で切れないフレームワーク向けモジュラモノリス構成スターター（Rails+packwerk）",
        "repo_url": "https://github.com/Akinori901/modular-monolith-starter",
        "period_start": "2026-08",
        "period_end": "2026-08",
        "tech_stack": ["Ruby", "Rails", "packwerk", "Docker", "AWS Lambda"],
        "industry": "開発ツール / OSS",
        "overview": "Rails+packwerk でパッケージ境界を CI で機械検証する。clean-arch-starter の対。"
        "層ではなく機能パッケージで切り、依存と公開面を強制する。",
    },
    {
        "project_key": "clean_arch_laravel",
        "title": "Laravel のクリーンアーキ規約を deptrac で機械検知する構成",
        "repo_url": "https://github.com/Akinori901/clean-arch-laravel",
        "period_start": "2026-08",
        "period_end": "2026-08",
        "tech_stack": ["PHP", "Laravel", "deptrac", "PHPStan"],
        "industry": "開発ツール / OSS",
        "overview": "層構成・依存表と、それをそのまま強制する deptrac 設定。"
        "Service から Model を直接呼ぶような層破壊を CI で落とす。",
    },
    {
        "project_key": "errand_worker",
        "title": "Claude Code を自前ホストの非同期 AI ワーカーにする OSS",
        "repo_url": "https://github.com/Akinori901/errand-worker",
        "period_start": "2026-08",
        "period_end": "2026-08",
        "tech_stack": ["Python", "Claude Code CLI", "DynamoDB", "S3"],
        "industry": "開発ツール / OSS",
        "overview": "サブスク課金・ローカル完結・APIキー不要で AI ジョブを処理する。"
        "キュー（ファイル/DynamoDB）と出力先（ディレクトリ/S3）を小さなアダプタで差し替え可能。",
    },
    {
        "project_key": "api_migration_diff",
        "title": "モノリスから切り出したAPIが同じ動作か検証する差分レポート AIスキル",
        "repo_url": "https://github.com/Akinori901/api-migration-diff",
        "period_start": "2026-08",
        "period_end": "2026-08",
        "tech_stack": ["Claude Code", "Laravel", "Django", "Rails"],
        "industry": "開発ツール / OSS",
        "overview": "旧新システムの同一エンドポイントを読み比べ、差分を「対応が要る/要らない」に"
        "分類してレポートする。旧環境が動かなくてもコード読み取りだけで成立する。",
    },
    {
        "project_key": "skill_inventory_tool",
        "title": "過去案件を安全に棚卸しするツール（NDA読解・帰属判定・匿名化）",
        "repo_url": "https://github.com/Akinori901/skill-inventory-tool",
        "period_start": "2026-07",
        "period_end": "2026-08",
        "tech_stack": ["Shell", "Claude Code", "git", "GitHub API"],
        "industry": "開発ツール / OSS",
        "overview": "NDA読解で掲載可否（帰属/複製可否）を判定し、技術メタデータ集計と"
        "匿名化コード生成を外部依存ゼロで行う。",
    },
]


# 公開リポは無いが自社の作品（local_path から記事化するネタ源）。engagement_type="own"。
# web-shop-creator-v2: EC モール連携システムを自分の EC 用に作った本体のマイクロサービス版。
# 現在は非稼働（モール仕様変更に追随せず）＝記事専用。原典(PHPモノリス)は別途登録済み。
OWN_LOCAL_PROJECTS: list[dict[str, Any]] = [
    {
        "project_key": "web_shop_creator_v2",
        "title": "ECモール連携システムのマイクロサービス化（自作ECの作り替え・25サービス）",
        "local_path": "/Users/akinori/Documents/Projects/QOL/web-shop-creator-v2",
        "period_start": "",
        "period_end": "",
        "tech_stack": ["Python", "Django", "PHP", "Laravel", "React", "TypeScript", "AWS Lambda", "Docker"],
        "industry": "EC・小売 / 自社プロダクト",
        "overview": "自分の EC 運用のために作った受注・出品・商品管理システムを、モノリスから"
        "業務ドメインごとの25サービス（catalog/lister/product/connector/gateway/billing 等）へ"
        "作り替えたマイクロサービス構成。BE=Django+Laravel隔離、FE=React、→Lambda。"
        "gateway が認証・権限(Cognito連携)の中枢、catalog が全サービス依存の中心。"
        "現在は楽天等のモール仕様変更に追随できず非稼働＝記事・設計知見の素材として保持。",
    },
]


class Command(BaseCommand):
    help = "自社の公開リポ（OSS/スターター）・自作プロダクトを自社プロダクト案件として登録する（冪等）"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--user", default=None, help="登録先ユーザー名（省略時は先頭 superuser）")
        parser.add_argument("--dry-run", action="store_true", help="登録せず内容だけ表示")
        parser.add_argument("--list", action="store_true", help="既存案件の project_key / title を一覧表示して終了")

    def handle(self, *args: Any, **options: Any) -> None:
        user = self._resolve_user(options["user"])
        repo = container.careers_list_engagements_usecase()
        save = container.careers_save_engagement_usecase()

        if options.get("list"):
            for e in repo.execute(user.pk):
                repo_url = next((u.url for u in e.urls or [] if u.kind == "repo"), "")
                self.stdout.write(
                    f"  [{e.engagement_type or '-':6}] {e.project_key or '(なし)':22} "
                    f"repo={'✓' if repo_url else '-'} | {e.title[:40]}"
                )
            return

        existing = {e.project_key: e for e in repo.execute(user.pk) if e.project_key}

        created = updated = 0
        for spec in OWN_REPOS:
            key = spec["project_key"]
            repo_url = spec["repo_url"]
            prior = existing.get(key)

            if prior is not None:
                # 既存案件: engagement_type / repo リンクだけ補完し、他は温存する。
                changed = False
                if prior.engagement_type != "own":
                    prior.engagement_type = "own"
                    changed = True
                if not any(u.kind == "repo" for u in prior.urls):
                    prior.urls = [*prior.urls, EngagementUrlEntity(url=repo_url, label="GitHub", kind="repo")]
                    changed = True
                if changed:
                    if not options["dry_run"]:
                        save.execute(prior)
                    updated += 1
                    self.stdout.write(self.style.WARNING(f"  [update] {key}（own/repo 補完）"))
                else:
                    self.stdout.write(f"  [skip] {key}（既に own+repo 登録済み）")
                continue

            # 未登録: 新規作成。
            entity = EngagementEntity(
                user_id=user.pk,
                title=spec["title"],
                company_name=COMPANY,
                engagement_type="own",
                project_key=key,
                industry=spec.get("industry", ""),
                overview=spec.get("overview", ""),
                period_start=spec.get("period_start", ""),
                period_end=spec.get("period_end", ""),
                tech_stack=list(spec.get("tech_stack", [])),
                urls=[EngagementUrlEntity(url=repo_url, label="GitHub", kind="repo")],
            )
            if not options["dry_run"]:
                save.execute(entity)
            created += 1
            self.stdout.write(self.style.SUCCESS(f"  [create] {key}"))

        # 公開リポは無いが自社の作品（local_path から記事化するネタ源）。
        for spec in OWN_LOCAL_PROJECTS:
            key = spec["project_key"]
            local_path = spec["local_path"]
            prior = existing.get(key)

            if prior is not None:
                changed = False
                if prior.engagement_type != "own":
                    prior.engagement_type = "own"
                    changed = True
                if not (prior.local_path or "").strip():
                    prior.local_path = local_path
                    changed = True
                if changed:
                    if not options["dry_run"]:
                        save.execute(prior)
                    updated += 1
                    self.stdout.write(self.style.WARNING(f"  [update] {key}（own/local_path 補完）"))
                else:
                    self.stdout.write(f"  [skip] {key}（既に own+local_path 登録済み）")
                continue

            entity = EngagementEntity(
                user_id=user.pk,
                title=spec["title"],
                company_name=COMPANY,
                engagement_type="own",
                project_key=key,
                industry=spec.get("industry", ""),
                overview=spec.get("overview", ""),
                period_start=spec.get("period_start", ""),
                period_end=spec.get("period_end", ""),
                tech_stack=list(spec.get("tech_stack", [])),
                local_path=local_path,
            )
            if not options["dry_run"]:
                save.execute(entity)
            created += 1
            self.stdout.write(self.style.SUCCESS(f"  [create] {key}（local_path 記事専用）"))

        prefix = "dry-run: " if options["dry_run"] else "完了: "
        self.stdout.write(self.style.SUCCESS(f"{prefix}新規{created} / 更新{updated}"))

    def _resolve_user(self, username: str | None) -> Any:
        if username:
            user = User.objects.filter(username=username).first()
            if not user:
                raise CommandError(f"ユーザーが見つかりません: {username}")
            return user
        user = User.objects.filter(is_superuser=True).order_by("pk").first()
        if not user:
            raise CommandError("superuser が見つかりません（--user で指定してください）")
        return user
