import argparse
import json
from collections import Counter
from pathlib import Path

DEFAULT_INPUT_JSON = "carbon_capture/reaction_level_carbonation_pathways_v1.json"
DEFAULT_OUTPUT_JSON = "carbon_capture/exact_oxide_conversion_subset_v1.json"
DEFAULT_TOP_N = 25


def write_json_output(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))


def load_pathway_rows(path):
    payload = json.loads(Path(path).read_text())
    return payload["candidates"]


def build_artifact(input_json, top_n):
    rows = load_pathway_rows(input_json)
    exact_rows = [
        row
        for row in rows
        if row["reaction_level_pathway"]["exact_mass_balance_passed"]
    ]
    exact_rows.sort(
        key=lambda row: (
            -row["thermochemical_corroboration"]["corroborated_readiness_score"],
            -row["reaction_level_pathway"]["pathway_confidence"],
            row["formula"],
        )
    )
    family_counts = Counter(row["reaction_level_pathway"]["pathway_family"] for row in exact_rows[:top_n])
    return {
        "artifact_type": "exact_oxide_conversion_subset_v1",
        "source": input_json,
        "exact_candidate_count": len(exact_rows),
        "top_n": top_n,
        "pathway_family_counts_top_n": dict(family_counts),
        "top_candidates": exact_rows[:top_n],
        "candidates": exact_rows,
        "boundary_note": (
            "This subset isolates formulas whose simplified carbonation ceiling "
            "admits an exact mass-balanced oxide-to-carbonate conversion. It is "
            "the cleanest internal chemistry lane in the current carbon set, but "
            "it still does not replace measured reaction thermodynamics."
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

    print("--- Exact Oxide Conversion Subset v1 ---")
    print(f"Source:                         {args.input_json}")
    print(f"Exact Candidate Count:         {artifact['exact_candidate_count']}")
    print(f"Top-N Pathway Families:        {artifact['pathway_family_counts_top_n']}")
    print("")
    print(
        f"{'Rank':<5} {'Formula':<24} {'Pathway':<40} {'Corr Score'}"
    )
    print("-" * 110)
    for index, row in enumerate(artifact["top_candidates"][:10], start=1):
        print(
            f"{index:<5} {row['formula']:<24} "
            f"{row['reaction_level_pathway']['pathway_family']:<40} "
            f"{row['thermochemical_corroboration']['corroborated_readiness_score']:<10.2f}"
        )

    write_json_output(args.json_output, artifact)
    print("")
    print(f"Saved Artifact:                 {args.json_output}")


if __name__ == "__main__":
    main()
