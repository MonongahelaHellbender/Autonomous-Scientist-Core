import math
import re
from collections import Counter

from cage_stress_test import simulate_cage_stress
from property_conditioned_stress_proxy import (
    clamp,
    load_candidate_rows,
    load_retained_candidates,
    normalize,
)

ALKALI_METALS = {"Li", "Na", "K", "Rb", "Cs"}
ALKALINE_EARTH = {"Be", "Mg", "Ca", "Sr", "Ba"}
NETWORK_FORMERS = {"B", "Al", "Si", "P", "Ge"}
HALIDES = {"F", "Cl", "Br", "I"}
TRANSITION_METALS = {"Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Zr", "Mo"}
POST_TRANSITION_METALS = {"Ga", "In", "Sn"}
ANION_SPECIES = {"O", "S", "F", "Cl", "N", "C", "H", "P", "B"}

ELEMENT_DATA = {
    "Al": {"electronegativity": 1.61, "atomic_mass": 26.98},
    "B": {"electronegativity": 2.04, "atomic_mass": 10.81},
    "Ba": {"electronegativity": 0.89, "atomic_mass": 137.33},
    "Be": {"electronegativity": 1.57, "atomic_mass": 9.01},
    "C": {"electronegativity": 2.55, "atomic_mass": 12.01},
    "Ca": {"electronegativity": 1.00, "atomic_mass": 40.08},
    "Cl": {"electronegativity": 3.16, "atomic_mass": 35.45},
    "Co": {"electronegativity": 1.88, "atomic_mass": 58.93},
    "Cr": {"electronegativity": 1.66, "atomic_mass": 52.00},
    "Cu": {"electronegativity": 1.90, "atomic_mass": 63.55},
    "F": {"electronegativity": 3.98, "atomic_mass": 19.00},
    "Fe": {"electronegativity": 1.83, "atomic_mass": 55.85},
    "Ga": {"electronegativity": 1.81, "atomic_mass": 69.72},
    "Ge": {"electronegativity": 2.01, "atomic_mass": 72.63},
    "H": {"electronegativity": 2.20, "atomic_mass": 1.01},
    "In": {"electronegativity": 1.78, "atomic_mass": 114.82},
    "K": {"electronegativity": 0.82, "atomic_mass": 39.10},
    "Li": {"electronegativity": 0.98, "atomic_mass": 6.94},
    "Mg": {"electronegativity": 1.31, "atomic_mass": 24.31},
    "Mn": {"electronegativity": 1.55, "atomic_mass": 54.94},
    "Mo": {"electronegativity": 2.16, "atomic_mass": 95.95},
    "N": {"electronegativity": 3.04, "atomic_mass": 14.01},
    "Na": {"electronegativity": 0.93, "atomic_mass": 22.99},
    "Ni": {"electronegativity": 1.91, "atomic_mass": 58.69},
    "O": {"electronegativity": 3.44, "atomic_mass": 16.00},
    "P": {"electronegativity": 2.19, "atomic_mass": 30.97},
    "Rb": {"electronegativity": 0.82, "atomic_mass": 85.47},
    "S": {"electronegativity": 2.58, "atomic_mass": 32.06},
    "Sc": {"electronegativity": 1.36, "atomic_mass": 44.96},
    "Si": {"electronegativity": 1.90, "atomic_mass": 28.09},
    "Sn": {"electronegativity": 1.96, "atomic_mass": 118.71},
    "Sr": {"electronegativity": 0.95, "atomic_mass": 87.62},
    "Ti": {"electronegativity": 1.54, "atomic_mass": 47.87},
    "V": {"electronegativity": 1.63, "atomic_mass": 50.94},
    "Zn": {"electronegativity": 1.65, "atomic_mass": 65.38},
    "Zr": {"electronegativity": 1.33, "atomic_mass": 91.22},
}

TOKEN_PATTERN = re.compile(r"([A-Z][a-z]?|\(|\)|\d+)")


def parse_formula_counts(formula):
    tokens = TOKEN_PATTERN.findall(formula)
    if not tokens:
        raise ValueError(f"Could not parse formula: {formula}")

    stack = [Counter()]
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "(":
            stack.append(Counter())
            index += 1
            continue
        if token == ")":
            if len(stack) == 1:
                raise ValueError(f"Unmatched closing parenthesis in formula: {formula}")
            group = stack.pop()
            index += 1
            multiplier = 1
            if index < len(tokens) and tokens[index].isdigit():
                multiplier = int(tokens[index])
                index += 1
            for element, count in group.items():
                stack[-1][element] += count * multiplier
            continue
        if token.isdigit():
            raise ValueError(f"Unexpected standalone multiplier in formula: {formula}")

        element = token
        index += 1
        multiplier = 1
        if index < len(tokens) and tokens[index].isdigit():
            multiplier = int(tokens[index])
            index += 1
        stack[-1][element] += multiplier

    if len(stack) != 1:
        raise ValueError(f"Unmatched opening parenthesis in formula: {formula}")
    return dict(stack[0])


def counts_to_fractions(counts):
    total_atoms = sum(counts.values())
    if total_atoms <= 0:
        raise ValueError("Formula must contain a positive atom count")
    return {element: count / total_atoms for element, count in counts.items()}


def weighted_mean(values, fractions):
    return sum(values[element] * fraction for element, fraction in fractions.items())


def oxygen_to_network_closeness(oxygen_to_network_ratio, target=4.0, span=2.5):
    if oxygen_to_network_ratio is None:
        return 0.0
    return max(0.0, 1.0 - abs(oxygen_to_network_ratio - target) / span)


