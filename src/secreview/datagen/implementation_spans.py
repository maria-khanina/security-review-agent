"""Gold character positions of the lines each planted mutation changed."""

from difflib import SequenceMatcher
import re

from secreview.datagen.implementation import build_implementation_text
from secreview.datagen.models import Case

SpanList = list[list[int]]


def compute_line_offsets(lines: list[str]) -> list[int]:
    """Return the character offset at which each line starts."""
    offsets: list[int] = []
    position = 0
    for line in lines:
        offsets.append(position)
        position += len(line)
    return offsets


def trim_line_span(line: str, start: int) -> tuple[int, int]:
    """Return the span of a line without its indentation and line break."""
    stripped = line.strip()
    first = start + line.index(stripped) if stripped else start
    return first, first + len(stripped)


def measure_indentation(line: str) -> int:
    """Count the leading whitespace characters of a line."""
    return len(line) - len(line.lstrip())


def find_enclosing_header(
    lines: list[str],
    position: int,
    indentation: int,
) -> int | None:
    """Find the closest earlier line that opens the block of a removed line."""
    for index in range(min(position, len(lines)) - 1, -1, -1):
        line = lines[index]
        if line.strip() and measure_indentation(line) < indentation:
            return index
    return None


def pick_changed_lines(
    before_lines: list[str],
    after_lines: list[str],
    opcode: tuple[str, int, int, int, int],
) -> tuple[int, int] | None:
    """Return the first and last line of the after text that show a change."""
    _, before_start, _, after_start, after_end = opcode
    if after_end > after_start:
        return after_start, after_end - 1
    indentation = measure_indentation(before_lines[before_start])
    header = find_enclosing_header(after_lines, after_start, indentation)
    return (header, header) if header is not None else None


def build_block_span(
    lines: list[str],
    offsets: list[int],
    changed: tuple[int, int],
) -> list[int]:
    """Return the trimmed character span of a block of changed lines."""
    first, last = changed
    start, _ = trim_line_span(lines[first], offsets[first])
    _, end = trim_line_span(lines[last], offsets[last])
    return [start, end]


def pick_block(
    before_lines: list[str],
    after_lines: list[str],
    opcode: tuple[str, int, int, int, int],
) -> tuple[int, int] | None:
    """Return the changed lines of an edit step, or None for unchanged lines."""
    if opcode[0] == "equal":
        return None
    return pick_changed_lines(before_lines, after_lines, opcode)


def collect_changed_spans(before: str, after: str) -> SpanList:
    """Return one span per changed block of lines, measured in the after text."""
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    offsets = compute_line_offsets(after_lines)
    matcher = SequenceMatcher(None, before_lines, after_lines, autojunk=False)
    spans: SpanList = []
    for opcode in matcher.get_opcodes():
        block = pick_block(before_lines, after_lines, opcode)
        if block is not None:
            spans.append(build_block_span(after_lines, offsets, block))
    return spans


def locate_resource_header(text: str, anchor: str | None) -> SpanList:
    """Return the span of the resource declaration line an anchor names."""
    if not anchor or "." not in anchor:
        return []
    kind, name = anchor.split(".", 1)
    header = rf'^resource "{re.escape(kind)}" "{re.escape(name)}" \{{'
    pattern = re.compile(header, re.M)
    match = pattern.search(text)
    return [[match.start(), match.end()]] if match else []


def remove_mutation(case: Case, flaw_id: str) -> Case:
    """Return a copy of the case in which one flaw's mutation is not applied."""
    without = case.model_copy(deep=True)
    for flaw in without.flaws:
        if flaw.flaw_id == flaw_id:
            flaw.implementation_mutation = None
    return without


def compute_implementation_spans(case: Case) -> dict[str, SpanList]:
    """Map each mutated flaw to the lines its mutation changed in the artifact."""
    final_text = build_implementation_text(case)
    spans: dict[str, SpanList] = {}
    for flaw in case.flaws:
        if not flaw.implementation_mutation:
            continue
        without = remove_mutation(case, flaw.flaw_id)
        changed = collect_changed_spans(build_implementation_text(without), final_text)
        spans[flaw.flaw_id] = changed or locate_resource_header(
            final_text,
            flaw.implementation_anchor,
        )
    return spans
