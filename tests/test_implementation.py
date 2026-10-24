"""Tests for the generated OpenAPI and Terraform artifacts and their checks."""

import pytest

from secreview.datagen.catalog import (
    load_all_documented_services,
    load_rules,
)
from secreview.datagen.openapi_build import build_openapi_document
from secreview.datagen.openapi_checks import OPENAPI_CHECKS, run_openapi_check
from secreview.datagen.openapi_mutations import (
    OPENAPI_MUTATIONS,
    apply_openapi_mutation,
)
from secreview.datagen.openapi_templates import load_openapi_templates
from secreview.datagen.terraform_checks import TERRAFORM_CHECKS, run_terraform_check
from secreview.datagen.terraform_mutations import (
    TERRAFORM_MUTATIONS,
    apply_terraform_mutation,
    is_mutation_applicable,
)
from secreview.datagen.terraform_render import render_terraform
from secreview.datagen.terraform_specs import (
    default_resources,
    load_terraform_templates,
)

OPENAPI_DOCUMENTED_SERVICES = sorted(load_openapi_templates())
TERRAFORM_DOCUMENTED_SERVICES = sorted(load_terraform_templates())


def documented_service_ids_by_format(implementation_format: str) -> set[str]:
    """List the documented service ids that use one implementation format."""
    return {
        documented_service.id
        for documented_service in load_all_documented_services()
        if documented_service.implementation_format == implementation_format
    }


def test_templates_match_the_company_configuration() -> None:
    openapi_ids = documented_service_ids_by_format("openapi")
    terraform_ids = documented_service_ids_by_format("terraform")
    assert set(OPENAPI_DOCUMENTED_SERVICES) == openapi_ids
    assert set(TERRAFORM_DOCUMENTED_SERVICES) == terraform_ids


@pytest.mark.parametrize("documented_service", OPENAPI_DOCUMENTED_SERVICES)
def test_openapi_baseline_is_valid_and_clean(documented_service: str) -> None:
    document = build_openapi_document(documented_service)
    for check_name in OPENAPI_CHECKS:
        assert run_openapi_check(check_name, document) == [], check_name


@pytest.mark.parametrize("documented_service", OPENAPI_DOCUMENTED_SERVICES)
@pytest.mark.parametrize("mutation_name", sorted(OPENAPI_MUTATIONS))
def test_openapi_mutation_is_detected(
    documented_service: str,
    mutation_name: str,
) -> None:
    document = build_openapi_document(documented_service)
    mutated, anchor = apply_openapi_mutation(
        document,
        mutation_name,
        documented_service,
    )
    assert run_openapi_check(mutation_name, mutated)
    assert anchor


@pytest.mark.parametrize("documented_service", TERRAFORM_DOCUMENTED_SERVICES)
def test_terraform_baseline_parses_and_is_clean(documented_service: str) -> None:
    text = render_terraform(default_resources(documented_service))
    for check_name in TERRAFORM_CHECKS:
        assert run_terraform_check(check_name, text) == [], check_name


@pytest.mark.parametrize("documented_service", TERRAFORM_DOCUMENTED_SERVICES)
@pytest.mark.parametrize("mutation_name", sorted(TERRAFORM_MUTATIONS))
def test_terraform_mutation_is_detected(
    documented_service: str,
    mutation_name: str,
) -> None:
    if not is_mutation_applicable(documented_service, mutation_name):
        pytest.skip("mutation targets a resource this documented service lacks")
    resources = default_resources(documented_service)
    mutated, anchor = apply_terraform_mutation(resources, mutation_name)
    assert run_terraform_check(mutation_name, render_terraform(mutated))
    assert anchor


def test_every_rule_check_is_registered() -> None:
    available: set[str] = set(OPENAPI_MUTATIONS) | set(TERRAFORM_MUTATIONS)
    for rule in load_rules():
        check = rule.implementation_check
        assert check is None or check in available, rule.id
