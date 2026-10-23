"""Validates authored cases and writes their final labels."""

import argparse
import sys

from secreview.datagen.case_build import finalize_case


def parse_case_ids() -> list[str]:
    """Read the case ids to finalize from the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("case_ids", nargs="+")
    return list(parser.parse_args().case_ids)


def finalize_one(case_id: str) -> bool:
    """Finalize one case and report whether it succeeded."""
    try:
        labels = finalize_case(case_id)
    except (ValueError, LookupError, OSError) as error:
        print(f"FAIL {case_id}: {error}")
        return False
    flaw_count = len(labels.flaws)
    print(f"ok   {case_id}: {flaw_count} flaws, {len(labels.satisfied)} satisfied")
    return True


def main() -> int:
    """Finalize every requested case and return the process exit code."""
    results: list[bool] = [finalize_one(case_id) for case_id in parse_case_ids()]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
