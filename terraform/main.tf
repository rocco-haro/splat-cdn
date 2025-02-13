terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = "us-west-2"  # or your preferred region
}

# S3 bucket for splat data
resource "aws_s3_bucket" "splat_data" {
  bucket = "splat-prototype-data"
}

resource "aws_s3_bucket_public_access_block" "splat_data" {
  bucket = aws_s3_bucket.splat_data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudFront distributions
resource "aws_cloudfront_distribution" "single_tier" {
  enabled = true
  
  origin {
    domain_name = aws_s3_bucket.splat_data.bucket_regional_domain_name
    origin_id   = "S3Origin"
    
    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.oai.cloudfront_access_identity_path
    }
  }
  
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3Origin"
    viewer_protocol_policy = "https-only"
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }
  
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

resource "aws_cloudfront_distribution" "two_tier" {
  # Similar to single_tier but with regional edge caches enabled
  enabled = true
  
  origin {
    domain_name = aws_s3_bucket.splat_data.bucket_regional_domain_name
    origin_id   = "S3Origin"
    
    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.oai.cloudfront_access_identity_path
    }
  }
  
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3Origin"
    viewer_protocol_policy = "https-only"
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }
  
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

# CloudFront OAI
resource "aws_cloudfront_origin_access_identity" "oai" {
  comment = "OAI for splat prototype"
}

# Lambda function
resource "aws_lambda_function" "api" {
  filename         = "../lambda-service/function.zip"  # Need to zip lambda code first
  function_name    = "splat-service"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.9"
  
  environment {
    variables = {
      SINGLE_TIER_DISTRIBUTION_ID = aws_cloudfront_distribution.single_tier.id
      TWO_TIER_DISTRIBUTION_ID    = aws_cloudfront_distribution.two_tier.id
      S3_BUCKET                   = aws_s3_bucket.splat_data.id
    }
  }
}

# Basic Lambda role
resource "aws_iam_role" "lambda_role" {
  name = "splat_lambda_role"

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
}

# Output important values
output "single_tier_domain" {
  value = aws_cloudfront_distribution.single_tier.domain_name
}

output "two_tier_domain" {
  value = aws_cloudfront_distribution.two_tier.domain_name
}

output "bucket_name" {
  value = aws_s3_bucket.splat_data.id
}

output "lambda_function_name" {
  value = aws_lambda_function.api.function_name
}