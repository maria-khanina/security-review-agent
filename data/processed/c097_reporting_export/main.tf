terraform {
  required_version = ">= 1.5"
}

variable "vpc_id" {
  type = string
}

resource "aws_kms_key" "export_key" {
  description = "export_key"
  enable_key_rotation = true
  deletion_window_in_days = 30
}

resource "aws_s3_bucket" "exports_bucket" {
  bucket = "meridian-exports-bucket-prod"
}

resource "aws_s3_bucket_public_access_block" "exports_bucket" {
  bucket = aws_s3_bucket.exports_bucket.id
  block_public_acls = true
  block_public_policy = true
  ignore_public_acls = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "exports_bucket" {
  bucket = aws_s3_bucket.exports_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
      kms_master_key_id = aws_kms_key.export_key.arn
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "exports_bucket" {
  bucket = aws_s3_bucket.exports_bucket.id
  rule {
    id = "expire"
    status = "Enabled"
    expiration {
      days = 7
    }
  }
}

resource "aws_db_instance" "reporting_ro_db" {
  identifier = "reporting_ro_db"
  engine = "postgres"
  instance_class = "db.m6g.large"
  allocated_storage = 100
  storage_encrypted = true
  kms_key_id = aws_kms_key.export_key.arn
  publicly_accessible = false
  db_subnet_group_name = "private-data"
  vpc_security_group_ids = [aws_security_group.reporting_sg.id]
  parameter_group_name = aws_db_parameter_group.reporting_ro_db_params.name
  backup_retention_period = 7
  manage_master_user_password = true
}

resource "aws_db_parameter_group" "reporting_ro_db_params" {
  name = "reporting_ro_db-params"
  family = "postgres15"
  parameter {
    name = "rds.force_ssl"
    value = "1"
  }
}

resource "aws_security_group" "reporting_sg" {
  name = "reporting_sg"
  vpc_id = var.vpc_id
  ingress {
    from_port = 5432
    to_port = 5432
    protocol = "tcp"
    cidr_blocks = ["10.0.16.0/24"]
  }
}

resource "aws_cloudwatch_log_group" "export_audit" {
  name = "/meridian/export_audit"
  retention_in_days = 365
  kms_key_id = aws_kms_key.export_key.arn
}

data "aws_iam_policy_document" "export_job_policy" {
  statement {
    effect = "Allow"
    actions = ["s3:PutObject", "rds-db:connect"]
    resources = ["arn:aws:s3:::meridian-exports-prod/*"]
  }
}
