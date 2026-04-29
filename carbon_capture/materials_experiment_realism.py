import json
from collections import Counter
from pathlib import Path

from chemical_formula_features import calculate_formula_mass, parse_formula_counts
from shared_screening_utils import clamp

DEFAULT_CALIBRATION_JSON = "carbon_capture/exact_subset_thermodynamic_calibration_v1.json"
DEFAULT_PACKET_JSON = "carbon_capture/reinforced_exact_lane_experimental_packet_v1.json"
DEFAULT_OVERLAY_JSON = "carbon_capture/reinforced_exact_lane_stability_overlay_v1.json"
DEFAULT_OUTPUT_JSON = "carbon_capture/materials_experiment_realism_v1.json"


def load_json(path):
    return json.loads(Path(path).read_text())


def calibrated_row_map(payload):
    return {row["formula"]: row for row in payload["candidates"]}


def overlay_map(payload):
    return {row["formula"]: row for row in payload["candidate_stability_profiles"]}


def product_mass_breakdown(row):
    parent_mass = row["theoretical_capacity"]["formula_mass_g_mol"]
    product_masses = {}
    total_product_mass = 0.0
    for product in row["reaction_level_pathway"]["exact_conversion_products"]:
        phase_mass = calculate_formula_mass(parse_formula_counts(product["phase"]))
        mass = float(product["coefficient"]) * phase_mass
        product_masses[product["phase"]] = mass
        total_product_mass += mass

    carbonate_mass = sum(
        mass for phase, mass in product_masses.items() if phase.endswith("CO3")
    )
    residual_mass = total_product_mass - carbonate_mass
    return {
        "parent_mass": parent_mass,
        "product_masses": product_masses,
        "total_product_mass": total_product_mass,
        "carbonate_mass_fraction_full_conversion": carbonate_mass / total_product_mass,
        "residual_mass_fraction_full_conversion": residual_mass / total_product_mass,
    }


def base_screen_window(pathway_family, condition_label):
    if condition_label == "baseline identity screen":
        return {
            "temperature_c_window": [25, 80],
            "relative_humidity_percent_window": [20, 50],
            "co2_environment": "ambient laboratory air",
            "dwell_hours_window": [0.5, 2.0],
            "particle_size_guidance": "record as-received particle size before aggressive milling",
        }
    if condition_label == "repeat post-treatment phase scan":
        return {
            "temperature_c_window": [25, 80],
            "relative_humidity_percent_window": [20, 50],
            "co2_environment": "ambient after treatment",
            "dwell_hours_window": [0.5, 2.0],
            "particle_size_guidance": "rescan the treated powder without reprocessing it",
        }

    if "bulk mineralization" in pathway_family and "dry CO2" in condition_label:
        return {
            "temperature_c_window": [380, 560],
            "relative_humidity_percent_window": [0, 5],
            "co2_environment": "dry high-CO2 flow or near-pure CO2",
            "dwell_hours_window": [2.0, 8.0],
            "particle_size_guidance": "finely divided oxide-rich powder",
        }
    if "bulk mineralization" in pathway_family:
        return {
            "temperature_c_window": [240, 420],
            "relative_humidity_percent_window": [40, 80],
            "co2_environment": "humidified high-CO2 flow",
            "dwell_hours_window": [2.0, 8.0],
            "particle_size_guidance": "finely divided oxide-rich powder with controlled moisture",
        }

    if "hybrid mineralization" in pathway_family and "dry CO2" in condition_label:
        return {
            "temperature_c_window": [320, 500],
            "relative_humidity_percent_window": [0, 5],
            "co2_environment": "dry high-CO2 flow or near-pure CO2",
            "dwell_hours_window": [2.0, 10.0],
            "particle_size_guidance": "finely divided powder, but keep a coarser split for surface-versus-bulk comparison",
        }
    if "hybrid mineralization" in pathway_family:
        return {
            "temperature_c_window": [160, 320],
            "relative_humidity_percent_window": [40, 85],
            "co2_environment": "humidified high-CO2 flow",
            "dwell_hours_window": [2.0, 10.0],
            "particle_size_guidance": "compare a finely milled fraction against a gentler size cut",
        }

    if "surface carbonation" in pathway_family and "dry CO2" in condition_label:
        return {
            "temperature_c_window": [120, 260],
            "relative_humidity_percent_window": [0, 5],
            "co2_environment": "dry CO2-rich flow",
            "dwell_hours_window": [1.0, 6.0],
            "particle_size_guidance": "surface-accessible powder or lightly roughened grains",
        }
    if "surface carbonation" in pathway_family:
        return {
            "temperature_c_window": [40, 180],
            "relative_humidity_percent_window": [50, 90],
            "co2_environment": "humidified CO2-rich flow",
            "dwell_hours_window": [1.0, 6.0],
            "particle_size_guidance": "preserve surface area and pore access rather than forcing dense sintering",
        }

    if "dry CO2" in condition_label:
        return {
            "temperature_c_window": [280, 480],
            "relative_humidity_percent_window": [0, 5],
            "co2_environment": "dry high-CO2 flow",
            "dwell_hours_window": [2.0, 10.0],
            "particle_size_guidance": "finely divided powder with a comparison split left slightly coarser",
        }
    return {
        "temperature_c_window": [120, 300],
        "relative_humidity_percent_window": [40, 85],
        "co2_environment": "humidified high-CO2 flow",
        "dwell_hours_window": [2.0, 10.0],
        "particle_size_guidance": "preserve accessible surfaces while avoiding uncontrolled hydration",
    }


