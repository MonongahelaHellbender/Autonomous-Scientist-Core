#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CARBON = ROOT / "carbon_capture"
ARTIFACTS = CARBON / "corroboration_artifacts"
OUTPUT_JSON = ARTIFACTS / "co2_mineralization_dual_track_campaign_v1.json"
OUTPUT_MD = ARTIFACTS / "co2_mineralization_dual_track_campaign_v1.md"

SHADOW_LIMIT = 4
HOLD_OUT_LIMIT = 2


def load_json(path: Path):
    return json.loads(path.read_text())


def load_sources() -> dict:
    return {
        "pilot": load_json(ARTIFACTS / "co2_mineralization_first_pass_pilot_v1.json"),
        "packet": load_json(CARBON / "reinforced_exact_lane_experimental_packet_v1.json"),
        "proxy": load_json(CARBON / "co2_uptake_proxy_v1.json"),
        "thermo": load_json(CARBON / "thermochemical_carbonation_corroboration_v1.json"),
        "pathways": load_json(CARBON / "reaction_level_carbonation_pathways_v1.json"),
        "sensitivity": load_json(CARBON / "stress_artifacts" / "co2_uptake_proxy_sensitivity_audit_v1.json"),
    }


def shadow_score(proxy_row: dict, thermo_row: dict, sensitivity_row: dict | None) -> float:
    readiness = proxy_row["uptake_proxy"]["readiness_score"]
    corroborated = thermo_row["thermochemical_corroboration"]["corroborated_readiness_score"]
    top10_frequency = sensitivity_row["top10_frequency"] if sensitivity_row else 0.0
    return round(0.48 * readiness + 0.42 * corroborated + 10.0 * top10_frequency, 3)


def shadow_role(proxy_row: dict, pathway_row: dict) -> str:
    fractions = proxy_row["composition_profile"]
    if fractions["sulfur_fraction"] > 0:
        return "sulfur_mixed_network_challenger"
    if fractions["halide_fraction"] > 0:
        return "halide_mixed_network_challenger"
    if pathway_row["reaction_level_pathway"]["pathway_family"] == "pre-carbonated completion pathway":
        return "precarbonated_completion_probe"
    return "broad_corrobation_challenger"


def shadow_rationale(proxy_row: dict, thermo_row: dict, pathway_row: dict) -> str:
    profile = proxy_row["composition_profile"]
    thermo = thermo_row["thermochemical_corroboration"]
    pathway = pathway_row["reaction_level_pathway"]
    tags = []
    if profile["sulfur_fraction"] > 0:
        tags.append("sulfur-bearing")
    if profile["halide_fraction"] > 0:
        tags.append("halide-bearing")
    if profile["carbon_fraction"] > 0:
        tags.append("already carbon-containing")
    if not tags:
        tags.append("non-core corroboration")
    return (
        f"Recent proxy and thermochemical passes keep this {', '.join(tags)} candidate near the top, "
        f"but the current pathway family is '{pathway['pathway_family']}' rather than a clean exact-core conversion. "
        f"That makes it useful as a challenger track rather than a core anchor."
    )


def build_shadow_pick(
    formula: str,
    proxy_row: dict,
    thermo_row: dict,
    pathway_row: dict,
    sensitivity_row: dict | None,
) -> dict:
    proxy = proxy_row["uptake_proxy"]
    thermo = thermo_row["thermochemical_corroboration"]
    pathway = pathway_row["reaction_level_pathway"]
    return {
        "formula": formula,
        "shadow_role": shadow_role(proxy_row, pathway_row),
        "shadow_priority_score": shadow_score(proxy_row, thermo_row, sensitivity_row),
        "proxy_readiness_score": round(proxy["readiness_score"], 3),
        "corroborated_readiness_score": round(thermo["corroborated_readiness_score"], 3),
        "top10_frequency": sensitivity_row["top10_frequency"] if sensitivity_row else None,
        "baseline_rank": sensitivity_row["baseline_rank"] if sensitivity_row else None,
        "uptake_mode": proxy["uptake_mode"],
        "corroboration_class": thermo["corroboration_class"],
        "pathway_family": pathway["pathway_family"],
        "pathway_confidence": round(pathway["pathway_confidence"], 3),
        "exact_oxide_conversion_supported": pathway["exact_oxide_conversion_supported"],
        "environment_risk": proxy_row["candidate_record"]["environment_risk"],
        "challenge_reason": shadow_rationale(proxy_row, thermo_row, pathway_row),
        "falsification_hook": pathway["falsification_hook"],
    }


