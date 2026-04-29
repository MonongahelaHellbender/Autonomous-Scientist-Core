import argparse
import json
import random
import statistics
from pathlib import Path

from exact_subset_thermodynamic_calibration import (
    DEFAULT_CALIBRATION_WEIGHTS,
    DEFAULT_CARBONATE_SUPPORT,
    DEFAULT_INPUT_JSON,
    DEFAULT_RESIDUAL_SUPPORT,
    build_calibration_rows,
    load_exact_subset_rows,
)

DEFAULT_OUTPUT_JSON = (
    "carbon_capture/corroboration_artifacts/"
    "exact_subset_thermodynamic_calibration_sensitivity_v1.json"
)
DEFAULT_NUM_TRIALS = 1000
DEFAULT_SEED = 20260429


def write_json_output(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))


def perturbed_weights(rng):
    return {
        key: value * rng.uniform(0.85, 1.15)
        for key, value in DEFAULT_CALIBRATION_WEIGHTS.items()
    }


def perturbed_support_map(base_map, rng, low=0.55, high=1.05):
    return {
        key: max(low, min(high, value + rng.uniform(-0.05, 0.05)))
        for key, value in base_map.items()
    }


def build_audit(input_json, num_trials, seed):
    rows = load_exact_subset_rows(input_json)
    baseline_rows, _ = build_calibration_rows(rows)
    baseline_top_10 = [row["formula"] for row in baseline_rows[:10]]

    rng = random.Random(seed)
    rank_samples = {formula: [] for formula in baseline_top_10}
    band_agreement = {formula: [] for formula in baseline_top_10}
    top10_frequency = {}

    for _ in range(num_trials):
        trial_rows, _ = build_calibration_rows(
            rows,
            weights=perturbed_weights(rng),
            carbonate_support=perturbed_support_map(DEFAULT_CARBONATE_SUPPORT, rng),
            residual_support=perturbed_support_map(DEFAULT_RESIDUAL_SUPPORT, rng),
        )
        rank_map = {row["formula"]: rank for rank, row in enumerate(trial_rows, start=1)}
        band_map = {
            row["formula"]: row["thermodynamic_calibration"]["calibration_band"]
            for row in trial_rows
        }
        for row in trial_rows[:10]:
            top10_frequency[row["formula"]] = top10_frequency.get(row["formula"], 0) + 1
        for formula in baseline_top_10:
            rank_samples[formula].append(rank_map[formula])
            band_agreement[formula].append(band_map[formula])

    stability_summary = []
    for formula in baseline_top_10:
        baseline_band = next(
            row["thermodynamic_calibration"]["calibration_band"]
            for row in baseline_rows
            if row["formula"] == formula
        )
        bands = band_agreement[formula]
        stability_summary.append(
            {
                "formula": formula,
                "baseline_rank": baseline_top_10.index(formula) + 1,
                "baseline_band": baseline_band,
                "top10_frequency": top10_frequency.get(formula, 0) / num_trials,
                "median_rank": statistics.median(rank_samples[formula]),
                "worst_rank": max(rank_samples[formula]),
                "band_agreement_frequency": sum(
                    band == baseline_band for band in bands
                ) / num_trials,
            }
        )

    return {
        "artifact_type": "exact_subset_thermodynamic_calibration_sensitivity_v1",
        "source": input_json,
        "num_trials": num_trials,
        "seed": seed,
        "baseline_top_10": baseline_top_10,
        "stability_summary": stability_summary,
        "boundary_note": (
            "This audit perturbs the calibration weights and the surrogate "
            "product-family support coefficients around the same exact-subset "
            "artifact. It tests rank and band stability, not physical truth."
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

    print("--- Exact Subset Thermodynamic Calibration Audit ---")
    print(f"Trials:                         {audit['num_trials']}")
    print(f"Seed:                           {audit['seed']}")
    print("")
    print(
        f"{'Rank':<5} {'Formula':<24} {'Top10 Freq':<11} {'Median Rank':<12} {'Band Agree'}"
    )
    print("-" * 104)
    for index, row in enumerate(audit["stability_summary"][:10], start=1):
        print(
            f"{index:<5} {row['formula']:<24} {row['top10_frequency']:<11.2%} "
            f"{row['median_rank']:<12} {row['band_agreement_frequency']:.2%}"
        )

    write_json_output(args.json_output, audit)
    print("")
    print(f"Saved Artifact:                 {args.json_output}")


if __name__ == "__main__":
    main()
