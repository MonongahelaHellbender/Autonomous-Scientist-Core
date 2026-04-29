from collections import Counter
from fractions import Fraction

from chemical_formula_features import CARBONATABLE_CATIONS, NETWORK_FORMERS, parse_formula_counts
from shared_screening_utils import clamp

EXACT_OXIDE_ELEMENTS = CARBONATABLE_CATIONS | NETWORK_FORMERS | {"O"}
NETWORK_OXIDE_PHASES = {
    "Al": ("Al2O3", Fraction(1, 2)),
    "B": ("B2O3", Fraction(1, 2)),
    "Ge": ("GeO2", Fraction(1, 1)),
    "P": ("P2O5", Fraction(1, 2)),
    "Si": ("SiO2", Fraction(1, 1)),
}


def coeff_to_string(value):
    if value == 1:
        return ""
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def format_phase_term(coefficient, phase):
    prefix = coeff_to_string(coefficient)
    return f"{prefix} {phase}".strip()


def build_residual_phase_descriptors(counts):
    descriptors = []
    if counts.get("Si", 0):
        descriptors.append("SiO2-rich residual")
    if counts.get("Al", 0):
        descriptors.append("Al-O residual")
    if counts.get("P", 0):
        descriptors.append("phosphate-rich residual")
    if counts.get("B", 0):
        descriptors.append("borate-rich residual")
    if counts.get("Ge", 0):
        descriptors.append("germanate-rich residual")
    if counts.get("Cl", 0) or counts.get("F", 0):
        descriptors.append("halide-redistributed side products")
    if counts.get("S", 0):
        descriptors.append("sulfur-bearing side products")
    if counts.get("H", 0):
        descriptors.append("hydration-dependent side products")
    if counts.get("K", 0) or counts.get("Na", 0) or counts.get("Li", 0) or counts.get("Rb", 0) or counts.get("Cs", 0):
        descriptors.append("alkali-bearing residual salts")
    if not descriptors:
        descriptors.append("oxide-rich residual")
    return descriptors


def build_exact_oxide_conversion(formula):
    counts = parse_formula_counts(formula)
    disallowed = sorted(set(counts) - EXACT_OXIDE_ELEMENTS)
    if disallowed:
        return None

    carbonate_counts = {element: counts.get(element, 0) for element in CARBONATABLE_CATIONS}
    carbonatable_sites = sum(carbonate_counts.values())
    if carbonatable_sites <= 0:
        return None

    products = []
    for element in sorted(carbonate_counts):
        count = carbonate_counts[element]
        if count:
            products.append((Fraction(count, 1), f"{element}CO3"))

    for element in sorted(set(counts) & set(NETWORK_OXIDE_PHASES)):
        phase, multiplier = NETWORK_OXIDE_PHASES[element]
        products.append((multiplier * counts[element], phase))

    reactant_counts = Counter({element: Fraction(count, 1) for element, count in counts.items()})
    reactant_counts["C"] += Fraction(carbonatable_sites, 1)
    reactant_counts["O"] += Fraction(2 * carbonatable_sites, 1)

    product_counts = Counter()
    for coefficient, phase in products:
        phase_counts = parse_formula_counts(phase)
        for element, count in phase_counts.items():
            product_counts[element] += coefficient * count

    mass_balance_passed = reactant_counts == product_counts
    equation = (
        f"{formula} + {format_phase_term(Fraction(carbonatable_sites, 1), 'CO2')} -> "
        + " + ".join(format_phase_term(coefficient, phase) for coefficient, phase in products)
    )
    return {
        "carbonatable_sites": carbonatable_sites,
        "disallowed_elements": disallowed,
        "mass_balance_passed": mass_balance_passed,
        "products": [
            {
                "coefficient": float(coefficient),
                "coefficient_label": coeff_to_string(coefficient) or "1",
                "phase": phase,
            }
            for coefficient, phase in products
        ],
        "equation": equation,
    }


