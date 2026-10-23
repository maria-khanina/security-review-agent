"""A small fixed subset of the dev cases for quick screening of prompt variants."""

import random

from pydantic import BaseModel
import yaml

from secreview.agents.case_materials import list_case_ids, load_case_materials
from secreview.datagen.settings import project_path
from secreview.review_settings import REVIEW_SETTINGS


class PilotSample(BaseModel):
    case_ids: list[str]


def group_cases(case_ids: list[str]) -> dict[tuple[str, bool], list[str]]:
    """Group case ids by documented service and by whether the case is clean."""
    groups: dict[tuple[str, bool], list[str]] = {}
    for case_id in case_ids:
        labels = load_case_materials(case_id).labels
        key = (labels.documented_service, labels.clean)
        groups.setdefault(key, []).append(case_id)
    return groups


def build_queues(
    groups: dict[tuple[str, bool], list[str]],
    generator: random.Random,
) -> list[list[str]]:
    """Shuffle every group, in a fixed group order, into a queue of case ids."""
    queues: list[list[str]] = []
    for key in sorted(groups):
        members: list[str] = list(groups[key])
        generator.shuffle(members)
        queues.append(members)
    return queues


def select_pilot_sample(case_ids: list[str], size: int, seed: int) -> list[str]:
    """Pick cases round-robin over the service and cleanliness groups."""
    queues = build_queues(group_cases(case_ids), random.Random(seed))
    selected: list[str] = []
    while len(selected) < size and any(queues):
        for queue in queues:
            if queue and len(selected) < size:
                selected.append(queue.pop())
    return sorted(selected)


def build_pilot_sample() -> PilotSample:
    """Select the pilot cases from the dev split with the configured size and seed."""
    pilot = REVIEW_SETTINGS.pilot
    case_ids = list_case_ids("dev")
    size, seed = pilot.sample_size, pilot.sample_seed
    return PilotSample(case_ids=select_pilot_sample(case_ids, size, seed))


def save_pilot_sample(sample: PilotSample) -> None:
    """Write the pilot case list to the configuration file."""
    path = project_path(REVIEW_SETTINGS.pilot.sample_file)
    path.write_text(yaml.safe_dump(sample.model_dump()), encoding="utf-8")


def load_pilot_sample() -> list[str]:
    """Read the stored pilot case list."""
    path = project_path(REVIEW_SETTINGS.pilot.sample_file)
    return PilotSample.model_validate(yaml.safe_load(path.read_text("utf-8"))).case_ids
