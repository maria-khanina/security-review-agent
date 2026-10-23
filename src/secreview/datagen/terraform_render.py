"""Renders typed resources into Terraform HCL text."""

from collections.abc import Callable
from functools import singledispatch

from secreview.datagen.settings import load_settings
from secreview.datagen.terraform_specs import (
    BackupVaultResource,
    IamPolicyResource,
    KmsResource,
    LogGroupResource,
    MskResource,
    RdsResource,
    S3Resource,
    SecurityGroupResource,
    TerraformResource,
)

DOUBLE_QUOTE = '"'


@singledispatch
def render_resource(resource: object) -> str:
    """Render any supported Terraform resource."""
    raise TypeError(type(resource).__name__)


def quote_list(values: list[str]) -> str:
    """Format strings as an HCL list literal body."""
    return ", ".join(DOUBLE_QUOTE + value + DOUBLE_QUOTE for value in values)


def lower_bool(flag: bool) -> str:
    """Format a boolean the way HCL spells it."""
    return str(flag).lower()


def key_reference(key: str) -> str:
    """Reference the ARN of a KMS key resource."""
    return f"aws_kms_key.{key}.arn"


@render_resource.register
def render_kms(resource: KmsResource) -> str:
    """Render a KMS key with rotation enabled."""
    window = load_settings().terraform.key_deletion_window_days
    return (
        f'resource "aws_kms_key" "{resource.name}" {{\n'
        f'  description = "{resource.name}"\n'
        "  enable_key_rotation = true\n"
        f"  deletion_window_in_days = {window}\n"
        "}\n"
    )


def render_rds_instance(resource: RdsResource) -> str:
    """Render the database instance block."""
    settings = load_settings().terraform
    lines: list[str] = [
        f'resource "aws_db_instance" "{resource.name}" {{',
        f'  identifier = "{resource.name}"',
        f'  engine = "{settings.engine}"',
        f'  instance_class = "{settings.instance_class}"',
        f"  allocated_storage = {settings.allocated_storage}",
        f"  storage_encrypted = {lower_bool(resource.encrypted)}",
    ]
    if resource.encrypted:
        lines.append(f"  kms_key_id = {key_reference(resource.key)}")
    lines += render_rds_network_lines(resource)
    lines.append(render_rds_password_line(resource))
    lines.append("}\n")
    return "\n".join(lines)


def render_rds_network_lines(resource: RdsResource) -> list[str]:
    """Render accessibility, subnet, security group and backup attributes."""
    settings = load_settings().terraform
    return [
        f"  publicly_accessible = {lower_bool(resource.public)}",
        f'  db_subnet_group_name = "{settings.subnet_group}"',
        f"  vpc_security_group_ids = [aws_security_group.{resource.security_group}.id]",
        f"  parameter_group_name = aws_db_parameter_group.{resource.name}_params.name",
        f"  backup_retention_period = {settings.backup_retention_period}",
    ]


def render_rds_password_line(resource: RdsResource) -> str:
    """Render either a managed or a literal master password."""
    if resource.hardcoded_password:
        return f'  password = "{load_settings().terraform.hardcoded_password}"'
    return "  manage_master_user_password = true"


def render_parameter_group(resource: RdsResource) -> str:
    """Render the parameter group that controls forced TLS."""
    family = load_settings().terraform.parameter_group_family
    force_ssl = "1" if resource.force_ssl else "0"
    return (
        f'resource "aws_db_parameter_group" "{resource.name}_params" {{\n'
        f'  name = "{resource.name}-params"\n'
        f'  family = "{family}"\n'
        "  parameter {\n"
        '    name = "rds.force_ssl"\n'
        f'    value = "{force_ssl}"\n'
        "  }\n"
        "}\n"
    )


@render_resource.register
def render_rds(resource: RdsResource) -> str:
    """Render a database instance together with its parameter group."""
    return render_rds_instance(resource) + "\n" + render_parameter_group(resource)


@render_resource.register
def render_security_group(resource: SecurityGroupResource) -> str:
    """Render a security group with one ingress rule."""
    return (
        f'resource "aws_security_group" "{resource.name}" {{\n'
        f'  name = "{resource.name}"\n'
        "  vpc_id = var.vpc_id\n"
        "  ingress {\n"
        f"    from_port = {resource.port}\n"
        f"    to_port = {resource.port}\n"
        '    protocol = "tcp"\n'
        f'    cidr_blocks = ["{resource.cidr}"]\n'
        "  }\n"
        "}\n"
    )


@render_resource.register
def render_log_group(resource: LogGroupResource) -> str:
    """Render an encrypted log group with a retention period."""
    return (
        f'resource "aws_cloudwatch_log_group" "{resource.name}" {{\n'
        f'  name = "/meridian/{resource.name}"\n'
        f"  retention_in_days = {resource.retention}\n"
        f"  kms_key_id = {key_reference(resource.key)}\n"
        "}\n"
    )


