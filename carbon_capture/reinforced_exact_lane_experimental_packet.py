import json
from pathlib import Path

DEFAULT_INPUT_JSON = "carbon_capture/exact_subset_thermodynamic_calibration_v1.json"


def load_calibrated_exact_rows(path=DEFAULT_INPUT_JSON):
    payload = json.loads(Path(path).read_text())
    return payload["candidates"]


def technique_library():
    return {
        "xrd_phase_scan": {
            "purpose": "Check whether carbonate and residual oxide families appear in the treated solid.",
            "pass_signal": "carbonate growth plus the residual family expected by the exact-conversion hypothesis",
            "fail_signal": "parent-only pattern or a product family incompatible with the proposed pathway",
        },
        "vibrational_carbonate_scan": {
            "purpose": "Check whether carbonate signatures appear while framework signatures persist or collapse as predicted.",
            "pass_signal": "carbonate signature intensity evolves in the direction predicted by the pathway family",
            "fail_signal": "no coherent carbonate growth or framework behavior opposite to the pathway hypothesis",
        },
        "mass_change_or_thermal_release_screen": {
            "purpose": "Check whether treated material shows a coherent carbon-uptake or carbonate-release signal.",
            "pass_signal": "repeatable uptake or release evidence consistent with carbonate formation",
            "fail_signal": "flat response or irreproducible behavior across repeat runs",
        },
        "microscopy_elemental_map": {
            "purpose": "Check whether carbonate growth looks bulk-like, hybrid, or surface-limited.",
            "pass_signal": "spatial distribution matches the pathway family rather than random degradation",
            "fail_signal": "no coherent spatial pattern or complete mismatch with pathway expectations",
        },
        "surface_sensitive_carbonate_check": {
            "purpose": "Check whether carbonation is confined near accessible surfaces or defects.",
            "pass_signal": "surface-skewed carbonate evidence with most framework signatures retained",
            "fail_signal": "bulk-collapse pattern where a surface-limited route was predicted",
        },
        "cycle_reversibility_screen": {
            "purpose": "Check whether repeated exposure changes the product family or only strengthens an existing one.",
            "pass_signal": "repeat cycles reinforce the same pathway interpretation",
            "fail_signal": "candidate flips unpredictably between pathways across repeated cycles",
        },
    }


def choose_required_techniques(row):
    pathway_family = row["reaction_level_pathway"]["pathway_family"]
    calibration_band = row["thermodynamic_calibration"]["calibration_band"]

    techniques = [
        "xrd_phase_scan",
        "vibrational_carbonate_scan",
        "mass_change_or_thermal_release_screen",
    ]

    if "surface carbonation" in pathway_family:
        techniques.extend(
            [
                "surface_sensitive_carbonate_check",
                "cycle_reversibility_screen",
            ]
        )
    else:
        techniques.append("microscopy_elemental_map")

    if calibration_band != "thermodynamically reinforced exact conversion":
        techniques.append("cycle_reversibility_screen")

    ordered = []
    for technique in techniques:
        if technique not in ordered:
            ordered.append(technique)
    return ordered


def campaign_batch_for_row(row, selected_role=None):
    if selected_role == "contrast_candidates":
        return "batch_4_low_confidence_contrasts"
    if selected_role == "surface_controls":
        return "batch_3_surface_controls"
    if selected_role == "plausible_restructuring":
        return "batch_2_plausible_restructuring"
    if selected_role == "reinforced_anchors":
        return "batch_1_reinforced_anchors"

    band = row["thermodynamic_calibration"]["calibration_band"]
    pathway = row["reaction_level_pathway"]["pathway_family"]
    if band == "thermodynamically reinforced exact conversion":
        return "batch_1_reinforced_anchors"
    if band == "thermodynamically plausible exact restructuring":
        return "batch_2_plausible_restructuring"
    if band == "surface-limited exact conversion" or "surface carbonation" in pathway:
        return "batch_3_surface_controls"
    return "batch_4_low_confidence_contrasts"


def experimental_intent_for_row(row, selected_role=None):
    if selected_role == "contrast_candidates":
        return "use as contrast material to falsify over-broad conversion claims"
    if selected_role == "surface_controls":
        return "test whether uptake stays surface-confined rather than proceeding toward bulk conversion"

    pathway = row["reaction_level_pathway"]["pathway_family"]
    band = row["thermodynamic_calibration"]["calibration_band"]
    if band == "thermodynamically reinforced exact conversion":
        return "confirm the strongest exact-conversion or hybrid-conversion route first"
    if band == "thermodynamically plausible exact restructuring":
        return "test whether hybrid or restructuring behavior survives direct experimental challenge"
    if "surface carbonation" in pathway or band == "surface-limited exact conversion":
        return "test whether uptake stays surface-confined rather than proceeding toward bulk conversion"
    return "use as contrast material to falsify over-broad conversion claims"


