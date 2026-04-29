import argparse
import json
from collections import Counter
from pathlib import Path

from exact_subset_thermodynamic_calibration import (
    DEFAULT_INPUT_JSON,
    build_calibration_rows,
    load_exact_subset_rows,
)

DEFAULT_OUTPUT_JSON = "carbon_capture/exact_subset_thermodynamic_calibration_v1.json"
DEFAULT_TOP_N = 25


def write_json_output(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))


def build_artifact(input_json, top_n):
    rows = load_exact_subset_rows(input_json)
    calibrated_rows, stats = build_calibration_rows(rows)
    top_rows = calibrated_rows[:top_n]
    band_counts = Counter(
        row["thermodynamic_calibration"]["calibration_band"] for row in top_rows
    )
    family_counts = Counter(
        row["reaction_level_pathway"]["pathway_family"] for row in top_rows
    )
    return {
        "artifact_type": "exact_subset_thermodynamic_calibration_v1",
        "source": input_json,
        "stats_reference": stats,
        "top_candidates_by_thermodynamic_raw_score": top_rows,
        "calibration_band_counts_top_n": dict(band_counts),
        "pathway_family_counts_top_n": dict(family_counts),
        "candidates": calibrated_rows,
        "boundary_note": (
            "This artifact applies a surrogate thermodynamic calibration to the "
            "exact oxide-conversion subset. It combines product-family support, "
            "stoichiometric yield, and internal thermal/corroboration signals, "
            "but it still does not replace first-principles or experimental "
            "thermodynamics."
        ),
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", default=DEFAULT_INPUT_JSON)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--json-output", default=DEFAULT_OUTPUT_JSON)
    return parser.parse_args()


def main():
    args = parse_args()
    artifact = build_artifact(args.input_json, args.top_n)

    print("--- Exact Subset Thermodynamic Calibration v1 ---")
    print(f"Source:                         {args.input_json}")
    print(f"Top-N Calibration Bands:       {artifact['calibration_band_counts_top_n']}")
    print(f"Top-N Pathway Families:        {artifact['pathway_family_counts_top_n']}")
    print("")
    print(
        f"{'Rank':<5} {'Formula':<24} {'Thermo Raw':<11} {'Band':<44} {'Pathway'}"
    )
    print("-" * 140)
    for index, row in enumerate(artifact["top_candidates_by_thermodynamic_raw_score"][:10], start=1):
        payload = row["thermodynamic_calibration"]
        print(
            f"{index:<5} {row['formula']:<24} "
            f"{payload['thermodynamic_raw_score']:<11.2f} "
            f"{payload['calibration_band']:<44} "
            f"{row['reaction_level_pathway']['pathway_family']}"
        )

    write_json_output(args.json_output, artifact)
    print("")
    print(f"Saved Artifact:                 {args.json_output}")


if __name__ == "__main__":
    main()
