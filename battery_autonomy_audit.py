#!/usr/bin/env python3
"""
Offline autonomy and reproducibility audit for the battery lane.

Plain language:

- The battery lane is still the repo's flagship story.
- This audit checks whether the stored artifacts support that story right now.
- It also tests whether the silicon pivot looks justified under explicit
  openness-versus-stability tradeoffs instead of only narrative preference.

This is an offline artifact audit.
It does not rerun live Materials Project queries.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs" / "validation" / "battery_autonomy_audit_v1.json"


@dataclass(frozen=True)
class Paths:
    baseline_history: str = "discovery_history.json"
    pivot_history: str = "discovery_history_v2.json"
    lab_ready: str = "lab_ready_candidates.json"
    physics_validated: str = "physics_validated_candidates.json"
    thermal_validated: str = "thermal_validated_candidates.json"
    final_validated: str = "final_validated_candidates.json"
    discovery_report: str = "discovery_report_v1.1.json"
    readme: str = "README.md"
    research_summary: str = "RESEARCH_SUMMARY_v1.md"


def load_json(rel_path: str):
    return json.loads((ROOT / rel_path).read_text())


def dedupe_by_formula_best_stability(candidates: list[dict]) -> list[dict]:
    best = {}
    for candidate in candidates:
        formula = candidate["formula"]
        current = best.get(formula)
        if current is None:
            best[formula] = candidate
            continue
        if candidate["stability"] < current["stability"]:
            best[formula] = candidate
        elif candidate["stability"] == current["stability"] and candidate["room_per_atom"] > current["room_per_atom"]:
            best[formula] = candidate
    return list(best.values())


def duplicate_formulas(candidates: list[dict]) -> list[str]:
    seen = set()
    duplicates = set()
    for candidate in candidates:
        formula = candidate["formula"]
        if formula in seen:
            duplicates.add(formula)
        seen.add(formula)
    return sorted(duplicates)


def normalize(values: list[float], reverse: bool = False) -> list[float]:
    if not values:
        return []
    lo = min(values)
    hi = max(values)
    if hi - lo < 1e-12:
        return [0.5 for _ in values]
    scaled = [(value - lo) / (hi - lo) for value in values]
    if reverse:
        return [1.0 - value for value in scaled]
    return scaled


def candidate_summary(candidates: list[dict]) -> dict:
    rooms = [candidate["room_per_atom"] for candidate in candidates]
    stabilities = [candidate["stability"] for candidate in candidates]
    return {
        "count": len(candidates),
        "max_room_per_atom": round(max(rooms), 6),
        "mean_room_per_atom": round(sum(rooms) / len(rooms), 6),
        "best_stability": round(min(stabilities), 6),
        "mean_stability": round(sum(stabilities) / len(stabilities), 6),
    }


def pareto_frontier(candidates: list[dict], x_key: str, y_key: str, y_reverse: bool = False) -> list[str]:
    frontier = []
    for candidate in candidates:
        dominated = False
        for other in candidates:
            if other["formula"] == candidate["formula"] and other is candidate:
                continue
            better_x = other[x_key] >= candidate[x_key]
            if y_reverse:
                better_y = other[y_key] <= candidate[y_key]
                strict_y = other[y_key] < candidate[y_key]
            else:
                better_y = other[y_key] >= candidate[y_key]
                strict_y = other[y_key] > candidate[y_key]
            strict_x = other[x_key] > candidate[x_key]
            if better_x and better_y and (strict_x or strict_y):
                dominated = True
                break
        if not dominated:
            frontier.append(candidate["formula"])
    return sorted(set(frontier))


def pivot_tradeoff_audit(baseline: list[dict], pivot: list[dict]) -> dict:
    if not baseline and not pivot:
        return {
            "baseline_summary": [], "pivot_summary": [], "pareto_frontier_formulas": [],
            "pivot_weight_settings_won": 0, "baseline_weight_settings_won": 0,
            "tie_weight_settings": 0, "weight_sweep": [],
            "interpretation": "Both lanes empty — live query returned no candidates.",
            "live_result": "no_candidates",
        }
    if not pivot:
        return {
            "baseline_summary": candidate_summary(baseline), "pivot_summary": [],
            "pareto_frontier_formulas": [], "pivot_weight_settings_won": 0,
            "baseline_weight_settings_won": 21, "tie_weight_settings": 0, "weight_sweep": [],
            "interpretation": "Pivot lane empty — live query found no pivot candidates. Baseline wins by default.",
            "live_result": "pivot_empty",
        }
    if not baseline:
        return {
            "baseline_summary": [], "pivot_summary": candidate_summary(pivot),
            "pareto_frontier_formulas": [], "pivot_weight_settings_won": 21,
            "baseline_weight_settings_won": 0, "tie_weight_settings": 0, "weight_sweep": [],
            "interpretation": "Baseline lane empty — pivot wins by default.",
            "live_result": "baseline_empty",
        }

    combined = baseline + pivot
    room_norm = normalize([candidate["room_per_atom"] for candidate in combined])
    stability_norm = normalize([-candidate["stability"] for candidate in combined])
    scored = []
    for candidate, room_score, stability_score in zip(combined, room_norm, stability_norm):
        scored.append(
            {
                "formula": candidate["formula"],
                "lane": candidate["lane"],
                "room_score": room_score,
                "stability_score": stability_score,
            }
        )

    settings = []
    pivot_wins = 0
    baseline_wins = 0
    ties = 0
    for openness_weight_index in range(21):
        openness_weight = openness_weight_index / 20.0
        stability_weight = 1.0 - openness_weight
        by_lane = {"baseline": [], "pivot": []}
        for candidate in scored:
            total_score = (
                openness_weight * candidate["room_score"]
                + stability_weight * candidate["stability_score"]
            )
            by_lane[candidate["lane"]].append((total_score, candidate["formula"]))
        if not by_lane["baseline"] or not by_lane["pivot"]:
            continue
        baseline_best = max(by_lane["baseline"])
        pivot_best = max(by_lane["pivot"])
        if pivot_best[0] > baseline_best[0] + 1e-12:
            pivot_wins += 1
            verdict = "pivot"
        elif baseline_best[0] > pivot_best[0] + 1e-12:
            baseline_wins += 1
            verdict = "baseline"
        else:
            ties += 1
            verdict = "tie"
        settings.append(
            {
                "openness_weight": round(openness_weight, 2),
                "stability_weight": round(stability_weight, 2),
                "baseline_best_formula": baseline_best[1],
                "pivot_best_formula": pivot_best[1],
                "winner": verdict,
            }
        )

    frontier = pareto_frontier(combined, "room_per_atom", "stability", y_reverse=True)
    return {
        "baseline_summary": candidate_summary(baseline),
        "pivot_summary": candidate_summary(pivot),
        "pareto_frontier_formulas": frontier,
        "pivot_weight_settings_won": pivot_wins,
        "baseline_weight_settings_won": baseline_wins,
        "tie_weight_settings": ties,
        "weight_sweep": settings,
        "interpretation": (
            "If the pivot only wins under extreme openness weighting, it is a weak "
            "autonomous decision. If it wins across a broad tradeoff band, the "
            "pivot is locally defensible even before downstream physics."
        ),
    }


def final_lane_snapshot(final_candidates: list[dict]) -> dict:
    unique_final = dedupe_by_formula_best_stability(final_candidates)
    room_norm = normalize([candidate["room_per_atom"] for candidate in unique_final])
    bottleneck_norm = normalize([candidate["bottleneck_width_angstrom"] for candidate in unique_final])
    thermal_norm = normalize([candidate["max_operating_temp_celsius"] for candidate in unique_final])
    activation_norm = normalize([candidate["activation_energy_ev"] for candidate in unique_final], reverse=True)

    scored = []
    for candidate, room_score, bottleneck_score, thermal_score, activation_score in zip(
        unique_final,
        room_norm,
        bottleneck_norm,
        thermal_norm,
        activation_norm,
    ):
        total = (room_score + bottleneck_score + thermal_score + activation_score) / 4.0
        scored.append(
            {
                "formula": candidate["formula"],
                "score": round(total, 6),
            }
        )

    frontier = []
    for candidate in unique_final:
        dominated = False
        for other in unique_final:
            if other["formula"] == candidate["formula"] and other is candidate:
                continue
            better_or_equal = (
                other["room_per_atom"] >= candidate["room_per_atom"]
                and other["bottleneck_width_angstrom"] >= candidate["bottleneck_width_angstrom"]
                and other["max_operating_temp_celsius"] >= candidate["max_operating_temp_celsius"]
                and other["activation_energy_ev"] <= candidate["activation_energy_ev"]
            )
            strictly_better = (
                other["room_per_atom"] > candidate["room_per_atom"]
                or other["bottleneck_width_angstrom"] > candidate["bottleneck_width_angstrom"]
                or other["max_operating_temp_celsius"] > candidate["max_operating_temp_celsius"]
                or other["activation_energy_ev"] < candidate["activation_energy_ev"]
            )
            if better_or_equal and strictly_better:
                dominated = True
                break
        if not dominated:
            frontier.append(candidate["formula"])

    return {
        "unique_final_formula_count": len(unique_final),
        "equal_weight_top_formula": max(scored, key=lambda row: row["score"]),
        "pareto_frontier_formulas": sorted(set(frontier)),
        "max_reported_conductivity_ms_cm": max(candidate["conductivity_ms_cm"] for candidate in unique_final),
        "performance_ratings": {
            candidate["formula"]: candidate["perf_rating"]
            for candidate in unique_final
        },
    }


def chain_integrity(paths: Paths) -> dict:
    baseline_history = load_json(paths.baseline_history)
    pivot_history = load_json(paths.pivot_history)
    lab_ready = load_json(paths.lab_ready)
    physics = load_json(paths.physics_validated)
    thermal = load_json(paths.thermal_validated)
    final_candidates = load_json(paths.final_validated)
    discovery_report = load_json(paths.discovery_report)
    readme_text = (ROOT / paths.readme).read_text()
    summary_path = ROOT / paths.research_summary
    summary_text = summary_path.read_text() if summary_path.exists() else ""

    final_formulas = {candidate["formula"] for candidate in final_candidates}
    drift_flags = {
        "readme_mentions_5_minute_target": "5-minute target" in readme_text,
        "readme_mentions_ultra_fast": "Ultra-Fast Charging" in readme_text,
        "research_summary_mentions_superionic": "Superionic" in summary_text,
        "discovery_report_primary_candidate": discovery_report["primary_candidate"],
        "discovery_report_primary_candidate_in_current_final": discovery_report["primary_candidate"] in final_formulas,
        "current_final_has_viable_or_superionic_perf_rating": any(
            candidate["perf_rating"] != "LOW FLOW" for candidate in final_candidates
        ),
        "duplicate_formula_present_in_pivot_history": duplicate_formulas(pivot_history),
        "duplicate_formula_present_in_final_candidates": duplicate_formulas(final_candidates),
    }
    drift_flags["headline_vs_current_conductivity_mismatch"] = bool(
        drift_flags["readme_mentions_5_minute_target"]
        and not drift_flags["current_final_has_viable_or_superionic_perf_rating"]
    )
    drift_flags["generated_summary_overstates_current_final"] = bool(
        drift_flags["research_summary_mentions_superionic"]
        and not drift_flags["current_final_has_viable_or_superionic_perf_rating"]
    )

    return {
        "stage_counts": {
            "baseline_history": len(baseline_history),
            "pivot_history": len(pivot_history),
            "lab_ready": len(lab_ready),
            "physics_validated": len(physics),
            "thermal_validated": len(thermal),
            "final_validated": len(final_candidates),
        },
        "subset_checks": {
            "lab_ready_subset_of_pivot_history": {candidate["formula"] for candidate in lab_ready}.issubset(
                {candidate["formula"] for candidate in pivot_history}
            ),
            "physics_subset_of_lab_ready": {candidate["formula"] for candidate in physics}.issubset(
                {candidate["formula"] for candidate in lab_ready}
            ),
            "thermal_subset_of_physics": {candidate["formula"] for candidate in thermal}.issubset(
                {candidate["formula"] for candidate in physics}
            ),
            "final_subset_of_thermal": final_formulas.issubset(
                {candidate["formula"] for candidate in thermal}
            ),
        },
        "drift_flags": drift_flags,
    }


def build_artifact() -> dict:
    paths = Paths()
    baseline = [dict(candidate, lane="baseline") for candidate in dedupe_by_formula_best_stability(load_json(paths.baseline_history))]
    pivot = [dict(candidate, lane="pivot") for candidate in dedupe_by_formula_best_stability(load_json(paths.pivot_history))]
    final_candidates = load_json(paths.final_validated)

    return {
        "artifact_type": "battery_autonomy_audit_v1",
        "boundary_note": (
            "This audit is limited to local stored artifacts. It does not rerun live "
            "Materials Project searches and should be read as a reproducibility and "
            "claim-calibration pass."
        ),
        "theoretical_question": (
            "Does the silicon pivot remain defensible when openness and stability are "
            "made explicit as a weighted tradeoff instead of an implicit narrative?"
        ),
        "empirical_question": (
            "Do the current stored battery artifacts support the repo's flagship "
            "battery claims without contradiction?"
        ),
        "chain_integrity": chain_integrity(paths),
        "pivot_tradeoff_audit": pivot_tradeoff_audit(baseline, pivot),
        "final_lane_snapshot": final_lane_snapshot(final_candidates),
    }


def main() -> None:
    artifact = build_artifact()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(artifact, indent=2) + "\n")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
