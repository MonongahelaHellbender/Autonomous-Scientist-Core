import argparse
import json
import random
import statistics
from pathlib import Path

from thermochemical_carbonation_corroboration import DEFAULT_WEIGHTS, build_corroboration_rows

DEFAULT_INPUT_JSON = "carbon_capture/co2_uptake_proxy_v1.json"
DEFAULT_OUTPUT_JSON = "carbon_capture/corroboration_artifacts/thermochemical_corroboration_sensitivity_v1.json"
DEFAULT_NUM_TRIALS = 1000
DEFAULT_SEED = 20260429


def write_json_output(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))


def load_uptake_rows(path):
    payload = json.loads(Path(path).read_text())
    return payload["candidates"]


def perturbed_weights(rng):
    return {key: value * rng.uniform(0.8, 1.2) for key, value in DEFAULT_WEIGHTS.items()}


def build_audit(input_json, num_trials, seed):
    uptake_rows = load_uptake_rows(input_json)
    baseline_rows, _ = build_corroboration_rows(uptake_rows)
    baseline_top_10 = [row["formula"] for row in baseline_rows[:10]]

    rng = random.Random(seed)
    rank_samples = {formula: [] for formula in baseline_top_10}
    class_agreement = {formula: [] for formula in baseline_top_10}
    top10_frequency = {}

    for _ in range(num_trials):
        rows, _ = build_corroboration_rows(uptake_rows, weights=perturbed_weights(rng))
        rank_map = {row["formula"]: rank for rank, row in enumerate(rows, start=1)}
        class_map = {
            row["formula"]: row["thermochemical_corroboration"]["corroboration_class"]
            for row in rows
        }
        for row in rows[:10]:
            top10_frequency[row["formula"]] = top10_frequency.get(row["formula"], 0) + 1
        for formula in baseline_top_10:
            rank_samples[formula].append(rank_map[formula])
            class_agreement[formula].append(class_map[formula])

    stability_summary = []
    for formula in baseline_top_10:
        baseline_class = next(
            row["thermochemical_corroboration"]["corroboration_class"]
            for row in baseline_rows
            if row["formula"] == formula
        )
        classes = class_agreement[formula]
        stability_summary.append(
            {
                "formula": formula,
                "baseline_rank": baseline_top_10.index(formula) + 1,
                "baseline_class": baseline_class,
                "top10_frequency": top10_frequency.get(formula, 0) / num_trials,
                "median_rank": statistics.median(rank_samples[formula]),
                "worst_rank": max(rank_samples[formula]),
                "class_agreement_frequency": sum(c == baseline_class for c in classes) / num_trials,
            }
        )

    return {
        "artifact_type": "thermochemical_corroboration_sensitivity_v1",
        "source": input_json,
        "num_trials": num_trials,
        "seed": seed,
        "baseline_top_10": baseline_top_10,
        "stability_summary": stability_summary,
        "boundary_note": (
            "This audit perturbs only the corroboration weights around the same "
            "uptake artifact. It tests pathway-label stability, not physical truth."
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
    print("--- Thermochemical Corroboration Sensitivity Audit ---")
    print(f"Trials:                     {audit['num_trials']}")
    print(f"Seed:                       {audit['seed']}")
    print("")
    print(
        f"{'Rank':<5} {'Formula':<24} {'Top10 Freq':<11} {'Median Rank':<12} {'Class Agree'}"
    )
    print("-" * 100)
    for index, row in enumerate(audit["stability_summary"][:10], start=1):
        print(
            f"{index:<5} {row['formula']:<24} {row['top10_frequency']:<11.2%} "
            f"{row['median_rank']:<12} {row['class_agreement_frequency']:.2%}"
        )

    write_json_output(args.json_output, audit)
    print("")
    print(f"Saved Artifact:             {args.json_output}")


if __name__ == "__main__":
    main()
