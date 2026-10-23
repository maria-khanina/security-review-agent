terraform {
  required_version = ">= 1.5"
}

variable "vpc_id" {
  type = string
}

resource "aws_kms_key" "audit_key" {
  description = "audit_key"
  enable_key_rotation = true
  deletion_window_in_days = 30
}

resource "aws_msk_cluster" "audit_stream" {
  cluster_name = "audit_stream"
  kafka_version = "3.6.0"
  number_of_broker_nodes = 3
  encryption_info {
    encryption_at_rest_kms_key_arn = aws_kms_key.audit_key.arn
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster = true
    }
  }
}

resource "aws_s3_bucket" "audit_archive" {
  bucket = "meridian-audit-archive-prod"
}

resource "aws_s3_bucket_public_access_block" "audit_archive" {
  bucket = aws_s3_bucket.audit_archive.id
  block_public_acls = true
  block_public_policy = true
  ignore_public_acls = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "audit_archive" {
  bucket = aws_s3_bucket.audit_archive.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
      kms_master_key_id = aws_kms_key.audit_key.arn
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "audit_archive" {
  bucket = aws_s3_bucket.audit_archive.id
  rule {
    id = "expire"
    status = "Enabled"
    expiration {
      days = 400
    }
  }
}

resource "aws_cloudwatch_log_group" "pipeline_audit" {
  name = "/meridian/pipeline_audit"
  retention_in_days = 365
  kms_key_id = aws_kms_key.audit_key.arn
}

resource "aws_backup_vault" "audit_backups" {
  name = "audit_backups"
}

data "aws_iam_policy_document" "pipeline_policy" {
  statement {
    effect = "Allow"
    actions = ["kafka-cluster:ReadData", "s3:PutObject"]
    resources = ["arn:aws:kafka:eu-west-1:111122223333:topic/audit_stream/*"]
  }
}
