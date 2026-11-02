from pathlib import Path
import tempfile

import pytest

from secreview.agents import verdict_run_config as module
from secreview.agents.verdict_review import ContextChoice
from secreview.agents.verdict_run_config import (
    NO_BATCH,
    VerdictRunConfig,
    fingerprint,
    store_run_config,
    with_analysis,
)
from secreview.review_settings import REVIEW_SETTINGS

RUN = "unit__test__run"
OTHER_PROMPT = "another prompt"
RECORD_FILE = "c001_x.json"
SMALL_GROUP = len("ab")
LARGE_GROUP = len("abcd")


def make_choice() -> ContextChoice:
    return ContextChoice(
        method=REVIEW_SETTINGS.verdict.ranker,
        window=REVIEW_SETTINGS.verdict.window,
        candidates=REVIEW_SETTINGS.verdict.candidates,
        oracle=False,
        strict=False,
        overview_chars=0,
        reasoned=False,
        whole_document=False,
        card_name="",
    )


def make_config() -> VerdictRunConfig:
    return module.build_verdict_run_config(
        make_choice(), REVIEW_SETTINGS.verdict.analysis_set, "v4", False, NO_BATCH
    )


def use_directory(monkeypatch: pytest.MonkeyPatch, directory: str) -> Path:
    def directory_of(name: str) -> Path:
        return Path(directory) / name

    monkeypatch.setattr(module, "verdict_run_directory", directory_of)
    return Path(directory)


def test_fingerprint_ignores_time_commit_and_note() -> None:
    config = make_config()
    changed = config.model_copy(
        update={"created_at": "later", "commit": "abc", "note": "text"}
    )
    assert fingerprint(config) == fingerprint(changed)


def test_fingerprint_changes_with_prompt_and_data() -> None:
    config = make_config()
    prompt = config.model_copy(update={"system_prompt": OTHER_PROMPT})
    data = config.model_copy(update={"data_digest": "other"})
    assert fingerprint(prompt) != fingerprint(config)
    assert fingerprint(data) != fingerprint(config)


def test_run_with_records_refuses_another_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = use_directory(monkeypatch, directory)
        config = make_config()
        store_run_config(RUN, config)
        (root / RUN / RECORD_FILE).write_text("{}", encoding="utf-8")
        store_run_config(RUN, config)
        other = config.model_copy(update={"system_prompt": OTHER_PROMPT})
        with pytest.raises(ValueError):
            store_run_config(RUN, other)


def test_run_without_records_is_rewritten(monkeypatch: pytest.MonkeyPatch) -> None:
    with tempfile.TemporaryDirectory() as directory:
        use_directory(monkeypatch, directory)
        config = make_config()
        store_run_config(RUN, config)
        other = config.model_copy(update={"system_prompt": OTHER_PROMPT})
        store_run_config(RUN, other)
        assert module.load_run_config(RUN).system_prompt == OTHER_PROMPT


def test_other_analysis_changes_the_digest() -> None:
    config = make_config()
    worded = with_analysis(config, REVIEW_SETTINGS.verdict.wording_analysis_set)
    assert worded.analysis_digest != config.analysis_digest


def test_batched_run_differs_from_single_run_and_from_other_size() -> None:
    choice = make_choice()
    analysis = REVIEW_SETTINGS.verdict.analysis_set
    single = make_config()
    batched = module.build_batched_run_config(choice, analysis, "v4", SMALL_GROUP)
    larger = module.build_batched_run_config(choice, analysis, "v4", LARGE_GROUP)
    assert fingerprint(batched) != fingerprint(single)
    assert fingerprint(batched) != fingerprint(larger)