def classify_pathway_family(row, exact_conversion):
    profile = row["composition_profile"]
    uptake = row["uptake_proxy"]
    corr = row["thermochemical_corroboration"]

    halide_load = profile["chloride_fraction"] + profile["fluoride_fraction"]
    sulfur_load = profile["sulfur_fraction"]
    carbon_load = profile["carbon_fraction"]
    hydrogen_load = profile["hydrogen_fraction"]
    alkali_load = profile["alkali_fraction"]
    structural_gap = corr["structural_capture_propensity"] - corr["mineralization_propensity"]

    if carbon_load > 0.0:
        return "pre-carbonated completion pathway"
    if exact_conversion and corr["corroboration_class"] == "mineralization corroborated":
        return "oxide-framework bulk mineralization"
    if exact_conversion and corr["corroboration_class"] == "hybrid framework mineralization":
        return "oxide-framework hybrid mineralization"
    if exact_conversion and corr["corroboration_class"] == "structural-capture corroborated":
        return "oxide-framework surface carbonation"
    if exact_conversion and corr["corroboration_class"] == "mixed / ambiguous":
        return "oxide-framework mixed restructuring"
    if halide_load + sulfur_load + hydrogen_load + alkali_load >= 0.12:
        if corr["corroboration_class"] == "hybrid framework mineralization":
            return "mixed-anion hybrid mineralization"
        if corr["corroboration_class"] == "mineralization corroborated":
            return "mixed-anion mineralization"
        return "mixed-anion restructuring carbonation"
    if structural_gap > 0.10 and uptake["pore_openness"] >= 0.55:
        return "framework-retaining surface carbonation"
    return "mixed network restructuring"


def build_pathway_rationale(pathway_family, row, exact_conversion):
    corr = row["thermochemical_corroboration"]
    uptake = row["uptake_proxy"]
    profile = row["composition_profile"]

    if pathway_family == "oxide-framework bulk mineralization":
        return (
            "Exact oxide-only carbonate conversion is available, mineralization "
            "propensity exceeds structural support, and the formula has no mixed "
            "anion complication."
        )
    if pathway_family == "oxide-framework hybrid mineralization":
        return (
            "Exact oxide-only carbonate conversion is available, but structural "
            "and mineralization propensities are both high, which points to "
            "partial framework retention alongside carbonate growth."
        )
    if pathway_family == "oxide-framework mixed restructuring":
        return (
            "Exact oxide-only carbonate conversion is available, but the "
            "corroboration gap is too narrow to choose cleanly between surface "
            "retention and bulk conversion."
        )
    if pathway_family == "oxide-framework surface carbonation":
        return (
            "Exact oxide-only carbonate conversion is available as a ceiling, but "
            "the corroboration signal leans toward framework retention instead of "
            "deep bulk mineralization."
        )
    if pathway_family == "framework-retaining surface carbonation":
        return (
            "Structural capture support exceeds mineralization support and pore "
            "openness is high enough that surface or near-surface carbonation is "
            "a cleaner hypothesis than wholesale conversion."
        )
    if pathway_family == "mixed-anion hybrid mineralization":
        return (
            "Both pathway propensities are high, but mixed-anion chemistry makes "
            "a clean oxide-only conversion story too strong; expect carbonate "
            "growth plus substantial anion redistribution."
        )
    if pathway_family == "mixed-anion mineralization":
        return (
            "Mineralization support dominates, but mixed-anion chemistry implies "
            "that carbonate formation likely proceeds through a more complicated "
            "restructuring route than a clean oxide-only conversion."
        )
    if pathway_family == "mixed-anion restructuring carbonation":
        return (
            "The formula carries halide, sulfur, hydration, or alkali load large "
            "enough that carbonate formation likely competes with anion or defect "
            "rearrangement."
        )
    if pathway_family == "pre-carbonated completion pathway":
        return (
            "The formula already contains carbon, so the cleaner hypothesis is "
            "incremental carbonate completion or redistribution rather than a "
            "fresh zero-carbon capture route."
        )
    return (
        "The current signals do not cleanly favor one exact pathway family, so "
        "the safest posture is mixed network restructuring."
    )


