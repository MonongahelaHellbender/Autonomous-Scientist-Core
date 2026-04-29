import argparse
import json
from collections import Counter
from pathlib import Path

DEFAULT_PACKET_JSON = "carbon_capture/reinforced_exact_lane_experimental_packet_v1.json"
DEFAULT_PACKET_AUDIT_JSON = (
    "carbon_capture/corroboration_artifacts/"
    "reinforced_exact_lane_experimental_packet_sensitivity_v1.json"
)
DEFAULT_CALIBRATION_AUDIT_JSON = (
    "carbon_capture/corroboration_artifacts/"
    "exact_subset_thermodynamic_calibration_sensitivity_v1.json"
)
DEFAULT_OUTPUT_JSON = "carbon_capture/reinforced_exact_lane_stability_overlay_v1.json"


def load_json(path):
    return json.loads(Path(path).read_text())


def calibration_agreement_map(calibration_audit):
    return {
        row["formula"]: row["band_agreement_frequency"]
        for row in calibration_audit["stability_summary"]
    }


def role_tier_for_dossier(dossier, packet_audit, band_agreement):
    role = dossier["selected_role"]
    formula = dossier["formula"]

    if role == "reinforced_anchors":
        freq = next(
            row["anchor_membership_frequency"]
            for row in packet_audit["anchor_summary"]
            if row["formula"] == formula
        )
        if freq >= 0.95:
            return "core_anchor", freq
        if freq >= 0.80:
            return "provisional_anchor", freq
        return "fragile_anchor", freq

    if role == "plausible_restructuring":
        freq = packet_audit["plausible_membership_frequency"][formula]
        if freq >= 0.85 and band_agreement >= 0.85:
            return "stable_plausible_restructuring", freq
        if freq >= 0.50:
            return "threshold_sensitive_plausible", freq
        return "fragile_plausible", freq

    if role == "surface_controls":
        freq = packet_audit["surface_membership_frequency"][formula]
        if freq >= 0.90:
            return "stable_surface_control", freq
        return "threshold_sensitive_surface_control", freq

    freq = packet_audit["contrast_membership_frequency"][formula]
    if freq >= 0.95:
        return "stable_contrast_control", freq
    return "fragile_contrast_control", freq


def recommended_replicates_for_tier(tier):
    mapping = {
        "core_anchor": 3,
        "provisional_anchor": 4,
        "fragile_anchor": 5,
        "stable_plausible_restructuring": 3,
        "threshold_sensitive_plausible": 4,
        "fragile_plausible": 5,
        "stable_surface_control": 3,
        "threshold_sensitive_surface_control": 4,
        "stable_contrast_control": 2,
        "fragile_contrast_control": 3,
    }
    return mapping[tier]


def root_cause_note(dossier, tier, role_frequency, band_agreement):
    if tier == "core_anchor":
        return "This candidate is robust against current calibration and packet perturbations."
    if tier == "provisional_anchor":
        return (
            "This candidate stays near the top lane, but anchor status is somewhat "
            "threshold-sensitive under calibration perturbations."
        )
    if tier == "fragile_anchor":
        return (
            "This candidate only intermittently behaves like an anchor; hard top-lane "
            "promotion would be premature."
        )
    if tier == "stable_plausible_restructuring":
        return "This candidate is a good restructuring comparator because both role and band are stable."
    if tier == "threshold_sensitive_plausible":
        return (
            "This candidate sits near a calibration boundary. Its restructuring role is "
            "useful, but it should carry extra replicate burden."
        )
    if tier == "fragile_plausible":
        return "This candidate drifts too much to be trusted as a primary plausible comparator."
    if tier == "stable_surface_control":
        return "This candidate is a reliable surface-limited control under current packet logic."
    if tier == "threshold_sensitive_surface_control":
        return (
            "This candidate behaves like a surface control now, but that assignment is "
            "sensitive enough that extra confirmation is warranted."
        )
    if tier == "stable_contrast_control":
        return "This candidate is a good falsification contrast because it stays in the contrast set."
    return "This contrast candidate needs additional scrutiny before it is trusted as a stable control."


