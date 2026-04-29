import argparse
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
DEFAULT_SEED = 20260429


def load_candidates(input_json=None):
    if input_json:
        return load_candidate_rows(input_json)
    return load_retained_candidates()


def slugify_formula(formula):
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in formula).strip("_")


def build_artifact(formula, seed, input_json=None):
    source = input_json or DEFAULT_INPUT_JSON
    candidates = load_candidates(source)
    stats, feature_map = build_stats(candidates)
    candidate = next((row for row in candidates if row["formula"] == formula), None)
    if candidate is None:
        raise ValueError(f"{formula} not found in {source}")
    result = run_composition_sensitive_stress(candidate, stats, feature_map, seed)
    return {
        "artifact_type": "composition_sensitive_stress_artifact",
        "source": source,
        **result,
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--formula", default=DEFAULT_FORMULA)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--input-json", default=DEFAULT_INPUT_JSON)
    parser.add_argument("--json-output")
    return parser.parse_args()


def main():
    args = parse_args()
    artifact = build_artifact(args.formula, args.seed, input_json=args.input_json)

    print("--- Composition-Sensitive Calcium Stress Artifact ---")
    print(f"Formula:                 {artifact['formula']}")
    print(f"Seed:                    {artifact['stress_result']['seed']}")
    print(f"Source:                  {artifact['source']}")
    print(f"Failure Rate:            {artifact['stress_result']['failure_rate']:.2%}")
    print(f"Failure Threshold:       {artifact['stress_result']['failure_threshold_c']:.2f}°C")
    print(f"Mean Exposure Temp:      {artifact['stress_result']['mean_temp_c']:.2f}°C")
    print(f"Peak Temperature Spike:  {artifact['stress_result']['peak_temp_c']:.2f}°C")
    print(f"Family Tags:             {', '.join(artifact['composition_profile']['family_tags'])}")

    if args.json_output:
        output_path = Path(args.json_output)
    else:
        output_path = (
            ARTIFACT_DIR
            / f"{slugify_formula(args.formula)}_composition_sensitive_stress_artifact_seed_{args.seed}.json"
        )
    write_json_output(output_path, artifact)
    print(f"Saved Artifact:          {output_path}")


if __name__ == "__main__":
    main()
