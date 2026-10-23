"""Splitting a design document into sentence-sized units and windowed chunks."""

import re

from pydantic import BaseModel

from secreview.review_settings import REVIEW_SETTINGS

LIST_MARKER = re.compile(REVIEW_SETTINGS.retrieval.list_marker_pattern)
SENTENCE_BOUNDARY = re.compile(REVIEW_SETTINGS.retrieval.sentence_boundary_pattern)


class DesignUnit(BaseModel):
    start: int
    end: int
    text: str
    section: int
    heading: str


class Section(BaseModel):
    heading: str
    lines: list[tuple[int, str]]


class Chunk(BaseModel):
    first: int
    last: int
    center: int
    key: str


def find_content_start(line: str) -> int:
    """Return where the text of a line begins, after any list marker."""
    marker = LIST_MARKER.match(line)
    if marker is None:
        return len(line) - len(line.lstrip())
    return marker.end()


def find_sentence_bounds(line: str, content_start: int) -> list[tuple[int, int]]:
    """Split the content of a line into sentence bounds inside the line."""
    bounds: list[tuple[int, int]] = []
    start = content_start
    for match in SENTENCE_BOUNDARY.finditer(line, content_start):
        bounds.append((start, match.start()))
        start = match.end()
    bounds.append((start, len(line)))
    return bounds


def build_line_units(
    line: str,
    offset: int,
    section: int,
    heading: str,
) -> list[DesignUnit]:
    """Turn one non-heading line into its sentence units with text offsets."""
    units: list[DesignUnit] = []
    for start, end in find_sentence_bounds(line, find_content_start(line)):
        text = line[start:end].rstrip()
        if text:
            units.append(
                DesignUnit(
                    start=offset + start,
                    end=offset + start + len(text),
                    text=text,
                    section=section,
                    heading=heading,
                )
            )
    return units


def split_sections(design_text: str) -> list[Section]:
    """Group the lines of a design by the heading above them, with their offsets."""
    marker = REVIEW_SETTINGS.retrieval.heading_marker
    sections: list[Section] = [Section(heading="", lines=[])]
    offset = 0
    for line in design_text.split("\n"):
        if line.startswith(marker):
            sections.append(Section(heading=line.lstrip(marker).strip(), lines=[]))
        else:
            sections[-1].lines.append((offset, line))
        offset += len(line) + 1
    return sections


def split_units(design_text: str) -> list[DesignUnit]:
    """Split a design into sentence units, remembering the section of each."""
    units: list[DesignUnit] = []
    for number, section in enumerate(split_sections(design_text)):
        for offset, line in section.lines:
            units.extend(build_line_units(line, offset, number, section.heading))
    return units


def walk_window(units: list[DesignUnit], index: int, step: int, window: int) -> int:
    """Move up to window units in one direction without leaving the section."""
    position = index
    for _ in range(window):
        following = position + step
        if not 0 <= following < len(units):
            break
        if units[following].section != units[index].section:
            break
        position = following
    return position


def find_window(units: list[DesignUnit], index: int, window: int) -> tuple[int, int]:
    """Find the first and last unit of the window, kept inside the section."""
    return walk_window(units, index, -1, window), walk_window(units, index, 1, window)


def build_chunk_key(
    units: list[DesignUnit],
    bounds: tuple[int, int],
    with_heading: bool,
) -> str:
    """Join the texts of a window, optionally led by the section heading."""
    first, last = bounds
    body = " ".join(unit.text for unit in units[first:last + 1])
    heading = units[first].heading
    if with_heading and heading:
        return f"{heading}: {body}"
    return body


def build_chunks(
    units: list[DesignUnit],
    window: int,
    with_heading: bool,
) -> list[Chunk]:
    """Create one chunk per unit, widened by the window of neighbouring units."""
    chunks: list[Chunk] = []
    for index in range(len(units)):
        bounds = find_window(units, index, window)
        key = build_chunk_key(units, bounds, with_heading)
        chunks.append(Chunk(first=bounds[0], last=bounds[1], center=index, key=key))
    return chunks
