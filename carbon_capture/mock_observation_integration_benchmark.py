#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import integrate_reinforced_exact_lane_observations as integration


ROOT = Path(__file__).resolve().parents[1]
CARBON_ROOT = ROOT / "carbon_capture"
TEMPLATE_PATH = CARBON_ROOT / "reinforced_exact_lane_observation_template_v1.json"
SYNTHETIC_INPUT = CARBON_ROOT / "corroboration_artifacts" / "synthetic_observation_template_v1.json"
OUTPUT = CARBON_ROOT / "corroboration_artifacts" / "mock_observation_integration_benchmark_v1.json"

SUPPORTED_FORMULAS = {"Ca3SiO5", "Ca2SiO4", "CaMgSiO4"}
PARTIAL_FORMULAS = {"Ca3Mg(SiO4)2", "CaSiO3"}
CONTRADICTED_FORMULAS = {
    "CaAl12Si4O27",
    "CaAl2(Si3O8)2",
    "CaAl2(SiO4)2",
    "CaSi2(BO4)2",
}


def synthetic_record(record: dict) -> dict:
    updated = json.loads(json.dumps(record))
    formula = updated["formula"]
    if formula in SUPPORTED_FORMULAS:
        updated["completed"] = True
        updated["technique_results"] = {
            key: "SUPPORTS" for key in updated["required_techniques"]
        }
        updated["overall_condition_outcome"] = "SUPPORTS"
        updated["notes"] = "Synthetic benchmark support case."
    elif formula in PARTIAL_FORMULAS:
        updated["completed"] = True
        updated["technique_results"] = {
            key: "MIXED" if index % 2 else "SUPPORTS"
            for index, key in enumerate(updated["required_techniques"])
        }
        updated["overall_condition_outcome"] = "MIXED"
        updated["notes"] = "Synthetic benchmark mixed case."
    elif formula in CONTRADICTED_FORMULAS:
        updated["completed"] = True
        updated["technique_results"] = {
            key: "CONTRADICTS" for key in updated["required_techniques"]
        }
        updated["overall_condition_outcome"] = "CONTRADICTS"
        updated["notes"] = "Synthetic benchmark contradiction case."
    return updated


def build_benchmark() -> dict:
    template = json.loads(TEMPLATE_PATH.read_text())
    synthetic_template = {
        **template,
        "artifact_type": "synthetic_observation_template_v1",
        "observation_records": [synthetic_record(record) for record in template["observation_records"]],
    }
    SYNTHETIC_INPUT.parent.mkdir(parents=True, exist_ok=True)
    SYNTHETIC_INPUT.write_text(json.dumps(synthetic_template, indent=2) + "\n")

    integrated = integration.build_artifact(str(SYNTHETIC_INPUT))
    by_formula = {row["formula"]: row["candidate_status"] for row in integrated["candidate_status"]}

    benchmark = {
        "artifact_type": "mock_observation_integration_benchmark_v1",
        "source_template": str(TEMPLATE_PATH),
        "synthetic_input": str(SYNTHETIC_INPUT),
        "integrated_status_artifact": integrated,
        "expected_status_examples": {
            "supported_ready_for_review": sorted(SUPPORTED_FORMULAS),
            "partial_signal_present": sorted(PARTIAL_FORMULAS),
            "contradicted_signal_present": sorted(CONTRADICTED_FORMULAS),
        },
        "observed_status_examples": {
            "supported_ready_for_review": sorted(
                formula for formula in SUPPORTED_FORMULAS if by_formula.get(formula) == "supported_ready_for_review"
            ),
            "partial_signal_present": sorted(
                formula for formula in PARTIAL_FORMULAS if by_formula.get(formula) == "partial_signal_present"
            ),
            "contradicted_signal_present": sorted(
                formula for formula in CONTRADICTED_FORMULAS if by_formula.get(formula) == "contradicted_signal_present"
            ),
        },
        "boundary_note": (
            "This is a synthetic observation benchmark. It does not add real evidence; "
            "it checks whether the observation integration logic reacts sensibly to "
            "supporting, mixed, and contradicting records."
        ),
    }
    return benchmark


def main() -> None:
    artifact = build_benchmark()
    OUTPUT.write_text(json.dumps(artifact, indent=2) + "\n")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