def adjust_window(window, row, stability_profile):
    calibration = row["thermodynamic_calibration"]
    resistance_norm = calibration["reactant_resistance_norm"]
    mineralization = row["thermochemical_corroboration"]["mineralization_propensity"]
    structural_capture = row["thermochemical_corroboration"]["structural_capture_propensity"]

    temp_shift = round((resistance_norm - 0.5) * 120)
    dwell_shift = 1.5 if stability_profile["stability_tier"] != "core_anchor" else 0.0
    if mineralization < structural_capture:
        dwell_shift += 1.0

    low_temp, high_temp = window["temperature_c_window"]
    low_temp = int(clamp(low_temp + temp_shift, 25, 700))
    high_temp = int(clamp(high_temp + temp_shift, low_temp + 20, 750))

    low_dwell, high_dwell = window["dwell_hours_window"]
    low_dwell = round(clamp(low_dwell + 0.5 * dwell_shift, 0.5, 24.0), 1)
    high_dwell = round(clamp(high_dwell + 1.5 * dwell_shift, low_dwell + 0.5, 48.0), 1)

    humidity_window = list(window["relative_humidity_percent_window"])
    if row["composition_profile"]["halide_fraction"] > 0.0:
        humidity_window[1] = min(humidity_window[1], 70)
    if row["composition_profile"]["hydrogen_fraction"] > 0.0:
        humidity_window[0] = max(humidity_window[0], 30)

    return {
        **window,
        "temperature_c_window": [low_temp, high_temp],
        "relative_humidity_percent_window": humidity_window,
        "dwell_hours_window": [low_dwell, high_dwell],
    }


def condition_window_map(row, dossier, stability_profile):
    windows = {}
    pathway_family = row["reaction_level_pathway"]["pathway_family"]
    for condition_label in dossier["condition_family"]:
        base = base_screen_window(pathway_family, condition_label)
        adjusted = adjust_window(base, row, stability_profile)
        adjusted["rationale"] = (
            "Window chosen from pathway family, reactant resistance, and current "
            "stability tier. Treat this as a starting-screen bracket rather than "
            "as a first-principles optimum."
        )
        windows[condition_label] = adjusted
    return windows


