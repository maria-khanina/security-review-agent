"""Writes the deterministic brief an author follows to compose a design doc.

The brief lists the author's profile, the architecture to describe, the
planted flaws to realize and the compliance statements to include. The free
text of the design document itself is written separately, following it.
"""

from secreview.datagen.catalog import (
    load_architecture,
    load_author_profiles,
    load_rules,
)
from secreview.datagen.flaw_sampling import find_documented_service
from secreview.datagen.models import Case, Rule
from secreview.datagen.openapi_templates import load_openapi_templates
from secreview.datagen.settings import load_settings
from secreview.datagen.terraform_specs import (
    RdsResource,
    S3Resource,
    load_terraform_templates,
)

OPENAPI_FORMAT = "openapi"
DESIGN_MARKED_FILE = "design_marked.md"
NEWLINE = "\n"
CLEAN_CASE_NOTE = (
    "None. This is a clean case: no violation, no ambiguity, no drift."
)


def describe_openapi_endpoints(documented_service: str) -> str:
    """List the endpoints of the OpenAPI documented service, one per line."""
    lines: list[str] = []
    for endpoint in load_openapi_templates()[documented_service].endpoints:
        method = endpoint.method.upper()
        lines.append(f"- {method} {endpoint.path}: {endpoint.summary}")
    return "\n".join(lines)


def describe_terraform_resources(documented_service: str) -> str:
    """List the Terraform resources of the documented service, one per line."""
    lines: list[str] = []
    for resource in load_terraform_templates()[documented_service].resources:
        extra = ""
        if isinstance(resource, (RdsResource, S3Resource)):
            extra = f" (holds {resource.holds})"
        lines.append(f"- {resource.kind} `{resource.name}`{extra}")
    return "\n".join(lines)


def describe_implementation(case: Case) -> str:
    """Describe the implementation facts the document must stay consistent with."""
    if case.implementation_format == OPENAPI_FORMAT:
        return describe_openapi_endpoints(case.documented_service)
    return describe_terraform_resources(case.documented_service)


def build_author_profile_lines(case: Case) -> list[str]:
    """Describe the author profile and the noise level of the document."""
    author_profile = load_author_profiles()[case.author_profile]
    low, high = author_profile.length_words
    noise = case.noise
    return [
        f"# Writer brief: {case.case_id}",
        "",
        f"Author profile `{author_profile.id}`: {author_profile.summary}",
        f"- structure={author_profile.structure}, english={author_profile.english}, "
        f"hedging={author_profile.hedging}, terminology={author_profile.terminology}, "
        f"staleness={author_profile.staleness}",
        f"- typical gaps: {', '.join(author_profile.typical_gaps)}",
        f"- length {low}-{high} words; typo rate {noise.typo_rate}; "
        f"markdown breakage {noise.markdown_breakage}; "
        f"dangling references {noise.dangling_references}; "
        f"TBD markers {noise.tbd_markers}",
        "",
    ]


def build_architecture_lines(case: Case) -> list[str]:
    """Describe the service, its components and its data flows."""
    documented_service = find_documented_service(case.documented_service)
    facts = load_architecture()[case.documented_service]
    lines: list[str] = [
        f"Service: {documented_service.summary} (Meridian Pay, "
        f"{documented_service.exposure} exposure, "
        f"data: {', '.join(documented_service.data)})",
        "",
        "Components:",
    ]
    for component in facts.components:
        lines.append(f"- {component.name} ({component.kind})")
    lines += ["", "Flows:"]
    for flow in facts.flows:
        lines.append(f"- {flow.source} -> {flow.target}: {flow.data}")
    return lines


def build_flaw_lines(case: Case) -> list[str]:
    """Describe the planted flaws the author must realize."""
    lines: list[str] = ["", "## Planted items"]
    if not case.flaws:
        lines.append(CLEAN_CASE_NOTE)
    for flaw in case.flaws:
        label = f"{flaw.flaw_id} [{flaw.type}, {flaw.severity}]"
        lines.append(f"- {label} {flaw.instruction}")
    return lines


def build_required_lines(case: Case) -> list[str]:
    """Describe the compliance statements the author must include."""
    rules: dict[str, Rule] = {rule.id: rule for rule in load_rules()}
    lines: list[str] = [
        "",
        "## Required compliance statements",
        "State each of these concretely (terse is fine for terse profiles) "
        "and wrap the statement in the marker shown.",
    ]
    for rule_id in case.required_rules:
        lines.append(f"- ⟦S:{rule_id}|...⟧ {rules[rule_id].statement}")
    return lines


def describe_endpoint_fields(documented_service: str) -> list[str]:
    """Describe the request and response fields of every endpoint."""
    template = load_openapi_templates()[documented_service]
    lines: list[str] = []
    for endpoint in template.endpoints:
        response = ", ".join(template.schemas[endpoint.response_schema])
        request = "none"
        if endpoint.request_schema:
            request = ", ".join(template.schemas[endpoint.request_schema])
        method = endpoint.method.upper()
        lines.append(
            f"- {method} {endpoint.path}: request fields {request}; "
            f"response fields {response}"
        )
    return lines


def build_functional_lines(case: Case) -> list[str]:
    """Describe the realistic functional content that pads the document."""
    low, _ = load_author_profiles()[case.author_profile].length_words
    sections = ", ".join(load_settings().functional_sections)
    lines: list[str] = [
        "",
        "## Functional content (no security claims)",
        f"Aim for at least {low} words in total. Reach the length with functional "
        "detail written in the author's voice, never with extra security statements.",
        f"Suggested sections: {sections}.",
        "Do not mention authentication, authorization, encryption, secrets, network "
        "exposure, logging, retention, third-party data sharing, input validation, "
        "rate limits, dependency scanning, containers or backups except through the "
        "planted items and required statements above.",
    ]
    if case.implementation_format == OPENAPI_FORMAT:
        lines.append("Functional detail to describe for each endpoint:")
        lines += describe_endpoint_fields(case.documented_service)
    return lines


def build_writing_rules(case: Case) -> list[str]:
    """Return the fixed writing rules of every brief."""
    raw_directory = load_settings().paths.raw_directory
    return [
        "",
        "## Rules for writing",
        "- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; "
        "markers must not nest.",
        "- Introduce no other policy violation, ambiguity about a required "
        "statement, or contradiction beyond the planted items.",
        "- Typos, sloppy structure, TBDs and stale mentions are welcome but "
        "must not hide or alter the planted items or required statements.",
        f"- Save to {raw_directory}/{case.case_id}/{DESIGN_MARKED_FILE}",
    ]


def write_brief(case: Case) -> str:
    """Assemble the complete writer brief of a case."""
    lines = build_author_profile_lines(case) + build_architecture_lines(case)
    lines += [
        "",
        f"Implementation ({case.implementation_format}) the document describes:",
        describe_implementation(case),
    ]
    lines += build_flaw_lines(case)
    lines += build_required_lines(case)
    lines += build_functional_lines(case)
    lines += build_writing_rules(case)
    return NEWLINE.join(lines) + NEWLINE
