"""支援領域マスタ（Expert 申請の12領域）を投入するコマンド。

Usage:
    python manage.py seed_support_domains
"""

from typing import Any

from django.core.management.base import BaseCommand

from apps.careers.infrastructure.models import SupportDomain

# Expert 申請フォームの支援領域（表示順）
SUPPORT_DOMAINS = [
    ("modernization", "モダナイゼーション"),
    ("in_house_dev", "システム内製化"),
    ("ai_adoption", "AI活用・導入"),
    ("data_platform", "データ基盤・分析"),
    ("security", "セキュリティ"),
    ("architecture", "アーキテクチャ"),
    ("cicd", "CI/CD・開発プロセス整備"),
    ("org_building", "開発組織の構築・強化"),
    ("hiring_training", "採用・育成"),
    ("tech_strategy", "技術戦略策定"),
    ("ai_new_business", "AI×新規事業"),
    ("other", "その他"),
]


class Command(BaseCommand):
    help = "支援領域マスタ（Expert 申請の12領域）を投入する"

    def handle(self, *args: Any, **options: Any) -> None:
        created = 0
        for order, (code, name) in enumerate(SUPPORT_DOMAINS):
            _, is_created = SupportDomain.objects.update_or_create(
                code=code,
                defaults={"name": name, "display_order": order},
            )
            if is_created:
                created += 1
        self.stdout.write(
            self.style.SUCCESS(f"  [support_domains] {len(SUPPORT_DOMAINS)}件（新規{created}件）を投入しました")
        )
