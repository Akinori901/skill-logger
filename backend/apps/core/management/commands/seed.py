"""開発用初期データ投入コマンド。

Usage:
    python manage.py seed          # 管理者ユーザー + 支援領域マスタ
    python manage.py seed --admin  # 管理者ユーザーのみ

- 管理者ユーザー（admin/admin1234）は MVP 仮認証の固定ユーザー（DEV_FIXED_USER_ID）を兼ねる。
- 支援領域マスタ（Expert 申請の12領域）は careers の seed_support_domains に委譲する。
"""

from typing import Any

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandParser

User = get_user_model()

ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin1234"


class Command(BaseCommand):
    help = "開発用の初期データを投入する"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--admin", action="store_true", help="管理者ユーザーのみ作成")

    def handle(self, *args: Any, **options: Any) -> None:
        self._seed_admin()

        if not options["admin"]:
            call_command("seed_support_domains")

        self.stdout.write(self.style.SUCCESS("シード完了"))

    def _seed_admin(self) -> None:
        if User.objects.filter(username=ADMIN_USERNAME).exists():
            self.stdout.write(f"  [skip] ユーザー '{ADMIN_USERNAME}' は既に存在します")
            return

        User.objects.create_superuser(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
        )
        self.stdout.write(self.style.SUCCESS(f"  [created] 管理者ユーザー: {ADMIN_USERNAME} / {ADMIN_PASSWORD}"))
