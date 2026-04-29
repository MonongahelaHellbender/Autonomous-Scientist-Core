from chemical_formula_features import extract_composition_features
from shared_screening_utils import clamp, normalize


def build_feature_map(candidates):
    return {row["formula"]: extract_composition_features(row["formula"]) for row in candidates}


def build_stats(candidates, feature_map=None):
    feature_map = feature_map or build_feature_map(candidates)
    stabilities = [row["stability"] for row in candidates]
    pores = [row["pore_space"] for row in candidates]

    stat_fields = {
        "oxide_backbone_raw": [feature_map[row["formula"]]["oxide_backbone_raw"] for row in candidates],
        "anion_lability_raw": [feature_map[row["formula"]]["anion_lability_raw"] for row in candidates],
        "cation_mobility_raw": [feature_map[row["formula"]]["cation_mobility_raw"] for row in candidates],
        "redox_complexity_raw": [feature_map[row["formula"]]["redox_complexity_raw"] for row in candidates],
        "cation_support_raw": [feature_map[row["formula"]]["cation_support_raw"] for row in candidates],
        "composition_entropy": [feature_map[row["formula"]]["composition_entropy"] for row in candidates],
        "electronegativity_spread": [
            feature_map[row["formula"]]["electronegativity_spread"] for row in candidates
        ],
        "mean_atomic_mass": [feature_map[row["formula"]]["mean_atomic_mass"] for row in candidates],
        "hydrogen_fraction": [feature_map[row["formula"]]["hydrogen_fraction"] for row in candidates],
        "distinct_element_count": [
            feature_map[row["formula"]]["distinct_element_count"] for row in candidates
        ],
    }

    stats = {
        "stability_min": min(stabilities),
        "stability_max": max(stabilities),
        "pore_min": min(pores),
        "pore_max": max(pores),
    }
    for field, values in stat_fields.items():
        stats[f"{field}_min"] = min(values)
        stats[f"{field}_max"] = max(values)
    return stats


def derive_candidate_parameters(candidate, stats, composition_features):
    stability_strength = normalize(
        stats["stability_max"] - candidate["stability"],
        0.0,
        stats["stability_max"] - stats["stability_min"],
    )
    pore_openness = normalize(candidate["pore_space"], stats["pore_min"], stats["pore_max"])
    oxide_backbone = normalize(
        composition_features["oxide_backbone_raw"],
        stats["oxide_backbone_raw_min"],
        stats["oxide_backbone_raw_max"],
    )
    anion_lability = normalize(
        composition_features["anion_lability_raw"],
        stats["anion_lability_raw_min"],
        stats["anion_lability_raw_max"],
    )
    cation_mobility = normalize(
        composition_features["cation_mobility_raw"],
        stats["cation_mobility_raw_min"],
        stats["cation_mobility_raw_max"],
    )
    redox_complexity = normalize(
        composition_features["redox_complexity_raw"],
        stats["redox_complexity_raw_min"],
        stats["redox_complexity_raw_max"],
    )
    cation_support = normalize(
        composition_features["cation_support_raw"],
        stats["cation_support_raw_min"],
        stats["cation_support_raw_max"],
    )
    composition_complexity = 0.5 * normalize(
        composition_features["composition_entropy"],
        stats["composition_entropy_min"],
        stats["composition_entropy_max"],
    ) + 0.5 * normalize(
        composition_features["distinct_element_count"],
        stats["distinct_element_count_min"],
        stats["distinct_element_count_max"],
    )
    electrostatic_strain = normalize(
        composition_features["electronegativity_spread"],
        stats["electronegativity_spread_min"],
        stats["electronegativity_spread_max"],
    )
    mass_heaviness = normalize(
        composition_features["mean_atomic_mass"],
        stats["mean_atomic_mass_min"],
        stats["mean_atomic_mass_max"],
    )
    hydration_load = normalize(
        composition_features["hydrogen_fraction"],
        stats["hydrogen_fraction_min"],
        stats["hydrogen_fraction_max"],
    )

    baseline_temp_c = clamp(
        580.0
        + 9.0 * (stability_strength - 0.5)
        + 8.0 * (oxide_backbone - 0.5)
        + 5.0 * (cation_support - 0.5)
        - 5.0 * (anion_lability - 0.5)
        - 4.0 * (cation_mobility - 0.5)
        - 3.0 * (redox_complexity - 0.5)
        - 2.0 * (composition_complexity - 0.5)
        - 2.0 * (pore_openness - 0.5),
        555.0,
        600.0,
    )
    noise_std = clamp(
        0.043
        + 0.012 * (anion_lability - 0.5)
        + 0.010 * (cation_mobility - 0.5)
        + 0.008 * (hydration_load - 0.5)
        + 0.007 * (composition_complexity - 0.5)
        + 0.006 * (electrostatic_strain - 0.5)
        - 0.010 * (stability_strength - 0.5)
        - 0.009 * (oxide_backbone - 0.5),
        0.025,
        0.075,
    )
    failure_threshold_c = clamp(
        648.0
        + 22.0 * (stability_strength - 0.5)
        + 18.0 * (oxide_backbone - 0.5)
        + 8.0 * (cation_support - 0.5)
        - 18.0 * (anion_lability - 0.5)
        - 14.0 * (cation_mobility - 0.5)
        - 10.0 * (redox_complexity - 0.5)
        - 6.0 * (composition_complexity - 0.5)
        - 4.0 * (mass_heaviness - 0.5)
        - 5.0 * (pore_openness - 0.5),
        620.0,
        690.0,
    )

    return {
        "stability_strength": stability_strength,
        "pore_openness": pore_openness,
        "oxide_backbone": oxide_backbone,
        "anion_lability": anion_lability,
        "cation_mobility": cation_mobility,
        "redox_complexity": redox_complexity,
        "cation_support": cation_support,
        "composition_complexity": composition_complexity,
        "electrostatic_strain": electrostatic_strain,
        "mass_heaviness": mass_heaviness,
        "hydration_load": hydration_load,
        "baseline_temp_c": baseline_temp_c,
        "noise_std": noise_std,
        "failure_threshold_c": failure_threshold_c,
        "proxy_boundary_note": (
            "Composition-sensitive stress proxy derived from parsed formula "
            "stoichiometry, chemistry-family fractions, electronegativity spread, "
            "and candidate stability / pore metrics. This is materially stronger "
            "than element-count conditioning, but it is still a proxy rather than "
            "a first-principles thermal simulation."
        ),
    }


__all__ = [
    "build_feature_map",
    "build_stats",
    "derive_candidate_parameters",
]
