"""Cognito ログイン許可 email を追加する管理コマンド。

同じ cognito-auth-service を使う別サービス（例: Publicity/dev-branding）から
案件レジストリ連携で SkillLogger API を叩く際、その利用者の email を
m_user_allowed_emails に登録してログイン(JIT プロビジョニング)を通すために使う。

本番では worker Lambda 経由で実行する:
    aws lambda invoke --function-name skilllogger-worker \\
      --payload '{"command": "add_allowed_email", "args": ["user@example.com", "--label", "dev-branding"]}' \\
      /tmp/resp.json

冪等（既に登録済みならスキップ）。
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandParser

User = get_user_model()


class Command(BaseCommand):
    help = "Cognito ログイン許可 email を追加する（案件レジストリ等の他サービス利用者向け）"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("email", type=str, help="許可する email アドレス")
        parser.add_argument(
            "--label",
            type=str,
            default="",
            help="許可 email のラベル（用途メモ。例: dev-branding）",
        )
        parser.add_argument(
            "--superuser",
            action="store_true",
            help="紐付けユーザーを superuser にする（既定は一般ユーザー・--link-to 未指定時のみ）",
        )
        parser.add_argument(
            "--link-to",
            type=str,
            default="",
            help=(
                "既存ユーザー(username か email)に紐付ける。同一人物が複数 email/identity "
                "(例: user@example.com と user@example.org)を持つとき、両 email を同じ "
                "auth_user に丸めて同じデータを見せるために使う。JIT は許可 email の user_id で "
                "ユーザーを解決するため、既存ユーザーに紐付ければその人の案件がそのまま見える。"
            ),
        )

    def handle(self, *args: object, **options: object) -> None:
        from apps.auth_cognito.infrastructure.models import UserAllowedEmail

        email = str(options["email"]).strip()
        label = str(options.get("label") or "")
        as_superuser = bool(options.get("superuser"))
        link_to = str(options.get("link_to") or "").strip()

        if not email:
            self.stderr.write("email が空です")
            return

        if link_to:
            # 既存ユーザーに紐付ける（新規ユーザーは作らない）。同一人物への丸め。
            user = (
                User.objects.filter(username=link_to).first()
                or User.objects.filter(email__iexact=link_to).first()
            )
            if user is None:
                self.stderr.write(f"--link-to のユーザー '{link_to}' が見つかりません")
                return
            self.stdout.write(f"[link] 既存ユーザー '{user.username}'(id={user.pk}) に紐付けます")
        else:
            # username=email のユーザーを用意（JIT と同じ規約）。Cognito ログイン専用で
            # パスワードは使わない。
            user = User.objects.filter(username=email).first()
            if user is None:
                if as_superuser:
                    user = User.objects.create_superuser(username=email, email=email)
                else:
                    user = User.objects.create_user(username=email, email=email)
                user.set_unusable_password()
                user.save(update_fields=["password"])
                self.stdout.write(self.style.SUCCESS(f"[created] ユーザー: {email}"))
            else:
                self.stdout.write(f"[skip] ユーザー '{email}' は既に存在します")

        if UserAllowedEmail.objects.filter(email__iexact=email).exists():
            self.stdout.write(f"[skip] 許可email '{email}' は既に登録済み")
            return

        UserAllowedEmail.objects.create(user=user, email=email, label=label)
        self.stdout.write(self.style.SUCCESS(f"[created] 許可email: {email} (label={label!r})"))
