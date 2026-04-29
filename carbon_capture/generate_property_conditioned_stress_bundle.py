import argparse
import json
from datetime import date
from pathlib import Path

from cage_stress_test import write_json_output
from property_conditioned_stress_proxy import (
    build_stats,
    load_candidate_rows,
    load_retained_candidates,
    run_property_conditioned_stress,
)

ARTIFACT_DIR = Path("carbon_capture/stress_artifacts")
DEFAULT_SEED = 20260429
DEFAULT_TOP_N = 25


def load_candidates(input_json=None):
    if input_json:
        return load_candidate_rows(input_json)
    return load_retained_candidates()


def build_bundle(seed, top_n, input_json=None):
    candidates = load_candidates(input_json)
    stats = build_stats(candidates)
    selected = sorted(
        candidates, key=lambda row: (-row["pore_space"], row["stability"], row["formula"])
    )[:top_n]
    results = [run_property_conditioned_stress(row, stats, seed) for row in selected]
    ranked = sorted(
        results,
        key=lambda row: (
            row["stress_result"]["failure_rate"],
            -row["stress_result"]["failure_threshold_c"],
            row["formula"],
        ),
    )

    return {
        "artifact_type": "property_conditioned_stress_bundle",
        "created_on": str(date.today()),
        "seed": seed,
        "source": input_json or "carbon_capture/vetted_carbon_results.json",
        "selection_rule": f"top {top_n} candidates by pore space",
        "stats_reference": stats,
        "results": ranked,
        "boundary_note": (
            "This bundle is stronger than the generic one-formula proxy because "
            "it conditions stress parameters on retained candidate properties. "
            "It still remains heuristic and should not be treated as "
            "composition-specific physics."
        ),
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--input-json")
    parser.add_argument("--json-output")
    return parser.parse_args()


def main():
    args = parse_args()
    bundle = build_bundle(args.seed, args.top_n, input_json=args.input_json)

    print("--- Property-Conditioned Calcium Stress Bundle ---")
    print(f"Seed:                    {bundle['seed']}")
    print(f"Source:                  {bundle['source']}")
    print(f"Selection Rule:          {bundle['selection_rule']}")
    print(f"Candidates Evaluated:    {len(bundle['results'])}")
    print("")
    print(f"{'Rank':<5} {'Formula':<24} {'Failure':<10} {'Threshold':<10} {'Noise':<8}")
    print("-" * 70)
    for index, row in enumerate(bundle["results"][:10], start=1):
        stress = row["stress_result"]
        params = row["property_conditioning"]
        print(
            f"{index:<5} {row['formula']:<24} {stress['failure_rate']:<10.3%} "
            f"{stress['failure_threshold_c']:<10.2f} {params['noise_std']:<8.4f}"
        )

    if args.json_output:
        output_path = args.json_output
    else:
        prefix = "property_conditioned_stress_bundle"
        if args.input_json:
            source_name = Path(args.input_json).stem
            prefix = f"{source_name}_{prefix}"
        output_path = ARTIFACT_DIR / f"{prefix}_top_{args.top_n}_seed_{args.seed}.json"

    write_json_output(output_path, bundle)
    print("")
    print(f"Saved Artifact:          {output_path}")


if __name__ == "__main__":
    main()
