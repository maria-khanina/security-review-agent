"""Deterministic detectors that confirm planted flaws in Terraform files.

Each detector returns the addresses of offending resources, or an empty list.
They double as negative controls: they must stay silent on clean files.
"""

from collections.abc import Callable
import re

from secreview.datagen.settings import load_settings
from secreview.datagen.terraform_parse import (
    HclBlock,
    TerraformDocument,
    attribute_bool,
    attribute_int,
    attribute_strings,
    child_blocks,
    parse_terraform,
)

TerraformCheck = Callable[[TerraformDocument, str], list[str]]
PUBLIC_ACCESS_FLAGS = (
    "block_public_acls",
    "block_public_policy",
    "ignore_public_acls",
    "restrict_public_buckets",
)
TLS_VALUE = "TLS"
FORCE_SSL_PARAMETER = "rds.force_ssl"
FORCE_SSL_ON = "1"


def check_encryption_missing(document: TerraformDocument, text: str) -> list[str]:
    """Detect databases and buckets without encryption at rest."""
    addresses: list[str] = []
    for name, block in document.resources_of_type("aws_db_instance").items():
        if attribute_bool(block, "storage_encrypted") is not True:
            addresses.append(f"aws_db_instance.{name}")
    encrypted = document.resources_of_type(
        "aws_s3_bucket_server_side_encryption_configuration"
    )
    for name in document.resources_of_type("aws_s3_bucket"):
        if name not in encrypted:
            addresses.append(f"aws_s3_bucket.{name}")
    return addresses


def check_database_public(document: TerraformDocument, text: str) -> list[str]:
    """Detect databases with a public endpoint."""
    addresses: list[str] = []
    for name, block in document.resources_of_type("aws_db_instance").items():
        if attribute_bool(block, "publicly_accessible") is True:
            addresses.append(f"aws_db_instance.{name}")
    return addresses


def check_bucket_public(document: TerraformDocument, text: str) -> list[str]:
    """Detect buckets that do not block public access or have a public ACL."""
    blocks = document.resources_of_type("aws_s3_bucket_public_access_block")
    acls = document.resources_of_type("aws_s3_bucket_acl")
    addresses: list[str] = []
    for name in document.resources_of_type("aws_s3_bucket"):
        block = blocks.get(name)
        blocked = block is not None and all(
            attribute_bool(block, flag) is True for flag in PUBLIC_ACCESS_FLAGS
        )
        acl_is_public = name in acls and "public" in str(acls[name].get("acl"))
        if not blocked or acl_is_public:
            addresses.append(f"aws_s3_bucket.{name}")
    return addresses


def check_open_ingress(document: TerraformDocument, text: str) -> list[str]:
    """Detect security groups that accept traffic from every address."""
    public_cidr = load_settings().terraform.public_cidr
    addresses: list[str] = []
    for name, block in document.resources_of_type("aws_security_group").items():
        for rule in child_blocks(block, "ingress"):
            if public_cidr in attribute_strings(rule, "cidr_blocks"):
                addresses.append(f"aws_security_group.{name}")
    return addresses


def check_short_log_retention(document: TerraformDocument, text: str) -> list[str]:
    """Detect log groups retained for less than the audit requirement."""
    minimum = load_settings().terraform.minimum_audit_retention_days
    addresses: list[str] = []
    for name, block in document.resources_of_type("aws_cloudwatch_log_group").items():
        retention = attribute_int(block, "retention_in_days")
        if retention is None or retention < minimum:
            addresses.append(f"aws_cloudwatch_log_group.{name}")
    return addresses


def check_backup_unencrypted(document: TerraformDocument, text: str) -> list[str]:
    """Detect backup vaults without a customer-managed key."""
    addresses: list[str] = []
    for name, block in document.resources_of_type("aws_backup_vault").items():
        if "kms_key_arn" not in block:
            addresses.append(f"aws_backup_vault.{name}")
    return addresses


