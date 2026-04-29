import argparse
from datetime import date
from pathlib import Path

from cage_stress_test import write_json_output
from composition_sensitive_stress_proxy import (
    build_stats,
    load_candidate_rows,
    load_retained_candidates,
    run_composition_sensitive_stress,
)

ARTIFACT_DIR = Path("carbon_capture/stress_artifacts")
DEFAULT_INPUT_JSON = "carbon_capture/abundance_safe_subset_v1.json"
DEFAULT_SEED = 20260429
DEFAULT_TOP_N = 25


def load_candidates(input_json=None):
    if input_json:
        return load_candidate_rows(input_json)
    return load_retained_candidates()


def build_bundle(seed, top_n, input_json=None):
    source = input_json or DEFAULT_INPUT_JSON
    candidates = load_candidates(source)
    stats, feature_map = build_stats(candidates)
    selected = sorted(
        candidates, key=lambda row: (-row["pore_space"], row["stability"], row["formula"])
    )[:top_n]
    results = [
        run_composition_sensitive_stress(row, stats, feature_map, seed) for row in selected
    ]
    ranked = sorted(
        results,
        key=lambda row: (
            row["stress_result"]["failure_rate"],
            -row["stress_result"]["failure_threshold_c"],
            row["formula"],
        ),
    )
    family_counts = {}
    for row in ranked:
        family_key = " / ".join(row["composition_profile"]["family_tags"])
        family_counts[family_key] = family_counts.get(family_key, 0) + 1

    return {
        "artifact_type": "composition_sensitive_stress_bundle",
        "created_on": str(date.today()),
        "seed": seed,
        "source": source,
        "selection_rule": f"top {top_n} candidates by pore space",
        "stats_reference": stats,
        "family_counts": family_counts,
        "results": ranked,
        "boundary_note": (
            "This bundle uses parsed formula stoichiometry and chemistry-family "
            "features to drive the stress proxy. It is more composition-aware "
            "than the earlier property-conditioned bundle, but it still remains "
            "proxy evidence rather than direct thermal or sequestration physics."
        ),
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--input-json", default=DEFAULT_INPUT_JSON)
    parser.add_argument("--json-output")
    return parser.parse_args()


def main():
    args = parse_args()
    bundle = build_bundle(args.seed, args.top_n, input_json=args.input_json)

    print("--- Composition-Sensitive Calcium Stress Bundle ---")
    print(f"Seed:                    {bundle['seed']}")
    print(f"Source:                  {bundle['source']}")
    print(f"Selection Rule:          {bundle['selection_rule']}")
    print(f"Candidates Evaluated:    {len(bundle['results'])}")
    print("")
    print(
        f"{'Rank':<5} {'Formula':<24} {'Failure':<10} {'Threshold':<10} "
        f"{'Noise':<8} {'Family'}"
    )
    print("-" * 110)
    for index, row in enumerate(bundle["results"][:10], start=1):
        stress = row["stress_result"]
        params = row["composition_conditioning"]
        family = ",".join(row["composition_profile"]["family_tags"])
        print(
            f"{index:<5} {row['formula']:<24} {stress['failure_rate']:<10.3%} "
            f"{stress['failure_threshold_c']:<10.2f} {params['noise_std']:<8.4f} {family}"
        )

    if args.json_output:
        output_path = args.json_output
    else:
        source_name = Path(bundle["source"]).stem
        output_path = (
            ARTIFACT_DIR
            / f"{source_name}_composition_sensitive_stress_bundle_top_{args.top_n}_seed_{args.seed}.json"
        )

    write_json_output(output_path, bundle)
    print("")
    print(f"Saved Artifact:          {output_path}")


if __name__ == "__main__":
    main()
