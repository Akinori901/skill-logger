variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-1"
}

variable "aws_account_id" {
  description = "Target AWS account ID (personal products account: fvc / money-pilot と同一)"
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
  default     = "Akinori901/SkillLogger"
}

# 信頼ポリシーの sub 条件パターン。
# ⚠️ このリポジトリは組織/リポジトリの OIDC 設定で「immutable ID を subject claim に含める」が
# 有効なため、実際の sub は `repo:<owner>@<orgId>/<repo>@<repoId>:...` 形式になる。
# 通常の `repo:owner/repo:*` ではマッチしないため、実 ID を含むパターンを tfvars で注入する。
# ID はアカウント固有情報なのでコードにハードコードせず tfvars(gitignore) に置く。
# 実 sub は OIDC トークンの claim で確認する（例: repo:Akinori901@80678496/SkillLogger@1310786215:*）。
variable "github_deploy_subject_pattern" {
  description = "StringLike pattern for token.actions.githubusercontent.com:sub (supports immutable-ID subjects)"
  type        = string
  default     = "repo:Akinori901/SkillLogger:*"
}
