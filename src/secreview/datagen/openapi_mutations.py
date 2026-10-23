"""Mutations that inject known security flaws into a baseline OpenAPI document.

Every mutation edits the specification in place and returns the JSON pointer
of the edited location, which becomes the implementation anchor of the flaw.
"""

from collections.abc import Callable
import copy

from secreview.datagen.openapi_build import (
    JSON_MEDIA_TYPE,
    build_error_response,
    build_path_parameter,
    build_request_body,
)
from secreview.datagen.openapi_io import (
    json_pointer,
    properties_of,
    request_body_of,
    required_of,
    validate_document,
)
from secreview.datagen.openapi_templates import (
    TemplateEndpoint,
    load_openapi_templates,
)
from secreview.datagen.openapi_types import OpenApiDocument, Operation, Response
from secreview.datagen.settings import load_settings

STATE_CHANGING_METHODS = {"post", "put", "patch"}
API_KEY_SCHEME = "apiKeyAuth"
SANDBOX_KEY_VARIABLE = "apiKey"
SANDBOX_KEY_DESCRIPTION = "Default key for the sandbox environment"

OpenApiMutation = Callable[[OpenApiDocument, str], str]


def find_endpoint(
    documented_service: str,
    matches: Callable[[TemplateEndpoint], bool],
) -> TemplateEndpoint:
    """Find the first endpoint of a documented service that satisfies a test."""
    for endpoint in load_openapi_templates()[documented_service].endpoints:
        if matches(endpoint):
            return endpoint
    raise LookupError(documented_service)


def is_state_changing(endpoint: TemplateEndpoint) -> bool:
    """Tell whether an endpoint modifies server state."""
    return endpoint.method in STATE_CHANGING_METHODS


def has_request_schema(endpoint: TemplateEndpoint) -> bool:
    """Tell whether an endpoint accepts a request body."""
    return endpoint.request_schema is not None


def is_single_resource(endpoint: TemplateEndpoint) -> bool:
    """Tell whether an endpoint returns one resource rather than a list."""
    return not endpoint.is_list


def operation_of(document: OpenApiDocument, endpoint: TemplateEndpoint) -> Operation:
    """Return the specification operation that implements an endpoint."""
    return document["paths"][endpoint.path][endpoint.method]


def remove_security(document: OpenApiDocument, documented_service: str) -> str:
    """Drop the global security requirement and all security schemes."""
    document.pop("security", None)
    document["components"]["securitySchemes"] = {}
    return "/security"


def replace_with_api_key(document: OpenApiDocument, documented_service: str) -> str:
    """Replace bearer authentication by a static API key header."""
    header = load_settings().openapi.api_key_header
    document["components"]["securitySchemes"] = {
        API_KEY_SCHEME: {"type": "apiKey", "in": "header", "name": header},
    }
    document["security"] = [{API_KEY_SCHEME: []}]
    return "/components/securitySchemes"


def add_debug_endpoint(document: OpenApiDocument, documented_service: str) -> str:
    """Add an internal debug path that the design never mentions."""
    settings = load_settings().openapi
    body: Response = {
        "description": "Success",
        "content": {JSON_MEDIA_TYPE: {"schema": {"type": "object"}}},
    }
    document["paths"][settings.debug_path] = {
        "get": {
            "operationId": "dumpInternalState",
            "summary": "Dump internal service state",
            "responses": {settings.default_success_status: body},
        },
    }
    return json_pointer("paths", settings.debug_path)


def build_admin_operation(documented_service: str) -> Operation:
    """Create an administrative limit-override operation."""
    settings = load_settings().openapi
    endpoint = find_endpoint(documented_service, has_request_schema)
    request_schema = endpoint.request_schema
    responses: dict[str, Response] = {
        settings.default_success_status: {"description": "Success"},
    }
    for status in settings.error_statuses:
        responses[status] = build_error_response()
    return {
        "operationId": "overrideLimits",
        "summary": "Override account limits",
        "parameters": [build_path_parameter("accountId")],
        "requestBody": build_request_body(request_schema or ""),
        "responses": responses,
    }


def add_public_admin_endpoint(
    document: OpenApiDocument,
    documented_service: str,
) -> str:
    """Expose an administrative path on the same public specification."""
    path = load_settings().openapi.admin_path
    document["paths"][path] = {"put": build_admin_operation(documented_service)}
    return json_pointer("paths", path)