def hardening_action_for_tier(tier):
    mapping = {
        "core_anchor": "Use as a first-pass anchor with the lowest replicate burden.",
        "provisional_anchor": "Keep in the anchor lane, but require extra repeat cycles before promotion into stronger claim language.",
        "fragile_anchor": "Move out of the anchor lane unless direct observations rescue it.",
        "stable_plausible_restructuring": "Use as a main restructuring comparator after the anchor batch.",
        "threshold_sensitive_plausible": "Retain as a comparator, but interpret as threshold-sensitive rather than stable.",
        "fragile_plausible": "Demote to exploratory support only.",
        "stable_surface_control": "Use to separate surface-limited behavior from bulk conversion.",
        "threshold_sensitive_surface_control": "Use only after the main anchor lane is established.",
        "stable_contrast_control": "Keep as a falsification control in every packet revision.",
        "fragile_contrast_control": "Do not rely on this contrast without extra justification.",
    }
    return mapping[tier]


def build_artifact(packet_json, packet_audit_json, calibration_audit_json):
    packet = load_json(packet_json)
    packet_audit = load_json(packet_audit_json)
    calibration_audit = load_json(calibration_audit_json)
    band_agreement_by_formula = calibration_agreement_map(calibration_audit)

    profiles = []
    for dossier in packet["candidate_dossiers"]:
        formula = dossier["formula"]
        band_agreement = band_agreement_by_formula.get(formula)
        tier, role_frequency = role_tier_for_dossier(dossier, packet_audit, band_agreement)
        profiles.append(
            {
                "formula": formula,
                "selected_role": dossier["selected_role"],
                "campaign_batch": dossier["campaign_batch"],
                "calibration_band": dossier["calibration_band"],
                "thermodynamic_raw_score": dossier["thermodynamic_raw_score"],
                "role_membership_frequency": role_frequency,
                "band_agreement_frequency": band_agreement,
                "stability_tier": tier,
                "recommended_replicates": recommended_replicates_for_tier(tier),
                "root_cause_note": root_cause_note(
                    dossier,
                    tier,
                    role_frequency,
                    band_agreement,
                ),
                "hardening_action": hardening_action_for_tier(tier),
            }
        )

    tier_counts = Counter(profile["stability_tier"] for profile in profiles)
    return {
        "artifact_type": "reinforced_exact_lane_stability_overlay_v1",
        "sources": {
            "packet": packet_json,
            "packet_audit": packet_audit_json,
            "calibration_audit": calibration_audit_json,
        },
        "stability_tier_counts": dict(tier_counts),
        "candidate_stability_profiles": profiles,
        "boundary_note": (
            "This overlay does not change the underlying chemistry lane. It adds a "
            "stability-aware interpretation layer so threshold-sensitive roles are "
            "labeled honestly before anyone treats them like equally strong anchors."
        ),
    }


def write_json_output(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-json", default=DEFAULT_PACKET_JSON)
    parser.add_argument("--packet-audit-json", default=DEFAULT_PACKET_AUDIT_JSON)
    parser.add_argument("--calibration-audit-json", default=DEFAULT_CALIBRATION_AUDIT_JSON)
    parser.add_argument("--json-output", default=DEFAULT_OUTPUT_JSON)
    return parser.parse_args()


def main():
    args = parse_args()
    artifact = build_artifact(
        args.packet_json,
        args.packet_audit_json,
        args.calibration_audit_json,
    )
    print("--- Reinforced Exact Lane Stability Overlay v1 ---")
    print(f"Packet Source:                  {args.packet_json}")
    print(f"Stability Tiers:               {artifact['stability_tier_counts']}")
    print("")
    print(f"{'Formula':<24} {'Tier':<34} {'Role Freq':<10} {'Band Agree'}")
    print("-" * 100)
    for row in artifact["candidate_stability_profiles"][:12]:
        band_agree = ""
        if row["band_agreement_frequency"] is not None:
            band_agree = f"{row['band_agreement_frequency']:.2%}"
        print(
            f"{row['formula']:<24} {row['stability_tier']:<34} "
            f"{row['role_membership_frequency']:<10.2%} "
            f"{band_agree}"
        )
    write_json_output(args.json_output, artifact)
    print("")
    print(f"Saved Artifact:                 {args.json_output}")


if __name__ == "__main__":
    main()
