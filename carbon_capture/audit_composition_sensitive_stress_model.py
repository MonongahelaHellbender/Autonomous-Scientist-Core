import argparse
import statistics
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
DEFAULT_FORMULA = "Ca3Si(ClO2)2"
DEFAULT_NUM_TRIALS = 2000


def load_candidates(input_json=None):
    if input_json:
        return load_candidate_rows(input_json)
    return load_retained_candidates()


def slugify_formula(formula):
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in formula).strip("_")


def build_audit(formula, num_trials, input_json=None):
    source = input_json or DEFAULT_INPUT_JSON
    candidates = load_candidates(source)
    stats, feature_map = build_stats(candidates)
    candidate = next((row for row in candidates if row["formula"] == formula), None)
    if candidate is None:
        raise ValueError(f"{formula} not found in {source}")

    runs = [
        run_composition_sensitive_stress(candidate, stats, feature_map, seed)
        for seed in range(num_trials)
    ]
    failures = [row["stress_result"]["failure_rate"] for row in runs]
    peaks = [row["stress_result"]["peak_temp_c"] for row in runs]

    return {
        "artifact_type": "composition_sensitive_stress_audit",
        "source": source,
        "formula": formula,
        "num_trials": num_trials,
        "seed_range": [0, num_trials - 1],
        "composition_conditioning": runs[0]["composition_conditioning"],
        "composition_profile": runs[0]["composition_profile"],
        "summary": {
            "mean_failure_rate": statistics.mean(failures),
            "median_failure_rate": statistics.median(failures),
            "min_failure_rate": min(failures),
            "max_failure_rate": max(failures),
            "pass_fraction_below_1pct": sum(rate < 0.01 for rate in failures) / len(failures),
            "mean_peak_temp_c": statistics.mean(peaks),
            "max_peak_temp_c": max(peaks),
        },
        "runs": [
            {
                "seed": row["stress_result"]["seed"],
                "failure_rate": row["stress_result"]["failure_rate"],
                "peak_temp_c": row["stress_result"]["peak_temp_c"],
                "mean_temp_c": row["stress_result"]["mean_temp_c"],
                "verdict": row["stress_result"]["verdict"],
            }
            for row in runs
        ],
        "boundary_note": (
            "This audit tests replay stability for the composition-sensitive proxy "
            "on one named candidate across many random seeds. It does not convert "
            "the model into first-principles physics."
        ),
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--formula", default=DEFAULT_FORMULA)
    parser.add_argument("--num-trials", type=int, default=DEFAULT_NUM_TRIALS)
    parser.add_argument("--input-json", default=DEFAULT_INPUT_JSON)
    parser.add_argument("--json-output")
    return parser.parse_args()


def main():
    args = parse_args()
    audit = build_audit(args.formula, args.num_trials, input_json=args.input_json)

    summary = audit["summary"]
    print("--- Composition-Sensitive Stress Audit ---")
    print(f"Formula:                 {audit['formula']}")
    print(f"Source:                  {audit['source']}")
    print(f"Trials:                  {audit['num_trials']}")
    print(f"Mean Failure Rate:       {summary['mean_failure_rate']:.4%}")
    print(f"Median Failure Rate:     {summary['median_failure_rate']:.4%}")
    print(f"Pass Fraction <1%:       {summary['pass_fraction_below_1pct']:.2%}")
    print(f"Mean Peak Temp:          {summary['mean_peak_temp_c']:.2f}°C")
    print(f"Max Peak Temp:           {summary['max_peak_temp_c']:.2f}°C")

    if args.json_output:
        output_path = Path(args.json_output)
    else:
        output_path = (
            ARTIFACT_DIR
            / f"{slugify_formula(args.formula)}_composition_sensitive_stress_audit_{args.num_trials}_seeds_0_to_{args.num_trials - 1}.json"
        )
    write_json_output(output_path, audit)
    print(f"Saved Artifact:          {output_path}")


if __name__ == "__main__":
    main()