def database_requires_ssl(document: TerraformDocument, name: str) -> bool:
    """Tell whether a database's parameter group forces SSL."""
    groups = document.resources_of_type("aws_db_parameter_group")
    group = groups.get(f"{name}_params")
    if group is None:
        return False
    for parameter in child_blocks(group, "parameter"):
        if parameter.get("name") == FORCE_SSL_PARAMETER:
            return parameter.get("value") == FORCE_SSL_ON
    return False


def transit_encrypts_traffic(transit: HclBlock) -> bool:
    """Tell whether an in-transit block encrypts client and broker traffic."""
    uses_tls = transit.get("client_broker") == TLS_VALUE
    return uses_tls and transit.get("in_cluster") is True


def check_internal_tls_missing(document: TerraformDocument, text: str) -> list[str]:
    """Detect unencrypted connections to databases or Kafka clusters."""
    addresses: list[str] = []
    for name in document.resources_of_type("aws_db_instance"):
        if not database_requires_ssl(document, name):
            addresses.append(f"aws_db_instance.{name}")
    for name, block in document.resources_of_type("aws_msk_cluster").items():
        if not msk_requires_tls(block):
            addresses.append(f"aws_msk_cluster.{name}")
    return addresses


def msk_requires_tls(block: HclBlock) -> bool:
    """Tell whether a Kafka cluster block enforces encryption in transit."""
    for encryption in child_blocks(block, "encryption_info"):
        for transit in child_blocks(encryption, "encryption_in_transit"):
            return transit_encrypts_traffic(transit)
    return False


def check_bucket_without_lifecycle(document: TerraformDocument, text: str) -> list[str]:
    """Detect buckets whose objects never expire."""
    lifecycles = document.resources_of_type("aws_s3_bucket_lifecycle_configuration")
    addresses: list[str] = []
    for name in document.resources_of_type("aws_s3_bucket"):
        if name not in lifecycles:
            addresses.append(f"aws_s3_bucket.{name}")
    return addresses


def check_overbroad_iam(document: TerraformDocument, text: str) -> list[str]:
    """Detect IAM statements that use wildcard actions or resources."""
    wildcard = load_settings().terraform.overbroad_wildcard
    addresses: list[str] = []
    for (_, name), block in document.data_sources.items():
        for statement in child_blocks(block, "statement"):
            actions = attribute_strings(statement, "actions")
            resources = attribute_strings(statement, "resources")
            if wildcard in actions or wildcard in resources:
                addresses.append(f"data.aws_iam_policy_document.{name}")
    return addresses


def check_hardcoded_secret(document: TerraformDocument, text: str) -> list[str]:
    """Detect literal passwords and secret-looking strings."""
    addresses: list[str] = []
    for name, block in document.resources_of_type("aws_db_instance").items():
        if "password" in block:
            addresses.append(f"aws_db_instance.{name}")
    if re.search(load_settings().secret_pattern, text):
        addresses.append("literal")
    return addresses


TERRAFORM_CHECKS: dict[str, TerraformCheck] = {
    "terraform_encryption_missing": check_encryption_missing,
    "terraform_db_public": check_database_public,
    "terraform_bucket_public": check_bucket_public,
    "terraform_open_ingress": check_open_ingress,
    "terraform_log_retention_short": check_short_log_retention,
    "terraform_backup_unencrypted": check_backup_unencrypted,
    "terraform_internal_tls_missing": check_internal_tls_missing,
    "terraform_export_no_lifecycle": check_bucket_without_lifecycle,
    "terraform_overbroad_iam": check_overbroad_iam,
    "spec_hardcoded_secret": check_hardcoded_secret,
}


def run_terraform_check(check_name: str, text: str) -> list[str]:
    """Parse Terraform text and run one named detector against it."""
    return TERRAFORM_CHECKS[check_name](parse_terraform(text), text)
