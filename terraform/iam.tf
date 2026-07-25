# =============================================================================
# IAM — Lambda 実行ロール + GitHub Actions OIDC デプロイロール
# =============================================================================

# -----------------------------------------------------------------------------
# Lambda 実行ロール
# -----------------------------------------------------------------------------

resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-lambda-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = { Name = "${var.project_name}-lambda-role" }
}

# CloudWatch Logs 書き込み権限
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# VPC 内 ENI 管理権限
resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# SSM Parameter Store 読取権限（SECRET_KEY / DB パスワードの正本を参照する場合に使用）
resource "aws_iam_role_policy" "lambda_ssm_read" {
  name = "${var.project_name}-lambda-ssm-read"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadAppSecrets"
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
        ]
        Resource = [
          aws_ssm_parameter.django_secret_key.arn,
        ]
      },
      # SecureString の復号に必要（デフォルト alias/aws/ssm KMS キーを使用）
      {
        Sid      = "DecryptSsmSecureString"
        Effect   = "Allow"
        Action   = ["kms:Decrypt"]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = "ssm.${var.aws_region}.amazonaws.com"
          }
        }
      },
    ]
  })
}

# Lambda が EFS(SQLite) をマウント・読み書きするための権限
resource "aws_iam_role_policy" "lambda_efs" {
  name = "${var.project_name}-lambda-efs"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "EFSAccess"
        Effect = "Allow"
        Action = [
          "elasticfilesystem:ClientMount",
          "elasticfilesystem:ClientWrite",
        ]
        Resource = aws_efs_file_system.main.arn
      },
    ]
  })
}

# -----------------------------------------------------------------------------
# GitHub Actions OIDC Provider
# -----------------------------------------------------------------------------
# GitHub Actions が短命の OIDC トークンでこのアカウントの Role を AssumeRole する。
# 静的アクセスキーを GitHub Secrets に置かずに済む（キー漏洩リスクの排除）。
#
# thumbprint は GitHub OIDC の中間 CA。configure-aws-credentials@v4 以降は
# AWS 側が信頼チェーンを検証するため実質参照されないが、Provider 作成には必須。
# GitHub Actions OIDC Provider はアカウントに1つだけ（他アプリが作成済み）。
# 新規作成せず既存を参照する。
data "aws_iam_openid_connect_provider" "github" {
  arn = "arn:aws:iam::${var.aws_account_id}:oidc-provider/token.actions.githubusercontent.com"
}

# -----------------------------------------------------------------------------
# GitHub Actions デプロイ用 IAM Role（OIDC AssumeRole）
# -----------------------------------------------------------------------------

resource "aws_iam_role" "github_deploy" {
  name = "${var.project_name}-github-deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = data.aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          # 対象リポジトリのみに限定（全ブランチ許可: :* 部分）。
          # ⚠️ このリポは immutable ID を subject claim に含む設定のため、
          # 実 sub は `repo:<owner>@<orgId>/<repo>@<repoId>:...`。パターンは tfvars で注入。
          StringLike = {
            "token.actions.githubusercontent.com:sub" = var.github_deploy_subject_pattern
          }
        }
      }
    ]
  })

  tags = { Name = "${var.project_name}-github-deploy-role" }
}

resource "aws_iam_role_policy" "github_deploy" {
  name = "${var.project_name}-github-deploy"
  role = aws_iam_role.github_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ECRAuth"
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      },
      {
        Sid    = "ECRPush"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
        ]
        Resource = aws_ecr_repository.backend.arn
      },
      {
        Sid    = "LambdaUpdate"
        Effect = "Allow"
        Action = [
          "lambda:UpdateFunctionCode",
          "lambda:GetFunction",
          "lambda:GetFunctionConfiguration",
          "lambda:InvokeFunction",
        ]
        Resource = [
          aws_lambda_function.api.arn,
          aws_lambda_function.worker.arn,
        ]
      },
      {
        Sid    = "S3Deploy"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket",
        ]
        Resource = [
          aws_s3_bucket.frontend.arn,
          "${aws_s3_bucket.frontend.arn}/*",
        ]
      },
      {
        Sid    = "CloudFrontInvalidation"
        Effect = "Allow"
        Action = [
          "cloudfront:CreateInvalidation",
          "cloudfront:GetInvalidation",
        ]
        Resource = aws_cloudfront_distribution.main.arn
      },
    ]
  })
}
