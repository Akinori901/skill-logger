# =============================================================================
# Lambda — API + Worker
# =============================================================================

# -----------------------------------------------------------------------------
# API Lambda（HTTP リクエスト処理）
# -----------------------------------------------------------------------------

resource "aws_lambda_function" "api" {
  function_name = "${var.project_name}-api"
  role          = aws_iam_role.lambda_execution.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.backend.repository_url}:latest"

  memory_size = 1536
  timeout     = 90

  # 同時実行の上限。1 だとフロントが画面ロード時に複数 API(engagements /
  # support-domains / auth/user)を並列で叩いた際にスロットリング(503)が発生する
  # ため 10 に設定する。SQLite への書き込み競合は production.py の busy_timeout(20s)
  # で直列化される（実質単一ユーザー運用のため書き込み競合の実害はほぼ無い）。
  reserved_concurrent_executions = 10

  image_config {
    command = ["config.asgi.handler"]
  }

  environment {
    variables = {
      DJANGO_SETTINGS_MODULE = "config.settings.production"
      SECRET_KEY             = var.django_secret_key
      ALLOWED_HOSTS          = "*"
      # DB は EFS 上の SQLite（/mnt/efs は access point のマウント先）。
      SQLITE_PATH = "/mnt/efs/db.sqlite3"
      # AI 申請文生成: プロバイダ既定エンドポイントを使うため空。
      # eval-proxy 等で上書きしたい場合のみ値を設定する。
      LLM_API_BASE_URL = ""
      # Cognito 認証（共通基盤 qol-user-pool）。未設定時は CognitoJWTAuthentication が
      # 常に None を返すため、値が揃うまで認証は無効（＝仮認証時代と同じく全通過ではなく 401）。
      COGNITO_USER_POOL_ID  = var.cognito_user_pool_id
      COGNITO_REGION        = var.aws_region
      COGNITO_WEB_CLIENT_ID = var.cognito_web_client_id
      COGNITO_DOMAIN_PREFIX = var.cognito_domain_prefix
      # seed が m_user_allowed_emails に登録する初期許可メール（締め出し防止）。
      INITIAL_ADMIN_EMAIL = var.initial_admin_email
    }
  }

  file_system_config {
    arn              = aws_efs_access_point.lambda.arn
    local_mount_path = "/mnt/efs"
  }

  vpc_config {
    subnet_ids         = [aws_subnet.private_a.id, aws_subnet.private_c.id]
    security_group_ids = [aws_security_group.lambda.id]
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy_attachment.lambda_vpc,
    aws_iam_role_policy.lambda_efs,
    aws_iam_role_policy.lambda_ssm_read,
    aws_cloudwatch_log_group.lambda_api,
    aws_efs_mount_target.private_a,
    aws_efs_mount_target.private_c,
  ]

  tags = { Name = "${var.project_name}-api-lambda" }
}

# -----------------------------------------------------------------------------
# Worker Lambda（管理コマンド: migrate, createcachetable, seed 等）
# -----------------------------------------------------------------------------

resource "aws_lambda_function" "worker" {
  function_name = "${var.project_name}-worker"
  role          = aws_iam_role.lambda_execution.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.backend.repository_url}:latest"

  memory_size = 2048
  timeout     = 900

  image_config {
    command = ["config.management_handler.handler"]
  }

  environment {
    variables = {
      DJANGO_SETTINGS_MODULE = "config.settings.production"
      SECRET_KEY             = var.django_secret_key
      ALLOWED_HOSTS          = "*"
      SQLITE_PATH            = "/mnt/efs/db.sqlite3"
      LLM_API_BASE_URL       = ""
      # Cognito（API Lambda と揃える）。Worker は seed で INITIAL_ADMIN_EMAIL を使う。
      COGNITO_USER_POOL_ID  = var.cognito_user_pool_id
      COGNITO_REGION        = var.aws_region
      COGNITO_WEB_CLIENT_ID = var.cognito_web_client_id
      COGNITO_DOMAIN_PREFIX = var.cognito_domain_prefix
      INITIAL_ADMIN_EMAIL   = var.initial_admin_email
    }
  }

  file_system_config {
    arn              = aws_efs_access_point.lambda.arn
    local_mount_path = "/mnt/efs"
  }

  vpc_config {
    subnet_ids         = [aws_subnet.private_a.id, aws_subnet.private_c.id]
    security_group_ids = [aws_security_group.lambda.id]
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy_attachment.lambda_vpc,
    aws_iam_role_policy.lambda_efs,
    aws_cloudwatch_log_group.lambda_worker,
    aws_efs_mount_target.private_a,
    aws_efs_mount_target.private_c,
  ]

  tags = { Name = "${var.project_name}-worker-lambda" }
}

# -----------------------------------------------------------------------------
# CloudWatch Log Groups
# -----------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "lambda_api" {
  name              = "/aws/lambda/${var.project_name}-api"
  retention_in_days = 14

  tags = { Name = "${var.project_name}-api-logs" }
}

resource "aws_cloudwatch_log_group" "lambda_worker" {
  name              = "/aws/lambda/${var.project_name}-worker"
  retention_in_days = 14

  tags = { Name = "${var.project_name}-worker-logs" }
}