def build_condition_family(row, selected_role=None):
    if selected_role == "contrast_candidates":
        return [
            "baseline identity screen",
            "single contrast exposure",
            "post-treatment mismatch check",
        ]
    if selected_role == "surface_controls":
        return [
            "baseline identity screen",
            "short exposure surface challenge",
            "surface-sensitive post-treatment scan",
            "cycle challenge for retention versus collapse",
        ]

    pathway = row["reaction_level_pathway"]["pathway_family"]
    band = row["thermodynamic_calibration"]["calibration_band"]
    if band == "thermodynamically reinforced exact conversion":
        return [
            "baseline identity screen",
            "dry CO2 conversion challenge",
            "humidified CO2 conversion challenge",
            "repeat post-treatment phase scan",
        ]
    if band == "thermodynamically plausible exact restructuring":
        return [
            "baseline identity screen",
            "moderate CO2 exposure with repeated intermediate scans",
            "cycle challenge to separate stable hybrid behavior from drift",
        ]
    if "surface carbonation" in pathway or band == "surface-limited exact conversion":
        return [
            "baseline identity screen",
            "short exposure surface challenge",
            "surface-sensitive post-treatment scan",
            "cycle challenge for retention versus collapse",
        ]
    return [
        "baseline identity screen",
        "single contrast exposure",
        "post-treatment mismatch check",
    ]


def build_pass_criteria(row, selected_role=None):
    pathway = row["reaction_level_pathway"]
    band = row["thermodynamic_calibration"]["calibration_band"]

    criteria = [
        "The treated material shows a coherent carbonate signal in at least two independent readout families.",
        "The observed product family is closer to the exact-pathway hypothesis than to a parent-only no-reaction result.",
    ]

    if selected_role == "contrast_candidates":
        criteria.append(
            "The candidate behaves measurably differently from the reinforced anchor lane and therefore works as a genuine contrast case."
        )
        return criteria
    if band == "thermodynamically reinforced exact conversion":
        criteria.append(
            "The candidate reproduces the predicted carbonate-plus-residual family without needing a special pleading reinterpretation."
        )
    elif band == "thermodynamically plausible exact restructuring":
        criteria.append(
            "The candidate shows mixed carbonate growth plus retained framework signatures consistent with restructuring rather than clean bulk collapse."
        )
    elif "surface carbonation" in pathway["pathway_family"]:
        criteria.append(
            "Carbonate evidence remains surface-skewed while most parent-framework signatures persist."
        )
    else:
        criteria.append(
            "The candidate behaves measurably differently from the reinforced anchor lane and therefore works as a genuine contrast case."
        )
    return criteria


def build_falsification_triggers(row, selected_role=None):
    pathway = row["reaction_level_pathway"]
    band = row["thermodynamic_calibration"]["calibration_band"]

    triggers = [
        pathway["falsification_hook"],
        "If repeated runs fail to recover the same product-family direction, downgrade the candidate.",
    ]

    if selected_role == "contrast_candidates":
        triggers.append(
            "If the candidate unexpectedly behaves like a reinforced exact conversion, it should leave the contrast bucket."
        )
        return triggers
    if band == "thermodynamically reinforced exact conversion":
        triggers.append(
            "If the candidate behaves no better than the low-confidence contrast set, remove it from the reinforced lane."
        )
    elif band == "thermodynamically plausible exact restructuring":
        triggers.append(
            "If the candidate collapses cleanly into a different product family or shows no repeatable carbonate growth, demote it to lower-confidence."
        )
    elif "surface carbonation" in pathway["pathway_family"]:
        triggers.append(
            "If the bulk lattice collapses into carbonate-plus-residual products, this is not a surface-limited control."
        )
    else:
        triggers.append(
            "If the candidate unexpectedly behaves like a reinforced exact conversion, it should leave the contrast bucket."
        )
    return triggers


