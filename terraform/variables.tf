variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-1"
}

variable "aws_account_id" {
  description = "Target AWS account ID"
  type        = string
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "skilllogger"
}

# DB は EFS 上の SQLite（RDS 不使用）のため db_* 変数は不要。

variable "django_secret_key" {
  description = "Django SECRET_KEY"
  type        = string
  sensitive   = true
}

variable "s3_bucket_name" {
  description = "S3 bucket name for frontend"
  type        = string
  default     = "skilllogger-frontend"
}

# -----------------------------------------------------------------------------
# Cognito 認証（共通基盤 cognito-auth-service）
# -----------------------------------------------------------------------------
# 値は cognito-auth-service の `terraform output` から取得して tfvars に設定する。
# Pool ID / Client ID / domain prefix は公開情報だが、運用の一貫性のため tfvars で管理する。

variable "cognito_user_pool_id" {
  description = "Cognito User Pool ID（cognito-auth-service の user_pool_id）"
  type        = string
  default     = ""
}

variable "cognito_web_client_id" {
  description = "Cognito App Client ID（cognito-auth-service の skilllogger_web_client_id）"
  type        = string
  default     = ""
}

variable "cognito_domain_prefix" {
  description = "Cognito Hosted UI ドメイン prefix（cognito-auth-service の domain_prefix、例: auth）"
  type        = string
  default     = ""
}

variable "initial_admin_email" {
  description = "初期管理者メール（seed が m_user_allowed_emails に登録。締め出し防止。cognito-auth-service と一致させる）"
  type        = string
  sensitive   = true
  default     = ""
}

variable "basic_auth_user" {
  description = "Basic auth username for CloudFront"
  type        = string
  sensitive   = true
}

variable "basic_auth_pass" {
  description = "Basic auth password for CloudFront"
  type        = string
  sensitive   = true
}

# -----------------------------------------------------------------------------
# GitHub OIDC — GitHub Actions デプロイ用
# -----------------------------------------------------------------------------
# GitHub Actions が OIDC でデプロイ Role を AssumeRole する際、信頼ポリシーで
# 許可する対象リポジトリ (owner/repo)。表示・タグ用途。
variable "github_repository" {
  description = "GitHub repository allowed to assume the deploy role (owner/repo)"
  type        = string
  default     = "your-org/your-repo"
}

# 信頼ポリシーの sub 条件パターン。
# ⚠️ このリポジトリは組織/リポジトリの OIDC 設定で「immutable ID を subject claim に含める」が
# 有効なため、実際の sub は `repo:<owner>@<orgId>/<repo>@<repoId>:...` 形式になる。
# 通常の `repo:owner/repo:*` ではマッチしないため、実 ID を含むパターンを tfvars で注入する。
# ID はアカウント固有情報なのでコードにハードコードせず tfvars(gitignore) に置く。
# 実 sub は OIDC トークンの claim で確認する（例: repo:<owner>/<repo>:*）。
variable "github_deploy_subject_pattern" {
  description = "StringLike pattern for token.actions.githubusercontent.com:sub (supports immutable-ID subjects)"
  type        = string
  default     = "repo:your-org/your-repo:*"
}
