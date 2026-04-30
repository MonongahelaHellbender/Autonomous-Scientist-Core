#!/usr/bin/env python3
"""
expanded_pipeline.py
--------------------
Runs top candidates from expanded_discovery_results.json through the full
validation chain: synthesis → tunnel physics → thermal → performance.

Results are saved to outputs/expanded_pipeline/ and NOT written over the
original stored pipeline artifacts.

Run:
  export MP_API_KEY='your_key'
  python expanded_pipeline.py

Optional: pass --top N to override the default 20 candidates.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import performance_engine
import synthesis_validator
import thermal_simulator
import tunnel_physics

ROOT = Path(__file__).resolve().parent
DISCOVERY_RESULTS = ROOT / "expanded_discovery_results.json"
OUT_DIR = ROOT / "outputs" / "expanded_pipeline"

# Elements that signal chemically unsafe compounds for Li electrolyte use
_OXIDIZER_ELEMENTS = {"O", "N", "F"}  # F ok in small doses; O/N in polyatomic anions = risk
_UNSAFE_ANIONS = ["ClO3", "ClO4", "NO3", "NO2"]


def flag_safety(formula: str) -> str | None:
    """Return a warning string if the formula contains high-risk functional groups."""
    for anion in _UNSAFE_ANIONS:
        if anion in formula:
            return f"OXIDIZER RISK — contains {anion} group; not suitable for metallic Li contact"
    return None


def load_and_dedupe_candidates(path: Path, top_n: int) -> list[dict]:
    """
    Load expanded discovery results, deduplicate polymorphs by formula (keeping
    best score), and return the top_n by score.
    """
    data = json.loads(path.read_text())
    all_candidates: list[dict] = data["all_candidates"]

    # Final dedup across the full set (catches any cross-family polymorphs)
    best: dict[str, dict] = {}
    for c in all_candidates:
        formula = c["formula"]
        if formula not in best or c["score"] > best[formula]["score"]:
            best[formula] = c

    ranked = sorted(best.values(), key=lambda c: -c["score"])
    return ranked[:top_n]


def run_pipeline(top_n: int = 20) -> dict:
    if not DISCOVERY_RESULTS.exists():
        raise FileNotFoundError(
            f"{DISCOVERY_RESULTS.name} not found. "
            "Run expanded_discovery.py first."
        )

    print("=" * 60)
    print("EXPANDED PIPELINE: FULL VALIDATION CHAIN")
    print("=" * 60 + "\n")

    # ── Stage 0: Load + safety screen ──────────────────────────────
    candidates = load_and_dedupe_candidates(DISCOVERY_RESULTS, top_n)
    print(f"Loaded {len(candidates)} unique candidates from expanded discovery.\n")

    safety_flags: dict[str, str] = {}
    screened = []
    for c in candidates:
        warning = flag_safety(c["formula"])
        if warning:
            safety_flags[c["formula"]] = warning
            print(f"  SAFETY SKIP: {c['formula']} — {warning}")
        else:
            screened.append(c)

    print(f"\nSafety screen: {len(screened)} candidates proceed "
          f"({len(safety_flags)} flagged).\n")

    # ── Stage 1: Synthesis validation (re-queries MP) ───────────────
    print("-" * 40)
    lab_ready = synthesis_validator.validate_synthesis(
        candidates=screened,
        ehull_threshold=0.08,   # match expanded discovery threshold
    )
    _save(OUT_DIR / "01_lab_ready.json", lab_ready)

    # ── Stage 2: Tunnel physics ─────────────────────────────────────
    print("\n" + "-" * 40)
    physics = tunnel_physics.analyze_tunnels(candidates=lab_ready)
    _save(OUT_DIR / "02_physics.json", physics)

    # ── Stage 3: Thermal simulation ─────────────────────────────────
    print("\n" + "-" * 40)
    thermal = thermal_simulator.simulate_thermal_stability(candidates=physics)
    _save(OUT_DIR / "03_thermal.json", thermal)

    # ── Stage 4: Performance (conductivity) ─────────────────────────
    print("\n" + "-" * 40)
    final = performance_engine.predict_conductivity(candidates=thermal)
    _save(OUT_DIR / "04_final.json", final)

    # ── Summary ─────────────────────────────────────────────────────
    viable = [c for c in final if c["perf_rating"] != "LOW FLOW"]
    final_sorted = sorted(final, key=lambda c: -c["conductivity_ms_cm"])

    print("\n" + "=" * 60)
    print("EXPANDED PIPELINE COMPLETE")
    print("=" * 60)
    print(f"  Discovery candidates:  {len(candidates)}")
    print(f"  After safety screen:   {len(screened)}")
    print(f"  Lab-ready (synthesis): {len(lab_ready)}")
    print(f"  Physics validated:     {len(physics)}")
    print(f"  Thermal validated:     {len(thermal)}")
    print(f"  Final:                 {len(final)}")
    print(f"  Viable / Superionic:   {len(viable)}")

    if final_sorted:
        print(f"\nTop candidates by conductivity:\n")
        print(f"{'#':>3}  {'Formula':<22}  {'Cond (mS/cm)':>12}  {'Rating':<25}  {'Bottleneck':>10}")
        print("-" * 80)
        for i, c in enumerate(final_sorted[:10], 1):
            print(f"{i:>3}. {c['formula']:<22}  {c['conductivity_ms_cm']:>12.4f}  "
                  f"{c['perf_rating']:<25}  {c['bottleneck_width_angstrom']:>10.3f} Å")

    result = {
        "artifact_type": "expanded_pipeline_v1",
        "stage_counts": {
            "discovery_input": len(candidates),
            "after_safety_screen": len(screened),
            "lab_ready": len(lab_ready),
            "physics": len(physics),
            "thermal": len(thermal),
            "final": len(final),
            "viable_or_better": len(viable),
        },
        "safety_flags": safety_flags,
        "top_by_conductivity": final_sorted[:10],
        "all_final": final,
    }
    _save(OUT_DIR / "summary.json", result)
    print(f"\nAll stage outputs saved to: {OUT_DIR}")
    return result


def _save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run expanded discovery candidates through full pipeline.")
    parser.add_argument("--top", type=int, default=20, help="Number of top candidates to process (default 20)")
    args = parser.parse_args()
    run_pipeline(top_n=args.top)


if __name__ == "__main__":
    main()
