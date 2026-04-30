#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from mp_auth import get_mp_rester
from sulfide_discovery import TARGET_TOP_K


ROOT = Path(__file__).resolve().parent
BASELINE_HISTORY_PATH = ROOT / "discovery_history.json"
OUTPUT_PATH = ROOT / "discovery_history_v2.json"
PIVOT_SEARCH_ELEMENTS = ["Li", "S", "Si"]
ENERGY_ABOVE_HULL = (0, 0.08)   # 0.08 eV — standard synthesizable threshold (0.03 now returns 0 on live MP)
MIN_ROOM_PER_ATOM = 16.0        # relaxed from 18.0 to match updated baseline
SUMMARY_FIELDS = [
    "formula_pretty",
    "volume",
    "structure",
    "formation_energy_per_atom",
]


def _search_summary(*, materials_client=None, **kwargs):
    if materials_client is not None:
        return list(materials_client.search_summary(**kwargs))

    with get_mp_rester() as mpr:
        return list(mpr.materials.summary.search(**kwargs))


def evaluate_pivot_decision(history, *, target_pool_size=TARGET_TOP_K):
    history = history or []
    candidate_count = len(history)
    best_room = max((row["room_per_atom"] for row in history), default=None)
    mean_stability = (
        sum(row["stability"] for row in history) / candidate_count
        if candidate_count
        else None
    )

    reasons = []
    if candidate_count == 0:
        reasons.append("baseline_search_empty")
    if candidate_count < target_pool_size:
        reasons.append("baseline_pool_underfilled")

    return {
        "baseline_candidate_count": candidate_count,
        "target_pool_size": target_pool_size,
        "best_room_per_atom": best_room,
        "mean_stability": mean_stability,
        "should_pivot": bool(reasons),
        "reasons": reasons or ["baseline_pool_sufficient"],
    }


def _screen_candidate_docs(docs, *, min_room_per_atom):
    refined_results = []
    for doc in docs:
        vol_per_atom = doc.volume / len(doc.structure)
        if vol_per_atom > min_room_per_atom:
            refined_results.append(
                {
                    "formula": doc.formula_pretty,
                    "room_per_atom": vol_per_atom,
                    "stability": doc.formation_energy_per_atom,
                }
            )

    refined_results.sort(key=lambda row: row["stability"])
    return refined_results


def autonomous_refinement(
    *,
    baseline_history=None,
    baseline_history_path=BASELINE_HISTORY_PATH,
    materials_client=None,
    force_pivot=False,
    target_pool_size=TARGET_TOP_K,
    min_room_per_atom=MIN_ROOM_PER_ATOM,
):
    if baseline_history is None:
        baseline_history = json.loads(Path(baseline_history_path).read_text())

    decision = evaluate_pivot_decision(
        baseline_history,
        target_pool_size=target_pool_size,
    )
    if not (force_pivot or decision["should_pivot"]):
        return []

    docs = _search_summary(
        materials_client=materials_client,
        elements=PIVOT_SEARCH_ELEMENTS,
        energy_above_hull=ENERGY_ABOVE_HULL,
        fields=SUMMARY_FIELDS,
    )
    return _screen_candidate_docs(docs, min_room_per_atom=min_room_per_atom)


def write_refinement_history(path, candidates):
    Path(path).write_text(json.dumps(candidates, indent=4) + "\n")


def main() -> None:
    print("ANALYZING DISCOVERY HISTORY...")
    baseline_history = json.loads(BASELINE_HISTORY_PATH.read_text())
    decision = evaluate_pivot_decision(baseline_history)

    if not decision["should_pivot"]:
        print("DECISION: Baseline pool is already sufficient. No pivot executed.")
        write_refinement_history(OUTPUT_PATH, [])
        return

    print(
        "DECISION: Baseline pool is underfilled. Pivoting to Silicon (Si) "
        "for a broader candidate search..."
    )
    results = autonomous_refinement(baseline_history=baseline_history)

    print(f"\nREFINEMENT COMPLETE: Found {len(results)} Silicon-based high-speed candidates.")
    for res in results[:3]:
        print(f"NEW CANDIDATE: {res['formula']} | Room per Atom: {res['room_per_atom']:.2f} Å^3")

    write_refinement_history(OUTPUT_PATH, results)


if __name__ == "__main__":
    main()
