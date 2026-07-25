# =============================================================================
# CloudFront — CDN (フロントエンド + API ルーティング)
# =============================================================================
#
# Basic 認証について:
#   開発フェーズではドメイン未取得で *.cloudfront.net のデフォルトドメインを利用しており、
#   /api/* は将来的にアプリ層(Cognito等)で認証する想定のため、
#   CloudFront 層の Basic 認証は外している。
#   Basic 認証用 CloudFront Function はリソースだけ残置し、必要になったら
#   function_association を default_cache_behavior に復活させればよい。
resource "aws_cloudfront_function" "basic_auth" {
  name    = "${var.project_name}-basic-auth"
  runtime = "cloudfront-js-2.0"
  comment = "Basic authentication for SkillLogger (currently unused -- see header comment)"
  publish = true
  code    = <<-JS
    function handler(event) {
      var request = event.request;
      var headers = request.headers;
      var expected = "Basic ${base64encode("${var.basic_auth_user}:${var.basic_auth_pass}")}";
      if (
        typeof headers.authorization === "undefined" ||
        headers.authorization.value !== expected
      ) {
        return {
          statusCode: 401,
          statusDescription: "Unauthorized",
          headers: {
            "www-authenticate": { value: "Basic realm=\"SkillLogger\"" },
            "content-type": { value: "text/plain" },
          },
          body: "Unauthorized",
        };
      }
      return request;
    }
  JS
}

# S3 用 Origin Access Control
resource "aws_cloudfront_origin_access_control" "s3" {
  name                              = "${var.project_name}-s3-oac"
  description                       = "OAC for S3 frontend bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  comment             = "SkillLogger CDN"
  price_class         = "PriceClass_200"

  # ---------------------------------------------------------------------------
  # オリジン 1: S3（フロントエンド）
  # ---------------------------------------------------------------------------
  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "s3-frontend"
    origin_access_control_id = aws_cloudfront_origin_access_control.s3.id
  }

  # ---------------------------------------------------------------------------
  # オリジン 2: API Gateway（バックエンド）
  # ---------------------------------------------------------------------------
  origin {
    domain_name = replace(aws_apigatewayv2_api.main.api_endpoint, "https://", "")
    origin_id   = "api-gateway"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # ---------------------------------------------------------------------------
  # デフォルト: S3（React SPA）
  # ---------------------------------------------------------------------------
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "s3-frontend"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 86400
    max_ttl                = 31536000
    compress               = true
  }

  # ---------------------------------------------------------------------------
  # /api/* → API Gateway（キャッシュなし）
  # ---------------------------------------------------------------------------
  ordered_cache_behavior {
    path_pattern     = "/api/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "api-gateway"

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Content-Type", "Origin", "Accept"]
      cookies {
        forward = "all"
      }
    }

    viewer_protocol_policy = "https-only"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
    compress               = true
  }

  # ---------------------------------------------------------------------------
  # /admin/* → API Gateway（Django admin）
  #
  # Django 自身の認証で守られているので CloudFront 層の追加認証は外している。
  # 本番公開時には IP 制限 or Basic 認証を再導入することを検討。
  # ---------------------------------------------------------------------------
  ordered_cache_behavior {
    path_pattern     = "/admin/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "api-gateway"

    forwarded_values {
      query_string = true
      headers      = ["*"]
      cookies {
        forward = "all"
      }
    }

    viewer_protocol_policy = "https-only"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
  }

  # ---------------------------------------------------------------------------
  # SPA フォールバック（React Router 対応）
  # ---------------------------------------------------------------------------
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  # ---------------------------------------------------------------------------
  # 地域制限なし
  # ---------------------------------------------------------------------------
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # ---------------------------------------------------------------------------
  # デフォルト証明書（*.cloudfront.net）
  # ---------------------------------------------------------------------------
  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = { Name = "${var.project_name}-cloudfront" }
}
