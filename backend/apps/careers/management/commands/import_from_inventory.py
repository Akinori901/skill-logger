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

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError, CommandParser

from config import container

User = get_user_model()


class Command(BaseCommand):
    help = "skill-inventory の供給JSONから案件（技術メタ下書き）を取り込む"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--file", default=None, help="skilllogger-feed.json のパス")
        parser.add_argument(
            "--feed-base64",
            default=None,
            help="feed JSON を base64 で直接渡す（Lambda payload 経由の取込用。--file の代替）",
        )
        parser.add_argument("--user", default=None, help="取り込み先ユーザー名（省略時は DEV_FIXED_USER_ID）")
        parser.add_argument("--only-decision", default=None, help="指定 decision の案件だけ（例: as_is）")
        parser.add_argument("--dry-run", action="store_true", help="登録せず内容だけ表示")

    def handle(self, *args: Any, **options: Any) -> None:
        if options.get("feed_base64"):
            feed = self._load_feed_base64(options["feed_base64"])
        elif options.get("file"):
            feed = self._load_feed(options["file"])
        else:
            raise CommandError("--file か --feed-base64 のいずれかを指定してください")
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

    def _load_feed_base64(self, b64: str) -> dict[str, Any]:
        import base64  # noqa: PLC0415

        try:
            raw = base64.b64decode(b64)
            feed: dict[str, Any] = json.loads(raw)
        except (ValueError, json.JSONDecodeError) as e:
            raise CommandError(f"feed(base64)をデコードできません: {e}") from e
        self._validate_schema(feed)
        return feed

    def _load_feed(self, path: str) -> dict[str, Any]:
        try:
            with open(path, encoding="utf-8") as f:
                feed: dict[str, Any] = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise CommandError(f"供給JSONを読めません: {e}") from e
        self._validate_schema(feed)
        return feed

    @staticmethod
    def _validate_schema(feed: dict[str, Any]) -> None:
        if not isinstance(feed, dict) or feed.get("schema", "").split("/")[0] != "skilllogger-feed":
            raise CommandError("schema が skilllogger-feed ではありません")

    def _resolve_user(self, username: str | None) -> Any:
        if username:
            user = User.objects.filter(username=username).first()
            if user is None:
                raise CommandError(f"ユーザーが見つかりません: {username}")
            return user
        # --user 省略時は先頭の superuser（seed で作られる管理者）を取り込み先にする。
        user = User.objects.filter(is_superuser=True).order_by("pk").first()
        if user is None:
            raise CommandError("取り込み先ユーザーが存在しません（seed を実行してください）")
        return user
