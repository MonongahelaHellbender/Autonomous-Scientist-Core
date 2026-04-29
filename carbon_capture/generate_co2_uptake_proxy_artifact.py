import argparse
import json
from datetime import date
from pathlib import Path

from co2_uptake_proxy import build_proxy_rows, load_candidates, select_formula_representatives

DEFAULT_INPUT_JSON = "carbon_capture/abundance_safe_subset_v1.json"
DEFAULT_OUTPUT_JSON = "carbon_capture/co2_uptake_proxy_v1.json"
DEFAULT_TOP_N = 25


def write_json_output(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))


def build_artifact(input_json, top_n):
    source_rows = load_candidates(input_json)
    representatives, multiplicity = select_formula_representatives(source_rows)
    proxy_rows, stats = build_proxy_rows(representatives)
    duplicate_formula_count = sum(1 for count in multiplicity.values() if count > 1)
    return {
        "artifact_type": "co2_uptake_proxy_v1",
        "created_on": str(date.today()),
        "source": input_json,
        "source_row_count": len(source_rows),
        "formula_level_candidate_count": len(representatives),
        "duplicate_formula_count": duplicate_formula_count,
        "formula_representative_rule": "highest pore space, then strongest stability",
        "stats_reference": stats,
        "top_candidates_by_readiness": proxy_rows[:top_n],
        "top_candidates_by_theoretical_capacity": sorted(
            proxy_rows,
            key=lambda row: (
                -row["theoretical_capacity"]["theoretical_capacity_gco2_per_g"],
                -row["uptake_proxy"]["readiness_score"],
                row["formula"],
            ),
        )[:top_n],
        "candidates": proxy_rows,
        "boundary_note": (
            "This artifact combines a stoichiometric carbonate-capacity upper bound "
            "with accessibility and chemistry penalties. It is stronger than a "
            "purely heuristic uptake score, but it is still a screening artifact "
            "rather than measured CO2 adsorption or throughput data."
        ),
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", default=DEFAULT_INPUT_JSON)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--json-output", default=DEFAULT_OUTPUT_JSON)
    return parser.parse_args()


def main():
    args = parse_args()
    artifact = build_artifact(args.input_json, args.top_n)
    print("--- CO2 Uptake Proxy v1 ---")
    print(f"Source Rows:                {artifact['source_row_count']}")
    print(f"Formula-Level Candidates:   {artifact['formula_level_candidate_count']}")
    print(f"Duplicate Formula Count:    {artifact['duplicate_formula_count']}")
    print("")
    print(
        f"{'Rank':<5} {'Formula':<24} {'Readiness':<10} {'Eff g/g':<10} "
        f"{'Ceiling g/g':<12} {'Mode'}"
    )
    print("-" * 110)
    for index, row in enumerate(artifact["top_candidates_by_readiness"][:10], start=1):
        metrics = row["uptake_proxy"]
        capacity = row["theoretical_capacity"]
        print(
            f"{index:<5} {row['formula']:<24} {metrics['readiness_score']:<10.2f} "
            f"{metrics['effective_uptake_proxy_gco2_per_g']:<10.3f} "
            f"{capacity['theoretical_capacity_gco2_per_g']:<12.3f} {metrics['uptake_mode']}"
        )

    write_json_output(args.json_output, artifact)
    print("")
    print(f"Saved Artifact:             {args.json_output}")


if __name__ == "__main__":
    main()
