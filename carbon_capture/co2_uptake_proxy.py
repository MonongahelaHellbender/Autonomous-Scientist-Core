from datetime import date

from chemical_formula_features import (
    compute_theoretical_carbonate_capacity,
    extract_composition_features,
)
from shared_screening_utils import clamp, load_candidate_rows, load_retained_candidates, normalize

DEFAULT_BASELINE_WEIGHTS = {
    "pore_openness": 0.26,
    "site_density": 0.22,
    "basic_oxygen_support": 0.18,
    "stability_strength": 0.10,
    "halide_penalty": -0.12,
    "sulfur_penalty": -0.08,
    "alkali_penalty": -0.07,
    "network_rigidity": -0.07,
    "transition_penalty": -0.05,
    "hydration_penalty": -0.04,
}


def oxygen_ratio_factor(oxygen_to_network_ratio):
    if oxygen_to_network_ratio is None:
        return 0.0
    return min(1.0, oxygen_to_network_ratio / 8.0)


def select_formula_representatives(candidates):
    by_formula = {}
    multiplicity = {}
    for candidate in candidates:
        formula = candidate["formula"]
        multiplicity[formula] = multiplicity.get(formula, 0) + 1
        best = by_formula.get(formula)
        if best is None:
            by_formula[formula] = candidate
            continue
        if (
            candidate["pore_space"] > best["pore_space"]
            or (
                candidate["pore_space"] == best["pore_space"]
                and candidate["stability"] < best["stability"]
            )
        ):
            by_formula[formula] = candidate

    representatives = []
    for formula, candidate in by_formula.items():
        enriched = dict(candidate)
        enriched["source_formula_multiplicity"] = multiplicity[formula]
        enriched["formula_representative_rule"] = "highest pore space, then strongest stability"
        representatives.append(enriched)

    representatives.sort(key=lambda row: (-row["pore_space"], row["stability"], row["formula"]))
    return representatives, multiplicity


def build_stats(candidates):
    profile_map = {}
    capacity_map = {}

    pore_values = [row["pore_space"] for row in candidates]
    stability_values = [row["stability"] for row in candidates]

    stat_fields = {
        "theoretical_capacity_gco2_per_g": [],
        "site_density": [],
        "basic_oxygen_support_raw": [],
        "halide_fraction": [],
        "sulfur_fraction": [],
        "alkali_fraction": [],
        "network_former_fraction": [],
        "transition_fraction": [],
        "hydrogen_fraction": [],
    }

    for candidate in candidates:
        formula = candidate["formula"]
        profile = extract_composition_features(formula)
        capacity = compute_theoretical_carbonate_capacity(profile["counts"])
        halide_fraction = profile["fluoride_fraction"] + profile["chloride_fraction"]
        basic_oxygen_support_raw = (
            0.45 * profile["oxygen_fraction"]
            + 0.35 * capacity["site_density"]
            + 0.20 * oxygen_ratio_factor(profile["oxygen_to_network_ratio"])
        )

        profile_map[formula] = {
            **profile,
            "halide_fraction": halide_fraction,
            "basic_oxygen_support_raw": basic_oxygen_support_raw,
        }
        capacity_map[formula] = capacity

        stat_fields["theoretical_capacity_gco2_per_g"].append(
            capacity["theoretical_capacity_gco2_per_g"]
        )
        stat_fields["site_density"].append(capacity["site_density"])
        stat_fields["basic_oxygen_support_raw"].append(basic_oxygen_support_raw)
        stat_fields["halide_fraction"].append(halide_fraction)
        stat_fields["sulfur_fraction"].append(profile["sulfur_fraction"])
        stat_fields["alkali_fraction"].append(profile["alkali_fraction"])
        stat_fields["network_former_fraction"].append(profile["network_former_fraction"])
        stat_fields["transition_fraction"].append(profile["transition_fraction"])
        stat_fields["hydrogen_fraction"].append(profile["hydrogen_fraction"])

    stats = {
        "created_on": str(date.today()),
        "pore_min": min(pore_values),
        "pore_max": max(pore_values),
        "stability_min": min(stability_values),
        "stability_max": max(stability_values),
    }
    for field, values in stat_fields.items():
        stats[f"{field}_min"] = min(values)
        stats[f"{field}_max"] = max(values)
    return stats, profile_map, capacity_map


