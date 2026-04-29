import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

PYTHON_FILES = [
    "carbon_capture/composition_sensitive_stress_proxy.py",
    "carbon_capture/composition_conditioning.py",
    "carbon_capture/thermochemical_carbonation_corroboration.py",
    "carbon_capture/reaction_level_carbonation_pathways.py",
    "carbon_capture/exact_subset_thermodynamic_calibration.py",
    "carbon_capture/reinforced_exact_lane_experimental_packet.py",
    "carbon_capture/materials_experiment_realism.py",
]

JSON_FILES = [
    "carbon_capture/exact_oxide_conversion_subset_v1.json",
    "carbon_capture/exact_subset_thermodynamic_calibration_v1.json",
    "carbon_capture/reinforced_exact_lane_experimental_packet_v1.json",
    "carbon_capture/reinforced_exact_lane_stability_overlay_v1.json",
    "carbon_capture/reinforced_exact_lane_observation_template_v1.json",
    "carbon_capture/reinforced_exact_lane_observation_status_v1.json",
    "carbon_capture/materials_experiment_realism_v1.json",
    "carbon_capture/corroboration_artifacts/exact_subset_thermodynamic_calibration_sensitivity_v1.json",
    "carbon_capture/corroboration_artifacts/reinforced_exact_lane_experimental_packet_sensitivity_v1.json",
]

EXPECTED_REINFORCED = {"Ca3SiO5", "Ca2SiO4", "CaMgSiO4", "Ca3Mg(SiO4)2"}
EXPECTED_CORE_ANCHORS = {"Ca3SiO5", "Ca2SiO4", "CaMgSiO4"}


def run_py_compile():
    cmd = [sys.executable, "-m", "py_compile", *[str(REPO_ROOT / path) for path in PYTHON_FILES]]
    subprocess.run(cmd, check=True)


def load_json(path):
    return json.loads((REPO_ROOT / path).read_text())


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    run_py_compile()

    for path in JSON_FILES:
        load_json(path)

    exact_subset = load_json("carbon_capture/exact_oxide_conversion_subset_v1.json")
    calibration = load_json("carbon_capture/exact_subset_thermodynamic_calibration_v1.json")
    packet = load_json("carbon_capture/reinforced_exact_lane_experimental_packet_v1.json")
    overlay = load_json("carbon_capture/reinforced_exact_lane_stability_overlay_v1.json")
    observation_template = load_json("carbon_capture/reinforced_exact_lane_observation_template_v1.json")
    observation_status = load_json("carbon_capture/reinforced_exact_lane_observation_status_v1.json")
    materials_realism = load_json("carbon_capture/materials_experiment_realism_v1.json")

    assert_true(exact_subset["exact_candidate_count"] >= 20, "Exact subset unexpectedly small")
    assert_true(
        len(packet["next_ten_logical_steps"]) == 10,
        "Experimental packet lost its next-ten-step pipeline",
    )
    reinforced = set(packet["reinforced_anchor_formulas"])
    assert_true(
        EXPECTED_REINFORCED.issubset(reinforced),
        "Reinforced anchor lane no longer contains the expected top exact candidates",
    )
    contrast_dossiers = [
        row for row in packet["candidate_dossiers"] if row["selected_role"] == "contrast_candidates"
    ]
    assert_true(
        all(row["campaign_batch"] == "batch_4_low_confidence_contrasts" for row in contrast_dossiers),
        "Contrast candidates drifted out of the contrast batch",
    )
    top_calibration = calibration["top_candidates_by_thermodynamic_raw_score"][:4]
    assert_true(
        {row["formula"] for row in top_calibration} == reinforced,
        "Packet reinforced anchors no longer match the top calibrated exact lane",
    )
    core_anchors = {
        row["formula"]
        for row in overlay["candidate_stability_profiles"]
        if row["stability_tier"] == "core_anchor"
    }
    assert_true(
        EXPECTED_CORE_ANCHORS.issubset(core_anchors),
        "Core-anchor overlay no longer contains the stable leading formulas",
    )
    assert_true(
        overlay["stability_tier_counts"].get("provisional_anchor", 0) >= 1,
        "Overlay lost its provisional-anchor distinction",
    )
    assert_true(
        observation_template["candidate_count"] == len(packet["candidate_dossiers"]),
        "Observation template no longer matches packet candidate count",
    )
    assert_true(
        observation_status["candidate_status_counts"].get("unobserved", 0)
        == len(packet["candidate_dossiers"]),
        "Fresh observation template should integrate to an all-unobserved status artifact",
    )
    assert_true(
        materials_realism["candidate_count"] == len(packet["candidate_dossiers"]),
        "Materials realism artifact no longer matches packet candidate count",
    )

    realism_by_formula = {
        row["formula"]: row for row in materials_realism["candidate_profiles"]
    }
    for formula in EXPECTED_REINFORCED:
        profile = realism_by_formula[formula]
        assert_true(
            "dry CO2 conversion challenge" in profile["reaction_window_suggestions"],
            f"{formula} lost dry CO2 window guidance",
        )
        assert_true(
            "humidified CO2 conversion challenge"
            in profile["phase_fraction_expectations"]["condition_expectations"],
            f"{formula} lost humidified phase expectations",
        )
        assert_true(
            profile["synthesis_feasibility"]["synthesis_feasibility_tier"] in {"HIGH", "MODERATE"},
            f"{formula} has an invalid synthesis feasibility tier",
        )

    print("carbon lane regression check: PASS")
    print(f"exact subset count: {exact_subset['exact_candidate_count']}")
    print(f"reinforced anchors: {sorted(reinforced)}")
    print(f"contrast dossier count: {len(contrast_dossiers)}")


if __name__ == "__main__":
    main()