def build_hold_out(formula: str, proxy_row: dict, thermo_row: dict, pathway_row: dict) -> dict:
    return {
        "formula": formula,
        "proxy_readiness_score": round(proxy_row["uptake_proxy"]["readiness_score"], 3),
        "corroborated_readiness_score": round(
            thermo_row["thermochemical_corroboration"]["corroborated_readiness_score"], 3
        ),
        "pathway_family": pathway_row["reaction_level_pathway"]["pathway_family"],
        "reason_not_in_shadow_slate": (
            "Useful to remember, but still too ambiguous or already covered by the exact-lane reserve "
            "to include in the first expanded comparison run."
        ),
        "falsification_hook": pathway_row["reaction_level_pathway"]["falsification_hook"],
    }


def build_artifact() -> dict:
    sources = load_sources()
    pilot = sources["pilot"]
    proxy_rows = {row["formula"]: row for row in sources["proxy"]["candidates"]}
    thermo_rows = {row["formula"]: row for row in sources["thermo"]["candidates"]}
    pathway_rows = {row["formula"]: row for row in sources["pathways"]["candidates"]}
    sensitivity_rows = {
        row["formula"]: row for row in sources["sensitivity"]["stability_summary"]
    }

    primary_formulas = {
        row["formula"] for row in pilot["first_pass_slate"] + pilot["phase_two_reserve"]
    }
    ranked_candidates = sources["sensitivity"]["baseline_top_10"]

    shadow_pool: list[dict] = []
    hold_outs: list[dict] = []
    for formula in ranked_candidates:
        if formula in primary_formulas:
            continue
        proxy_row = proxy_rows.get(formula)
        thermo_row = thermo_rows.get(formula)
        pathway_row = pathway_rows.get(formula)
        if not proxy_row or not thermo_row or not pathway_row:
            continue

        if formula == "Ca3Si(ClO2)2":
            hold_outs.append(build_hold_out(formula, proxy_row, thermo_row, pathway_row))
            continue

        shadow_pool.append(
            build_shadow_pick(
                formula=formula,
                proxy_row=proxy_row,
                thermo_row=thermo_row,
                pathway_row=pathway_row,
                sensitivity_row=sensitivity_rows.get(formula),
            )
        )

    shadow_pool.sort(
        key=lambda row: (
            -row["shadow_priority_score"],
            row["formula"],
        )
    )
    shadow_slate = shadow_pool[:SHADOW_LIMIT]

    for formula in ranked_candidates:
        if len(hold_outs) >= HOLD_OUT_LIMIT:
            break
        if formula in primary_formulas or any(row["formula"] == formula for row in shadow_slate):
            continue
        if formula == "Ca3Si(ClO2)2":
            continue
        proxy_row = proxy_rows.get(formula)
        thermo_row = thermo_rows.get(formula)
        pathway_row = pathway_rows.get(formula)
        if proxy_row and thermo_row and pathway_row:
            hold_outs.append(build_hold_out(formula, proxy_row, thermo_row, pathway_row))

    return {
        "artifact_type": "co2_mineralization_dual_track_campaign_v1",
        "decision_question": (
            "How should the first-pass mineralization pilot expand once we include the nearby "
            "proxy, thermochemical, pathway, and sensitivity tests from the last few days?"
        ),
        "plain_language_summary": (
            "Keep the clean calcium-silicate pilot as Track A, then add a shadow challenger "
            "Track B made of high-scoring but more ambiguous candidates. That lets us test "
            "whether the current lane is too narrow without muddying the main experiment."
        ),
        "technical_summary": (
            "Track A remains the exact-lane-centered anchor/control experiment. Track B is a "
            "corroboration-driven challenger set drawn from repeated top-10 proxy stability, "
            "thermochemical corroboration, and reaction-pathway screening, but kept outside the "
            "core exact-conversion interpretation because pathway families remain mixed or underconstrained."
        ),
        "recent_supporting_passes": [
            {
                "artifact": "reinforced_exact_lane_experimental_packet_v1.json",
                "what_it_added": "core anchors, restructuring probes, controls, and explicit batch logic",
            },
            {
                "artifact": "materials_experiment_realism_v1.json",
                "what_it_added": "which candidates are actually easy enough to screen in a real lab",
            },
            {
                "artifact": "thermochemical_carbonation_corroboration_v1.json",
                "what_it_added": "a stronger ranking of candidates under thermal and compositional plausibility",
            },
            {
                "artifact": "reaction_level_carbonation_pathways_v1.json",
                "what_it_added": "which candidates support exact oxide conversion versus mixed restructuring",
            },
            {
                "artifact": "co2_uptake_proxy_sensitivity_audit_v1.json",
                "what_it_added": "which top candidates stay near the top under weight perturbation",
            },
        ],
        "track_a_core_pilot": {
            "label": "Track A: exact-core interpretability run",
            "materials": pilot["first_pass_slate"],
            "why_it_exists": (
                "This is still the safest first real-world test because it prioritizes clean "
                "product-family interpretation over raw score alone."
            ),
        },
        "track_b_shadow_challengers": {
            "label": "Track B: corroboration challenger run",
            "materials": shadow_slate,
            "why_it_exists": (
                "These candidates repeatedly score well in recent broader passes, but their "
                "reaction pathway stories are less constrained. Running them as a shadow slate "
                "tests whether the exact-core lane is too narrow."
            ),
        },
        "expanded_run_sizes": {
            "minimum_interpretable_run_materials": len(pilot["first_pass_slate"]),
            "expanded_two_track_run_materials": len(pilot["first_pass_slate"]) + len(shadow_slate),
        },
        "decision_branches": [
            "If Track A anchors separate cleanly from both controls and Track B challengers, keep the lane narrow and anchor-centered.",
            "If Track B challengers show stronger uptake but weaker product-family coherence, widen the exploratory lane but do not replace the core anchors.",
            "If one or more Track B challengers produce coherent, repeated mixed-network carbonation signatures, promote them into a new challenger appendix lane rather than forcing them into the exact-core interpretation.",
            "If Track B challengers outperform Track A on both signal strength and coherence, the current exact-core calibration is too restrictive and should be reopened.",
        ],
        "hold_out_candidates": hold_outs,
        "boundary_note": (
            "This is an experimental design expansion built from local autonomous screening artifacts. "
            "It is a test-planning surface, not a measured mineralization result."
        ),
        "sources": {
            "first_pass_pilot": str(ARTIFACTS / "co2_mineralization_first_pass_pilot_v1.json"),
            "experimental_packet": str(CARBON / "reinforced_exact_lane_experimental_packet_v1.json"),
            "realism": str(CARBON / "materials_experiment_realism_v1.json"),
            "thermochemical_corroboration": str(CARBON / "thermochemical_carbonation_corroboration_v1.json"),
            "reaction_pathways": str(CARBON / "reaction_level_carbonation_pathways_v1.json"),
            "sensitivity_audit": str(CARBON / "stress_artifacts" / "co2_uptake_proxy_sensitivity_audit_v1.json"),
        },
    }


