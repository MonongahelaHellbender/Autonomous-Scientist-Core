#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_CAMPAIGN_JSON = "carbon_capture/corroboration_artifacts/co2_mineralization_dual_track_campaign_v1.json"
DEFAULT_PACKET_JSON = "carbon_capture/reinforced_exact_lane_experimental_packet_v1.json"
DEFAULT_OVERLAY_JSON = "carbon_capture/reinforced_exact_lane_stability_overlay_v1.json"
DEFAULT_REALISM_JSON = "carbon_capture/materials_experiment_realism_v1.json"
DEFAULT_OUTPUT_JSON = "carbon_capture/co2_mineralization_dual_track_observation_template_v1.json"

BASE_TECHNIQUES = [
    "xrd_phase_scan",
    "vibrational_carbonate_scan",
    "mass_change_or_thermal_release_screen",
    "microscopy_elemental_map",
]

SHADOW_BASE_CONDITIONS = [
    "baseline identity screen",
    "shadow dry CO2 challenger run",
    "shadow humidified CO2 challenger run",
    "repeat post-treatment phase scan",
]


def load_json(path):
    return json.loads(resolve_path(path).read_text())


def write_json_output(path, payload):
    output_path = resolve_path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n")


def resolve_path(path):
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return ROOT / candidate


def overlay_map(overlay):
    return {row["formula"]: row for row in overlay["candidate_stability_profiles"]}


def packet_map(packet):
    return {row["formula"]: row for row in packet["candidate_dossiers"]}


def realism_map(realism):
    return {row["formula"]: row for row in realism["candidate_profiles"]}


def shadow_required_techniques(row: dict) -> list[str]:
    techniques = list(BASE_TECHNIQUES)
    role = row["shadow_role"]
    if "halide" in role or "sulfur" in role:
        techniques.append("elemental_redistribution_screen")
    if role == "precarbonated_completion_probe":
        techniques.append("carbon_inventory_balance_screen")
    return techniques


def shadow_replicates(row: dict) -> int:
    if row["shadow_role"] == "precarbonated_completion_probe":
        return 2
    if row["pathway_confidence"] < 0.65:
        return 3
    return 2


def condition_guidance(realism_row: dict | None, condition_label: str) -> dict:
    if not realism_row:
        return {
            "suggested_window": None,
            "expected_phase_fraction_proxy": None,
            "kinetics_expectation": None,
            "synthesis_feasibility_tier": None,
        }

    condition_expectations = realism_row["phase_fraction_expectations"]["condition_expectations"]
    return {
        "suggested_window": realism_row["reaction_window_suggestions"].get(condition_label),
        "expected_phase_fraction_proxy": condition_expectations.get(condition_label),
        "kinetics_expectation": {
            "kinetics_rate_class": realism_row["kinetics_expectation"]["kinetics_rate_class"],
            "expected_onset_window_hours": realism_row["kinetics_expectation"][
                "expected_onset_window_hours"
            ],
            "expected_bulk_signal_window_hours": realism_row["kinetics_expectation"][
                "expected_bulk_signal_window_hours"
            ],
        },
        "synthesis_feasibility_tier": realism_row["synthesis_feasibility"][
            "synthesis_feasibility_tier"
        ],
    }


def blank_actual_run_metadata() -> dict:
    return {
        "temperature_c": None,
        "relative_humidity_percent": None,
        "dwell_hours": None,
        "co2_environment": "",
        "particle_size_note": "",
        "sample_mass_mg": None,
        "operator_batch_id": "",
    }


def build_track_a_records(
    campaign: dict,
    packet: dict,
    overlay: dict,
    realism: dict,
) -> list[dict]:
    packet_by_formula = packet_map(packet)
    stability_by_formula = overlay_map(overlay)
    realism_by_formula = realism_map(realism)
    records = []

    for entry in campaign["track_a_core_pilot"]["materials"]:
        dossier = packet_by_formula[entry["formula"]]
        stability = stability_by_formula[entry["formula"]]
        realism_row = realism_by_formula.get(entry["formula"])
        replicate_count = stability["recommended_replicates"]
        for condition_label in dossier["condition_family"]:
            guidance = condition_guidance(realism_row, condition_label)
            for replicate_id in range(1, replicate_count + 1):
                records.append(
                    {
                        "formula": dossier["formula"],
                        "track_label": "track_a_core_pilot",
                        "track_role": entry["label"],
                        "selected_role": dossier["selected_role"],
                        "stability_tier": stability["stability_tier"],
                        "campaign_batch": dossier["campaign_batch"],
                        "condition_label": condition_label,
                        "replicate_id": replicate_id,
                        "required_techniques": dossier["required_techniques"],
                        "comparison_goal": "core_interpretability",
                        "pathway_family": dossier["pathway_family"],
                        "suggested_window": guidance["suggested_window"],
                        "expected_phase_fraction_proxy": guidance["expected_phase_fraction_proxy"],
                        "kinetics_expectation": guidance["kinetics_expectation"],
                        "synthesis_feasibility_tier": guidance["synthesis_feasibility_tier"],
                        "actual_run_metadata": blank_actual_run_metadata(),
                        "observed_phase_family": [],
                        "measured_mass_change_percent": None,
                        "measured_carbonate_signal_strength": "",
                        "window_alignment": "PENDING",
                        "completed": False,
                        "technique_results": {
                            technique: "PENDING" for technique in dossier["required_techniques"]
                        },
                        "overall_condition_outcome": "PENDING",
                        "notes": "",
                    }
                )
    return records


