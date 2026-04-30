#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CARBON = ROOT / "carbon_capture"
OUTPUT_JSON = CARBON / "corroboration_artifacts" / "co2_mineralization_first_pass_pilot_v1.json"
OUTPUT_MD = CARBON / "corroboration_artifacts" / "co2_mineralization_first_pass_pilot_v1.md"


ROLE_ORDER = {
    "reinforced_anchors": 0,
    "plausible_restructuring": 1,
    "surface_controls": 2,
    "contrast_candidates": 3,
}

STABILITY_BONUS = {
    "core_anchor": 18.0,
    "provisional_anchor": 13.0,
    "stable_plausible_restructuring": 10.0,
    "threshold_sensitive_plausible": 6.0,
    "stable_surface_control": 8.0,
    "stable_contrast_control": 8.0,
}

KINETICS_BONUS = {
    "FAST_SCREENABLE": 8.0,
    "MODERATE_SCREENABLE": 4.0,
    "SLOW_OR_RESTRUCTURING_LIMITED": 0.0,
}

ROLE_BONUS = {
    "reinforced_anchors": 10.0,
    "plausible_restructuring": 5.0,
    "surface_controls": 3.0,
    "contrast_candidates": 2.0,
}


def load_json(path: Path):
    return json.loads(path.read_text())


def load_sources() -> dict:
    return {
        "packet": load_json(CARBON / "reinforced_exact_lane_experimental_packet_v1.json"),
        "overlay": load_json(CARBON / "reinforced_exact_lane_stability_overlay_v1.json"),
        "realism": load_json(CARBON / "materials_experiment_realism_v1.json"),
        "thermo": load_json(CARBON / "thermochemical_carbonation_corroboration_v1.json"),
        "observation_status": load_json(CARBON / "reinforced_exact_lane_observation_status_v1.json"),
    }


def merge_candidates(sources: dict) -> dict[str, dict]:
    packet_rows = {row["formula"]: row for row in sources["packet"]["candidate_dossiers"]}
    overlay_rows = {
        row["formula"]: row for row in sources["overlay"]["candidate_stability_profiles"]
    }
    realism_rows = {row["formula"]: row for row in sources["realism"]["candidate_profiles"]}
    thermo_rows = {
        row["formula"]: row for row in sources["thermo"]["candidates"]
    }
    observation_rows = {
        row["formula"]: row for row in sources["observation_status"]["candidate_status"]
    }

    merged = {}
    for formula in packet_rows:
        merged[formula] = {
            "formula": formula,
            "packet": packet_rows[formula],
            "overlay": overlay_rows[formula],
            "realism": realism_rows[formula],
            "thermo": thermo_rows.get(formula),
            "observation": observation_rows.get(formula),
        }
    return merged


def first_active_window(realism_row: dict, dossier: dict) -> tuple[str | None, dict | None]:
    windows = realism_row["reaction_window_suggestions"]
    for name in dossier["condition_family"]:
        if name != "baseline identity screen" and name in windows:
            return name, windows[name]
    return None, None


def candidate_score(candidate: dict) -> float:
    dossier = candidate["packet"]
    overlay = candidate["overlay"]
    realism = candidate["realism"]
    thermo = candidate["thermo"]

    role = dossier["selected_role"]
    synth = realism["synthesis_feasibility"]["synthesis_feasibility_score"]
    kinetics = realism["kinetics_expectation"]["kinetics_rate_class"]
    readiness = 0.0
    if thermo is not None:
        readiness = thermo["thermochemical_corroboration"]["corroborated_readiness_score"]

    if role in {"reinforced_anchors", "plausible_restructuring"}:
        base = 0.60 * readiness + 0.25 * synth
    else:
        base = 0.55 * synth

    return (
        base
        + STABILITY_BONUS.get(overlay["stability_tier"], 0.0)
        + KINETICS_BONUS.get(kinetics, 0.0)
        + ROLE_BONUS.get(role, 0.0)
    )


def build_pick(candidate: dict, label: str) -> dict:
    dossier = candidate["packet"]
    overlay = candidate["overlay"]
    realism = candidate["realism"]
    thermo = candidate["thermo"]
    observation = candidate["observation"]
    condition_name, condition_window = first_active_window(realism, dossier)

    return {
        "label": label,
        "formula": dossier["formula"],
        "selected_role": dossier["selected_role"],
        "campaign_batch": dossier["campaign_batch"],
        "stability_tier": overlay["stability_tier"],
        "pilot_priority_score": round(candidate_score(candidate), 3),
        "corroborated_readiness_score": (
            round(thermo["thermochemical_corroboration"]["corroborated_readiness_score"], 3)
            if thermo is not None
            else None
        ),
        "synthesis_feasibility_tier": realism["synthesis_feasibility"]["synthesis_feasibility_tier"],
        "kinetics_rate_class": realism["kinetics_expectation"]["kinetics_rate_class"],
        "experimental_intent": dossier["experimental_intent"],
        "first_active_condition": {
            "name": condition_name,
            "window": condition_window,
        },
        "required_techniques": dossier["required_techniques"],
        "pass_criteria": dossier["pass_criteria"][:2],
        "falsification_triggers": dossier["falsification_triggers"][:2],
        "current_observation_status": observation["candidate_status"] if observation else None,
        "hardening_action": overlay["hardening_action"],
    }


