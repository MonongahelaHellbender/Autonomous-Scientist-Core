import json
from pathlib import Path

from shared_screening_utils import clamp, normalize

DEFAULT_INPUT_JSON = "carbon_capture/exact_oxide_conversion_subset_v1.json"

DEFAULT_CALIBRATION_WEIGHTS = {
    "capacity_norm": 0.24,
    "site_density": 0.16,
    "carbonate_support": 0.16,
    "residual_support": 0.12,
    "phase_simplicity": 0.10,
    "mineralization_propensity": 0.12,
    "pathway_confidence": 0.10,
    "reactant_resistance_penalty": 0.20,
    "corroborated_readiness": 0.15,
    "durability_support": 0.10,
}

DEFAULT_CARBONATE_SUPPORT = {
    "CaCO3": 1.00,
    "MgCO3": 0.95,
    "SrCO3": 0.90,
    "BaCO3": 0.88,
}

DEFAULT_RESIDUAL_SUPPORT = {
    "SiO2": 1.00,
    "Al2O3": 0.92,
    "P2O5": 0.78,
    "B2O3": 0.72,
    "GeO2": 0.68,
}


def load_exact_subset_rows(path=DEFAULT_INPUT_JSON):
    payload = json.loads(Path(path).read_text())
    return payload["candidates"]


def compute_product_family_metrics(
    row,
    carbonate_support=None,
    residual_support=None,
):
    carbonate_support = carbonate_support or DEFAULT_CARBONATE_SUPPORT
    residual_support = residual_support or DEFAULT_RESIDUAL_SUPPORT

    products = row["reaction_level_pathway"]["exact_conversion_products"]
    carbonate_products = []
    residual_products = []
    for product in products:
        phase = product["phase"]
        coefficient = float(product["coefficient"])
        if phase.endswith("CO3"):
            carbonate_products.append((phase, coefficient))
        else:
            residual_products.append((phase, coefficient))

    carbonate_total = sum(coefficient for _, coefficient in carbonate_products) or 1.0
    residual_total = sum(coefficient for _, coefficient in residual_products) or 1.0

    carbonate_family_support = sum(
        carbonate_support.get(phase, 0.80) * coefficient
        for phase, coefficient in carbonate_products
    ) / carbonate_total
    residual_family_support = sum(
        residual_support.get(phase, 0.60) * coefficient
        for phase, coefficient in residual_products
    ) / residual_total

    product_phase_count = len(products)
    distinct_product_phase_count = len({product["phase"] for product in products})
    product_phase_simplicity = 1.0 / (
        1.0
        + 0.35 * max(0, product_phase_count - 2)
        + 0.20 * max(0, distinct_product_phase_count - 2)
    )

    return {
        "carbonate_family_support": carbonate_family_support,
        "residual_family_support": residual_family_support,
        "product_phase_count": product_phase_count,
        "distinct_product_phase_count": distinct_product_phase_count,
        "product_phase_simplicity": product_phase_simplicity,
    }


def classify_calibration_band(raw_score, pathway_family):
    if raw_score >= 74.0 and pathway_family in {
        "oxide-framework bulk mineralization",
        "oxide-framework hybrid mineralization",
    }:
        return "thermodynamically reinforced exact conversion"
    if raw_score >= 68.0 and pathway_family in {
        "oxide-framework hybrid mineralization",
        "oxide-framework mixed restructuring",
    }:
        return "thermodynamically plausible exact restructuring"
    if raw_score >= 62.0 and pathway_family == "oxide-framework surface carbonation":
        return "surface-limited exact conversion"
    return "lower-confidence exact conversion"


