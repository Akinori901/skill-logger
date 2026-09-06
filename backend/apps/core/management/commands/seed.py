"""開発用初期データ投入コマンド。

Usage:
    python manage.py seed          # 管理者ユーザー + 許可email + 支援領域マスタ
    python manage.py seed --admin  # 管理者ユーザー + 許可email のみ

- 管理者ユーザー（admin/admin1234）はローカル開発・admin 画面用。
- Cognito ログイン用の許可 email（m_user_allowed_emails）を初期登録する。
  env INITIAL_ADMIN_EMAIL（= cognito-auth-service の initial_admin_email）で指定した
  メールを、Cognito ログインする superuser に紐付ける。これがログイン締め出しを
  防ぐ第2の関門（第1は Cognito 側の初期ユーザー）。両方に登録されて初めて通る。
- 支援領域マスタ（Expert 申請の12領域）は careers の seed_support_domains に委譲する。
"""

from typing import Any

from django.conf import settings
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
        parser.add_argument("--admin", action="store_true", help="管理者ユーザー + 許可email のみ作成")

    def handle(self, *args: Any, **options: Any) -> None:
        self._seed_admin()
        self._seed_initial_allowed_email()

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

    def _seed_initial_allowed_email(self) -> None:
        """Cognito ログイン用の初期許可 email を登録する（締め出し防止）。

        INITIAL_ADMIN_EMAIL の superuser を用意し、そのメールを
        m_user_allowed_emails に登録する。JIT がこのメールを照合してログインを通す。
        """
        from apps.auth_cognito.infrastructure.models import UserAllowedEmail

        email = getattr(settings, "INITIAL_ADMIN_EMAIL", "")
        if not email:
            self.stdout.write("  [skip] INITIAL_ADMIN_EMAIL 未設定のため許可email初期登録をスキップ")
            return

        # このメールを主に持つ superuser を用意（username=email）。
        user = User.objects.filter(username=email).first()
        if user is None:
            user = User.objects.create_superuser(username=email, email=email)
            # Cognito ログイン専用なのでパスワードは使わない。
            user.set_unusable_password()
            user.save(update_fields=["password"])
            self.stdout.write(self.style.SUCCESS(f"  [created] Cognito 管理者ユーザー: {email}"))
        else:
            self.stdout.write(f"  [skip] ユーザー '{email}' は既に存在します")

        if UserAllowedEmail.objects.filter(email__iexact=email).exists():
            self.stdout.write(f"  [skip] 許可email '{email}' は既に登録済み")
            return

        UserAllowedEmail.objects.create(user=user, email=email, label="初期管理者")
        self.stdout.write(self.style.SUCCESS(f"  [created] 許可email: {email}"))
