"""skill-inventory の供給JSON（skilllogger-feed/v1）から案件を取り込むコマンド。

ロジックは ImportFromInventoryUseCase に一元化（DRF View と共通）。

Usage:
    python manage.py import_from_inventory --file /path/to/skilllogger-feed.json
    python manage.py import_from_inventory --file feed.json --user admin
    python manage.py import_from_inventory --file feed.json --only-decision as_is
    python manage.py import_from_inventory --file feed.json --dry-run
"""

from __future__ import annotations

import json
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError, CommandParser

from config import container

User = get_user_model()


class Command(BaseCommand):
    help = "skill-inventory の供給JSONから案件（技術メタ下書き）を取り込む"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--file", required=True, help="skilllogger-feed.json のパス")
        parser.add_argument("--user", default=None, help="取り込み先ユーザー名（省略時は DEV_FIXED_USER_ID）")
        parser.add_argument("--only-decision", default=None, help="指定 decision の案件だけ（例: as_is）")
        parser.add_argument("--dry-run", action="store_true", help="登録せず内容だけ表示")

    def handle(self, *args: Any, **options: Any) -> None:
        feed = self._load_feed(options["file"])
        user = self._resolve_user(options["user"])

        usecase = container.careers_import_from_inventory_usecase()
        result = usecase.execute(
            user.pk,
            feed,
            only_decision=options["only_decision"],
            dry_run=options["dry_run"],
        )

        for name in result.created:
            self.stdout.write(self.style.SUCCESS(f"  [create] {name}"))
        for name in result.updated:
            self.stdout.write(self.style.WARNING(f"  [update] {name}"))
        for name in result.skipped:
            self.stdout.write(f"  [skip] {name}")

        prefix = "dry-run: " if options["dry_run"] else "完了: "
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}新規{len(result.created)} / 更新{len(result.updated)} / スキップ{len(result.skipped)}"
            )
        )

    def _load_feed(self, path: str) -> dict[str, Any]:
        try:
            with open(path, encoding="utf-8") as f:
                feed: dict[str, Any] = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise CommandError(f"供給JSONを読めません: {e}") from e
        if not isinstance(feed, dict) or feed.get("schema", "").split("/")[0] != "skilllogger-feed":
            raise CommandError("schema が skilllogger-feed ではありません")
        return feed

    def _resolve_user(self, username: str | None) -> Any:
        if username:
            user = User.objects.filter(username=username).first()
            if user is None:
                raise CommandError(f"ユーザーが見つかりません: {username}")
            return user
        user = User.objects.filter(pk=getattr(settings, "DEV_FIXED_USER_ID", 1)).first()
        if user is None:
            raise CommandError("取り込み先ユーザーが存在しません（seed を実行してください）")
        return user
