terraform {
  required_version = ">= 1.5"
}

variable "vpc_id" {
  type = string
}

resource "aws_kms_key" "scoring_key" {
  description = "scoring_key"
  enable_key_rotation = true
  deletion_window_in_days = 30
}

resource "aws_msk_cluster" "payment_events" {
  cluster_name = "payment_events"
  kafka_version = "3.6.0"
  number_of_broker_nodes = 3
  encryption_info {
    encryption_at_rest_kms_key_arn = aws_kms_key.scoring_key.arn
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster = true
    }
  }
}

resource "aws_db_instance" "decisions_db" {
  identifier = "decisions_db"
  engine = "postgres"
  instance_class = "db.m6g.large"
  allocated_storage = 100
  storage_encrypted = true
  kms_key_id = aws_kms_key.scoring_key.arn
  publicly_accessible = false
  db_subnet_group_name = "private-data"
  vpc_security_group_ids = [aws_security_group.decisions_sg.id]
  parameter_group_name = aws_db_parameter_group.decisions_db_params.name
  backup_retention_period = 7
  manage_master_user_password = true
}

resource "aws_db_parameter_group" "decisions_db_params" {
  name = "decisions_db-params"
  family = "postgres15"
  parameter {
    name = "rds.force_ssl"
    value = "1"
  }
}

resource "aws_security_group" "decisions_sg" {
  name = "decisions_sg"
  vpc_id = var.vpc_id
  ingress {
    from_port = 5432
    to_port = 5432
    protocol = "tcp"
    cidr_blocks = ["10.0.12.0/24"]
  }
}

resource "aws_cloudwatch_log_group" "scoring_audit" {
  name = "/meridian/scoring_audit"
  retention_in_days = 365
  kms_key_id = aws_kms_key.scoring_key.arn
}

data "aws_iam_policy_document" "scoring_policy" {
  statement {
    effect = "Allow"
    actions = ["*"]
    resources = ["*"]
  }
}