def build_track_b_records(campaign: dict, realism: dict) -> list[dict]:
    realism_by_formula = realism_map(realism)
    records = []
    for entry in campaign["track_b_shadow_challengers"]["materials"]:
        techniques = shadow_required_techniques(entry)
        replicate_count = shadow_replicates(entry)
        realism_row = realism_by_formula.get(entry["formula"])
        for condition_label in SHADOW_BASE_CONDITIONS:
            guidance = condition_guidance(realism_row, condition_label)
            for replicate_id in range(1, replicate_count + 1):
                records.append(
                    {
                        "formula": entry["formula"],
                        "track_label": "track_b_shadow_challengers",
                        "track_role": entry["shadow_role"],
                        "selected_role": "shadow_challengers",
                        "stability_tier": "shadow_challenger",
                        "campaign_batch": "track_b_shadow_challengers",
                        "condition_label": condition_label,
                        "replicate_id": replicate_id,
                        "required_techniques": techniques,
                        "comparison_goal": "shadow_challenger_comparison",
                        "pathway_family": entry["pathway_family"],
                        "suggested_window": guidance["suggested_window"],
                        "expected_phase_fraction_proxy": guidance["expected_phase_fraction_proxy"],
                        "kinetics_expectation": guidance["kinetics_expectation"],
                        "synthesis_feasibility_tier": guidance["synthesis_feasibility_tier"],
                        "actual_run_metadata": blank_actual_run_metadata(),
                        "observed_phase_family": [],
                        "measured_mass_change_percent": None,
                        "measured_carbonate_signal_strength": "",
                        "window_alignment": "PENDING",
                        "completed": False,
                        "technique_results": {technique: "PENDING" for technique in techniques},
                        "overall_condition_outcome": "PENDING",
                        "notes": "",
                    }
                )
    return records


def build_artifact(campaign_json, packet_json, overlay_json, realism_json):
    campaign = load_json(campaign_json)
    packet = load_json(packet_json)
    overlay = load_json(overlay_json)
    realism = load_json(realism_json)
    records = build_track_a_records(campaign, packet, overlay, realism) + build_track_b_records(
        campaign,
        realism,
    )

    return {
        "artifact_type": "co2_mineralization_dual_track_observation_template_v1",
        "sources": {
            "dual_track_campaign": campaign_json,
            "experimental_packet": packet_json,
            "stability_overlay": overlay_json,
            "materials_realism": realism_json,
        },
        "record_count": len(records),
        "candidate_count": len(
            campaign["track_a_core_pilot"]["materials"]
        )
        + len(campaign["track_b_shadow_challengers"]["materials"]),
        "observation_records": records,
        "boundary_note": (
            "This template is a scaffold for future dual-track mineralization observations. "
            "Track A tests the exact-core interpretation, while Track B tests whether strong "
            "mixed-anion challengers deserve promotion."
        ),
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign-json", default=DEFAULT_CAMPAIGN_JSON)
    parser.add_argument("--packet-json", default=DEFAULT_PACKET_JSON)
    parser.add_argument("--overlay-json", default=DEFAULT_OVERLAY_JSON)
    parser.add_argument("--realism-json", default=DEFAULT_REALISM_JSON)
    parser.add_argument("--json-output", default=DEFAULT_OUTPUT_JSON)
    return parser.parse_args()


def main():
    args = parse_args()
    artifact = build_artifact(
        args.campaign_json,
        args.packet_json,
        args.overlay_json,
        args.realism_json,
    )
    print("--- CO2 Mineralization Dual-Track Observation Template v1 ---")
    print(f"Campaign Source:                {args.campaign_json}")
    print(f"Candidate Count:                {artifact['candidate_count']}")
    print(f"Observation Record Count:       {artifact['record_count']}")
    write_json_output(args.json_output, artifact)
    print(f"Saved Artifact:                 {args.json_output}")


if __name__ == "__main__":
    main()
