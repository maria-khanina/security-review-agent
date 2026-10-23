"""Builds the secure baseline OpenAPI specification of a service documented service."""

import re

from secreview.datagen.openapi_io import validate_document
from secreview.datagen.openapi_templates import (
    OpenApiTemplate,
    TemplateEndpoint,
    load_openapi_templates,
)
from secreview.datagen.openapi_types import (
    MediaType,
    OpenApiDocument,
    Operation,
    Parameter,
    RequestBody,
    Response,
    SchemaObject,
)
from secreview.datagen.settings import load_settings

BEARER_SCHEME = "bearerAuth"
JSON_MEDIA_TYPE = "application/json"
SCHEMA_REF_PREFIX = "#/components/schemas/"
PATH_PARAMETER_PATTERN = re.compile(r"\{(\w+)\}")
BASE64_SUFFIX = "_base64"
ERROR_SCHEMA = "Error"
ERROR_FIELDS = {"code": "string", "message": "string"}


def schema_reference(schema_name: str) -> SchemaObject:
    """Create a reference to a named component schema."""
    return {"$ref": SCHEMA_REF_PREFIX + schema_name}


def array_of(item_schema: SchemaObject) -> SchemaObject:
    """Wrap a schema into an array schema."""
    return {"type": "array", "items": item_schema}


def build_property(name: str, kind: str) -> SchemaObject:
    """Create the constrained schema of one object property."""
    settings = load_settings().openapi
    if kind == "integer":
        return {"type": "integer", "minimum": settings.integer_minimum}
    if kind == "boolean":
        return {"type": "boolean"}
    if name.endswith(BASE64_SUFFIX):
        return {
            "type": "string",
            "format": "byte",
            "maxLength": settings.base64_max_length,
        }
    return {"type": "string", "maxLength": settings.string_max_length}


def build_object_schema(fields: dict[str, str]) -> SchemaObject:
    """Create a strict object schema with every field required."""
    properties: dict[str, SchemaObject] = {}
    for name, kind in fields.items():
        properties[name] = build_property(name, kind)
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(fields),
        "properties": properties,
    }


def build_schemas(template: OpenApiTemplate) -> dict[str, SchemaObject]:
    """Create all component schemas including the shared error schema."""
    schemas: dict[str, SchemaObject] = {}
    for name, fields in template.schemas.items():
        schemas[name] = build_object_schema(fields)
    schemas[ERROR_SCHEMA] = build_object_schema(ERROR_FIELDS)
    return schemas


def success_status_for(endpoint: TemplateEndpoint) -> str:
    """Pick the HTTP status code that signals success for an endpoint."""
    settings = load_settings().openapi
    if endpoint.method == "post":
        return settings.create_status
    return settings.default_success_status


def build_responses(endpoint: TemplateEndpoint) -> dict[str, Response]:
    """Create success and error responses of an endpoint."""
    body: SchemaObject = schema_reference(endpoint.response_schema)
    if endpoint.is_list:
        body = array_of(body)
    media: dict[str, MediaType] = {JSON_MEDIA_TYPE: {"schema": body}}
    responses: dict[str, Response] = {
        success_status_for(endpoint): {"description": "Success", "content": media},
    }
    for status in load_settings().openapi.error_statuses:
        responses[status] = build_error_response()
    return responses


def build_error_response() -> Response:
    """Create the shared error response."""
    error_body = schema_reference(ERROR_SCHEMA)
    return {
        "description": "Error",
        "content": {JSON_MEDIA_TYPE: {"schema": error_body}},
    }


def build_path_parameter(name: str) -> Parameter:
    """Create a required, length-limited path parameter."""
    settings = load_settings().openapi
    schema: SchemaObject = {
        "type": "string",
        "maxLength": settings.path_parameter_max_length,
    }
    return {"name": name, "in": "path", "required": True, "schema": schema}


def build_query_parameter(name: str) -> Parameter:
    """Create an optional, length-limited query parameter."""
    settings = load_settings().openapi
    schema: SchemaObject = {
        "type": "string",
        "maxLength": settings.query_parameter_max_length,
    }
    return {"name": name, "in": "query", "required": False, "schema": schema}


def build_parameters(
    endpoint: TemplateEndpoint,
    template: OpenApiTemplate,
) -> list[Parameter]:
    """Create path parameters and, for list endpoints, query parameters."""
    parameters: list[Parameter] = []
    for name in PATH_PARAMETER_PATTERN.findall(endpoint.path):
        parameters.append(build_path_parameter(name))
    if endpoint.is_list:
        for name in template.list_query:
            parameters.append(build_query_parameter(name))
    return parameters


def build_request_body(schema_name: str) -> RequestBody:
    """Create a required JSON request body referencing a schema."""
    reference = schema_reference(schema_name)
    return {"required": True, "content": {JSON_MEDIA_TYPE: {"schema": reference}}}


def build_operation(
    endpoint: TemplateEndpoint,
    template: OpenApiTemplate,
) -> Operation:
    """Create one operation with parameters, body and responses."""
    operation: Operation = {
        "operationId": endpoint.operation_id,
        "summary": endpoint.summary,
        "responses": build_responses(endpoint),
    }
    parameters = build_parameters(endpoint, template)
    if parameters:
        operation["parameters"] = parameters
    if endpoint.request_schema:
        operation["requestBody"] = build_request_body(endpoint.request_schema)
    return operation


def build_paths(template: OpenApiTemplate) -> dict[str, dict[str, Operation]]:
    """Group the operations of a template by URL path."""
    paths: dict[str, dict[str, Operation]] = {}
    for endpoint in template.endpoints:
        path_item = paths.setdefault(endpoint.path, {})
        path_item[endpoint.method] = build_operation(endpoint, template)
    return paths


def build_openapi_document(documented_service: str) -> OpenApiDocument:
    """Build and validate the secure baseline specification of an documented service."""
    template = load_openapi_templates()[documented_service]
    settings = load_settings().openapi
    document: OpenApiDocument = {
        "openapi": settings.openapi_version,
        "info": {"title": template.title, "version": settings.api_version},
        "servers": [{"url": settings.server_url}],
        "security": [{BEARER_SCHEME: []}],
        "paths": build_paths(template),
        "components": {
            "securitySchemes": {
                BEARER_SCHEME: {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": settings.bearer_format,
                },
            },
            "schemas": build_schemas(template),
        },
    }
    validate_document(document)
    return document