def classify_family(features):
    labels = ["calcium-based"]
    if features["network_former_fraction"] > 0.10:
        labels.append("network-forming")
    if features["oxygen_fraction"] > 0.45:
        labels.append("oxide-rich")
    if features["chloride_fraction"] > 0.0:
        labels.append("chloride-bearing")
    elif features["fluoride_fraction"] > 0.0:
        labels.append("fluoride-bearing")
    if features["sulfur_fraction"] > 0.0:
        labels.append("sulfur-bearing")
    if features["alkali_fraction"] > 0.0:
        labels.append("alkali-bearing")
    if features["transition_fraction"] > 0.0:
        labels.append("transition-metal-bearing")
    return labels


def extract_composition_features(formula):
    counts = parse_formula_counts(formula)
    fractions = counts_to_fractions(counts)
    missing = sorted(set(counts) - set(ELEMENT_DATA))
    if missing:
        raise ValueError(f"Missing element data for {missing} in {formula}")

    mean_electronegativity = weighted_mean(
        {element: payload["electronegativity"] for element, payload in ELEMENT_DATA.items()},
        fractions,
    )
    mean_atomic_mass = weighted_mean(
        {element: payload["atomic_mass"] for element, payload in ELEMENT_DATA.items()},
        fractions,
    )
    electronegativity_spread = math.sqrt(
        sum(
            fraction
            * (ELEMENT_DATA[element]["electronegativity"] - mean_electronegativity) ** 2
            for element, fraction in fractions.items()
        )
    )
    composition_entropy = -sum(
        fraction * math.log(fraction) for fraction in fractions.values() if fraction > 0
    )

    network_atom_count = sum(counts.get(element, 0) for element in NETWORK_FORMERS)
    oxygen_to_network_ratio = None
    if network_atom_count:
        oxygen_to_network_ratio = counts.get("O", 0) / network_atom_count

    anion_species_present = sum(1 for element in counts if element in ANION_SPECIES)

    features = {
        "counts": counts,
        "fractions": fractions,
        "total_atoms": sum(counts.values()),
        "distinct_element_count": len(counts),
        "oxygen_fraction": fractions.get("O", 0.0),
        "sulfur_fraction": fractions.get("S", 0.0),
        "fluoride_fraction": fractions.get("F", 0.0),
        "chloride_fraction": fractions.get("Cl", 0.0),
        "hydrogen_fraction": fractions.get("H", 0.0),
        "carbon_fraction": fractions.get("C", 0.0),
        "nitrogen_fraction": fractions.get("N", 0.0),
        "network_former_fraction": sum(fractions.get(element, 0.0) for element in NETWORK_FORMERS),
        "alkali_fraction": sum(fractions.get(element, 0.0) for element in ALKALI_METALS),
        "alkaline_earth_fraction": sum(
            fractions.get(element, 0.0) for element in ALKALINE_EARTH
        ),
        "transition_fraction": sum(
            fractions.get(element, 0.0) for element in TRANSITION_METALS
        ),
        "post_transition_fraction": sum(
            fractions.get(element, 0.0) for element in POST_TRANSITION_METALS
        ),
        "anion_diversity": anion_species_present,
        "oxygen_to_network_ratio": oxygen_to_network_ratio,
        "oxygen_to_network_closeness": oxygen_to_network_closeness(oxygen_to_network_ratio),
        "mean_electronegativity": mean_electronegativity,
        "electronegativity_spread": electronegativity_spread,
        "mean_atomic_mass": mean_atomic_mass,
        "composition_entropy": composition_entropy,
    }

    features["oxide_backbone_raw"] = (
        0.45 * features["network_former_fraction"]
        + 0.35 * features["oxygen_fraction"]
        + 0.20 * features["oxygen_to_network_closeness"]
    )
    features["anion_lability_raw"] = (
        1.00 * features["chloride_fraction"]
        + 0.30 * features["fluoride_fraction"]
        + 0.45 * features["sulfur_fraction"]
    )
    features["cation_mobility_raw"] = (
        1.00 * features["alkali_fraction"] + 0.35 * features["hydrogen_fraction"]
    )
    features["redox_complexity_raw"] = (
        1.00 * features["transition_fraction"]
        + 0.60 * features["post_transition_fraction"]
        + 0.30 * features["nitrogen_fraction"]
    )
    features["cation_support_raw"] = (
        features["alkaline_earth_fraction"] - 0.60 * features["alkali_fraction"]
    )
    features["family_tags"] = classify_family(features)
    return features


def build_stats(candidates):
    feature_map = {row["formula"]: extract_composition_features(row["formula"]) for row in candidates}
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
    return stats, feature_map


def derive_candidate_parameters(candidate, stats, composition_features):
    stability_strength = normalize(
        stats["stability_max"] - candidate["stability"],
        0.0,
        stats["stability_max"] - stats["stability_min"],
    )
    pore_openness = normalize(
        candidate["pore_space"], stats["pore_min"], stats["pore_max"]
    )
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


def run_composition_sensitive_stress(candidate, stats, feature_map, seed):
    composition_features = feature_map[candidate["formula"]]
    params = derive_candidate_parameters(candidate, stats, composition_features)
    stress_result = simulate_cage_stress(
        seed=seed,
        baseline_temp_c=params["baseline_temp_c"],
        noise_std=params["noise_std"],
        failure_threshold_c=params["failure_threshold_c"],
    )
    stress_result["model_scope"] = "composition-sensitive calcium-based thermal hardening proxy"
    stress_result["candidate_specific_physics"] = False
    stress_result["composition_sensitive_inputs"] = True

    return {
        "formula": candidate["formula"],
        "candidate_record": candidate,
        "composition_profile": composition_features,
        "composition_conditioning": params,
        "stress_result": stress_result,
    }


__all__ = [
    "build_stats",
    "extract_composition_features",
    "load_candidate_rows",
    "load_retained_candidates",
    "run_composition_sensitive_stress",
]
