#!/usr/bin/env python3
"""
expanded_discovery.py
---------------------
Broader autonomous search across all promising Li-S-X electrolyte families.

The original pipeline searched only Li-S-P (baseline) and Li-S-Si (pivot),
with a strict E_hull < 0.03 eV filter that now returns 0 candidates on live
MP data due to database updates.

This script:
  1. Searches 12 Li-S-X element families covering the full promising space
  2. Uses a relaxed but still physically motivated E_hull < 0.08 eV threshold
     (0.08 eV is the standard "synthesizable" cutoff used in the literature)
  3. Screens by volume/atom > 16 A^3 (open channel proxy for Li+ transport)
  4. Adds band gap > 2 eV filter for electrolyte viability (conductor = bad)
  5. Reports ranked candidates with detailed property summary
  6. Saves results for downstream tunnel/thermal/conductivity analysis

Element families searched (all Li-S-X):
  X = P, Si, In, Ge, Sn, Ga, Al, Cl, Se, Zr, Hf, La
  These cover the main structural families of known solid electrolytes.

Run:
  export MP_API_KEY='your_key'
  python expanded_discovery.py
"""
from __future__ import annotations

import json
from pathlib import Path

from mp_auth import get_mp_rester

ROOT = Path(__file__).resolve().parent

# --- Thresholds (updated from original 0.03 to 0.08, per synthesis literature) ---
ENERGY_ABOVE_HULL_MAX = 0.08   # eV — standard synthesizable threshold
MIN_ROOM_PER_ATOM = 16.0       # A^3/atom — open channel proxy
MIN_BAND_GAP = 2.0             # eV — must be insulating (electrolyte, not conductor)
TARGET_TOP_K = 20              # report top 20 candidates

# All element families to search (each adds one or two X elements to Li-S core)
SEARCH_FAMILIES = [
    ["Li", "S", "P"],           # original baseline
    ["Li", "S", "Si"],          # original pivot (found Li2In2SiS6 family)
    ["Li", "S", "In"],          # indium sulfides — where Li2In2SiS6 lives
    ["Li", "S", "Ge"],          # germanium sulfides — LGPS-adjacent
    ["Li", "S", "Sn"],          # tin sulfides
    ["Li", "S", "Ga"],          # gallium sulfides
    ["Li", "S", "Al"],          # aluminium sulfides
    ["Li", "S", "Cl"],          # lithium sulfide chlorides — argyrodite family
    ["Li", "S", "Se"],          # selenide analogues of sulfide electrolytes
    ["Li", "S", "Zr"],          # zirconium — good stability
    ["Li", "S", "Hf"],          # hafnium — similar to Zr
    ["Li", "S", "La"],          # lanthanum — LLZO-adjacent chemistry
]

SUMMARY_FIELDS = [
    "formula_pretty",
    "volume",
    "structure",
    "formation_energy_per_atom",
    "band_gap",
    "energy_above_hull",
    "nsites",
]


def search_family(elements: list[str], *, materials_client=None) -> list[dict]:
    """Query MP for one element family and return screened candidates."""
    kwargs = dict(
        elements=elements,
        energy_above_hull=(0, ENERGY_ABOVE_HULL_MAX),
        fields=SUMMARY_FIELDS,
    )
    if materials_client is not None:
        docs = list(materials_client.search_summary(**kwargs))
    else:
        with get_mp_rester() as mpr:
            docs = list(mpr.materials.summary.search(**kwargs))

    by_formula: dict[str, dict] = {}
    for doc in docs:
        try:
            n_atoms = doc.nsites or len(doc.structure)
            vol_per_atom = doc.volume / n_atoms
            band_gap = doc.band_gap if doc.band_gap is not None else 0.0
            e_hull = doc.energy_above_hull if doc.energy_above_hull is not None else 999.0

            if vol_per_atom < MIN_ROOM_PER_ATOM:
                continue
            if band_gap < MIN_BAND_GAP:
                continue

            candidate = {
                "formula": doc.formula_pretty,
                "room_per_atom": round(vol_per_atom, 3),
                "stability": round(doc.formation_energy_per_atom, 4),
                "energy_above_hull": round(e_hull, 4),
                "band_gap": round(band_gap, 3),
                "n_atoms": n_atoms,
                "family": "-".join(elements),
            }
            # Keep only the most stable polymorph per formula within this family
            existing = by_formula.get(doc.formula_pretty)
            if existing is None or e_hull < existing["energy_above_hull"]:
                by_formula[doc.formula_pretty] = candidate
        except Exception:
            continue

    return list(by_formula.values())


