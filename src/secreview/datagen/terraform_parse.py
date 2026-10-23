"""Strict parsing of Terraform HCL into typed, navigable blocks."""

from dataclasses import dataclass
import io
from typing import cast

import hcl2

from secreview.datagen.json_types import JsonValue

BLOCK_MARKER = "__is_block__"
QUOTE = '"'

HclBlock = dict[str, JsonValue]
BlockKey = tuple[str, str]


@dataclass(frozen=True)
class TerraformDocument:
    resources: dict[BlockKey, HclBlock]
    data_sources: dict[BlockKey, HclBlock]

    def resources_of_type(self, resource_type: str) -> dict[str, HclBlock]:
        """Return the resource blocks of one type keyed by resource name."""
        selected: dict[str, HclBlock] = {}
        for (block_type, name), block in self.resources.items():
            if block_type == resource_type:
                selected[name] = block
        return selected


def strip_quotes(text: str) -> str:
    """Remove the surrounding double quotes python-hcl2 keeps on strings."""
    return text.strip(QUOTE)


def normalize_value(value: JsonValue) -> JsonValue:
    """Recursively unquote strings and drop parser bookkeeping keys."""
    if isinstance(value, dict):
        return normalize_mapping(value)
    if isinstance(value, list):
        return [normalize_value(item) for item in value]
    if isinstance(value, str):
        return strip_quotes(value)
    return value


def normalize_mapping(mapping: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Unquote the keys and values of a parsed HCL mapping."""
    normalized: dict[str, JsonValue] = {}
    for key, value in mapping.items():
        if key != BLOCK_MARKER:
            normalized[strip_quotes(key)] = normalize_value(value)
    return normalized


def collect_blocks(sections: JsonValue) -> dict[BlockKey, HclBlock]:
    """Flatten parsed HCL sections into blocks keyed by (type, name)."""
    blocks: dict[BlockKey, HclBlock] = {}
    if not isinstance(sections, list):
        return blocks
    for section in sections:
        if not isinstance(section, dict):
            continue
        for block_type, named_blocks in section.items():
            collect_named_blocks(blocks, block_type, named_blocks)
    return blocks


def collect_named_blocks(
    blocks: dict[BlockKey, HclBlock],
    block_type: str,
    named_blocks: JsonValue,
) -> None:
    """Add every named block of one HCL block type to the result."""
    if not isinstance(named_blocks, dict):
        return
    for name, attributes in named_blocks.items():
        if isinstance(attributes, dict):
            blocks[(block_type, name)] = attributes


def parse_terraform(text: str) -> TerraformDocument:
    """Parse HCL text, failing on any syntax error."""
    parsed = cast(dict[str, JsonValue], hcl2.load(io.StringIO(text)))
    document = normalize_mapping(parsed)
    return TerraformDocument(
        resources=collect_blocks(document.get("resource")),
        data_sources=collect_blocks(document.get("data")),
    )


def attribute_bool(block: HclBlock, name: str) -> bool | None:
    """Read a boolean attribute, or None when absent or not a boolean."""
    value = block.get(name)
    return value if isinstance(value, bool) else None


def attribute_int(block: HclBlock, name: str) -> int | None:
    """Read an integer attribute, or None when absent or not an integer."""
    value = block.get(name)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def attribute_strings(block: HclBlock, name: str) -> list[str]:
    """Read a list-of-strings attribute, or an empty list."""
    value = block.get(name)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def child_blocks(block: HclBlock, name: str) -> list[HclBlock]:
    """Read the nested blocks of one name inside a block."""
    value = block.get(name)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]
