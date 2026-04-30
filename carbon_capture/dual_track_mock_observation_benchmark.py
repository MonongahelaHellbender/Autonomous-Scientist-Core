#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import integrate_dual_track_campaign_observations as integration


ROOT = Path(__file__).resolve().parents[1]
CARBON_ROOT = ROOT / "carbon_capture"
TEMPLATE_PATH = CARBON_ROOT / "co2_mineralization_dual_track_observation_template_v1.json"
SYNTHETIC_INPUT = CARBON_ROOT / "corroboration_artifacts" / "synthetic_dual_track_observation_template_v1.json"
OUTPUT = CARBON_ROOT / "corroboration_artifacts" / "dual_track_mock_observation_benchmark_v1.json"

TRACK_A_SUPPORTED = {"Ca3SiO5", "Ca2SiO4", "CaMgSiO4"}
TRACK_A_PARTIAL = {"Ca3Mg(SiO4)2"}
TRACK_A_CONTRADICTED = {"CaSiO3", "CaAl12Si4O27"}
TRACK_B_PARTIAL = {"Ca11AlSi3ClO18", "Ca11Si4SO18", "Ca9Si4O17F", "Ca5Si2CO11"}


def midpoint(window):
    return round((window[0] + window[1]) / 2, 3)


def populate_runtime_metadata(updated: dict) -> None:
    suggested = updated.get("suggested_window")
    if not suggested:
        return

    updated["actual_run_metadata"] = {
        "temperature_c": midpoint(suggested["temperature_c_window"]),
        "relative_humidity_percent": midpoint(suggested["relative_humidity_percent_window"]),
        "dwell_hours": midpoint(suggested["dwell_hours_window"]),
        "co2_environment": suggested["co2_environment"],
        "particle_size_note": suggested["particle_size_guidance"],
        "sample_mass_mg": 50.0,
        "operator_batch_id": "synthetic-benchmark-batch",
    }


def synthetic_record(record: dict) -> dict:
    updated = json.loads(json.dumps(record))
    formula = updated["formula"]
    if formula in TRACK_A_SUPPORTED:
        populate_runtime_metadata(updated)
        updated["completed"] = True
        updated["technique_results"] = {
            key: "SUPPORTS" for key in updated["required_techniques"]
        }
        updated["overall_condition_outcome"] = "SUPPORTS"
        updated["measured_mass_change_percent"] = 7.5
        updated["measured_carbonate_signal_strength"] = "STRONG"
        updated["observed_phase_family"] = ["carbonate_product", "residual_silica_or_silicate"]
        updated["notes"] = "Synthetic benchmark support case."
    elif formula in TRACK_A_PARTIAL or formula in TRACK_B_PARTIAL:
        populate_runtime_metadata(updated)
        updated["completed"] = True
        updated["technique_results"] = {
            key: "MIXED" if index % 2 else "SUPPORTS"
            for index, key in enumerate(updated["required_techniques"])
        }
        updated["overall_condition_outcome"] = "MIXED"
        updated["measured_mass_change_percent"] = 3.2
        updated["measured_carbonate_signal_strength"] = "MODERATE"
        updated["observed_phase_family"] = ["partial_carbonate_signal"]
        updated["notes"] = "Synthetic benchmark mixed case."
    elif formula in TRACK_A_CONTRADICTED:
        populate_runtime_metadata(updated)
        updated["completed"] = True
        updated["technique_results"] = {
            key: "CONTRADICTS" for key in updated["required_techniques"]
        }
        updated["overall_condition_outcome"] = "CONTRADICTS"
        updated["measured_mass_change_percent"] = 0.2
        updated["measured_carbonate_signal_strength"] = "ABSENT"
        updated["observed_phase_family"] = ["parent_only"]
        updated["notes"] = "Synthetic benchmark contradiction case."
    return updated


def build_benchmark() -> dict:
    template = json.loads(TEMPLATE_PATH.read_text())
    synthetic_template = {
        **template,
        "artifact_type": "synthetic_dual_track_observation_template_v1",
        "observation_records": [synthetic_record(record) for record in template["observation_records"]],
    }
    SYNTHETIC_INPUT.parent.mkdir(parents=True, exist_ok=True)
    SYNTHETIC_INPUT.write_text(json.dumps(synthetic_template, indent=2) + "\n")

    integrated = integration.build_artifact(str(SYNTHETIC_INPUT))
    by_formula = {row["formula"]: row["candidate_status"] for row in integrated["candidate_status"]}

    return {
        "artifact_type": "dual_track_mock_observation_benchmark_v1",
        "source_template": str(TEMPLATE_PATH),
        "synthetic_input": str(SYNTHETIC_INPUT),
        "integrated_status_artifact": integrated,
        "expected_status_examples": {
            "supported_ready_for_review": sorted(TRACK_A_SUPPORTED),
            "partial_signal_present": sorted(TRACK_A_PARTIAL | TRACK_B_PARTIAL),
            "contradicted_signal_present": sorted(TRACK_A_CONTRADICTED),
        },
        "observed_status_examples": {
            "supported_ready_for_review": sorted(
                formula for formula in TRACK_A_SUPPORTED if by_formula.get(formula) == "supported_ready_for_review"
            ),
            "partial_signal_present": sorted(
                formula
                for formula in (TRACK_A_PARTIAL | TRACK_B_PARTIAL)
                if by_formula.get(formula) == "partial_signal_present"
            ),
            "contradicted_signal_present": sorted(
                formula for formula in TRACK_A_CONTRADICTED if by_formula.get(formula) == "contradicted_signal_present"
            ),
        },
        "expected_campaign_interpretation": "keep_core_lane_expand_shadow_exploration",
        "boundary_note": (
            "This is a synthetic dual-track observation benchmark. It checks whether the "
            "comparison logic recognizes strong core-anchor support, weak controls, and "
            "interesting-but-ambiguous challenger signals."
        ),
    }


def main() -> None:
    artifact = build_benchmark()
    OUTPUT.write_text(json.dumps(artifact, indent=2) + "\n")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
