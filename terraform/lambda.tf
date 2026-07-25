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

  # SQLite への書き込み競合を根本的に排除するため同時実行を 1 に制限する
  # （実質単一ユーザー運用のため実害はほぼ無い）。
  reserved_concurrent_executions = 1

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
      # 認証は現状「仮認証(DevFixedUserAuthentication)」のため Cognito 系は不要。
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
