from datetime import date

from chemical_formula_features import extract_composition_features
from composition_conditioning import (
    build_feature_map,
    build_stats as build_conditioning_stats,
    derive_candidate_parameters,
)
from shared_screening_utils import clamp, normalize

DEFAULT_WEIGHTS = {
    "mineral_capacity": 0.28,
    "mineral_site_density": 0.20,
    "mineral_oxygen_support": 0.15,
    "mineral_low_rigidity": 0.12,
    "mineral_low_halide": 0.10,
    "mineral_low_sulfur": 0.08,
    "mineral_low_alkali": 0.07,
    "structural_pore": 0.24,
    "structural_thermal_margin": 0.22,
    "structural_low_noise": 0.12,
    "structural_oxide_backbone": 0.16,
    "structural_stability": 0.12,
    "structural_low_alkali": 0.08,
    "structural_low_halide": 0.06,
}


def build_stats(uptake_rows):
    candidates = [row["candidate_record"] for row in uptake_rows]
    feature_map = build_feature_map(candidates)
    conditioning_stats = build_conditioning_stats(candidates, feature_map=feature_map)
    condition_map = {
        row["formula"]: derive_candidate_parameters(
            row["candidate_record"],
            conditioning_stats,
            feature_map[row["formula"]],
        )
        for row in uptake_rows
    }
    thermal_margins = [
        condition_map[row["formula"]]["failure_threshold_c"]
        - condition_map[row["formula"]]["baseline_temp_c"]
        for row in uptake_rows
    ]
    stats = {
        "created_on": str(date.today()),
        "thermal_margin_min": min(thermal_margins),
        "thermal_margin_max": max(thermal_margins),
        "readiness_score_min": min(row["uptake_proxy"]["readiness_score"] for row in uptake_rows),
        "readiness_score_max": max(row["uptake_proxy"]["readiness_score"] for row in uptake_rows),
        "theoretical_capacity_norm_min": min(
            row["uptake_proxy"]["theoretical_capacity_norm"] for row in uptake_rows
        ),
        "theoretical_capacity_norm_max": max(
            row["uptake_proxy"]["theoretical_capacity_norm"] for row in uptake_rows
        ),
    }
    return stats, feature_map, condition_map


def classify_corroboration(structural_capture_propensity, mineralization_propensity):
    gap = structural_capture_propensity - mineralization_propensity
    if (
        structural_capture_propensity >= 0.85
        and mineralization_propensity >= 0.85
        and abs(gap) <= 0.10
    ):
        return "hybrid framework mineralization"
    if gap > 0.07:
        return "structural-capture corroborated"
    if gap < -0.07:
        return "mineralization corroborated"
    return "mixed / ambiguous"


