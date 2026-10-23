"""Format-independent entry points to generated implementation artifacts.

A case describes its implementation either as an OpenAPI document or as a
Terraform file. This module hides that difference from the case planner,
the case writer and the validators.
"""

from secreview.datagen.models import Case
from secreview.datagen.openapi_build import build_openapi_document
from secreview.datagen.openapi_checks import OPENAPI_CHECKS, run_openapi_check
from secreview.datagen.openapi_io import document_to_yaml, parse_document_text
from secreview.datagen.openapi_mutations import (
    OPENAPI_MUTATIONS,
    apply_openapi_mutation,
)
from secreview.datagen.settings import load_settings
from secreview.datagen.terraform_checks import TERRAFORM_CHECKS, run_terraform_check
from secreview.datagen.terraform_mutations import (
    TERRAFORM_MUTATIONS,
    apply_terraform_mutation,
    is_mutation_applicable,
)
from secreview.datagen.terraform_render import render_terraform
from secreview.datagen.terraform_specs import default_resources

OPENAPI_FORMAT = "openapi"
OPENAPI_FILE_NAME = "impl.yaml"
TERRAFORM_FILE_NAME = "main.tf"


def implementation_file_name(implementation_format: str) -> str:
    """Return the file name that stores an implementation of a format."""
    if implementation_format == OPENAPI_FORMAT:
        return OPENAPI_FILE_NAME
    return TERRAFORM_FILE_NAME


def is_mutation_available(
    implementation_format: str,
    documented_service: str,
    mutation_name: str,
) -> bool:
    """Tell whether a mutation can be applied to an documented service's artifact."""
    if implementation_format == OPENAPI_FORMAT:
        return mutation_name in OPENAPI_MUTATIONS
    if mutation_name not in TERRAFORM_MUTATIONS:
        return False
    return is_mutation_applicable(documented_service, mutation_name)


def conflict_group(mutation_name: str) -> str:
    """Return the group of mutations that cannot be planted together."""
    return load_settings().mutation_conflict_groups.get(mutation_name, mutation_name)


def build_openapi_text(case: Case) -> str:
    """Build the OpenAPI document of a case with its planted mutations."""
    document = build_openapi_document(case.documented_service)
    for flaw in case.flaws:
        if flaw.implementation_mutation:
            document, flaw.implementation_anchor = apply_openapi_mutation(
                document,
                flaw.implementation_mutation,
                case.documented_service,
            )
    return document_to_yaml(document)


def build_terraform_text(case: Case) -> str:
    """Build the Terraform file of a case with its planted mutations."""
    resources = default_resources(case.documented_service)
    for flaw in case.flaws:
        if flaw.implementation_mutation:
            resources, flaw.implementation_anchor = apply_terraform_mutation(
                resources,
                flaw.implementation_mutation,
            )
    return render_terraform(resources)


def build_implementation_text(case: Case) -> str:
    """Build the implementation artifact of a case in its format."""
    if case.implementation_format == OPENAPI_FORMAT:
        return build_openapi_text(case)
    return build_terraform_text(case)


def available_check_names(implementation_format: str) -> list[str]:
    """List all detectors that exist for an implementation format."""
    if implementation_format == OPENAPI_FORMAT:
        return list(OPENAPI_CHECKS)
    return list(TERRAFORM_CHECKS)


def run_implementation_check(
    implementation_format: str,
    check_name: str,
    text: str,
) -> list[str]:
    """Run one detector against the text of an implementation artifact."""
    if implementation_format == OPENAPI_FORMAT:
        return run_openapi_check(check_name, parse_document_text(text))
    return run_terraform_check(check_name, text)
