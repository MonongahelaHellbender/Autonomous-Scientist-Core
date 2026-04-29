import argparse
import json
from pathlib import Path

import numpy as np

DEFAULT_BASELINE_TEMP_C = 582.0
DEFAULT_NOISE_STD = 0.05
DEFAULT_NUM_INTERVALS = 1000
DEFAULT_FAILURE_THRESHOLD_C = 650.0
DEFAULT_PASS_THRESHOLD = 0.01


def simulate_cage_stress(
    seed=None,
    baseline_temp_c=DEFAULT_BASELINE_TEMP_C,
    noise_std=DEFAULT_NOISE_STD,
    num_intervals=DEFAULT_NUM_INTERVALS,
    failure_threshold_c=DEFAULT_FAILURE_THRESHOLD_C,
    pass_threshold=DEFAULT_PASS_THRESHOLD,
):
    rng = np.random.default_rng(seed)
    noise_vector = rng.normal(0, noise_std, num_intervals)
    simulated_temps = baseline_temp_c * (1 + noise_vector)
    failure_mask = simulated_temps > failure_threshold_c
    failure_rate = float(np.mean(failure_mask))
    peak_temp_c = float(np.max(simulated_temps))
    mean_temp_c = float(np.mean(simulated_temps))

    return {
        "seed": seed,
        "baseline_temp_c": baseline_temp_c,
        "noise_std": noise_std,
        "num_intervals": num_intervals,
        "failure_threshold_c": failure_threshold_c,
        "pass_threshold": pass_threshold,
        "mean_temp_c": mean_temp_c,
        "peak_temp_c": peak_temp_c,
        "failure_rate": failure_rate,
        "verdict": "ROBUST" if failure_rate < pass_threshold else "VULNERABLE",
        "model_scope": "generic calcium-based thermal hardening proxy",
        "candidate_specific_physics": False,
    }


def format_summary(result):
    lines = [
        "--- UIL Material Science: Calcium-Based Cage Adversarial Stress Test ---",
        f"Seed:                    {result['seed']}",
        f"Mean Exposure Temp:      {result['mean_temp_c']:.2f}°C",
        f"Peak Temperature Spike:  {result['peak_temp_c']:.2f}°C",
        f"Structural Failure Rate: {result['failure_rate']:.2%}",
    ]

    if result["verdict"] == "ROBUST":
        lines.extend(
            [
                "",
                "[VERDICT] CAGE IS ROBUST.",
                "Finding: The current proxy stress model stayed below the pass threshold.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "[VERDICT] CAGE IS VULNERABLE.",
                "Finding: The current proxy stress model crossed the pass threshold.",
            ]
        )

    return "\n".join(lines)


def write_json_output(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--baseline-temp-c", type=float, default=DEFAULT_BASELINE_TEMP_C)
    parser.add_argument("--noise-std", type=float, default=DEFAULT_NOISE_STD)
    parser.add_argument("--num-intervals", type=int, default=DEFAULT_NUM_INTERVALS)
    parser.add_argument(
        "--failure-threshold-c", type=float, default=DEFAULT_FAILURE_THRESHOLD_C
    )
    parser.add_argument("--pass-threshold", type=float, default=DEFAULT_PASS_THRESHOLD)
    parser.add_argument("--json-output")
    return parser.parse_args()


def main():
    args = parse_args()
    result = simulate_cage_stress(
        seed=args.seed,
        baseline_temp_c=args.baseline_temp_c,
        noise_std=args.noise_std,
        num_intervals=args.num_intervals,
        failure_threshold_c=args.failure_threshold_c,
        pass_threshold=args.pass_threshold,
    )
    print(format_summary(result))

    if args.json_output:
        write_json_output(args.json_output, result)


if __name__ == "__main__":
    main()