def build_corroboration_rows(uptake_rows, weights=None):
    weights = weights or DEFAULT_WEIGHTS
    stats, feature_map, condition_map = build_stats(uptake_rows)
    rows = []

    for row in uptake_rows:
        formula = row["formula"]
        uptake = row["uptake_proxy"]
        profile = row["composition_profile"]
        condition = condition_map[formula]

        thermal_margin_c = condition["failure_threshold_c"] - condition["baseline_temp_c"]
        thermal_margin_norm = normalize(
            thermal_margin_c, stats["thermal_margin_min"], stats["thermal_margin_max"]
        )
        low_noise_support = 1.0 - normalize(condition["noise_std"], 0.025, 0.075)
        low_rigidity_support = 1.0 - uptake["network_rigidity"]
        low_halide_support = 1.0 - uptake["halide_penalty"]
        low_sulfur_support = 1.0 - uptake["sulfur_penalty"]
        low_alkali_support = 1.0 - uptake["alkali_penalty"]

        mineralization_propensity = clamp(
            0.05
            + weights["mineral_capacity"] * uptake["theoretical_capacity_norm"]
            + weights["mineral_site_density"] * uptake["site_density"]
            + weights["mineral_oxygen_support"] * uptake["basic_oxygen_support"]
            + weights["mineral_low_rigidity"] * low_rigidity_support
            + weights["mineral_low_halide"] * low_halide_support
            + weights["mineral_low_sulfur"] * low_sulfur_support
            + weights["mineral_low_alkali"] * low_alkali_support,
            0.0,
            1.0,
        )
        structural_capture_propensity = clamp(
            0.05
            + weights["structural_pore"] * uptake["pore_openness"]
            + weights["structural_thermal_margin"] * thermal_margin_norm
            + weights["structural_low_noise"] * low_noise_support
            + weights["structural_oxide_backbone"] * condition["oxide_backbone"]
            + weights["structural_stability"] * uptake["stability_strength"]
            + weights["structural_low_alkali"] * low_alkali_support
            + weights["structural_low_halide"] * low_halide_support,
            0.0,
            1.0,
        )
        corroboration_class = classify_corroboration(
            structural_capture_propensity, mineralization_propensity
        )
        uptake_mode = uptake["uptake_mode"]
        if uptake_mode == "capacity-driven mineralization":
            mode_alignment = corroboration_class == "mineralization corroborated"
            mode_compatibility = corroboration_class in {
                "mineralization corroborated",
                "hybrid framework mineralization",
            }
        elif uptake_mode == "balanced structural capture":
            mode_alignment = corroboration_class == "structural-capture corroborated"
            mode_compatibility = corroboration_class in {
                "structural-capture corroborated",
                "hybrid framework mineralization",
            }
        else:
            mode_alignment = corroboration_class == "mixed / ambiguous"
            mode_compatibility = corroboration_class in {
                "mixed / ambiguous",
                "hybrid framework mineralization",
            }

        corroboration_strength = max(structural_capture_propensity, mineralization_propensity)
        corroborated_readiness_raw = (
            uptake["effective_uptake_proxy_gco2_per_g"]
            * (0.60 + 0.40 * corroboration_strength)
            * (0.60 + 0.40 * thermal_margin_norm)
        )

        rows.append(
            {
                "formula": formula,
                "candidate_record": row["candidate_record"],
                "composition_profile": profile,
                "theoretical_capacity": row["theoretical_capacity"],
                "uptake_proxy": uptake,
                "thermochemical_corroboration": {
                    "thermal_margin_c": thermal_margin_c,
                    "thermal_margin_norm": thermal_margin_norm,
                    "low_noise_support": low_noise_support,
                    "low_rigidity_support": low_rigidity_support,
                    "low_halide_support": low_halide_support,
                    "low_sulfur_support": low_sulfur_support,
                    "low_alkali_support": low_alkali_support,
                    "mineralization_propensity": mineralization_propensity,
                    "structural_capture_propensity": structural_capture_propensity,
                    "corroboration_class": corroboration_class,
                    "mode_alignment": mode_alignment,
                    "mode_compatibility": mode_compatibility,
                    "corroborated_readiness_raw": corroborated_readiness_raw,
                    "proxy_boundary_note": (
                        "This corroboration layer combines the semi-physical uptake "
                        "proxy with deterministic composition-sensitive thermal "
                        "conditioning. It is meant to test pathway plausibility, "
                        "not to replace measured carbonation thermodynamics."
                    ),
                },
            }
        )

    raw_values = [row["thermochemical_corroboration"]["corroborated_readiness_raw"] for row in rows]
    raw_min = min(raw_values)
    raw_max = max(raw_values)
    for row in rows:
        row["thermochemical_corroboration"]["corroborated_readiness_score"] = 100.0 * normalize(
            row["thermochemical_corroboration"]["corroborated_readiness_raw"],
            raw_min,
            raw_max,
        )

    rows.sort(
        key=lambda row: (
            -row["thermochemical_corroboration"]["corroborated_readiness_score"],
            -row["uptake_proxy"]["effective_uptake_proxy_gco2_per_g"],
            row["formula"],
        )
    )
    return rows, stats


__all__ = [
    "DEFAULT_WEIGHTS",
    "build_corroboration_rows",
]
