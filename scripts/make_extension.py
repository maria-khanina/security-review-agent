"""Writes the raw skeletons of the extension cases; finished cases stay untouched."""

from secreview.datagen.case_files import is_finished, write_raw_case
from secreview.datagen.extension_plan import plan_extension_cases


def main() -> None:
    """Generate the briefs and implementation files of unfinished extension cases."""
    created = 0
    for planned in plan_extension_cases():
        case = planned.case
        if is_finished(case.case_id):
            continue
        write_raw_case(case)
        created += 1
        print(case.case_id, case.split, case.policy_version, len(case.flaws))
    print("created", created)


if __name__ == "__main__":
    main()