def choose_slates(merged: dict[str, dict]) -> dict:
    groups = {
        role: sorted(
            [row for row in merged.values() if row["packet"]["selected_role"] == role],
            key=lambda row: (-candidate_score(row), row["formula"]),
        )
        for role in ROLE_ORDER
    }

    first_pass = [
        build_pick(groups["reinforced_anchors"][0], "anchor_1"),
        build_pick(groups["reinforced_anchors"][1], "anchor_2"),
        build_pick(groups["reinforced_anchors"][2], "anchor_3"),
        build_pick(groups["reinforced_anchors"][3], "anchor_4_stretch"),
        build_pick(groups["surface_controls"][0], "surface_control"),
        build_pick(groups["contrast_candidates"][0], "contrast_control"),
    ]

    reserve = [
        build_pick(groups["plausible_restructuring"][0], "restructuring_probe_1"),
        build_pick(groups["plausible_restructuring"][1], "restructuring_probe_2"),
        build_pick(groups["plausible_restructuring"][2], "restructuring_probe_3"),
    ]

    return {
        "first_pass_slate": first_pass,
        "phase_two_reserve": reserve,
    }


def build_artifact() -> dict:
    sources = load_sources()
    merged = merge_candidates(sources)
    slates = choose_slates(merged)

    return {
        "artifact_type": "co2_mineralization_first_pass_pilot_v1",
        "decision_question": (
            "If a small lab or pilot team had to choose the first mineral solids to "
            "test for permanent CO2 mineralization, which slate should go first, which "
            "materials should act as controls, and what would falsify the current lane quickly?"
        ),
        "problem_significance": (
            "Permanent mineral CO2 capture is a major climate problem because it offers a "
            "route to durable carbon removal using abundant feedstocks rather than fragile "
            "short-cycle storage alone."
        ),
        "portfolio_hypothesis": [
            "If at least two core anchors reproduce the predicted carbonate-plus-residual product family under the planned windows, the reinforced exact lane gets materially stronger.",
            "If the surface or contrast controls behave like the anchors, the current exact-conversion story is overgeneralized and should be narrowed.",
            "If the provisional anchor behaves like the core anchors, the lane widens; if it fails cleanly, the lane should stay concentrated on the tighter calcium-silicate subset.",
        ],
        "first_pass_slate": slates["first_pass_slate"],
        "phase_two_reserve": slates["phase_two_reserve"],
        "campaign_sequence": [
            "Run baseline identity screens for the full first-pass slate.",
            "Run the anchor and stretch-anchor active carbonation windows first.",
            "Run the surface and contrast controls under their own matched challenge windows.",
            "Compare phase-family evolution rather than just total uptake magnitude.",
            "Promote only if anchors and controls separate in the predicted direction.",
        ],
        "boundary_note": (
            "This is a pilot-selection artifact built from current autonomous screening surfaces. "
            "It is an experimental decision aid, not a measured carbon-removal proof."
        ),
        "sources": {
            "experimental_packet": str(CARBON / "reinforced_exact_lane_experimental_packet_v1.json"),
            "stability_overlay": str(CARBON / "reinforced_exact_lane_stability_overlay_v1.json"),
            "materials_realism": str(CARBON / "materials_experiment_realism_v1.json"),
            "thermochemical_corroboration": str(CARBON / "thermochemical_carbonation_corroboration_v1.json"),
            "observation_status": str(CARBON / "reinforced_exact_lane_observation_status_v1.json"),
        },
    }


def write_markdown(artifact: dict) -> str:
    lines = [
        "# CO2 Mineralization First-Pass Pilot",
        "",
        artifact["decision_question"],
        "",
        artifact["problem_significance"],
        "",
        "## First-Pass Slate",
        "",
        "| Label | Formula | Role | Tier | Readiness | Synthesis | Kinetics |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in artifact["first_pass_slate"]:
        readiness = "n/a" if row["corroborated_readiness_score"] is None else row["corroborated_readiness_score"]
        lines.append(
            f"| {row['label']} | {row['formula']} | {row['selected_role']} | {row['stability_tier']} | {readiness} | {row['synthesis_feasibility_tier']} | {row['kinetics_rate_class']} |"
        )
    lines += ["", "## Phase-Two Reserve", ""]
    for row in artifact["phase_two_reserve"]:
        lines.append(
            f"- `{row['formula']}`: {row['selected_role']} / {row['stability_tier']} / {row['experimental_intent']}"
        )
    lines += ["", "## Portfolio Hypothesis", ""]
    for item in artifact["portfolio_hypothesis"]:
        lines.append(f"- {item}")
    lines += ["", "## Campaign Sequence", ""]
    for item in artifact["campaign_sequence"]:
        lines.append(f"- {item}")
    lines += ["", artifact["boundary_note"], ""]
    return "\n".join(lines)


def main() -> None:
    artifact = build_artifact()
    OUTPUT_JSON.write_text(json.dumps(artifact, indent=2) + "\n")
    OUTPUT_MD.write_text(write_markdown(artifact))
    print(f"Wrote {OUTPUT_JSON}")
    print(f"Wrote {OUTPUT_MD}")


if __name__ == "__main__":
    main()
