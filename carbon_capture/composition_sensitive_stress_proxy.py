from cage_stress_test import simulate_cage_stress
from chemical_formula_features import extract_composition_features
from composition_conditioning import (
    build_feature_map as build_conditioning_feature_map,
    build_stats as build_conditioning_stats,
    derive_candidate_parameters,
)
from shared_screening_utils import load_candidate_rows, load_retained_candidates


def build_feature_map(candidates):
    return build_conditioning_feature_map(candidates)


def build_stats(candidates):
    feature_map = build_feature_map(candidates)
    stats = build_conditioning_stats(candidates, feature_map=feature_map)
    return stats, feature_map


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
    "build_feature_map",
    "build_stats",
    "extract_composition_features",
    "load_candidate_rows",
    "load_retained_candidates",
    "derive_candidate_parameters",
    "run_composition_sensitive_stress",
]
