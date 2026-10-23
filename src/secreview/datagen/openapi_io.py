"""Reading, writing, validating and navigating generated OpenAPI documents."""

from collections.abc import Iterator
from typing import cast

from openapi_spec_validator import validate
import yaml

from secreview.datagen.openapi_types import (
    OpenApiDocument,
    Operation,
    RequestBody,
    SchemaObject,
)
from secreview.datagen.settings import load_settings

ESCAPED_TILDE = "~0"
ESCAPED_SLASH = "~1"


def validate_document(document: OpenApiDocument) -> None:
    """Fail loudly when a generated specification is not valid OpenAPI."""
    validate(cast(dict[str, object], document))


def document_to_yaml(document: OpenApiDocument) -> str:
    """Serialize a specification to YAML text."""
    return yaml.safe_dump(
        document,
        sort_keys=False,
        allow_unicode=True,
        width=load_settings().yaml_line_width,
    )


def parse_document_text(text: str) -> OpenApiDocument:
    """Parse YAML text of a specification produced by the generator."""
    return cast(OpenApiDocument, yaml.safe_load(text))


def json_pointer(*parts: str) -> str:
    """Build an RFC 6901 JSON pointer from raw path segments."""
    escaped: list[str] = []
    for part in parts:
        escaped.append(part.replace("~", ESCAPED_TILDE).replace("/", ESCAPED_SLASH))
    return "".join("/" + part for part in escaped)


def iterate_operations(
    document: OpenApiDocument,
) -> Iterator[tuple[str, str, Operation]]:
    """Yield (path, method, operation) for every operation of the document."""
    for path, path_item in document["paths"].items():
        for method, operation in path_item.items():
            yield path, method, operation


def request_body_of(operation: Operation) -> RequestBody:
    """Return the request body of an operation that must have one."""
    request_body = operation.get("requestBody")
    if request_body is None:
        raise LookupError(operation["operationId"])
    return request_body


def properties_of(schema: SchemaObject) -> dict[str, SchemaObject]:
    """Return the property map of an object schema."""
    properties = schema.get("properties")
    if properties is None:
        raise LookupError("schema has no properties")
    return properties


def required_of(schema: SchemaObject) -> list[str]:
    """Return the list of required property names of an object schema."""
    required = schema.get("required")
    if required is None:
        raise LookupError("schema has no required list")
    return required