def build_candidate_dossier(row, rank, selected_role=None):
    pathway = row["reaction_level_pathway"]
    calibration = row["thermodynamic_calibration"]
    techniques = choose_required_techniques(row)
    return {
        "formula": row["formula"],
        "priority_rank": rank,
        "selected_role": selected_role,
        "campaign_batch": campaign_batch_for_row(row, selected_role=selected_role),
        "experimental_intent": experimental_intent_for_row(row, selected_role=selected_role),
        "calibration_band": calibration["calibration_band"],
        "thermodynamic_raw_score": calibration["thermodynamic_raw_score"],
        "thermodynamic_score": calibration["thermodynamic_score"],
        "pathway_family": pathway["pathway_family"],
        "exact_conversion_equation": pathway["simplified_pathway_hypothesis"],
        "required_techniques": techniques,
        "condition_family": build_condition_family(row, selected_role=selected_role),
        "expected_observations": pathway["expected_measurement_hooks"],
        "pass_criteria": build_pass_criteria(row, selected_role=selected_role),
        "falsification_triggers": build_falsification_triggers(row, selected_role=selected_role),
        "exact_conversion_products": pathway["exact_conversion_products"],
    }


def build_measurement_matrix(candidate_dossiers):
    library = technique_library()
    matrix = []
    for dossier in candidate_dossiers:
        for technique in dossier["required_techniques"]:
            matrix.append(
                {
                    "formula": dossier["formula"],
                    "technique": technique,
                    "purpose": library[technique]["purpose"],
                    "expected_signal": library[technique]["pass_signal"],
                    "failure_signal": library[technique]["fail_signal"],
                    "campaign_batch": dossier["campaign_batch"],
                }
            )
    return matrix


def select_candidate_groups(rows):
    reinforced = [
        row
        for row in rows
        if row["thermodynamic_calibration"]["calibration_band"]
        == "thermodynamically reinforced exact conversion"
    ]
    plausible = [
        row
        for row in rows
        if row["thermodynamic_calibration"]["calibration_band"]
        == "thermodynamically plausible exact restructuring"
    ]
    surface_controls = [
        row
        for row in rows
        if row["thermodynamic_calibration"]["calibration_band"]
        == "surface-limited exact conversion"
        or "surface carbonation" in row["reaction_level_pathway"]["pathway_family"]
    ]
    low_confidence = [
        row
        for row in rows
        if row["thermodynamic_calibration"]["calibration_band"]
        == "lower-confidence exact conversion"
    ]

    contrast_candidates = []
    used = set()
    for row in sorted(
        surface_controls,
        key=lambda item: item["thermodynamic_calibration"]["thermodynamic_raw_score"],
    ):
        if row["formula"] not in used:
            contrast_candidates.append(row)
            used.add(row["formula"])
        if len(contrast_candidates) >= 2:
            break
    for row in sorted(
        low_confidence,
        key=lambda item: item["thermodynamic_calibration"]["thermodynamic_raw_score"],
    ):
        if row["formula"] not in used:
            contrast_candidates.append(row)
            used.add(row["formula"])
        if len(contrast_candidates) >= 4:
            break

    return {
        "reinforced_anchors": reinforced,
        "plausible_restructuring": plausible[:6],
        "surface_controls": surface_controls[:4],
        "contrast_candidates": contrast_candidates,
    }


def build_campaign_batches(candidate_groups):
    return [
        {
            "batch_id": "batch_1_reinforced_anchors",
            "objective": "Confirm that the strongest exact candidates show repeatable carbonate-plus-residual behavior.",
            "candidates": [row["formula"] for row in candidate_groups["reinforced_anchors"]],
            "promotion_rule": "At least two independent readout families agree with the exact-pathway hypothesis for most candidates in the batch.",
            "failure_rule": "If the batch behaves no better than the contrast set, the reinforced lane must be downgraded.",
        },
        {
            "batch_id": "batch_2_plausible_restructuring",
            "objective": "Test whether hybrid or restructuring candidates stay coherent under repeated challenge.",
            "candidates": [row["formula"] for row in candidate_groups["plausible_restructuring"]],
            "promotion_rule": "Candidates preserve a consistent hybrid or restructuring signature across repeat scans.",
            "failure_rule": "If candidates collapse into contradictory pathways, keep them below the reinforced lane.",
        },
        {
            "batch_id": "batch_3_surface_controls",
            "objective": "Check whether surface-limited candidates really stay surface-confined instead of drifting toward bulk conversion.",
            "candidates": [row["formula"] for row in candidate_groups["surface_controls"]],
            "promotion_rule": "Surface-sensitive and bulk readouts agree on a surface-skewed carbonation story.",
            "failure_rule": "If bulk conversion dominates, the surface-control interpretation fails.",
        },
        {
            "batch_id": "batch_4_low_confidence_contrasts",
            "objective": "Use lower-confidence candidates as contrast cases so the anchor lane has a genuine falsification baseline.",
            "candidates": [row["formula"] for row in candidate_groups["contrast_candidates"]],
            "promotion_rule": "Contrast candidates stay weaker or less coherent than the reinforced lane.",
            "failure_rule": "If contrast candidates outperform the anchors, revisit the calibration and packet ordering.",
        },
    ]


