"""Typed structure of the OpenAPI 3.0 documents produced by the generator."""

from typing import NotRequired, TypedDict

SchemaObject = TypedDict(
    "SchemaObject",
    {
        "$ref": str,
        "type": str,
        "format": str,
        "maxLength": int,
        "minimum": int,
        "additionalProperties": bool,
        "required": list[str],
        "properties": dict[str, "SchemaObject"],
        "items": "SchemaObject",
    },
    total=False,
)

MediaType = TypedDict("MediaType", {"schema": SchemaObject})

Parameter = TypedDict(
    "Parameter",
    {
        "name": str,
        "in": str,
        "required": bool,
        "schema": SchemaObject,
    },
)

SecurityRequirement = dict[str, list[str]]


class RequestBody(TypedDict):
    required: bool
    content: dict[str, MediaType]


class Response(TypedDict):
    description: str
    content: NotRequired[dict[str, MediaType]]


class Operation(TypedDict):
    operationId: str
    summary: str
    responses: dict[str, Response]
    parameters: NotRequired[list[Parameter]]
    requestBody: NotRequired[RequestBody]
    security: NotRequired[list[SecurityRequirement]]


SecurityScheme = TypedDict(
    "SecurityScheme",
    {
        "type": str,
        "scheme": NotRequired[str],
        "bearerFormat": NotRequired[str],
        "in": NotRequired[str],
        "name": NotRequired[str],
    },
)


class ServerVariable(TypedDict):
    default: str
    description: str


class Server(TypedDict):
    url: str
    variables: NotRequired[dict[str, ServerVariable]]


class ApiInformation(TypedDict):
    title: str
    version: str


class Components(TypedDict):
    securitySchemes: dict[str, SecurityScheme]
    schemas: dict[str, SchemaObject]


OpenApiDocument = TypedDict(
    "OpenApiDocument",
    {
        "openapi": str,
        "info": ApiInformation,
        "servers": list[Server],
        "security": NotRequired[list[SecurityRequirement]],
        "paths": dict[str, dict[str, Operation]],
        "components": Components,
    },
)
