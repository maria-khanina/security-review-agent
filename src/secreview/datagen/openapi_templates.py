"""Per-documented service endpoint and schema templates for generated OpenAPI files."""

from functools import cache

from pydantic import BaseModel, TypeAdapter
import yaml

from secreview.datagen.catalog import config_path, read_text


class TemplateEndpoint(BaseModel):
    operation_id: str
    method: str
    path: str
    summary: str
    request_schema: str | None = None
    response_schema: str
    is_list: bool = False


class OpenApiTemplate(BaseModel):
    title: str
    list_query: list[str]
    pii_parameter: str
    endpoints: list[TemplateEndpoint]
    schemas: dict[str, dict[str, str]]


@cache
def load_openapi_templates() -> dict[str, OpenApiTemplate]:
    """Load endpoint and schema templates of every OpenAPI documented service."""
    text = read_text(config_path("documented_service_templates.yaml"))
    raw_document = yaml.safe_load(text)
    adapter = TypeAdapter(dict[str, OpenApiTemplate])
    return adapter.validate_python(raw_document["openapi"])