def build_pathway_hypothesis(pathway_family, row, exact_conversion):
    formula = row["formula"]
    counts = row["composition_profile"]["counts"]
    carbonate_sites = row["theoretical_capacity"]["carbonatable_sites"]
    residuals = build_residual_phase_descriptors(counts)

    if exact_conversion:
        if pathway_family == "oxide-framework hybrid mineralization":
            return (
                f"{exact_conversion['equation']} (used here as a carbonate-conversion "
                "ceiling; the hybrid interpretation is that only part of this "
                "conversion happens before framework signatures begin to persist.)"
            )
        if pathway_family == "oxide-framework mixed restructuring":
            return (
                f"{exact_conversion['equation']} (used here as a stoichiometric ceiling; "
                "the observed signal does not yet decide between partial retention "
                "and deeper bulk conversion.)"
            )
        if pathway_family == "oxide-framework surface carbonation":
            return (
                f"{exact_conversion['equation']} (used here as a stoichiometric ceiling; "
                "the favored interpretation is that real uptake may stop earlier, "
                "with carbonate growth concentrated near surfaces or defect-accessible sites.)"
            )
        return exact_conversion["equation"]

    residual_clause = ", ".join(residuals)
    if pathway_family == "pre-carbonated completion pathway":
        return (
            f"{formula} + incremental CO2 -> CaCO3-rich growth with {residual_clause}; "
            "treat as completion or redistribution of an already carbon-bearing framework."
        )
    if pathway_family == "framework-retaining surface carbonation":
        return (
            f"{formula} + up to ~{carbonate_sites} CO2 equivalents -> surface or "
            f"pore-accessible carbonate formation with {residual_clause} and substantial "
            "framework retention."
        )
    if pathway_family == "mixed-anion restructuring carbonation":
        return (
            f"{formula} + up to ~{carbonate_sites} CO2 equivalents -> CaCO3-rich solids "
            f"plus {residual_clause}; expect anion redistribution rather than a single "
            "clean bulk-conversion product set."
        )
    if pathway_family == "mixed-anion hybrid mineralization":
        return (
            f"{formula} + up to ~{carbonate_sites} CO2 equivalents -> carbonate growth "
            f"plus {residual_clause}; expect both retained framework signatures and "
            "anion-driven restructuring."
        )
    if pathway_family == "mixed-anion mineralization":
        return (
            f"{formula} + up to ~{carbonate_sites} CO2 equivalents -> carbonate-rich "
            f"products with {residual_clause}; mineralization is favored, but exact "
            "mixed-anion products remain underconstrained."
        )
    return (
        f"{formula} + up to ~{carbonate_sites} CO2 equivalents -> mixed carbonate growth "
        f"with {residual_clause}; exact pathway remains underconstrained."
    )


def build_measurement_hooks(pathway_family, exact_conversion):
    if pathway_family == "oxide-framework bulk mineralization":
        return [
            "Look for strong carbonate-phase growth alongside silica- or oxide-rich residual phases.",
            "Framework signatures should diminish substantially if bulk conversion dominates.",
            "Post-carbonation solids should be closer to carbonate-plus-residual mixtures than to the parent lattice.",
        ]
    if pathway_family == "oxide-framework hybrid mineralization":
        return [
            "Look for carbonate-phase growth while parent framework signatures remain partially visible.",
            "Expect both product formation and residual framework persistence rather than full collapse.",
            "A pass would show mixed carbonate and network-residual signals in the same treated sample.",
        ]
    if pathway_family == "oxide-framework mixed restructuring":
        return [
            "Look for carbonate growth together with partial retention of the parent oxide framework.",
            "The key question is whether treatment trends toward full conversion or stalls in a mixed state.",
            "A pass would show a coherent mixed product set rather than random degradation.",
        ]
    if pathway_family == "oxide-framework surface carbonation":
        return [
            "Look for carbonate growth at accessible surfaces while the bulk oxide framework remains largely intact.",
            "The exact conversion equation should be treated as an upper ceiling rather than the default endpoint.",
            "A pass would show measurable uptake without broad lattice collapse.",
        ]
    if pathway_family == "framework-retaining surface carbonation":
        return [
            "Look for modest carbonate signatures concentrated at surfaces or accessible pores.",
            "Most parent-framework signatures should remain intact after treatment.",
            "A pass would show uptake without broad lattice conversion.",
        ]
    if pathway_family == "mixed-anion hybrid mineralization":
        return [
            "Look for carbonate growth together with persistent framework signatures and mixed-anion redistribution.",
            "Halide or sulfur signals should shift rather than vanish cleanly.",
            "A pass would show both carbonation and mixed-anion restructuring in the same treated sample.",
        ]
    if pathway_family == "mixed-anion mineralization":
        return [
            "Look for strong carbonate growth even though mixed-anion side products remain present.",
            "The product family should look more mineralized than surface-retained, but not as clean as an oxide-only conversion.",
            "A pass would show carbonate-rich products plus resolvable mixed-anion residuals.",
        ]
    if pathway_family == "mixed-anion restructuring carbonation":
        return [
            "Look for carbonate formation together with halide, sulfur, hydration, or alkali redistribution.",
            "Side-product or defect signatures matter more here than a single clean product phase.",
            "A pass would show that carbonate gain is coupled to mixed-anion restructuring rather than simple oxide conversion.",
        ]
    if pathway_family == "pre-carbonated completion pathway":
        return [
            "Look for incremental carbonate gain on top of an already carbon-bearing framework.",
            "Changes should look like carbonate completion or redistribution rather than a fresh full conversion route.",
            "A pass would show small but coherent carbonate growth without requiring a brand-new oxide-to-carbonate pathway.",
        ]
    return [
        "Look for a mixed product set rather than a single dominant route.",
        "A pass would show some carbonate gain together with unresolved framework restructuring.",
        "If no consistent product family appears, this pathway should stay internal only.",
    ]