def build_decision_gates():
    return [
        {
            "gate": "gate_1_identity",
            "question": "Does the starting material match the expected parent phase closely enough to trust the downstream readouts?",
            "pass_meaning": "Proceed to exposure challenge.",
            "fail_meaning": "Do not interpret later signals as pathway evidence.",
        },
        {
            "gate": "gate_2_carbon_signal",
            "question": "Do at least two readout families report a coherent carbonate signal after treatment?",
            "pass_meaning": "Promote the candidate to product-family matching.",
            "fail_meaning": "Treat the candidate as no-confidence for this round.",
        },
        {
            "gate": "gate_3_product_family_match",
            "question": "Do the observed products and residual signatures match the predicted pathway family better than a generic damage story?",
            "pass_meaning": "Keep the candidate in the active exact-conversion lane.",
            "fail_meaning": "Downgrade to exploratory or contrast status.",
        },
        {
            "gate": "gate_4_repeatability",
            "question": "Does the same pathway interpretation survive repeated exposure cycles?",
            "pass_meaning": "Candidate remains promotable.",
            "fail_meaning": "Candidate is unstable and should not anchor claim language.",
        },
        {
            "gate": "gate_5_anchor_vs_contrast",
            "question": "Do reinforced anchors still outperform contrast materials under the same workflow?",
            "pass_meaning": "The reinforced lane remains meaningful.",
            "fail_meaning": "Revisit the calibration and packet assumptions before promoting any candidate.",
        },
    ]


def build_consensus_hypotheses(candidate_groups):
    reinforced_formulas = [row["formula"] for row in candidate_groups["reinforced_anchors"]]
    plausible_formulas = [row["formula"] for row in candidate_groups["plausible_restructuring"]]
    surface_formulas = [row["formula"] for row in candidate_groups["surface_controls"][:2]]
    contrast_formulas = [row["formula"] for row in candidate_groups["contrast_candidates"]]

    return [
        {
            "hypothesis": "bulk anchor hypothesis",
            "statement": (
                f"{reinforced_formulas[0]} should behave like the cleanest exact bulk-conversion anchor, "
                "with carbonate growth and residual oxide-family formation that are easier to interpret than the rest of the lane."
            ),
        },
        {
            "hypothesis": "hybrid silicate hypothesis",
            "statement": (
                f"{', '.join(reinforced_formulas[1:])} should show carbonate growth plus partial framework persistence rather than immediate total collapse."
            ),
        },
        {
            "hypothesis": "plausible restructuring hypothesis",
            "statement": (
                f"{', '.join(plausible_formulas[:3])} should remain chemically coherent, but they are more likely to show mixed restructuring than the anchor lane."
            ),
        },
        {
            "hypothesis": "surface control hypothesis",
            "statement": (
                f"{', '.join(surface_formulas)} should help separate surface-confined carbonate behavior from true bulk exact conversion."
            ),
        },
        {
            "hypothesis": "contrast falsification hypothesis",
            "statement": (
                f"If lower-confidence candidates such as {', '.join(contrast_formulas[:3])} perform as well as or better than the anchors, the reinforced lane is overstated."
            ),
        },
    ]


