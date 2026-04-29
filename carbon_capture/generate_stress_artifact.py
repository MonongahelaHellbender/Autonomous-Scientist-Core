import argparse
import json
from datetime import date
from pathlib import Path

from cage_stress_test import format_summary, simulate_cage_stress, write_json_output

VETTED_RESULTS_PATH = Path("carbon_capture/vetted_carbon_results.json")
ARTIFACT_DIR = Path("carbon_capture/stress_artifacts")
DEFAULT_FORMULA = "Ca3Si(ClO2)2"
DEFAULT_SEED = 20260429


def load_retained_candidate(formula):
    data = json.loads(VETTED_RESULTS_PATH.read_text())
    for row in data:
        if row.get("formula") == formula and row.get("final_verdict") == "APPROVED":
            return row
    raise ValueError(f"No retained calcium-based candidate found for {formula!r}")


def sanitize_formula(formula):
    cleaned = []
    for char in formula:
        if char.isalnum():
            cleaned.append(char.lower())
        else:
            cleaned.append("_")
    return "".join(cleaned).strip("_")


def build_artifact(formula, seed):
    candidate = load_retained_candidate(formula)
    stress_result = simulate_cage_stress(seed=seed)

    return {
        "artifact_type": "deterministic_stress_probe",
        "created_on": str(date.today()),
        "formula": formula,
        "seed": seed,
        "seed_policy": "fixed date seed for deterministic replay",
        "candidate_source": str(VETTED_RESULTS_PATH),
        "candidate_record": candidate,
        "stress_result": stress_result,
        "boundary_note": (
            "This artifact is formula-linked and reproducible, but the current "
            "stress model is still a generic thermal proxy and does not yet "
            "encode composition-specific physics."
        ),
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--formula", default=DEFAULT_FORMULA)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--json-output")
    return parser.parse_args()


def main():
    args = parse_args()
    artifact = build_artifact(args.formula, args.seed)
    stress_result = artifact["stress_result"]

    print(format_summary(stress_result))
    print("")
    print(f"Formula:                 {artifact['formula']}")
    print(f"Candidate Verdict:       {artifact['candidate_record']['final_verdict']}")
    print(f"Boundary Note:           {artifact['boundary_note']}")

    if args.json_output:
        output_path = args.json_output
    else:
        output_path = ARTIFACT_DIR / (
            f"{sanitize_formula(args.formula)}_stress_artifact_seed_{args.seed}.json"
        )

    write_json_output(output_path, artifact)
    print(f"Saved Artifact:          {output_path}")


if __name__ == "__main__":
    main()
