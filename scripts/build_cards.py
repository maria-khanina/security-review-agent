"""Extracts the architecture card of every design of a split with the model."""

import argparse

from secreview.agents.architecture_card import build_cards
from secreview.agents.case_materials import (
    CaseMaterials,
    list_case_ids,
    load_case_materials,
)


def parse_arguments() -> argparse.Namespace:
    """Read the name of the card set, the split and the optional case list."""
    parser = argparse.ArgumentParser()
    parser.add_argument("card_name")
    parser.add_argument("--split", type=str, default="dev")
    parser.add_argument("--cases", nargs="*", default=[])
    return parser.parse_args()


def main() -> None:
    """Extract the cards that are missing and report how many were made."""
    arguments = parse_arguments()
    case_ids = arguments.cases or list_case_ids(arguments.split)
    materials: list[CaseMaterials] = [
        load_case_materials(case_id) for case_id in case_ids
    ]
    created = build_cards(arguments.card_name, materials)
    print(f"{created} cards created for {len(case_ids)} cases")


if __name__ == "__main__":
    main()