def build_next_ten_steps(candidate_groups):
    reinforced = [row["formula"] for row in candidate_groups["reinforced_anchors"]]
    plausible = [row["formula"] for row in candidate_groups["plausible_restructuring"]]
    surface = [row["formula"] for row in candidate_groups["surface_controls"][:2]]
    contrast = [row["formula"] for row in candidate_groups["contrast_candidates"]]

    return [
        {
            "step": 1,
            "action": f"Confirm starting-phase identity for the reinforced anchors: {', '.join(reinforced)}.",
            "pass_meaning": "The anchor lane is experimentally interpretable.",
            "fail_meaning": "Do not trust downstream carbonate signatures yet.",
        },
        {
            "step": 2,
            "action": f"Run the first dry CO2 challenge on the reinforced anchors: {', '.join(reinforced)}.",
            "pass_meaning": "The exact-conversion lane produces initial carbonate evidence.",
            "fail_meaning": "The reinforced lane may only be a ranking artifact.",
        },
        {
            "step": 3,
            "action": f"Repeat the anchor challenge under humidified conditions for {', '.join(reinforced)}.",
            "pass_meaning": "Carbonate growth survives a second challenge mode.",
            "fail_meaning": "The lane may be condition-fragile.",
        },
        {
            "step": 4,
            "action": f"Run post-treatment phase scans and compare against exact equations for {', '.join(reinforced)}.",
            "pass_meaning": "Product families support the exact hypotheses.",
            "fail_meaning": "Downgrade any anchor that misses its own product family.",
        },
        {
            "step": 5,
            "action": f"Challenge the plausible restructuring tier: {', '.join(plausible[:4])}.",
            "pass_meaning": "Hybrid or restructuring behavior remains coherent.",
            "fail_meaning": "These candidates stay below the anchor lane.",
        },
        {
            "step": 6,
            "action": f"Run cycle-based repeatability checks on the plausible tier: {', '.join(plausible[:4])}.",
            "pass_meaning": "The restructuring interpretation is repeatable.",
            "fail_meaning": "The candidates are too unstable for promotion.",
        },
        {
            "step": 7,
            "action": f"Run the surface-control packet on {', '.join(surface)}.",
            "pass_meaning": "Surface-limited behavior is distinguishable from bulk conversion.",
            "fail_meaning": "The packet cannot separate surface and bulk stories cleanly.",
        },
        {
            "step": 8,
            "action": f"Run the low-confidence contrast set: {', '.join(contrast)}.",
            "pass_meaning": "The contrast set stays weaker than the anchors.",
            "fail_meaning": "The reinforced lane is overstated.",
        },
        {
            "step": 9,
            "action": "Update the calibration artifact with observed outcomes and compare promotion/demotion decisions.",
            "pass_meaning": "The internal ranking survives contact with the first experiment packet.",
            "fail_meaning": "The calibration needs revision before further claim hardening.",
        },
        {
            "step": 10,
            "action": "Re-run the carbon-lane regression check so future edits cannot silently break the reinforced exact packet.",
            "pass_meaning": "The AI scientist now has a stronger self-check loop.",
            "fail_meaning": "The repo can drift without noticing.",
        },
    ]


def build_packet(rows):
    candidate_groups = select_candidate_groups(rows)

    candidate_dossiers = []
    for rank, row in enumerate(candidate_groups["reinforced_anchors"], start=1):
        candidate_dossiers.append(
            build_candidate_dossier(row, rank, selected_role="reinforced_anchors")
        )
    for row in candidate_groups["plausible_restructuring"]:
        candidate_dossiers.append(
            build_candidate_dossier(
                row,
                len(candidate_dossiers) + 1,
                selected_role="plausible_restructuring",
            )
        )
    for row in candidate_groups["surface_controls"]:
        candidate_dossiers.append(
            build_candidate_dossier(
                row,
                len(candidate_dossiers) + 1,
                selected_role="surface_controls",
            )
        )
    for row in candidate_groups["contrast_candidates"]:
        candidate_dossiers.append(
            build_candidate_dossier(
                row,
                len(candidate_dossiers) + 1,
                selected_role="contrast_candidates",
            )
        )

    packet = {
        "artifact_type": "reinforced_exact_lane_experimental_packet_v1",
        "source": DEFAULT_INPUT_JSON,
        "reinforced_anchor_formulas": [
            row["formula"] for row in candidate_groups["reinforced_anchors"]
        ],
        "candidate_groups": {
            key: [row["formula"] for row in values]
            for key, values in candidate_groups.items()
        },
        "candidate_dossiers": candidate_dossiers,
        "measurement_technique_matrix": build_measurement_matrix(candidate_dossiers),
        "campaign_batches": build_campaign_batches(candidate_groups),
        "decision_gates": build_decision_gates(),
        "consensus_hypotheses": build_consensus_hypotheses(candidate_groups),
        "next_ten_logical_steps": build_next_ten_steps(candidate_groups),
        "packet_boundary_note": (
            "This packet translates the reinforced exact lane into a concrete "
            "experimental and falsification workflow. It is still an internal "
            "planning artifact rather than real lab evidence."
        ),
    }
    return packet


__all__ = [
    "DEFAULT_INPUT_JSON",
    "build_packet",
    "campaign_batch_for_row",
    "load_calibrated_exact_rows",
    "select_candidate_groups",
    "technique_library",
]