def synthesis_feasibility(row):
    counts = row["composition_profile"]["counts"]
    features = row["composition_profile"]
    distinct_elements = len(counts)
    common_element_bonus = sum(
        {
            "Ca": 1.00,
            "Mg": 0.95,
            "Si": 0.95,
            "O": 1.00,
            "Al": 0.72,
            "P": 0.58,
            "S": 0.42,
            "F": 0.45,
            "Cl": 0.38,
            "Sr": 0.32,
            "Ba": 0.22,
        }.get(element, 0.40)
        for element in counts
    ) / distinct_elements

    impurity_risk = clamp(
        0.70 * features["halide_fraction"]
        + 0.60 * features["sulfur_fraction"]
        + 0.45 * features["alkali_fraction"]
        + 0.25 * max(0, distinct_elements - 4) / 6.0,
        0.0,
        1.0,
    )
    elemental_complexity_penalty = clamp(0.10 * max(0, distinct_elements - 3), 0.0, 0.35)
    special_handling_penalty = clamp(
        0.20 * int(any(element in counts for element in ("Sr", "Ba")))
        + 0.15 * int("P" in counts)
        + 0.18 * int(features["halide_fraction"] > 0.0)
        + 0.12 * int(features["sulfur_fraction"] > 0.0),
        0.0,
        0.45,
    )

    if features["halide_fraction"] > 0.0 or features["sulfur_fraction"] > 0.0:
        route_family = "mixed-anion controlled-atmosphere route"
    elif any(element in counts for element in ("Sr", "Ba")):
        route_family = "heavy alkaline-earth oxide/carbonate route"
    elif any(element in counts for element in ("P", "Al")):
        route_family = "mixed oxide network-former route"
    else:
        route_family = "simple oxide/carbonate solid-state route"

    route_penalty = {
        "simple oxide/carbonate solid-state route": 0.10,
        "mixed oxide network-former route": 0.20,
        "heavy alkaline-earth oxide/carbonate route": 0.28,
        "mixed-anion controlled-atmosphere route": 0.35,
    }[route_family]

    feasibility_score = 100.0 * clamp(
        0.60 * common_element_bonus
        + 0.25 * (1.0 - route_penalty)
        + 0.15 * (1.0 - impurity_risk)
        - 0.45 * elemental_complexity_penalty
        - 0.45 * special_handling_penalty,
        0.0,
        1.0,
    )

    if feasibility_score >= 74:
        tier = "HIGH"
    elif feasibility_score >= 55:
        tier = "MODERATE"
    else:
        tier = "CAUTION"

    precursor_families = []
    if "Ca" in counts:
        precursor_families.append("calcium carbonate or calcium oxide feed")
    if "Mg" in counts:
        precursor_families.append("magnesium oxide or carbonate co-feed")
    if "Si" in counts:
        precursor_families.append("silica or silicate network former")
    if "P" in counts:
        precursor_families.append("phosphate-retaining precursor control")
    if features["halide_fraction"] > 0.0:
        precursor_families.append("halide retention / volatilization control")

    return {
        "route_family": route_family,
        "synthesis_feasibility_score": feasibility_score,
        "synthesis_feasibility_tier": tier,
        "common_precursor_support": common_element_bonus,
        "impurity_risk_proxy": impurity_risk,
        "elemental_complexity_penalty": elemental_complexity_penalty,
        "special_handling_penalty": special_handling_penalty,
        "recommended_precursor_families": precursor_families,
        "root_cause_note": (
            "This is a precursor-burden and mixed-anion complexity screen, not a "
            "measured synthesis success predictor."
        ),
    }


