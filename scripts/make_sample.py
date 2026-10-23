"""Selects and stores the pilot sample of dev cases for quick screening."""

from secreview.agents.pilot_sample import build_pilot_sample, save_pilot_sample


def main() -> None:
    """Write the pilot sample to its configuration file and print its size."""
    sample = build_pilot_sample()
    save_pilot_sample(sample)
    print(len(sample.case_ids), sample.case_ids)


if __name__ == "__main__":
    main()