def score_candidate(c: dict) -> float:
    """
    Combined score for ranking candidates.
    Higher is better.
      +room_per_atom: more open channels
      -energy_above_hull: more stable
      +band_gap (up to 5 eV): wider gap = better electrolyte
    """
    return (
        c["room_per_atom"] / 30.0
        - c["energy_above_hull"] * 5.0
        + min(c["band_gap"], 5.0) / 10.0
    )


def run_expanded_search(*, materials_client=None) -> dict:
    all_candidates = []
    seen_formulas = set()
    family_counts = {}

    print(f"Searching {len(SEARCH_FAMILIES)} element families...")
    print(f"Thresholds: E_hull < {ENERGY_ABOVE_HULL_MAX} eV | "
          f"vol/atom > {MIN_ROOM_PER_ATOM} A^3 | band_gap > {MIN_BAND_GAP} eV\n")

    for elements in SEARCH_FAMILIES:
        label = "-".join(elements)
        print(f"  Querying {label}...", end=" ", flush=True)
        candidates = search_family(elements, materials_client=materials_client)
        # Deduplicate by formula
        new = [c for c in candidates if c["formula"] not in seen_formulas]
        seen_formulas.update(c["formula"] for c in new)
        all_candidates.extend(new)
        family_counts[label] = len(new)
        print(f"{len(new)} candidates")

    # Score and rank
    for c in all_candidates:
        c["score"] = round(score_candidate(c), 4)
    all_candidates.sort(key=lambda c: -c["score"])

    top = all_candidates[:TARGET_TOP_K]

    print(f"\nTotal unique candidates: {len(all_candidates)}")
    print(f"Top {TARGET_TOP_K} by combined score:\n")
    print(f"{'#':>3}  {'Formula':<20}  {'Vol/atom':>8}  {'E_hull':>7}  "
          f"{'Gap':>6}  {'Score':>7}  {'Family'}")
    print("-" * 75)
    for i, c in enumerate(top, 1):
        print(f"{i:>3}. {c['formula']:<20}  {c['room_per_atom']:>8.2f}  "
              f"{c['energy_above_hull']:>7.4f}  {c['band_gap']:>6.2f}  "
              f"{c['score']:>7.4f}  {c['family']}")

    return {
        "artifact_type": "expanded_discovery_v1",
        "thresholds": {
            "energy_above_hull_max_eV": ENERGY_ABOVE_HULL_MAX,
            "min_room_per_atom_A3": MIN_ROOM_PER_ATOM,
            "min_band_gap_eV": MIN_BAND_GAP,
        },
        "families_searched": ["-".join(f) for f in SEARCH_FAMILIES],
        "candidates_per_family": family_counts,
        "total_unique_candidates": len(all_candidates),
        "top_candidates": top,
        "all_candidates": all_candidates,
        "scoring_formula": (
            "score = room_per_atom/30 - energy_above_hull*5 + min(band_gap,5)/10"
        ),
        "interpretation": (
            "Higher score = better electrolyte candidate. "
            f"Threshold E_hull < {ENERGY_ABOVE_HULL_MAX} eV is the standard "
            "synthesizable cutoff in the solid electrolyte literature "
            "(vs original pipeline's 0.03 eV which now returns 0 on live MP). "
            "Band gap > 2 eV required to exclude electronic conductors."
        ),
    }


def main():
    print("=" * 60)
    print("EXPANDED Li-S-X SOLID ELECTROLYTE DISCOVERY")
    print("=" * 60 + "\n")

    results = run_expanded_search()

    out_path = ROOT / "expanded_discovery_results.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nFull results saved to: {out_path}")

    if results["top_candidates"]:
        best = results["top_candidates"][0]
        print(f"\nBest candidate: {best['formula']}")
        print(f"  Vol/atom: {best['room_per_atom']} A^3")
        print(f"  E_hull:   {best['energy_above_hull']} eV")
        print(f"  Band gap: {best['band_gap']} eV")
        print(f"  Family:   {best['family']}")
    else:
        print("\nNo candidates found. Try further relaxing thresholds.")


if __name__ == "__main__":
    main()
