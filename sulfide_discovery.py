#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from mp_auth import get_mp_rester


ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "discovery_history.json"
SEARCH_ELEMENTS = ["Li", "S", "P"]
ENERGY_ABOVE_HULL = (0, 0.08)   # 0.08 eV — standard synthesizable threshold (0.03 now returns 0 on live MP)
MIN_ROOM_PER_ATOM = 16.0        # relaxed from 17.0 to capture more candidates
TARGET_TOP_K = 5
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


def _screen_candidate_docs(docs, *, min_room_per_atom):
    results = []
    for doc in docs:
        vol_per_atom = doc.volume / len(doc.structure)
        if vol_per_atom > min_room_per_atom:
            results.append(
                {
                    "formula": doc.formula_pretty,
                    "room_per_atom": vol_per_atom,
                    "stability": doc.formation_energy_per_atom,
                }
            )
    results.sort(key=lambda row: row["stability"])
    return results


def discover_baseline_candidates(
    *,
    materials_client=None,
    min_room_per_atom=MIN_ROOM_PER_ATOM,
):
    docs = _search_summary(
        materials_client=materials_client,
        elements=SEARCH_ELEMENTS,
        energy_above_hull=ENERGY_ABOVE_HULL,
        fields=SUMMARY_FIELDS,
    )
    return _screen_candidate_docs(docs, min_room_per_atom=min_room_per_atom)


def write_discovery_history(path, candidates, *, top_k=TARGET_TOP_K):
    output_path = Path(path)
    output_path.write_text(json.dumps(candidates[:top_k], indent=4) + "\n")


def main() -> None:
    print("Autonomous Mission: Searching for 'Open Channel' Sulfide Electrolytes...")
    results = discover_baseline_candidates()

    print(f"\nSCREENING COMPLETE: Found {len(results)} High-Speed Candidates.")
    for i, res in enumerate(results[:TARGET_TOP_K], start=1):
        print(
            f"{i}. {res['formula']} | Room per Atom: {res['room_per_atom']:.2f} Å^3 | "
            f"Stability: {res['stability']:.2f} eV"
        )

    write_discovery_history(OUTPUT_PATH, results)


if __name__ == "__main__":
    main()
