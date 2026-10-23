"""Generates every planned case of the dataset with its brief and artifacts."""

from collections import Counter

from secreview.datagen.case_files import generate_dataset
from secreview.datagen.models import Case


def count_flaw_attribute(cases: list[Case], attribute: str) -> dict[str, int]:
    """Count planted flaws by one of their string attributes."""
    counter: Counter[str] = Counter()
    for case in cases:
        for flaw in case.flaws:
            counter[str(getattr(flaw, attribute))] += 1
    return dict(counter)


def main() -> None:
    """Generate the dataset skeleton and print a short summary."""
    cases = generate_dataset()
    clean_count = sum(1 for case in cases if not case.flaws)
    print(f"cases: {len(cases)}, clean: {clean_count}")
    print("flaw types:", count_flaw_attribute(cases, "type"))
    print("severities:", count_flaw_attribute(cases, "severity"))


if __name__ == "__main__":
    main()