def remove_operation_security(
    document: OpenApiDocument,
    documented_service: str,
) -> str:
    """Disable authentication on one state-changing operation."""
    endpoint = find_endpoint(documented_service, is_state_changing)
    operation_of(document, endpoint)["security"] = []
    return json_pointer("paths", endpoint.path, endpoint.method, "security")


def add_plaintext_server(document: OpenApiDocument, documented_service: str) -> str:
    """Add a server entry that uses plain HTTP."""
    document["servers"].append({"url": load_settings().openapi.plaintext_server_url})
    return "/servers"


def add_pan_to_response(document: OpenApiDocument, documented_service: str) -> str:
    """Return the full card number in a response schema."""
    max_length = load_settings().openapi.pan_max_length
    endpoint = find_endpoint(documented_service, is_single_resource)
    schema_name = endpoint.response_schema
    schema = document["components"]["schemas"][schema_name]
    properties_of(schema)["pan"] = {"type": "string", "maxLength": max_length}
    required_of(schema).append("pan")
    return json_pointer("components", "schemas", schema_name, "properties", "pan")


def add_pii_query_parameter(document: OpenApiDocument, documented_service: str) -> str:
    """Move a personal data field into the query string of a list call."""
    max_length = load_settings().openapi.pii_parameter_max_length
    pii_name = load_openapi_templates()[documented_service].pii_parameter
    endpoint = find_endpoint(documented_service, lambda candidate: candidate.is_list)
    operation = operation_of(document, endpoint)
    operation.setdefault("parameters", []).append(
        {
            "name": pii_name,
            "in": "query",
            "required": False,
            "schema": {"type": "string", "maxLength": max_length},
        }
    )
    return json_pointer("paths", endpoint.path, endpoint.method, "parameters")


def make_body_freeform(document: OpenApiDocument, documented_service: str) -> str:
    """Replace a request schema by an unconstrained object."""
    endpoint = find_endpoint(documented_service, has_request_schema)
    body = request_body_of(operation_of(document, endpoint))
    body["content"][JSON_MEDIA_TYPE]["schema"] = {
        "type": "object",
        "additionalProperties": True,
    }
    return json_pointer("paths", endpoint.path, endpoint.method, "requestBody")


def remove_rate_limit_responses(
    document: OpenApiDocument,
    documented_service: str,
) -> str:
    """Remove every rate-limit response from the specification."""
    status = load_settings().openapi.rate_limit_status
    for path_item in document["paths"].values():
        for operation in path_item.values():
            operation["responses"].pop(status, None)
    return "/paths"


def embed_sandbox_secret(document: OpenApiDocument, documented_service: str) -> str:
    """Leave a live-looking API key as a server variable default."""
    secret = load_settings().openapi.hardcoded_secret
    document["servers"][0]["variables"] = {
        SANDBOX_KEY_VARIABLE: {
            "default": secret,
            "description": SANDBOX_KEY_DESCRIPTION,
        },
    }
    return json_pointer("servers", "0", "variables", SANDBOX_KEY_VARIABLE)


OPENAPI_MUTATIONS: dict[str, OpenApiMutation] = {
    "openapi_security_missing": remove_security,
    "openapi_auth_mismatch": replace_with_api_key,
    "openapi_undocumented_endpoint": add_debug_endpoint,
    "openapi_admin_path_public": add_public_admin_endpoint,
    "openapi_operation_without_auth": remove_operation_security,
    "openapi_http_server": add_plaintext_server,
    "openapi_pan_in_response": add_pan_to_response,
    "openapi_pii_in_query": add_pii_query_parameter,
    "openapi_freeform_body": make_body_freeform,
    "openapi_rate_limit_absent": remove_rate_limit_responses,
    "spec_hardcoded_secret": embed_sandbox_secret,
}


def apply_openapi_mutation(
    document: OpenApiDocument,
    mutation_name: str,
    documented_service: str,
) -> tuple[OpenApiDocument, str]:
    """Return a mutated, re-validated copy of the document and the flaw anchor."""
    mutated = copy.deepcopy(document)
    anchor = OPENAPI_MUTATIONS[mutation_name](mutated, documented_service)
    validate_document(mutated)
    return mutated, anchor
