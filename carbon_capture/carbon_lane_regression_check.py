import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

PYTHON_FILES = [
    "carbon_capture/composition_sensitive_stress_proxy.py",
    "carbon_capture/composition_conditioning.py",
    "carbon_capture/co2_mineralization_dual_track_campaign.py",
    "carbon_capture/co2_mineralization_first_pass_pilot.py",
    "carbon_capture/co2_mineralization_run_packet.py",
    "carbon_capture/dual_track_mock_observation_benchmark.py",
    "carbon_capture/generate_dual_track_observation_template.py",
    "carbon_capture/integrate_dual_track_campaign_observations.py",
    "carbon_capture/thermochemical_carbonation_corroboration.py",
    "carbon_capture/reaction_level_carbonation_pathways.py",
    "carbon_capture/exact_subset_thermodynamic_calibration.py",
    "carbon_capture/integrate_reinforced_exact_lane_observations.py",
    "carbon_capture/reinforced_exact_lane_experimental_packet.py",
    "carbon_capture/mock_observation_integration_benchmark.py",
    "carbon_capture/materials_experiment_realism.py",
]

JSON_FILES = [
    "carbon_capture/co2_mineralization_dual_track_observation_status_v1.json",
    "carbon_capture/co2_mineralization_dual_track_observation_template_v1.json",
    "carbon_capture/corroboration_artifacts/co2_mineralization_run_packet_v1.json",
    "carbon_capture/corroboration_artifacts/dual_track_mock_observation_benchmark_v1.json",
    "carbon_capture/corroboration_artifacts/co2_mineralization_dual_track_campaign_v1.json",
    "carbon_capture/corroboration_artifacts/co2_mineralization_first_pass_pilot_v1.json",
    "carbon_capture/exact_oxide_conversion_subset_v1.json",
    "carbon_capture/exact_subset_thermodynamic_calibration_v1.json",
    "carbon_capture/reinforced_exact_lane_experimental_packet_v1.json",
    "carbon_capture/reinforced_exact_lane_stability_overlay_v1.json",
    "carbon_capture/reinforced_exact_lane_observation_template_v1.json",
    "carbon_capture/reinforced_exact_lane_observation_status_v1.json",
    "carbon_capture/materials_experiment_realism_v1.json",
    "carbon_capture/corroboration_artifacts/mock_observation_integration_benchmark_v1.json",
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
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "carbon_capture" / "integrate_reinforced_exact_lane_observations.py"),
            "--input-json",
            str(REPO_ROOT / "carbon_capture" / "reinforced_exact_lane_observation_template_v1.json"),
            "--json-output",
            str(REPO_ROOT / "carbon_capture" / "reinforced_exact_lane_observation_status_v1.json"),
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "carbon_capture" / "generate_dual_track_observation_template.py"),
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "carbon_capture" / "integrate_dual_track_campaign_observations.py"),
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "carbon_capture" / "dual_track_mock_observation_benchmark.py"),
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "carbon_capture" / "co2_mineralization_run_packet.py"),
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "carbon_capture" / "mock_observation_integration_benchmark.py"),
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "carbon_capture" / "co2_mineralization_dual_track_campaign.py"),
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "carbon_capture" / "co2_mineralization_first_pass_pilot.py"),
        ],
        check=True,
    )

    for path in JSON_FILES:
        load_json(path)

    exact_subset = load_json("carbon_capture/exact_oxide_conversion_subset_v1.json")
    calibration = load_json("carbon_capture/exact_subset_thermodynamic_calibration_v1.json")
    packet = load_json("carbon_capture/reinforced_exact_lane_experimental_packet_v1.json")
    overlay = load_json("carbon_capture/reinforced_exact_lane_stability_overlay_v1.json")
    observation_template = load_json("carbon_capture/reinforced_exact_lane_observation_template_v1.json")
    observation_status = load_json("carbon_capture/reinforced_exact_lane_observation_status_v1.json")
    mock_benchmark = load_json("carbon_capture/corroboration_artifacts/mock_observation_integration_benchmark_v1.json")
    materials_realism = load_json("carbon_capture/materials_experiment_realism_v1.json")
    pilot = load_json("carbon_capture/corroboration_artifacts/co2_mineralization_first_pass_pilot_v1.json")
    dual_track = load_json("carbon_capture/corroboration_artifacts/co2_mineralization_dual_track_campaign_v1.json")
    dual_track_template = load_json("carbon_capture/co2_mineralization_dual_track_observation_template_v1.json")
    dual_track_status = load_json("carbon_capture/co2_mineralization_dual_track_observation_status_v1.json")
    dual_track_benchmark = load_json("carbon_capture/corroboration_artifacts/dual_track_mock_observation_benchmark_v1.json")
    run_packet = load_json("carbon_capture/corroboration_artifacts/co2_mineralization_run_packet_v1.json")

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
    benchmark_status = mock_benchmark["integrated_status_artifact"]["candidate_status_counts"]
    assert_true(
        benchmark_status.get("supported_ready_for_review", 0) >= 3,
        "Mock observation benchmark lost its supported-review cases",
    )
    assert_true(
        benchmark_status.get("partial_signal_present", 0) >= 2,
        "Mock observation benchmark lost its mixed-signal cases",
    )
    assert_true(
        benchmark_status.get("contradicted_signal_present", 0) >= 4,
        "Mock observation benchmark lost its contradiction cases",
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

    first_pass = pilot["first_pass_slate"]
    first_pass_formulas = {row["formula"] for row in first_pass}
    assert_true(
        {"Ca3SiO5", "Ca2SiO4", "CaMgSiO4", "Ca3Mg(SiO4)2"}.issubset(first_pass_formulas),
        "Pilot slate lost the reinforced anchor family",
    )
    assert_true(
        any(row["selected_role"] == "surface_controls" for row in first_pass),
        "Pilot slate lost its surface control",
    )
    assert_true(
        any(row["selected_role"] == "contrast_candidates" for row in first_pass),
        "Pilot slate lost its contrast control",
    )
    assert_true(
        len(pilot["phase_two_reserve"]) >= 3,
        "Pilot slate lost the phase-two restructuring reserve",
    )
    assert_true(
        len(dual_track["track_b_shadow_challengers"]["materials"]) >= 4,
        "Dual-track artifact lost its shadow challenger slate",
    )
    shadow_formulas = {
        row["formula"] for row in dual_track["track_b_shadow_challengers"]["materials"]
    }
    assert_true(
        {"Ca11Si4SO18", "Ca11AlSi3ClO18", "Ca9Si4O17F", "Ca5Si2CO11"}.issubset(shadow_formulas),
        "Dual-track artifact lost its expected mixed-network challengers",
    )
    assert_true(
        dual_track["expanded_run_sizes"]["expanded_two_track_run_materials"]
        == dual_track["expanded_run_sizes"]["minimum_interpretable_run_materials"]
        + len(dual_track["track_b_shadow_challengers"]["materials"]),
        "Dual-track run sizes are inconsistent",
    )
    assert_true(
        any(row["formula"] == "Ca3Si(ClO2)2" for row in dual_track["hold_out_candidates"]),
        "Dual-track artifact lost its explicit ambiguous hold-out",
    )
    assert_true(
        dual_track_template["candidate_count"]
        == dual_track["expanded_run_sizes"]["expanded_two_track_run_materials"],
        "Dual-track observation template candidate count drifted from the campaign artifact",
    )
    track_labels = {
        row["track_label"] for row in dual_track_template["observation_records"]
    }
    assert_true(
        {"track_a_core_pilot", "track_b_shadow_challengers"}.issubset(track_labels),
        "Dual-track observation template lost one of its comparison tracks",
    )
    for record in dual_track_template["observation_records"]:
        assert_true(
            "suggested_window" in record and "actual_run_metadata" in record,
            "Dual-track observation template lost lab-intake runtime metadata fields",
        )
    assert_true(
        dual_track_status["campaign_interpretation"] == "no_data_yet",
        "Fresh dual-track observation status should remain in the no-data state",
    )
    assert_true(
        dual_track_status["candidate_evidence_quality_counts"].get("NO_DATA", 0)
        == dual_track_template["candidate_count"],
        "Fresh dual-track status should report every candidate as no-data quality",
    )
    benchmark_status = dual_track_benchmark["integrated_status_artifact"]["candidate_status_counts"]
    assert_true(
        benchmark_status.get("supported_ready_for_review", 0) >= 3,
        "Dual-track benchmark lost its supported core-anchor cases",
    )
    assert_true(
        benchmark_status.get("partial_signal_present", 0) >= 5,
        "Dual-track benchmark lost its mixed-signal challenger cases",
    )
    assert_true(
        benchmark_status.get("contradicted_signal_present", 0) >= 2,
        "Dual-track benchmark lost its control contradiction cases",
    )
    assert_true(
        dual_track_benchmark["integrated_status_artifact"]["campaign_interpretation"]
        == dual_track_benchmark["expected_campaign_interpretation"],
        "Dual-track benchmark no longer lands on the expected comparison branch",
    )
    assert_true(
        dual_track_benchmark["integrated_status_artifact"]["record_numeric_window_alignment_counts"].get(
            "WITHIN_WINDOW",
            0,
        )
        > 0,
        "Dual-track benchmark lost its in-window observation examples",
    )
    assert_true(
        dual_track_benchmark["integrated_status_artifact"]["record_environment_alignment_counts"].get(
            "MATCH",
            0,
        )
        > 0,
        "Dual-track benchmark lost its environment-matched observation examples",
    )
    assert_true(
        run_packet["run_modes"]["minimum_interpretable_run"]["planned_record_count"]
        < run_packet["run_modes"]["expanded_two_track_run"]["planned_record_count"],
        "Run packet lost the distinction between minimum and expanded run sizes",
    )
    assert_true(
        len(run_packet["run_modes"]["minimum_interpretable_run"]["materials"]) == 6,
        "Run packet minimum plan no longer matches the 6-material Track A design",
    )
    assert_true(
        len(run_packet["run_modes"]["expanded_two_track_run"]["materials"]) == 10,
        "Run packet expanded plan no longer matches the 10-material two-track design",
    )

    print("carbon lane regression check: PASS")
    print(f"exact subset count: {exact_subset['exact_candidate_count']}")
    print(f"reinforced anchors: {sorted(reinforced)}")
    print(f"contrast dossier count: {len(contrast_dossiers)}")


if __name__ == "__main__":
    main()
