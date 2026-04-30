#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from biology_structural_utils import (
    DEFAULT_NULL_TRIALS,
    DEFAULT_SEED,
    load_biology_cohort_registry,
    structural_null_audit,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_JSON = str(ROOT / "Biology_UIL" / "validated" / "null_model_audit_v1.json")


def build_artifact(num_trials: int = DEFAULT_NULL_TRIALS, seed: int = DEFAULT_SEED):
    registry = load_biology_cohort_registry()
    cohort_reports = {}
    null_win_counts = {}

    for cohort_name, cohort in registry.items():
        audit = structural_null_audit(
            cohort["frame"],
            seed=seed,
            num_trials=num_trials,
        )
        cohort_reports[cohort_name] = {
            "display_name": cohort["display_name"],
            "dataset_kind": cohort["dataset_kind"],
            "modality": cohort["modality"],
            **audit,
        }
        null_win_counts[cohort_name] = sum(audit["null_wins"].values())

    return {
        "artifact_type": "null_model_audit_v1",
        "cohort_count": len(cohort_reports),
        "num_trials": num_trials,
        "seed": seed,
        "cohorts": cohort_reports,
        "cross_cohort_summary": {
            "null_win_counts": null_win_counts,
            "stronger_than_null_on_at_least_three_metrics": [
                cohort_name
                for cohort_name, count in null_win_counts.items()
                if count >= 3
            ],
        },
        "boundary_note": (
            "This audit compares observed structural metrics to a feature-wise "
            "permutation null. It tests whether the reported topology and "
            "low-dimensional structure beat a simple dependence-destroying null, "
            "not whether they are universal biological laws."
        ),
    }


def write_json_output(path: str, payload: dict) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a biology null-model audit.")
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--num-trials", type=int, default=DEFAULT_NULL_TRIALS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    artifact = build_artifact(num_trials=args.num_trials, seed=args.seed)
    write_json_output(args.output_json, artifact)

    print("--- UIL Biology Null-Model Audit ---")
    print(f"Cohort Count: {artifact['cohort_count']}")
    print(f"Null Trials:  {artifact['num_trials']}")
    print("Cohort                    Null Wins")
    print("-" * 48)
    for cohort_name, count in artifact["cross_cohort_summary"]["null_win_counts"].items():
        print(f"{cohort_name:<24}{count}")
    print(f"\nSaved Artifact: {args.output_json}")


if __name__ == "__main__":
    main()