@render_resource.register
def render_backup_vault(resource: BackupVaultResource) -> str:
    """Render a backup vault, encrypted unless the resource says otherwise."""
    key_line = ""
    if resource.encrypted:
        key_line = f"  kms_key_arn = {key_reference(resource.key)}\n"
    return (
        f'resource "aws_backup_vault" "{resource.name}" {{\n'
        f'  name = "{resource.name}"\n'
        f"{key_line}"
        "}\n"
    )


@render_resource.register
def render_iam_policy(resource: IamPolicyResource) -> str:
    """Render an IAM policy document with a single allow statement."""
    return (
        f'data "aws_iam_policy_document" "{resource.name}" {{\n'
        "  statement {\n"
        '    effect = "Allow"\n'
        f"    actions = [{quote_list(resource.actions)}]\n"
        f"    resources = [{quote_list(resource.resources)}]\n"
        "  }\n"
        "}\n"
    )


@render_resource.register
def render_msk_cluster(resource: MskResource) -> str:
    """Render a Kafka cluster with encryption in transit settings."""
    settings = load_settings().terraform
    client_broker = "TLS" if resource.tls else "PLAINTEXT"
    return (
        f'resource "aws_msk_cluster" "{resource.name}" {{\n'
        f'  cluster_name = "{resource.name}"\n'
        f'  kafka_version = "{settings.kafka_version}"\n'
        f"  number_of_broker_nodes = {settings.broker_node_count}\n"
        "  encryption_info {\n"
        f"    encryption_at_rest_kms_key_arn = {key_reference(resource.key)}\n"
        "    encryption_in_transit {\n"
        f'      client_broker = "{client_broker}"\n'
        f"      in_cluster = {lower_bool(resource.tls)}\n"
        "    }\n"
        "  }\n"
        "}\n"
    )


def render_bucket_access_block(resource: S3Resource) -> str:
    """Render the public access block, relaxed when the bucket is public."""
    flag = lower_bool(not resource.public)
    return (
        f'resource "aws_s3_bucket_public_access_block" "{resource.name}" {{\n'
        f"  bucket = aws_s3_bucket.{resource.name}.id\n"
        f"  block_public_acls = {flag}\n"
        f"  block_public_policy = {flag}\n"
        f"  ignore_public_acls = {flag}\n"
        f"  restrict_public_buckets = {flag}\n"
        "}\n"
    )


def render_bucket_encryption(resource: S3Resource) -> str:
    """Render server-side encryption with a customer-managed key."""
    return (
        "resource "
        f'"aws_s3_bucket_server_side_encryption_configuration" "{resource.name}" {{\n'
        f"  bucket = aws_s3_bucket.{resource.name}.id\n"
        "  rule {\n"
        "    apply_server_side_encryption_by_default {\n"
        '      sse_algorithm = "aws:kms"\n'
        f"      kms_master_key_id = {key_reference(resource.key)}\n"
        "    }\n"
        "  }\n"
        "}\n"
    )


def render_bucket_lifecycle(resource: S3Resource) -> str:
    """Render an expiration rule for the bucket objects."""
    return (
        f'resource "aws_s3_bucket_lifecycle_configuration" "{resource.name}" {{\n'
        f"  bucket = aws_s3_bucket.{resource.name}.id\n"
        "  rule {\n"
        '    id = "expire"\n'
        '    status = "Enabled"\n'
        "    expiration {\n"
        f"      days = {resource.lifecycle_days}\n"
        "    }\n"
        "  }\n"
        "}\n"
    )


def render_bucket_acl(resource: S3Resource) -> str:
    """Render a public-read ACL for a bucket that is made public."""
    return (
        f'resource "aws_s3_bucket_acl" "{resource.name}" {{\n'
        f"  bucket = aws_s3_bucket.{resource.name}.id\n"
        '  acl = "public-read"\n'
        "}\n"
    )


@render_resource.register
def render_s3_bucket(resource: S3Resource) -> str:
    """Render a bucket with its access, encryption and lifecycle resources."""
    settings = load_settings().terraform
    name = resource.name.replace("_", "-")
    bucket = f"{settings.bucket_prefix}-{name}-{settings.bucket_suffix}"
    parts: list[str] = [
        f'resource "aws_s3_bucket" "{resource.name}" {{\n  bucket = "{bucket}"\n}}\n',
        render_bucket_access_block(resource),
    ]
    optional_parts: list[tuple[bool, Callable[[S3Resource], str]]] = [
        (resource.public, render_bucket_acl),
        (resource.encrypted, render_bucket_encryption),
        (resource.lifecycle_days > 0, render_bucket_lifecycle),
    ]
    for enabled, renderer in optional_parts:
        if enabled:
            parts.append(renderer(resource))
    return "\n".join(parts)


def render_terraform(resources: list[TerraformResource]) -> str:
    """Render a complete Terraform file for a list of resource resources."""
    version = load_settings().terraform.required_version
    header = (
        "terraform {\n"
        f'  required_version = "{version}"\n'
        "}\n\n"
        'variable "vpc_id" {\n'
        "  type = string\n"
        "}\n"
    )
    bodies: list[str] = [render_resource(resource) for resource in resources]
    return header + "\n" + "\n".join(bodies)
