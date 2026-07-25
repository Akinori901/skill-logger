# =============================================================================
# SSM Parameter Store — アプリケーションシークレット
# =============================================================================
#
# Django SECRET_KEY と DB パスワードを SecureString で保管する。
# Lambda 環境変数へは terraform で直接注入するが、シークレットの正本を
# Parameter Store にも保持しておき、ローテーションや他ツールからの参照に備える。
#
# 値の運用ポリシー:
#   - SECRET_KEY / DB password は terraform.tfvars から渡す（state には暗号化されて残る）
#   - value 差分は lifecycle.ignore_changes = [value] で以降無視し、
#     ローテーションは AWS Console / CLI から行う想定
# -----------------------------------------------------------------------------

resource "aws_ssm_parameter" "django_secret_key" {
  name        = "/${var.project_name}/production/django/secret-key"
  description = "Django SECRET_KEY (SecureString)"
  type        = "SecureString"
  value       = var.django_secret_key
  tier        = "Standard"

  tags = {
    Name    = "${var.project_name}-django-secret-key"
    Purpose = "app-secret"
  }

  lifecycle {
    ignore_changes = [value]
  }
}

# DB は EFS 上の SQLite（RDS 不使用）のため DB パスワードの SSM は不要。
