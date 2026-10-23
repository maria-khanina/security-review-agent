"""Typed descriptions of the cloud resources behind a Terraform documented service."""

from functools import cache
from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter
import yaml

from secreview.datagen.catalog import config_path, read_text


class KmsResource(BaseModel):
    kind: Literal["kms"]
    name: str


class RdsResource(BaseModel):
    kind: Literal["rds"]
    name: str
    key: str
    security_group: str
    holds: str
    encrypted: bool = True
    public: bool = False
    force_ssl: bool = True
    hardcoded_password: bool = False


class SecurityGroupResource(BaseModel):
    kind: Literal["sg"]
    name: str
    port: int
    cidr: str


class LogGroupResource(BaseModel):
    kind: Literal["loggroup"]
    name: str
    key: str
    retention: int


class BackupVaultResource(BaseModel):
    kind: Literal["backup_vault"]
    name: str
    key: str
    encrypted: bool = True


class IamPolicyResource(BaseModel):
    kind: Literal["iam"]
    name: str
    actions: list[str]
    resources: list[str]


class MskResource(BaseModel):
    kind: Literal["msk"]
    name: str
    key: str
    tls: bool = True


class S3Resource(BaseModel):
    kind: Literal["s3"]
    name: str
    key: str
    holds: str
    lifecycle_days: int
    encrypted: bool = True
    public: bool = False


TerraformResource = Annotated[
    KmsResource
    | RdsResource
    | SecurityGroupResource
    | LogGroupResource
    | BackupVaultResource
    | IamPolicyResource
    | MskResource
    | S3Resource,
    Field(discriminator="kind"),
]

ADDRESS_PREFIX: dict[str, str] = {
    "kms": "aws_kms_key",
    "rds": "aws_db_instance",
    "sg": "aws_security_group",
    "loggroup": "aws_cloudwatch_log_group",
    "backup_vault": "aws_backup_vault",
    "iam": "data.aws_iam_policy_document",
    "msk": "aws_msk_cluster",
    "s3": "aws_s3_bucket",
}


class TerraformTemplate(BaseModel):
    resources: list[TerraformResource]


@cache
def load_terraform_templates() -> dict[str, TerraformTemplate]:
    """Load the resource lists of every Terraform documented service."""
    text = read_text(config_path("documented_service_templates.yaml"))
    adapter = TypeAdapter(dict[str, TerraformTemplate])
    return adapter.validate_python(yaml.safe_load(text)["terraform"])


def default_resources(documented_service: str) -> list[TerraformResource]:
    """Return fresh, secure-by-default resources of an documented service."""
    resources: list[TerraformResource] = []
    for resource in load_terraform_templates()[documented_service].resources:
        resources.append(resource.model_copy(deep=True))
    return resources


def resource_address(resource: TerraformResource) -> str:
    """Return the Terraform address of a resource."""
    return f"{ADDRESS_PREFIX[resource.kind]}.{resource.name}"
