import argparse
import json
import random
import statistics
from pathlib import Path

from co2_uptake_proxy import (
    DEFAULT_BASELINE_WEIGHTS,
    build_proxy_rows,
    load_candidates,
    select_formula_representatives,
)

DEFAULT_INPUT_JSON = "carbon_capture/abundance_safe_subset_v1.json"
DEFAULT_NUM_TRIALS = 1000
DEFAULT_SEED = 20260429
DEFAULT_OUTPUT_JSON = "carbon_capture/stress_artifacts/co2_uptake_proxy_sensitivity_audit_v1.json"


def write_json_output(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))


def perturbed_weights(rng):
    return {
        key: value * rng.uniform(0.8, 1.2)
        for key, value in DEFAULT_BASELINE_WEIGHTS.items()
    }


def build_audit(input_json, num_trials, seed):
    source_rows = load_candidates(input_json)
    representatives, _ = select_formula_representatives(source_rows)
    baseline_rows, _ = build_proxy_rows(representatives)
    baseline_top_10 = [row["formula"] for row in baseline_rows[:10]]

    rng = random.Random(seed)
    top10_frequency = {}
    top25_frequency = {}
    rank_samples = {formula: [] for formula in baseline_top_10}

    for _ in range(num_trials):
        rows, _ = build_proxy_rows(representatives, weights=perturbed_weights(rng))
        rank_map = {row["formula"]: rank for rank, row in enumerate(rows, start=1)}
        for formula in rows[:10]:
            top10_frequency[formula["formula"]] = top10_frequency.get(formula["formula"], 0) + 1
        for formula in rows[:25]:
            top25_frequency[formula["formula"]] = top25_frequency.get(formula["formula"], 0) + 1
        for formula in baseline_top_10:
            rank_samples[formula].append(rank_map[formula])

    stability_summary = []
    for formula in baseline_top_10:
        ranks = rank_samples[formula]
        stability_summary.append(
            {
                "formula": formula,
                "baseline_rank": baseline_top_10.index(formula) + 1,
                "top10_frequency": top10_frequency.get(formula, 0) / num_trials,
                "top25_frequency": top25_frequency.get(formula, 0) / num_trials,
                "median_rank": statistics.median(ranks),
                "worst_rank": max(ranks),
                "best_rank": min(ranks),
            }
        )

    recurring_top10 = sorted(
        (
            {"formula": formula, "frequency": count / num_trials}
            for formula, count in top10_frequency.items()
        ),
        key=lambda row: (-row["frequency"], row["formula"]),
    )[:15]

    return {
        "artifact_type": "co2_uptake_proxy_sensitivity_audit_v1",
        "source": input_json,
        "num_trials": num_trials,
        "seed": seed,
        "baseline_top_10": baseline_top_10,
        "baseline_weights": DEFAULT_BASELINE_WEIGHTS,
        "stability_summary": stability_summary,
        "recurring_top10_candidates": recurring_top10,
        "boundary_note": (
            "This audit perturbs only the heuristic accessibility weights around the "
            "same stoichiometric capacity ceiling. It tests rank stability, not "
            "physical correctness."
        ),
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", default=DEFAULT_INPUT_JSON)
    parser.add_argument("--num-trials", type=int, default=DEFAULT_NUM_TRIALS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--json-output", default=DEFAULT_OUTPUT_JSON)
    return parser.parse_args()


def main():
    args = parse_args()
    audit = build_audit(args.input_json, args.num_trials, args.seed)
    print("--- CO2 Uptake Proxy Sensitivity Audit ---")
    print(f"Trials:                    {audit['num_trials']}")
    print(f"Seed:                      {audit['seed']}")
    print("")
    print(f"{'Rank':<5} {'Formula':<24} {'Top10 Freq':<11} {'Median Rank':<12} {'Worst Rank'}")
    print("-" * 90)
    for index, row in enumerate(audit["stability_summary"][:10], start=1):
        print(
            f"{index:<5} {row['formula']:<24} {row['top10_frequency']:<11.2%} "
            f"{row['median_rank']:<12} {row['worst_rank']}"
        )

    write_json_output(args.json_output, audit)
    print("")
    print(f"Saved Artifact:             {args.json_output}")


if __name__ == "__main__":
    main()