def write_markdown(artifact: dict) -> str:
    lines = [
        "# CO2 Mineralization Dual-Track Campaign",
        "",
        artifact["decision_question"],
        "",
        "Plain language:",
        artifact["plain_language_summary"],
        "",
        "Technical summary:",
        artifact["technical_summary"],
        "",
        "## Why This Expands The First Pilot",
        "",
    ]
    for row in artifact["recent_supporting_passes"]:
        lines.append(f"- `{row['artifact']}`: {row['what_it_added']}")

    lines.extend(
        [
            "",
            "## Track A: Exact-Core Interpretability Run",
            "",
            artifact["track_a_core_pilot"]["why_it_exists"],
            "",
            "| Label | Formula | Role | Tier | Readiness | Kinetics |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )

    for row in artifact["track_a_core_pilot"]["materials"]:
        lines.append(
            f"| {row['label']} | {row['formula']} | {row['selected_role']} | "
            f"{row['stability_tier']} | {row['corroborated_readiness_score']} | {row['kinetics_rate_class']} |"
        )

    lines.extend(
        [
            "",
            "## Track B: Corroboration Challengers",
            "",
            artifact["track_b_shadow_challengers"]["why_it_exists"],
            "",
            "| Formula | Shadow Role | Proxy | Corroborated | Pathway | Exact Support |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )

    for row in artifact["track_b_shadow_challengers"]["materials"]:
        lines.append(
            f"| {row['formula']} | {row['shadow_role']} | {row['proxy_readiness_score']} | "
            f"{row['corroborated_readiness_score']} | {row['pathway_family']} | "
            f"{'yes' if row['exact_oxide_conversion_supported'] else 'no'} |"
        )
        lines.append("")
        lines.append(f"- `{row['formula']}`: {row['challenge_reason']}")

    lines.extend(
        [
            "",
            "## Decision Branches",
            "",
        ]
    )
    for row in artifact["decision_branches"]:
        lines.append(f"- {row}")

    lines.extend(
        [
            "",
            "## Hold-Outs",
            "",
        ]
    )
    for row in artifact["hold_out_candidates"]:
        lines.append(
            f"- `{row['formula']}`: {row['reason_not_in_shadow_slate']} "
            f"Pathway `{row['pathway_family']}`."
        )

    lines.extend(
        [
            "",
            "## Run Size",
            "",
            f"- Minimum interpretable run: `{artifact['expanded_run_sizes']['minimum_interpretable_run_materials']}` materials",
            f"- Expanded two-track run: `{artifact['expanded_run_sizes']['expanded_two_track_run_materials']}` materials",
            "",
            artifact["boundary_note"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    artifact = build_artifact()
    OUTPUT_JSON.write_text(json.dumps(artifact, indent=2) + "\n")
    OUTPUT_MD.write_text(write_markdown(artifact) + "\n")
    print(f"wrote {OUTPUT_JSON}")
    print(f"wrote {OUTPUT_MD}")


if __name__ == "__main__":
    main()
