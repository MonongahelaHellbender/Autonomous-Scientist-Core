import json
import re
from pathlib import Path

from cage_stress_test import simulate_cage_stress

VETTED_RESULTS_PATH = Path("carbon_capture/vetted_carbon_results.json")


def load_candidate_rows(path):
    payload = json.loads(Path(path).read_text())
    if isinstance(payload, dict) and "candidates" in payload:
        return payload["candidates"]
    if isinstance(payload, list):
        return payload
    raise ValueError(f"Unsupported candidate payload format in {path}")


def load_retained_candidates(path=VETTED_RESULTS_PATH):
    data = load_candidate_rows(path)
    return [row for row in data if row.get("final_verdict") == "APPROVED"]


def distinct_elements(formula):
    return sorted(set(re.findall(r"[A-Z][a-z]?", formula)))


def normalize(value, low, high):
    if high == low:
        return 0.5
    scaled = (value - low) / (high - low)
    return max(0.0, min(1.0, scaled))


def clamp(value, low, high):
    return max(low, min(high, value))


def build_stats(candidates):
    stabilities = [row["stability"] for row in candidates]
    pores = [row["pore_space"] for row in candidates]
    richness = [len(distinct_elements(row["formula"])) for row in candidates]
    return {
        "stability_min": min(stabilities),
        "stability_max": max(stabilities),
        "pore_min": min(pores),
        "pore_max": max(pores),
        "richness_min": min(richness),
        "richness_max": max(richness),
    }


def derive_candidate_parameters(candidate, stats):
    stability_strength = normalize(
        stats["stability_max"] - candidate["stability"],
        0.0,
        stats["stability_max"] - stats["stability_min"],
    )
    pore_openness = normalize(
        candidate["pore_space"], stats["pore_min"], stats["pore_max"]
    )
    element_richness = normalize(
        len(distinct_elements(candidate["formula"])),
        stats["richness_min"],
        stats["richness_max"],
    )

    baseline_temp_c = clamp(
        582.0
        + 8.0 * (stability_strength - 0.5)
        - 4.0 * (pore_openness - 0.5)
        - 2.0 * (element_richness - 0.5),
        560.0,
        595.0,
    )
    noise_std = clamp(
        0.05
        + 0.015 * (pore_openness - 0.5)
        + 0.010 * (element_richness - 0.5)
        - 0.012 * (stability_strength - 0.5),
        0.03,
        0.07,
    )
    failure_threshold_c = clamp(
        650.0
        + 20.0 * (stability_strength - 0.5)
        - 12.0 * (pore_openness - 0.5)
        - 6.0 * (element_richness - 0.5),
        630.0,
        675.0,
    )

    return {
        "stability_strength": stability_strength,
        "pore_openness": pore_openness,
        "element_richness": element_richness,
        "distinct_elements": distinct_elements(candidate["formula"]),
        "baseline_temp_c": baseline_temp_c,
        "noise_std": noise_std,
        "failure_threshold_c": failure_threshold_c,
        "proxy_boundary_note": (
            "Property-conditioned stress proxy derived from retained-candidate "
            "stability, pore space, and formula richness. This is still a "
            "heuristic model, not a first-principles thermal simulation."
        ),
    }


def run_property_conditioned_stress(candidate, stats, seed):
    params = derive_candidate_parameters(candidate, stats)
    stress_result = simulate_cage_stress(
        seed=seed,
        baseline_temp_c=params["baseline_temp_c"],
        noise_std=params["noise_std"],
        failure_threshold_c=params["failure_threshold_c"],
    )
    return {
        "formula": candidate["formula"],
        "candidate_record": candidate,
        "property_conditioning": params,
        "stress_result": stress_result,
    }
