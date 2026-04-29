import math
import re
from collections import Counter

ALKALI_METALS = {"Li", "Na", "K", "Rb", "Cs"}
ALKALINE_EARTH = {"Be", "Mg", "Ca", "Sr", "Ba"}
CARBONATABLE_CATIONS = {"Ca", "Mg", "Sr", "Ba"}
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

CO2_MOLAR_MASS = 44.0095
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


def calculate_formula_mass(counts):
    missing = sorted(set(counts) - set(ELEMENT_DATA))
    if missing:
        raise ValueError(f"Missing element data for {missing}")
    return sum(count * ELEMENT_DATA[element]["atomic_mass"] for element, count in counts.items())


def compute_theoretical_carbonate_capacity(counts):
    total_atoms = sum(counts.values())
    if total_atoms <= 0:
        raise ValueError("Formula must contain a positive atom count")
    formula_mass = calculate_formula_mass(counts)
    carbonatable_sites = sum(counts.get(element, 0) for element in CARBONATABLE_CATIONS)
    site_density = carbonatable_sites / total_atoms
    if formula_mass <= 0:
        raise ValueError("Formula mass must be positive")
    return {
        "carbonatable_sites": carbonatable_sites,
        "formula_mass_g_mol": formula_mass,
        "site_density": site_density,
        "theoretical_capacity_gco2_per_g": CO2_MOLAR_MASS * carbonatable_sites / formula_mass,
        "theoretical_capacity_mmol_per_g": 1000.0 * carbonatable_sites / formula_mass,
    }


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


__all__ = [
    "ALKALI_METALS",
    "ALKALINE_EARTH",
    "ANION_SPECIES",
    "CARBONATABLE_CATIONS",
    "CO2_MOLAR_MASS",
    "ELEMENT_DATA",
    "HALIDES",
    "NETWORK_FORMERS",
    "POST_TRANSITION_METALS",
    "TRANSITION_METALS",
    "calculate_formula_mass",
    "classify_family",
    "compute_theoretical_carbonate_capacity",
    "counts_to_fractions",
    "extract_composition_features",
    "oxygen_to_network_closeness",
    "parse_formula_counts",
    "weighted_mean",
]
