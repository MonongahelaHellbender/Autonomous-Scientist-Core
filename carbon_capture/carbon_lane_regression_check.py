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
]

JSON_FILES = [
    "carbon_capture/exact_oxide_conversion_subset_v1.json",
    "carbon_capture/exact_subset_thermodynamic_calibration_v1.json",
    "carbon_capture/reinforced_exact_lane_experimental_packet_v1.json",
    "carbon_capture/corroboration_artifacts/exact_subset_thermodynamic_calibration_sensitivity_v1.json",
]

EXPECTED_REINFORCED = {"Ca3SiO5", "Ca2SiO4", "CaMgSiO4", "Ca3Mg(SiO4)2"}


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

    print("carbon lane regression check: PASS")
    print(f"exact subset count: {exact_subset['exact_candidate_count']}")
    print(f"reinforced anchors: {sorted(reinforced)}")
    print(f"contrast dossier count: {len(contrast_dossiers)}")


if __name__ == "__main__":
    main()