def kinetics_expectation(row, stability_profile):
    pathway_family = row["reaction_level_pathway"]["pathway_family"]
    calibration = row["thermodynamic_calibration"]
    uptake = row["uptake_proxy"]
    corroboration = row["thermochemical_corroboration"]

    resistance = calibration["reactant_resistance_norm"]
    site_density = row["theoretical_capacity"]["site_density"]
    mineralization = corroboration["mineralization_propensity"]
    structural_capture = corroboration["structural_capture_propensity"]

    if "bulk mineralization" in pathway_family:
        regime = "bulk-favored with diffusion-limited late stage"
        onset_window = [1.0, 4.0]
        bulk_window = [4.0, 16.0]
    elif "hybrid mineralization" in pathway_family:
        regime = "surface onset followed by partial bulk conversion"
        onset_window = [0.5, 3.0]
        bulk_window = [3.0, 18.0]
    elif "surface carbonation" in pathway_family:
        regime = "surface-confined early uptake"
        onset_window = [0.25, 2.0]
        bulk_window = [8.0, 24.0]
    else:
        regime = "restructuring-sensitive staged conversion"
        onset_window = [1.0, 6.0]
        bulk_window = [6.0, 24.0]

    if stability_profile["stability_tier"] not in {"core_anchor", "stable_plausible_restructuring"}:
        bulk_window = [round(bulk_window[0] * 1.2, 1), round(bulk_window[1] * 1.4, 1)]

    rate_proxy = clamp(
        0.35 * uptake["site_density"]
        + 0.25 * mineralization
        + 0.15 * structural_capture
        + 0.25 * (1.0 - resistance),
        0.0,
        1.0,
    )
    if rate_proxy >= 0.78:
        rate_class = "FAST_SCREENABLE"
    elif rate_proxy >= 0.60:
        rate_class = "MODERATE_SCREENABLE"
    else:
        rate_class = "SLOW_OR_RESTRUCTURING_LIMITED"

    return {
        "kinetics_regime": regime,
        "kinetics_rate_class": rate_class,
        "rate_proxy": rate_proxy,
        "expected_onset_window_hours": onset_window,
        "expected_bulk_signal_window_hours": bulk_window,
        "dominant_limiters": [
            limiter
            for limiter, flag in [
                ("reactant rigidity", resistance >= 0.60),
                ("site scarcity", site_density <= 0.26),
                ("surface-first competition", structural_capture > mineralization),
            ]
            if flag
        ],
    }


def conversion_extent_window(row, stability_profile, condition_label):
    pathway_family = row["reaction_level_pathway"]["pathway_family"]

    if "baseline identity screen" == condition_label:
        return [0.0, 0.02]
    if "repeat post-treatment phase scan" == condition_label:
        return None

    if "bulk mineralization" in pathway_family and "dry CO2" in condition_label:
        base = [0.55, 0.85]
    elif "bulk mineralization" in pathway_family:
        base = [0.45, 0.75]
    elif "hybrid mineralization" in pathway_family and "dry CO2" in condition_label:
        base = [0.35, 0.65]
    elif "hybrid mineralization" in pathway_family:
        base = [0.45, 0.80]
    elif "surface carbonation" in pathway_family and "dry CO2" in condition_label:
        base = [0.10, 0.28]
    elif "surface carbonation" in pathway_family:
        base = [0.18, 0.40]
    elif "dry CO2" in condition_label:
        base = [0.25, 0.50]
    else:
        base = [0.30, 0.55]

    tier = stability_profile["stability_tier"]
    if tier.startswith("provisional") or "threshold_sensitive" in tier:
        base = [max(0.02, base[0] - 0.08), max(base[0] + 0.10, base[1] - 0.10)]
    if tier.startswith("fragile"):
        base = [max(0.01, base[0] - 0.12), max(base[0] + 0.08, base[1] - 0.15)]

    return [round(base[0], 2), round(base[1], 2)]


def treated_phase_fractions(parent_mass, breakdown, extent):
    total_product_mass = breakdown["total_product_mass"]
    denominator = (1.0 - extent) * parent_mass + extent * total_product_mass
    phase_fractions = {
        phase: extent * mass / denominator
        for phase, mass in breakdown["product_masses"].items()
    }
    parent_fraction = (1.0 - extent) * parent_mass / denominator
    carbonate_fraction = sum(
        value for phase, value in phase_fractions.items() if phase.endswith("CO3")
    )
    residual_fraction = sum(
        value for phase, value in phase_fractions.items() if not phase.endswith("CO3")
    )
    return {
        "parent_fraction": parent_fraction,
        "carbonate_fraction": carbonate_fraction,
        "residual_fraction": residual_fraction,
        "phase_fractions": phase_fractions,
    }


