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
from reinforced_exact_lane_experimental_packet import build_packet

DEFAULT_OUTPUT_JSON = (
    "carbon_capture/corroboration_artifacts/"
    "reinforced_exact_lane_experimental_packet_sensitivity_v1.json"
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
    exact_rows = load_exact_subset_rows(input_json)
    baseline_calibrated_rows, _ = build_calibration_rows(exact_rows)
    baseline_packet = build_packet(baseline_calibrated_rows)

    baseline_groups = baseline_packet["candidate_groups"]
    baseline_anchor_set = baseline_groups["reinforced_anchors"]
    baseline_plausible_set = baseline_groups["plausible_restructuring"]
    baseline_surface_set = baseline_groups["surface_controls"]
    baseline_contrast_set = baseline_groups["contrast_candidates"]

    rng = random.Random(seed)
    anchor_membership = {formula: 0 for formula in baseline_anchor_set}
    plausible_membership = {formula: 0 for formula in baseline_plausible_set}
    surface_membership = {formula: 0 for formula in baseline_surface_set}
    contrast_membership = {formula: 0 for formula in baseline_contrast_set}
    anchor_overlap_scores = []
    anchor_rank_samples = {formula: [] for formula in baseline_anchor_set}

    for _ in range(num_trials):
        calibrated_rows, _ = build_calibration_rows(
            exact_rows,
            weights=perturbed_weights(rng),
            carbonate_support=perturbed_support_map(DEFAULT_CARBONATE_SUPPORT, rng),
            residual_support=perturbed_support_map(DEFAULT_RESIDUAL_SUPPORT, rng),
        )
        packet = build_packet(calibrated_rows)
        groups = packet["candidate_groups"]
        anchor_set = set(groups["reinforced_anchors"])
        plausible_set = set(groups["plausible_restructuring"])
        surface_set = set(groups["surface_controls"])
        contrast_set = set(groups["contrast_candidates"])
        anchor_overlap_scores.append(
            len(anchor_set & set(baseline_anchor_set)) / len(baseline_anchor_set)
        )

        rank_map = {
            row["formula"]: row["priority_rank"] for row in packet["candidate_dossiers"]
        }

        for formula in baseline_anchor_set:
            anchor_membership[formula] += int(formula in anchor_set)
            anchor_rank_samples[formula].append(rank_map.get(formula, 999))
        for formula in baseline_plausible_set:
            plausible_membership[formula] += int(formula in plausible_set)
        for formula in baseline_surface_set:
            surface_membership[formula] += int(formula in surface_set)
        for formula in baseline_contrast_set:
            contrast_membership[formula] += int(formula in contrast_set)

    anchor_summary = []
    for formula in baseline_anchor_set:
        anchor_summary.append(
            {
                "formula": formula,
                "anchor_membership_frequency": anchor_membership[formula] / num_trials,
                "median_priority_rank": statistics.median(anchor_rank_samples[formula]),
                "worst_priority_rank": max(anchor_rank_samples[formula]),
            }
        )

    return {
        "artifact_type": "reinforced_exact_lane_experimental_packet_sensitivity_v1",
        "source": input_json,
        "num_trials": num_trials,
        "seed": seed,
        "baseline_candidate_groups": baseline_groups,
        "anchor_overlap_mean": statistics.mean(anchor_overlap_scores),
        "anchor_overlap_min": min(anchor_overlap_scores),
        "anchor_summary": anchor_summary,
        "plausible_membership_frequency": {
            formula: count / num_trials for formula, count in plausible_membership.items()
        },
        "surface_membership_frequency": {
            formula: count / num_trials for formula, count in surface_membership.items()
        },
        "contrast_membership_frequency": {
            formula: count / num_trials for formula, count in contrast_membership.items()
        },
        "boundary_note": (
            "This audit perturbs the reinforced-exact packet through the same "
            "thermodynamic calibration knobs used upstream. It tests packet "
            "grouping stability, not experimental truth."
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

    print("--- Reinforced Exact Lane Experimental Packet Audit ---")
    print(f"Trials:                         {audit['num_trials']}")
    print(f"Seed:                           {audit['seed']}")
    print(f"Mean Anchor Overlap:            {audit['anchor_overlap_mean']:.2%}")
    print(f"Min Anchor Overlap:             {audit['anchor_overlap_min']:.2%}")
    print("")
    print(
        f"{'Rank':<5} {'Formula':<24} {'Anchor Freq':<12} {'Median Rank':<12} {'Worst Rank'}"
    )
    print("-" * 104)
    for index, row in enumerate(audit["anchor_summary"], start=1):
        print(
            f"{index:<5} {row['formula']:<24} {row['anchor_membership_frequency']:<12.2%} "
            f"{row['median_priority_rank']:<12} {row['worst_priority_rank']}"
        )

    write_json_output(args.json_output, audit)
    print("")
    print(f"Saved Artifact:                 {args.json_output}")


if __name__ == "__main__":
    main()