def build_calibration_rows(
    rows,
    weights=None,
    carbonate_support=None,
    residual_support=None,
):
    weights = weights or DEFAULT_CALIBRATION_WEIGHTS
    carbonate_support = carbonate_support or DEFAULT_CARBONATE_SUPPORT
    residual_support = residual_support or DEFAULT_RESIDUAL_SUPPORT

    calibrated_rows = []
    raw_scores = []
    reactant_resistances = []
    conversion_drives = []

    for row in rows:
        uptake = row["uptake_proxy"]
        corroboration = row["thermochemical_corroboration"]
        profile = row["composition_profile"]
        pathway = row["reaction_level_pathway"]
        product_metrics = compute_product_family_metrics(
            row,
            carbonate_support=carbonate_support,
            residual_support=residual_support,
        )

        reactant_resistance = (
            0.40 * uptake["stability_strength"]
            + 0.30 * uptake["network_rigidity"]
            + 0.20 * corroboration["thermal_margin_norm"]
            + 0.10 * profile["oxygen_to_network_closeness"]
        )

        conversion_drive = (
            weights["capacity_norm"] * uptake["theoretical_capacity_norm"]
            + weights["site_density"] * uptake["site_density"]
            + weights["carbonate_support"] * product_metrics["carbonate_family_support"]
            + weights["residual_support"] * product_metrics["residual_family_support"]
            + weights["phase_simplicity"] * product_metrics["product_phase_simplicity"]
            + weights["mineralization_propensity"]
            * corroboration["mineralization_propensity"]
            + weights["pathway_confidence"] * pathway["pathway_confidence"]
        )

        raw_score = 100.0 * clamp(
            0.55 * conversion_drive
            + weights["reactant_resistance_penalty"] * (1.0 - reactant_resistance)
            + weights["corroborated_readiness"]
            * (corroboration["corroborated_readiness_score"] / 100.0)
            + weights["durability_support"] * uptake["durability_support_factor"],
            0.0,
            1.0,
        )
        calibration_band = classify_calibration_band(raw_score, pathway["pathway_family"])

        thermodynamic_payload = {
            **product_metrics,
            "reactant_resistance": reactant_resistance,
            "conversion_drive": conversion_drive,
            "thermodynamic_raw_score": raw_score,
            "calibration_band": calibration_band,
            "calibration_rationale": (
                "This exact-subset calibration balances stoichiometric carbonate "
                "yield, product-family simplicity, oxide-residual family support, "
                "and the existing thermal/corroboration signals. It is intended "
                "to rank which exact mass-balanced pathways look most chemically "
                "self-consistent inside the current repo."
            ),
            "calibration_boundary_note": (
                "This is still a surrogate thermodynamic calibration layer built "
                "from internal heuristics and exact stoichiometric product sets. "
                "It is stronger than a pure pathway label, but it is not a "
                "first-principles free-energy calculation or measured reaction "
                "thermodynamics."
            ),
        }

        calibrated_rows.append(
            {
                **row,
                "thermodynamic_calibration": thermodynamic_payload,
            }
        )
        raw_scores.append(raw_score)
        reactant_resistances.append(reactant_resistance)
        conversion_drives.append(conversion_drive)

    raw_min = min(raw_scores)
    raw_max = max(raw_scores)
    resistance_min = min(reactant_resistances)
    resistance_max = max(reactant_resistances)
    drive_min = min(conversion_drives)
    drive_max = max(conversion_drives)

    for row in calibrated_rows:
        payload = row["thermodynamic_calibration"]
        payload["thermodynamic_score"] = 100.0 * normalize(
            payload["thermodynamic_raw_score"], raw_min, raw_max
        )
        payload["reactant_resistance_norm"] = normalize(
            payload["reactant_resistance"], resistance_min, resistance_max
        )
        payload["conversion_drive_norm"] = normalize(
            payload["conversion_drive"], drive_min, drive_max
        )

    calibrated_rows.sort(
        key=lambda row: (
            -row["thermodynamic_calibration"]["thermodynamic_raw_score"],
            -row["thermochemical_corroboration"]["corroborated_readiness_score"],
            row["formula"],
        )
    )

    stats = {
        "thermodynamic_raw_min": raw_min,
        "thermodynamic_raw_max": raw_max,
        "reactant_resistance_min": resistance_min,
        "reactant_resistance_max": resistance_max,
        "conversion_drive_min": drive_min,
        "conversion_drive_max": drive_max,
    }
    return calibrated_rows, stats


__all__ = [
    "DEFAULT_CALIBRATION_WEIGHTS",
    "DEFAULT_CARBONATE_SUPPORT",
    "DEFAULT_INPUT_JSON",
    "DEFAULT_RESIDUAL_SUPPORT",
    "build_calibration_rows",
    "classify_calibration_band",
    "compute_product_family_metrics",
    "load_exact_subset_rows",
]