def phase_fraction_expectations(row, dossier, stability_profile):
    parent_mass = row["theoretical_capacity"]["formula_mass_g_mol"]
    breakdown = product_mass_breakdown(row)
    expectation_map = {}
    for condition_label in dossier["condition_family"]:
        extent_window = conversion_extent_window(row, stability_profile, condition_label)
        if extent_window is None:
            continue
        low_state = treated_phase_fractions(parent_mass, breakdown, extent_window[0])
        high_state = treated_phase_fractions(parent_mass, breakdown, extent_window[1])
        phase_labels = sorted(breakdown["product_masses"])
        expectation_map[condition_label] = {
            "conversion_extent_window": extent_window,
            "parent_fraction_window": [
                round(low_state["parent_fraction"], 3),
                round(high_state["parent_fraction"], 3),
            ],
            "carbonate_fraction_window": [
                round(low_state["carbonate_fraction"], 3),
                round(high_state["carbonate_fraction"], 3),
            ],
            "residual_fraction_window": [
                round(low_state["residual_fraction"], 3),
                round(high_state["residual_fraction"], 3),
            ],
            "phase_fraction_windows": {
                phase: [
                    round(low_state["phase_fractions"].get(phase, 0.0), 3),
                    round(high_state["phase_fractions"].get(phase, 0.0), 3),
                ]
                for phase in phase_labels
            },
            "boundary_note": (
                "These are treated-solid fraction proxies derived from stoichiometric "
                "products and a heuristic conversion-extent window. They are not "
                "Rietveld-refined phase fractions."
            ),
        }
    return {
        "full_conversion_phase_mass_fractions": {
            phase: round(mass / breakdown["total_product_mass"], 3)
            for phase, mass in breakdown["product_masses"].items()
        },
        "condition_expectations": expectation_map,
    }


def realism_profile(row, dossier, stability_profile):
    return {
        "formula": row["formula"],
        "selected_role": dossier["selected_role"],
        "stability_tier": stability_profile["stability_tier"],
        "campaign_batch": dossier["campaign_batch"],
        "pathway_family": row["reaction_level_pathway"]["pathway_family"],
        "reaction_window_suggestions": condition_window_map(row, dossier, stability_profile),
        "synthesis_feasibility": synthesis_feasibility(row),
        "kinetics_expectation": kinetics_expectation(row, stability_profile),
        "phase_fraction_expectations": phase_fraction_expectations(
            row, dossier, stability_profile
        ),
        "realism_boundary_note": (
            "This layer is a candidate-specific lab-start heuristic built on current "
            "proxy and pathway results. It is meant to guide early screening, not to "
            "replace measured kinetics, equilibrium, or synthesis studies."
        ),
    }


def build_artifact(
    calibration_json=DEFAULT_CALIBRATION_JSON,
    packet_json=DEFAULT_PACKET_JSON,
    overlay_json=DEFAULT_OVERLAY_JSON,
):
    calibrated = load_json(calibration_json)
    packet = load_json(packet_json)
    overlay = load_json(overlay_json)

    rows_by_formula = calibrated_row_map(calibrated)
    stability_by_formula = overlay_map(overlay)
    profiles = []
    for dossier in packet["candidate_dossiers"]:
        formula = dossier["formula"]
        profiles.append(
            realism_profile(
                rows_by_formula[formula],
                dossier,
                stability_by_formula[formula],
            )
        )

    feasibility_counts = Counter(
        profile["synthesis_feasibility"]["synthesis_feasibility_tier"]
        for profile in profiles
    )
    kinetics_counts = Counter(
        profile["kinetics_expectation"]["kinetics_rate_class"] for profile in profiles
    )
    return {
        "artifact_type": "materials_experiment_realism_v1",
        "sources": {
            "calibration": calibration_json,
            "experimental_packet": packet_json,
            "stability_overlay": overlay_json,
        },
        "candidate_count": len(profiles),
        "synthesis_feasibility_counts": dict(feasibility_counts),
        "kinetics_rate_counts": dict(kinetics_counts),
        "candidate_profiles": profiles,
        "boundary_note": (
            "This artifact adds candidate-specific starting windows, route burden, "
            "kinetics expectations, and phase-fraction proxies so the carbon lane is "
            "closer to a real experimental screening program."
        ),
    }


def write_json_output(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))
