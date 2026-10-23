"""Deterministic detectors that confirm planted flaws in an OpenAPI document.

Each detector returns the anchors where the flaw is visible, or an empty list.
They double as negative controls: they must stay silent on clean resources.
"""

from collections.abc import Callable
import re

from secreview.datagen.openapi_io import (
    document_to_yaml,
    iterate_operations,
    json_pointer,
    request_body_of,
)
from secreview.datagen.openapi_templates import load_openapi_templates
from secreview.datagen.openapi_types import OpenApiDocument, Operation
from secreview.datagen.settings import load_settings

PRIVATE_PATH_PATTERN = re.compile(r"^/(admin|internal|debug)/")
PAN_FIELD_NAMES = {"pan", "card_number", "cvv", "full_card_number"}
GENERIC_PII_PARAMETERS = {"email", "phone_number", "national_id", "ssn"}
STRONG_SCHEME_TYPES = {"oauth2", "openIdConnect", "mutualTLS"}
JSON_MEDIA_TYPE = "application/json"

OpenApiCheck = Callable[[OpenApiDocument, str], list[str]]


def has_unprotected_operation(document: OpenApiDocument) -> bool:
    """Tell whether some operation ends up with no security requirement."""
    for _, _, operation in iterate_operations(document):
        effective = operation.get("security", document.get("security"))
        if not effective:
            return True
    return False


def check_security_missing(document: OpenApiDocument, text: str) -> list[str]:
    """Detect a specification without any global security requirement."""
    if has_unprotected_operation(document) and "security" not in document:
        return ["/security"]
    return []


def check_weak_auth_scheme(document: OpenApiDocument, text: str) -> list[str]:
    """Detect authentication that is neither bearer nor a strong scheme."""
    for scheme in document["components"]["securitySchemes"].values():
        is_bearer = scheme["type"] == "http" and scheme.get("scheme") == "bearer"
        if scheme["type"] not in STRONG_SCHEME_TYPES and not is_bearer:
            return ["/components/securitySchemes"]
    return []


def check_private_paths(document: OpenApiDocument, text: str) -> list[str]:
    """Detect administrative, internal or debug paths in the public document."""
    anchors: list[str] = []
    for path in document["paths"]:
        if PRIVATE_PATH_PATTERN.match(path):
            anchors.append(json_pointer("paths", path))
    return anchors


def check_operation_without_auth(document: OpenApiDocument, text: str) -> list[str]:
    """Detect operations that explicitly disable authentication."""
    anchors: list[str] = []
    for path, method, operation in iterate_operations(document):
        if operation.get("security") == []:
            anchors.append(json_pointer("paths", path, method, "security"))
    return anchors


def check_plaintext_server(document: OpenApiDocument, text: str) -> list[str]:
    """Detect a server entry that uses plain HTTP."""
    for server in document["servers"]:
        if server["url"].startswith("http://"):
            return ["/servers"]
    return []


def check_card_number_fields(document: OpenApiDocument, text: str) -> list[str]:
    """Detect schema properties that carry full card numbers."""
    anchors: list[str] = []
    for schema_name, schema in document["components"]["schemas"].items():
        for property_name in schema.get("properties", {}):
            if property_name in PAN_FIELD_NAMES:
                anchors.append(
                    json_pointer(
                        "components",
                        "schemas",
                        schema_name,
                        "properties",
                        property_name,
                    )
                )
    return anchors


def personal_data_parameter_names() -> set[str]:
    """Collect names of query parameters that carry personal data."""
    names: set[str] = set(GENERIC_PII_PARAMETERS)
    for template in load_openapi_templates().values():
        names.add(template.pii_parameter)
    return names


def check_personal_data_in_query(document: OpenApiDocument, text: str) -> list[str]:
    """Detect personal data passed through URL query parameters."""
    names = personal_data_parameter_names()
    anchors: list[str] = []
    for path, method, operation in iterate_operations(document):
        for parameter in operation.get("parameters", []):
            if parameter["in"] == "query" and parameter["name"] in names:
                anchors.append(json_pointer("paths", path, method, "parameters"))
    return anchors


def is_freeform_body(operation: Operation) -> bool:
    """Tell whether an operation accepts an unconstrained request body."""
    if "requestBody" not in operation:
        return False
    schema = request_body_of(operation)["content"][JSON_MEDIA_TYPE]["schema"]
    if "$ref" in schema:
        return False
    return schema.get("additionalProperties") is True or "properties" not in schema


def check_freeform_request_body(document: OpenApiDocument, text: str) -> list[str]:
    """Detect request bodies that accept arbitrary objects."""
    anchors: list[str] = []
    for path, method, operation in iterate_operations(document):
        if is_freeform_body(operation):
            anchors.append(json_pointer("paths", path, method, "requestBody"))
    return anchors


def check_rate_limit_absent(document: OpenApiDocument, text: str) -> list[str]:
    """Detect a specification that defines no rate-limit response at all."""
    status = load_settings().openapi.rate_limit_status
    for _, _, operation in iterate_operations(document):
        if status in operation["responses"]:
            return []
    return ["/paths"]


def check_hardcoded_secret(document: OpenApiDocument, text: str) -> list[str]:
    """Detect secret-looking literals anywhere in the specification text."""
    if re.search(load_settings().secret_pattern, text):
        return ["/servers"]
    return []


OPENAPI_CHECKS: dict[str, OpenApiCheck] = {
    "openapi_security_missing": check_security_missing,
    "openapi_auth_mismatch": check_weak_auth_scheme,
    "openapi_undocumented_endpoint": check_private_paths,
    "openapi_admin_path_public": check_private_paths,
    "openapi_operation_without_auth": check_operation_without_auth,
    "openapi_http_server": check_plaintext_server,
    "openapi_pan_in_response": check_card_number_fields,
    "openapi_pii_in_query": check_personal_data_in_query,
    "openapi_freeform_body": check_freeform_request_body,
    "openapi_rate_limit_absent": check_rate_limit_absent,
    "spec_hardcoded_secret": check_hardcoded_secret,
}


def run_openapi_check(check_name: str, document: OpenApiDocument) -> list[str]:
    """Run one named detector against a specification."""
    return OPENAPI_CHECKS[check_name](document, document_to_yaml(document))
