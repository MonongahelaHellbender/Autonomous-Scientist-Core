import argparse
import json
from collections import Counter
from pathlib import Path

from reaction_level_carbonation_pathways import build_pathway_rows

DEFAULT_INPUT_JSON = "carbon_capture/thermochemical_carbonation_corroboration_v1.json"
DEFAULT_OUTPUT_JSON = "carbon_capture/reaction_level_carbonation_pathways_v1.json"
DEFAULT_TOP_N = 25


def write_json_output(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))


def load_corroboration_rows(path):
    payload = json.loads(Path(path).read_text())
    return payload["candidates"]


def build_artifact(input_json, top_n):
    corroboration_rows = load_corroboration_rows(input_json)
    pathway_rows = build_pathway_rows(corroboration_rows)
    top_rows = pathway_rows[:top_n]
    family_counts = Counter(row["reaction_level_pathway"]["pathway_family"] for row in top_rows)
    exact_count = sum(
        row["reaction_level_pathway"]["exact_oxide_conversion_supported"] for row in top_rows
    )
    mass_balance_count = sum(
        row["reaction_level_pathway"]["exact_mass_balance_passed"] for row in top_rows
    )
    return {
        "artifact_type": "reaction_level_carbonation_pathways_v1",
        "source": input_json,
        "top_candidates_by_reaction_pathway_readiness": top_rows,
        "pathway_family_counts_top_n": dict(family_counts),
        "exact_oxide_conversion_count_top_n": exact_count,
        "exact_mass_balance_count_top_n": mass_balance_count,
        "candidates": pathway_rows,
        "boundary_note": (
            "This artifact converts the earlier uptake and corroboration signals "
            "into explicit reaction-family hypotheses. It is a stronger internal "
            "mechanistic layer, but still not direct reaction thermodynamics or "
            "measured sequestration chemistry."
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

    print("--- Reaction-Level Carbonation Pathways v1 ---")
    print(f"Source:                         {args.input_json}")
    print(f"Top-N Pathway Families:        {artifact['pathway_family_counts_top_n']}")
    print(f"Top-N Exact Oxide Pathways:    {artifact['exact_oxide_conversion_count_top_n']}")
    print(f"Top-N Mass-Balanced Paths:     {artifact['exact_mass_balance_count_top_n']}")
    print("")
    print(
        f"{'Rank':<5} {'Formula':<24} {'Pathway':<40} {'Exact'}"
    )
    print("-" * 110)
    for index, row in enumerate(artifact["top_candidates_by_reaction_pathway_readiness"][:10], start=1):
        pathway = row["reaction_level_pathway"]
        print(
            f"{index:<5} {row['formula']:<24} "
            f"{pathway['pathway_family']:<40} "
            f"{str(pathway['exact_mass_balance_passed']):<5}"
        )

    write_json_output(args.json_output, artifact)
    print("")
    print(f"Saved Artifact:                 {args.json_output}")


if __name__ == "__main__":
    main()
