"""Prints bootstrap intervals of a run, or paired differences between two runs."""

import argparse

from secreview.evaluation.bootstrap import bootstrap_difference, bootstrap_run
from secreview.evaluation.run_outcomes import load_run_outcomes


def parse_arguments() -> argparse.Namespace:
    """Read the split, the run and the optional second run to compare against."""
    parser = argparse.ArgumentParser()
    parser.add_argument("split")
    parser.add_argument("run_name")
    parser.add_argument("--against", type=str, default="")
    return parser.parse_args()


def print_intervals(run_name: str, split: str) -> None:
    """Print the interval of every headline metric of one run."""
    intervals = bootstrap_run(load_run_outcomes(run_name, split))
    for name, interval in intervals.items():
        bounds = f"[{interval.low:7.3f}, {interval.high:7.3f}]"
        print(f"{name:42} {interval.estimate:7.3f}  {bounds}")


def print_differences(first_run: str, second_run: str, split: str) -> None:
    """Print the paired difference second minus first for every headline metric."""
    differences = bootstrap_difference(
        load_run_outcomes(first_run, split),
        load_run_outcomes(second_run, split),
    )
    for name, item in differences.items():
        gap = item.difference
        flag = "SIGNIFICANT" if item.significant else ""
        change = f"{item.first:7.3f} -> {item.second:7.3f}"
        bounds = f"[{gap.low:+7.3f}, {gap.high:+7.3f}]"
        print(f"{name:42} {change}  diff {gap.estimate:+7.3f} {bounds} {flag}")


def main() -> None:
    """Run the plain or the paired bootstrap as requested."""
    arguments = parse_arguments()
    if arguments.against:
        print_differences(arguments.run_name, arguments.against, arguments.split)
    else:
        print_intervals(arguments.run_name, arguments.split)


if __name__ == "__main__":
    main()