def derive_uptake_metrics(candidate, stats, profile, capacity, weights=None):
    weights = weights or DEFAULT_BASELINE_WEIGHTS
    pore_openness = normalize(candidate["pore_space"], stats["pore_min"], stats["pore_max"])
    stability_strength = normalize(
        stats["stability_max"] - candidate["stability"],
        0.0,
        stats["stability_max"] - stats["stability_min"],
    )
    site_density = normalize(
        capacity["site_density"],
        stats["site_density_min"],
        stats["site_density_max"],
    )
    basic_oxygen_support = normalize(
        profile["basic_oxygen_support_raw"],
        stats["basic_oxygen_support_raw_min"],
        stats["basic_oxygen_support_raw_max"],
    )
    halide_penalty = normalize(
        profile["halide_fraction"],
        stats["halide_fraction_min"],
        stats["halide_fraction_max"],
    )
    sulfur_penalty = normalize(
        profile["sulfur_fraction"],
        stats["sulfur_fraction_min"],
        stats["sulfur_fraction_max"],
    )
    alkali_penalty = normalize(
        profile["alkali_fraction"],
        stats["alkali_fraction_min"],
        stats["alkali_fraction_max"],
    )
    network_rigidity = normalize(
        profile["network_former_fraction"],
        stats["network_former_fraction_min"],
        stats["network_former_fraction_max"],
    )
    transition_penalty = normalize(
        profile["transition_fraction"],
        stats["transition_fraction_min"],
        stats["transition_fraction_max"],
    )
    hydration_penalty = normalize(
        profile["hydrogen_fraction"],
        stats["hydrogen_fraction_min"],
        stats["hydrogen_fraction_max"],
    )
    theoretical_capacity_norm = normalize(
        capacity["theoretical_capacity_gco2_per_g"],
        stats["theoretical_capacity_gco2_per_g_min"],
        stats["theoretical_capacity_gco2_per_g_max"],
    )

    accessibility_factor = clamp(
        0.20
        + weights["pore_openness"] * pore_openness
        + weights["site_density"] * site_density
        + weights["basic_oxygen_support"] * basic_oxygen_support
        + weights["stability_strength"] * stability_strength
        + weights["halide_penalty"] * halide_penalty
        + weights["sulfur_penalty"] * sulfur_penalty
        + weights["alkali_penalty"] * alkali_penalty
        + weights["network_rigidity"] * network_rigidity
        + weights["transition_penalty"] * transition_penalty
        + weights["hydration_penalty"] * hydration_penalty,
        0.05,
        1.00,
    )
    effective_uptake_proxy_gco2_per_g = (
        capacity["theoretical_capacity_gco2_per_g"] * accessibility_factor
    )
    effective_uptake_proxy_mmol_per_g = (
        capacity["theoretical_capacity_mmol_per_g"] * accessibility_factor
    )
    durability_support_factor = clamp(
        0.25
        + 0.35 * stability_strength
        + 0.20 * basic_oxygen_support
        + 0.10 * (1.0 - halide_penalty)
        + 0.05 * (1.0 - sulfur_penalty)
        + 0.05 * (1.0 - transition_penalty),
        0.10,
        1.00,
    )
    readiness_raw = effective_uptake_proxy_gco2_per_g * (0.60 + 0.40 * durability_support_factor)

    if theoretical_capacity_norm >= 0.70 and pore_openness < 0.45:
        uptake_mode = "capacity-driven mineralization"
    elif theoretical_capacity_norm >= 0.55 and pore_openness >= 0.45:
        uptake_mode = "balanced structural capture"
    elif pore_openness >= 0.65 and theoretical_capacity_norm < 0.55:
        uptake_mode = "accessibility-leaning sorption"
    else:
        uptake_mode = "mixed proxy candidate"

    if readiness_raw >= 0.28:
        screening_tier = "HIGH"
    elif readiness_raw >= 0.18:
        screening_tier = "MEDIUM"
    else:
        screening_tier = "LOW"

    return {
        "theoretical_capacity_norm": theoretical_capacity_norm,
        "pore_openness": pore_openness,
        "stability_strength": stability_strength,
        "site_density": site_density,
        "basic_oxygen_support": basic_oxygen_support,
        "halide_penalty": halide_penalty,
        "sulfur_penalty": sulfur_penalty,
        "alkali_penalty": alkali_penalty,
        "network_rigidity": network_rigidity,
        "transition_penalty": transition_penalty,
        "hydration_penalty": hydration_penalty,
        "accessibility_factor": accessibility_factor,
        "effective_uptake_proxy_gco2_per_g": effective_uptake_proxy_gco2_per_g,
        "effective_uptake_proxy_mmol_per_g": effective_uptake_proxy_mmol_per_g,
        "durability_support_factor": durability_support_factor,
        "readiness_raw": readiness_raw,
        "uptake_mode": uptake_mode,
        "screening_tier": screening_tier,
    }


def build_proxy_rows(candidates, weights=None):
    stats, profile_map, capacity_map = build_stats(candidates)
    rows = []
    for candidate in candidates:
        formula = candidate["formula"]
        profile = profile_map[formula]
        capacity = capacity_map[formula]
        metrics = derive_uptake_metrics(candidate, stats, profile, capacity, weights=weights)
        rows.append(
            {
                "formula": formula,
                "candidate_record": candidate,
                "composition_profile": profile,
                "theoretical_capacity": capacity,
                "uptake_proxy": metrics,
            }
        )
    max_readiness = max(row["uptake_proxy"]["readiness_raw"] for row in rows)
    min_readiness = min(row["uptake_proxy"]["readiness_raw"] for row in rows)
    for row in rows:
        row["uptake_proxy"]["readiness_score"] = 100.0 * normalize(
            row["uptake_proxy"]["readiness_raw"],
            min_readiness,
            max_readiness,
        )
        row["uptake_proxy"]["proxy_boundary_note"] = (
            "Theoretical carbonate capacity is a stoichiometric upper bound derived "
            "from carbonatable cation count and formula mass. Effective uptake and "
            "readiness values are then modulated by accessibility and chemistry "
            "heuristics, so they should be treated as screening proxies rather than "
            "measured adsorption performance."
        )
    rows.sort(
        key=lambda row: (
            -row["uptake_proxy"]["readiness_score"],
            -row["uptake_proxy"]["effective_uptake_proxy_gco2_per_g"],
            row["candidate_record"]["stability"],
            row["formula"],
        )
    )
    return rows, stats


def load_candidates(input_json=None):
    if input_json:
        return load_candidate_rows(input_json)
    return load_retained_candidates()


__all__ = [
    "DEFAULT_BASELINE_WEIGHTS",
    "build_proxy_rows",
    "build_stats",
    "derive_uptake_metrics",
    "load_candidates",
    "select_formula_representatives",
]
