"""Mutations that inject known security flaws into Terraform resource resources.

Each mutation edits the resource resources in place and returns the Terraform
address of the changed resource, which becomes the flaw's implementation
anchor. A mutation raises LookupError when the documented service lacks its target.
"""

from collections.abc import Callable
import copy
from typing import TypeVar

from secreview.datagen.settings import load_settings
from secreview.datagen.terraform_specs import (
    BackupVaultResource,
    IamPolicyResource,
    LogGroupResource,
    MskResource,
    RdsResource,
    S3Resource,
    SecurityGroupResource,
    TerraformResource,
    default_resources,
    resource_address,
)

ResourceType = TypeVar("ResourceType")
TerraformMutation = Callable[[list[TerraformResource]], str]


def find_resource(
    resources: list[TerraformResource],
    resource_type: type[ResourceType],
) -> ResourceType:
    """Return the first resource resource of the requested type."""
    for resource in resources:
        if isinstance(resource, resource_type):
            return resource
    raise LookupError(resource_type.__name__)


def disable_encryption(resources: list[TerraformResource]) -> str:
    """Turn off encryption at rest on a resource that holds sensitive data."""
    for resource in resources:
        if isinstance(resource, (RdsResource, S3Resource)):
            resource.encrypted = False
            return resource_address(resource)
    raise LookupError("encryptable resource")


def make_database_public(resources: list[TerraformResource]) -> str:
    """Give the database instance a public endpoint."""
    database = find_resource(resources, RdsResource)
    database.public = True
    return resource_address(database)


def make_bucket_public(resources: list[TerraformResource]) -> str:
    """Make the bucket publicly readable."""
    bucket = find_resource(resources, S3Resource)
    bucket.public = True
    return resource_address(bucket)


def open_ingress_to_world(resources: list[TerraformResource]) -> str:
    """Open the security group to every address."""
    group = find_resource(resources, SecurityGroupResource)
    group.cidr = load_settings().terraform.public_cidr
    return resource_address(group)


def shorten_log_retention(resources: list[TerraformResource]) -> str:
    """Cut the log retention period below the audit requirement."""
    log_group = find_resource(resources, LogGroupResource)
    log_group.retention = load_settings().terraform.short_retention_days
    return resource_address(log_group)


def disable_backup_encryption(resources: list[TerraformResource]) -> str:
    """Remove the encryption key from the backup vault."""
    vault = find_resource(resources, BackupVaultResource)
    vault.encrypted = False
    return resource_address(vault)


def disable_internal_tls(resources: list[TerraformResource]) -> str:
    """Allow unencrypted connections to the broker or the database."""
    for resource in resources:
        if isinstance(resource, MskResource):
            resource.tls = False
            return resource_address(resource)
    database = find_resource(resources, RdsResource)
    database.force_ssl = False
    return resource_address(database)


def remove_bucket_lifecycle(resources: list[TerraformResource]) -> str:
    """Drop the expiration rule so exported files never expire."""
    bucket = find_resource(resources, S3Resource)
    bucket.lifecycle_days = 0
    return resource_address(bucket)


def widen_iam_policy(resources: list[TerraformResource]) -> str:
    """Replace the IAM statement with wildcard actions and resources."""
    wildcard = load_settings().terraform.overbroad_wildcard
    policy = find_resource(resources, IamPolicyResource)
    policy.actions = [wildcard]
    policy.resources = [wildcard]
    return resource_address(policy)


def hardcode_database_password(resources: list[TerraformResource]) -> str:
    """Write the database master password as a literal."""
    database = find_resource(resources, RdsResource)
    database.hardcoded_password = True
    return resource_address(database)


TERRAFORM_MUTATIONS: dict[str, TerraformMutation] = {
    "terraform_encryption_missing": disable_encryption,
    "terraform_db_public": make_database_public,
    "terraform_bucket_public": make_bucket_public,
    "terraform_open_ingress": open_ingress_to_world,
    "terraform_log_retention_short": shorten_log_retention,
    "terraform_backup_unencrypted": disable_backup_encryption,
    "terraform_internal_tls_missing": disable_internal_tls,
    "terraform_export_no_lifecycle": remove_bucket_lifecycle,
    "terraform_overbroad_iam": widen_iam_policy,
    "spec_hardcoded_secret": hardcode_database_password,
}


def is_mutation_applicable(documented_service: str, mutation_name: str) -> bool:
    """Tell whether an documented service has the resource a mutation targets."""
    try:
        TERRAFORM_MUTATIONS[mutation_name](default_resources(documented_service))
    except LookupError:
        return False
    return True


def apply_terraform_mutation(
    resources: list[TerraformResource],
    mutation_name: str,
) -> tuple[list[TerraformResource], str]:
    """Return mutated copies of the resource resources and the flaw anchor."""
    mutated = copy.deepcopy(resources)
    anchor = TERRAFORM_MUTATIONS[mutation_name](mutated)
    return mutated, anchor
