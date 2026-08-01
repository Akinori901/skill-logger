provider "aws" {
  region = var.aws_region

  # デプロイ先 AWS アカウントを固定する。
  # 誤ったアカウントへの apply を防ぐ。
  allowed_account_ids = [var.aws_account_id]

  default_tags {
    tags = {
      Project     = "skilllogger"
      Environment = "production"
      ManagedBy   = "terraform"
    }
  }
}
