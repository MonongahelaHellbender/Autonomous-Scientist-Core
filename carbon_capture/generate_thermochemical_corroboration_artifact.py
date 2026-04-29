import argparse
import json
from collections import Counter
from pathlib import Path

from thermochemical_carbonation_corroboration import build_corroboration_rows

DEFAULT_INPUT_JSON = "carbon_capture/co2_uptake_proxy_v1.json"
DEFAULT_OUTPUT_JSON = "carbon_capture/thermochemical_carbonation_corroboration_v1.json"
DEFAULT_TOP_N = 25


def write_json_output(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))


def load_uptake_rows(path):
    payload = json.loads(Path(path).read_text())
    return payload["candidates"]


def build_artifact(input_json, top_n):
    uptake_rows = load_uptake_rows(input_json)
    corroboration_rows, stats = build_corroboration_rows(uptake_rows)
    class_counts = Counter(
        row["thermochemical_corroboration"]["corroboration_class"]
        for row in corroboration_rows[:top_n]
    )
    aligned_top_n = sum(
        row["thermochemical_corroboration"]["mode_alignment"] for row in corroboration_rows[:top_n]
    )
    compatible_top_n = sum(
        row["thermochemical_corroboration"]["mode_compatibility"]
        for row in corroboration_rows[:top_n]
    )
    return {
        "artifact_type": "thermochemical_carbonation_corroboration_v1",
        "source": input_json,
        "stats_reference": stats,
        "top_candidates_by_corroborated_readiness": corroboration_rows[:top_n],
        "corroboration_class_counts_top_n": dict(class_counts),
        "mode_alignment_fraction_top_n": aligned_top_n / top_n,
        "mode_compatibility_fraction_top_n": compatible_top_n / top_n,
        "candidates": corroboration_rows,
        "boundary_note": (
            "This artifact tests whether the semi-physical uptake split is "
            "consistent with deterministic thermal and composition pathway "
            "signals. It is a corroboration layer, not direct thermodynamic data."
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
    print("--- Thermochemical Carbonation Corroboration v1 ---")
    print(f"Source:                     {args.input_json}")
    print(f"Top-N Mode Alignment:      {artifact['mode_alignment_fraction_top_n']:.2%}")
    print(f"Top-N Mode Compatibility:  {artifact['mode_compatibility_fraction_top_n']:.2%}")
    print(f"Top-N Class Counts:        {artifact['corroboration_class_counts_top_n']}")
    print("")
    print(
        f"{'Rank':<5} {'Formula':<24} {'Corr Score':<11} {'Class':<34} {'Mode'}"
    )
    print("-" * 120)
    for index, row in enumerate(artifact["top_candidates_by_corroborated_readiness"][:10], start=1):
        corr = row["thermochemical_corroboration"]
        print(
            f"{index:<5} {row['formula']:<24} "
            f"{corr['corroborated_readiness_score']:<11.2f} "
            f"{corr['corroboration_class']:<34} {row['uptake_proxy']['uptake_mode']}"
        )

    write_json_output(args.json_output, artifact)
    print("")
    print(f"Saved Artifact:            {args.json_output}")


if __name__ == "__main__":
    main()