def build_falsification_hook(pathway_family, exact_conversion):
    if exact_conversion and exact_conversion["mass_balance_passed"]:
        return (
            "If treated material shows neither carbonate products nor the expected "
            "oxide-residual family, the exact conversion hypothesis is weakened."
        )
    if pathway_family in {
        "mixed-anion hybrid mineralization",
        "mixed-anion mineralization",
        "mixed-anion restructuring carbonation",
    }:
        return (
            "If carbonation occurs without mixed-anion redistribution, this pathway "
            "family is probably overstating the side-chemistry burden."
        )
    if pathway_family == "framework-retaining surface carbonation":
        return (
            "If the bulk lattice collapses into carbonate-plus-residual products, the "
            "surface-retention hypothesis is too conservative."
        )
    if pathway_family == "pre-carbonated completion pathway":
        return (
            "If carbon content changes are large and accompanied by clean bulk-conversion "
            "products, this is not just a completion pathway."
        )
    return (
        "If repeated treatment does not yield a coherent product family, keep this "
        "candidate in the exploratory lane only."
    )


def build_pathway_confidence(row, pathway_family, exact_conversion):
    corr = row["thermochemical_corroboration"]
    uptake = row["uptake_proxy"]
    profile = row["composition_profile"]

    signal_agreement = 1.0 - abs(
        corr["structural_capture_propensity"] - corr["mineralization_propensity"]
    )
    impurity_load = min(
        1.0,
        profile["chloride_fraction"]
        + profile["fluoride_fraction"]
        + profile["sulfur_fraction"]
        + profile["alkali_fraction"]
        + profile["hydrogen_fraction"],
    )
    exact_bonus = 0.25 if exact_conversion and exact_conversion["mass_balance_passed"] else 0.0
    class_bonus = 0.15 if corr["corroboration_class"] != "mixed / ambiguous" else 0.05
    family_bonus = 0.10 if pathway_family in {
        "oxide-framework bulk mineralization",
        "oxide-framework hybrid mineralization",
        "oxide-framework mixed restructuring",
        "oxide-framework surface carbonation",
        "mixed-anion hybrid mineralization",
        "mixed-anion mineralization",
    } else 0.0

    return clamp(
        0.30
        + exact_bonus
        + class_bonus
        + family_bonus
        + 0.10 * signal_agreement
        + 0.10 * uptake["durability_support_factor"]
        - 0.15 * impurity_load,
        0.05,
        0.98,
    )


def build_pathway_rows(corroboration_rows):
    rows = []
    for row in corroboration_rows:
        exact_conversion = build_exact_oxide_conversion(row["formula"])
        pathway_family = classify_pathway_family(row, exact_conversion)
        pathway_confidence = build_pathway_confidence(row, pathway_family, exact_conversion)

        pathway_payload = {
            "pathway_family": pathway_family,
            "pathway_confidence": pathway_confidence,
            "stoichiometric_co2_ceiling_per_formula_unit": row["theoretical_capacity"][
                "carbonatable_sites"
            ],
            "exact_oxide_conversion_supported": bool(exact_conversion),
            "exact_mass_balance_passed": (
                exact_conversion["mass_balance_passed"] if exact_conversion else False
            ),
            "simplified_pathway_hypothesis": build_pathway_hypothesis(
                pathway_family, row, exact_conversion
            ),
            "pathway_rationale": build_pathway_rationale(pathway_family, row, exact_conversion),
            "expected_measurement_hooks": build_measurement_hooks(
                pathway_family, exact_conversion
            ),
            "falsification_hook": build_falsification_hook(pathway_family, exact_conversion),
            "exact_conversion_products": exact_conversion["products"] if exact_conversion else [],
            "pathway_boundary_note": (
                "This layer proposes simplified carbonation pathway families from "
                "stoichiometry, uptake signals, and corroboration signals. It is "
                "stronger than a pure ranking label, but it is still a hypothesis "
                "layer rather than measured reaction thermodynamics."
            ),
        }

        rows.append(
            {
                **row,
                "reaction_level_pathway": pathway_payload,
            }
        )

    rows.sort(
        key=lambda row: (
            -row["thermochemical_corroboration"]["corroborated_readiness_score"],
            -row["reaction_level_pathway"]["pathway_confidence"],
            row["formula"],
        )
    )
    return rows


__all__ = [
    "build_exact_oxide_conversion",
    "build_pathway_rows",
]
