"""Recursive JSON value type for parsed, schema-free documents."""

type JsonValue = (
    str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]
)
