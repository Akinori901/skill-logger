output "cloudfront_domain" {
  description = "CloudFront distribution domain name (the public URL)"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (for cache invalidation) -- GitHub Secret: CLOUDFRONT_DISTRIBUTION_ID"
  value       = aws_cloudfront_distribution.main.id
}

output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = aws_apigatewayv2_api.main.api_endpoint
}

output "ecr_repository_url" {
  description = "ECR repository URL -- GitHub Secret: ECR_REPOSITORY (repository name portion)"
  value       = aws_ecr_repository.backend.repository_url
}

output "s3_bucket_name" {
  description = "S3 bucket name -- GitHub Secret: S3_BUCKET"
  value       = aws_s3_bucket.frontend.bucket
}

output "lambda_api_function_name" {
  description = "API Lambda function name -- GitHub Secret: LAMBDA_FUNCTION_NAME"
  value       = aws_lambda_function.api.function_name
}

output "lambda_worker_function_name" {
  description = "Worker Lambda function name -- GitHub Secret: LAMBDA_WORKER_NAME"
  value       = aws_lambda_function.worker.function_name
}

output "oidc_deploy_role_arn" {
  description = "IAM Role ARN assumed by GitHub Actions via OIDC -- GitHub Secret: AWS_DEPLOY_ROLE_ARN"
  value       = aws_iam_role.github_deploy.arn
}
