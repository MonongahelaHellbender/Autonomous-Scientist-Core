import argparse
import json
import statistics
from datetime import date
from pathlib import Path

from cage_stress_test import simulate_cage_stress, write_json_output

ARTIFACT_DIR = Path("carbon_capture/stress_artifacts")
DEFAULT_NUM_TRIALS = 2000


def build_audit(num_trials):
    results = [simulate_cage_stress(seed=seed) for seed in range(num_trials)]
    failure_rates = [row["failure_rate"] for row in results]
    peak_temps = [row["peak_temp_c"] for row in results]

    return {
        "artifact_type": "deterministic_stress_model_audit",
        "created_on": str(date.today()),
        "seed_policy": f"sequential integer seeds 0..{num_trials - 1}",
        "num_trials": num_trials,
        "summary": {
            "failure_rate_mean": statistics.mean(failure_rates),
            "failure_rate_min": min(failure_rates),
            "failure_rate_max": max(failure_rates),
            "failure_rate_median": statistics.median(failure_rates),
            "peak_temp_mean_c": statistics.mean(peak_temps),
            "peak_temp_min_c": min(peak_temps),
            "peak_temp_max_c": max(peak_temps),
            "peak_temp_median_c": statistics.median(peak_temps),
            "fraction_below_pass_threshold": sum(
                row["verdict"] == "ROBUST" for row in results
            )
            / num_trials,
        },
        "boundary_note": (
            "This audit measures replayable behavior of the generic thermal proxy. "
            "It does not prove composition-specific stress performance."
        ),
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-trials", type=int, default=DEFAULT_NUM_TRIALS)
    parser.add_argument("--json-output")
    return parser.parse_args()


def main():
    args = parse_args()
    audit = build_audit(args.num_trials)

    print("--- Calcium-Based Stress Model Audit ---")
    print(f"Trials:                   {audit['num_trials']}")
    print(
        "Mean Failure Rate:        "
        f"{audit['summary']['failure_rate_mean']:.4%}"
    )
    print(
        "Median Failure Rate:      "
        f"{audit['summary']['failure_rate_median']:.4%}"
    )
    print(
        "Pass Fraction (<1%):      "
        f"{audit['summary']['fraction_below_pass_threshold']:.2%}"
    )

    if args.json_output:
        output_path = args.json_output
    else:
        output_path = ARTIFACT_DIR / (
            f"stress_model_audit_{args.num_trials}_seeds_0_to_{args.num_trials - 1}.json"
        )

    write_json_output(output_path, audit)
    print(f"Saved Artifact:           {output_path}")


if __name__ == "__main__":
    main()
