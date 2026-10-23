terraform {
  required_version = ">= 1.5"
}

variable "vpc_id" {
  type = string
}

resource "aws_kms_key" "vault_key" {
  description = "vault_key"
  enable_key_rotation = true
  deletion_window_in_days = 30
}

resource "aws_db_instance" "vault_db" {
  identifier = "vault_db"
  engine = "postgres"
  instance_class = "db.m6g.large"
  allocated_storage = 100
  storage_encrypted = true
  kms_key_id = aws_kms_key.vault_key.arn
  publicly_accessible = true
  db_subnet_group_name = "private-data"
  vpc_security_group_ids = [aws_security_group.vault_db_sg.id]
  parameter_group_name = aws_db_parameter_group.vault_db_params.name
  backup_retention_period = 7
  manage_master_user_password = true
}

resource "aws_db_parameter_group" "vault_db_params" {
  name = "vault_db-params"
  family = "postgres15"
  parameter {
    name = "rds.force_ssl"
    value = "1"
  }
}

resource "aws_security_group" "vault_db_sg" {
  name = "vault_db_sg"
  vpc_id = var.vpc_id
  ingress {
    from_port = 5432
    to_port = 5432
    protocol = "tcp"
    cidr_blocks = ["10.0.8.0/24"]
  }
}

resource "aws_cloudwatch_log_group" "vault_audit" {
  name = "/meridian/vault_audit"
  retention_in_days = 365
  kms_key_id = aws_kms_key.vault_key.arn
}

resource "aws_backup_vault" "vault_backups" {
  name = "vault_backups"
  kms_key_arn = aws_kms_key.vault_key.arn
}

data "aws_iam_policy_document" "vault_service_policy" {
  statement {
    effect = "Allow"
    actions = ["rds-db:connect"]
    resources = ["arn:aws:rds-db:eu-west-1:111122223333:dbuser:*/vault_app"]
  }
}
