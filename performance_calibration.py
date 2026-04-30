#!/usr/bin/env python3
"""
performance_calibration.py
--------------------------
Calibrates the performance engine against 3 experimentally validated
Li-S solid electrolytes and re-scores the expanded pipeline candidates.

The uncalibrated model uses a fixed pre-exponential of 1000 mS/cm and a
bottleneck→Ea formula that was never anchored to experiment. This module:
  1. Queries MP for 3 reference materials, computes their bottleneck widths
     using the identical formula as tunnel_physics.py
  2. Fits Ea = a + b × bottleneck (linear, least-squares over 3 points)
  3. Fits the pre-exponential A as the geometric mean over the 3 references
  4. Re-scores the expanded pipeline candidates with the calibrated model
  5. Saves calibrated_final.json to outputs/expanded_pipeline/

Reference materials and experimental values:
  Li10GeP2S12 (LGPS):    Ea=0.22 eV, σ=12.0 mS/cm  (Kamaya et al. 2011, Nature Mater.)
  Li3PS4 (β-phase):       Ea=0.35 eV, σ=0.16 mS/cm  (Liu et al. 2013, JACS)
  Li6PS5Cl (argyrodite):  Ea=0.17 eV, σ=1.30 mS/cm  (Deiseroth et al. 2008, Angew. Chem.)

Note on argyrodites: Li6PS5Cl conducts via cage-hopping disorder, not simple
geometric tunnels. The bottleneck model systematically undersells this class —
its reference point anchors the low-Ea / high-σ end of the fit.

Run:
  export MP_API_KEY='your_key'
  python performance_calibration.py
"""
from __future__ import annotations

import json
import numpy as np
from pathlib import Path

from mp_auth import get_mp_rester

ROOT = Path(__file__).resolve().parent
PIPELINE_FINAL = ROOT / "outputs" / "expanded_pipeline" / "04_final.json"
OUT_PATH = ROOT / "outputs" / "expanded_pipeline" / "calibrated_final.json"

KB_EV_PER_K = 8.617e-5
ROOM_TEMP_K = 298.15

REFERENCES = [
    {
        "label": "LGPS",
        "formula": "Li10GeP2S12",
        "ea_exp_ev": 0.22,
        "sigma_exp_ms_cm": 12.0,
        "citation": "Kamaya et al. 2011 Nature Mater.",
    },
    {
        "label": "β-Li3PS4",
        "formula": "Li3PS4",
        "ea_exp_ev": 0.35,
        "sigma_exp_ms_cm": 0.16,
        "citation": "Liu et al. 2013 JACS",
    },
    {
        "label": "Li6PS5Cl (argyrodite)",
        "formula": "Li6PS5Cl",
        "ea_exp_ev": 0.17,
        "sigma_exp_ms_cm": 1.30,
        "citation": "Deiseroth et al. 2008 Angew. Chem.",
        "note": "Cage-hopping disorder — bottleneck model structurally undersells argyrodites",
    },
]


def compute_bottleneck_from_mp(formula: str, mpr) -> tuple[float, float] | None:
    """
    Query MP for the most stable polymorph of `formula` and return
    (bottleneck_width_angstrom, room_per_atom) using the same formula
    as tunnel_physics.analyze_tunnels().
    Returns None if the formula is not found in MP.
    """
    docs = list(mpr.materials.summary.search(
        formula=formula,
        fields=["structure", "volume", "energy_above_hull", "nsites"],
        energy_above_hull=(0, 0.15),
    ))
    if not docs:
        return None

    docs.sort(key=lambda d: (d.energy_above_hull or 999.0))
    doc = docs[0]
    struct = doc.structure
    vol = doc.volume
    n_atoms = doc.nsites or len(struct)
    room_per_atom = vol / n_atoms

    atomic_rad_sum = sum(getattr(site.specie, "atomic_radius", 1.0) for site in struct)
    packing_fraction = atomic_rad_sum / vol
    bottleneck = (room_per_atom / 10.0) * (1.0 - packing_fraction)
    return round(bottleneck, 4), round(room_per_atom, 3)


def fit_calibration(bottlenecks: list[float], ea_exp: list[float], sigma_exp: list[float]) -> dict:
    """
    Fit Ea = a + b × bottleneck (linear least-squares).
    Fit A = geometric mean of sigma_i / exp(-Ea_i_exp / kT).
    Returns dict with keys: a, b, A.
    """
    x = np.array(bottlenecks)
    y = np.array(ea_exp)
    coeffs = np.polyfit(x, y, 1)   # [b, a]
    b, a = float(coeffs[0]), float(coeffs[1])

    log_A_vals = [
        np.log(s) + e / (KB_EV_PER_K * ROOM_TEMP_K)
        for s, e in zip(sigma_exp, ea_exp)
    ]
    A = float(np.exp(np.mean(log_A_vals)))

    return {"a": round(a, 6), "b": round(b, 6), "A": round(A, 2)}


EA_LGPS = 0.22   # eV — LGPS experimental lower bound; no geometric model beats this without DFT-NEB

def calibrated_predict(bottleneck: float, params: dict) -> tuple[float, float, bool]:
    """
    Return (Ea_eV, conductivity_mS_cm, ea_floored).
    ea_floored=True means the model extrapolated below the LGPS experimental Ea;
    the conductivity is then an upper-bound estimate, not a point prediction.
    """
    ea = params["a"] + params["b"] * bottleneck
    ea_floored = ea < EA_LGPS
    ea = max(EA_LGPS, ea)
    sigma = params["A"] * np.exp(-ea / (KB_EV_PER_K * ROOM_TEMP_K))
    return round(ea, 4), round(float(sigma), 4), ea_floored


def perf_rating(sigma: float, extrapolated: bool = False) -> str:
    if extrapolated:
        # Candidate has larger channels than any reference — could match or beat LGPS
        # but Ea is unknown without DFT-NEB; report as upper bound
        return "≥LGPS-class (verify Ea with DFT-NEB)"
    if sigma > 5.0:
        return "SUPERIONIC (Tesla-Grade)"
    elif sigma > 1.0:
        return "VIABLE"
    else:
        return "LOW FLOW"


def main() -> None:
    print("=" * 65)
    print("PERFORMANCE MODEL CALIBRATION")
    print("=" * 65 + "\n")

    # ── Step 1: Query reference materials ───────────────────────────
    valid_refs = []
    print("Querying reference materials from Materials Project...\n")

    with get_mp_rester() as mpr:
        for ref in REFERENCES:
            result = compute_bottleneck_from_mp(ref["formula"], mpr)
            if result is None:
                print(f"  WARNING: {ref['formula']} not found in MP — skipping")
                continue
            bn, room = result
            entry = {**ref, "bottleneck": bn, "room_per_atom": room}
            valid_refs.append(entry)
            print(f"  {ref['label']:<28}  bottleneck = {bn:.4f} Å  "
                  f"vol/atom = {room:.2f} Å³")

    if len(valid_refs) < 2:
        print("\nERROR: Need at least 2 reference materials. Aborting.")
        return

    # ── Step 2: Fit calibration ──────────────────────────────────────
    params = fit_calibration(
        [r["bottleneck"] for r in valid_refs],
        [r["ea_exp_ev"] for r in valid_refs],
        [r["sigma_exp_ms_cm"] for r in valid_refs],
    )

    print(f"\nCalibrated Ea model:   Ea = {params['a']:.4f} + ({params['b']:.4f}) × bottleneck Å")
    print(f"Pre-exponential A:     {params['A']:.1f} mS/cm\n")
    print(f"{'Reference':<30} {'BN':>6}  {'Ea_model':>9}  {'Ea_exp':>7}  {'σ_model':>10}  {'σ_exp':>8}")
    print("-" * 78)

    for r in valid_refs:
        ea_m, sig_m, floored = calibrated_predict(r["bottleneck"], params)
        print(f"  {r['label']:<28} {r['bottleneck']:>6.4f}  {ea_m:>9.4f}  "
              f"{r['ea_exp_ev']:>7.3f}  {sig_m:>10.4f}  {r['sigma_exp_ms_cm']:>8.2f}")
        if "note" in r:
            print(f"    ↳ Note: {r['note']}")

    max_ref_bn = max(r["bottleneck"] for r in valid_refs)
    print(f"\nEa floor: {EA_LGPS} eV (LGPS experimental minimum)")
    print(f"Max reference bottleneck: {max_ref_bn:.4f} Å — candidates above this are extrapolated\n")

    # ── Step 3: Re-score candidates ──────────────────────────────────
    if not PIPELINE_FINAL.exists():
        print(f"\nWARNING: {PIPELINE_FINAL.name} not found — run expanded_pipeline.py first.")
        return

    candidates = json.loads(PIPELINE_FINAL.read_text())
    calibrated = []

    for c in candidates:
        bn = c["bottleneck_width_angstrom"]
        ea_cal, sig_cal, ea_floored = calibrated_predict(bn, params)
        extrapolated = ea_floored or bn > max_ref_bn
        calibrated.append({
            **c,
            "ea_calibrated_ev": ea_cal,
            "conductivity_calibrated_ms_cm": sig_cal,
            "extrapolated": extrapolated,
            "perf_rating_calibrated": perf_rating(sig_cal, extrapolated=extrapolated),
        })

    calibrated.sort(key=lambda c: -c["bottleneck_width_angstrom"])

    extrapolated_group = [c for c in calibrated if c["extrapolated"]]
    interpolated_group = [c for c in calibrated if not c["extrapolated"]]

    print(f"\n── GROUP A: Larger channel than any reference (extrapolated — Ea unknown) ──")
    print(f"   All clamped to Ea ≥ {EA_LGPS} eV. Conductivity is an upper bound (≥LGPS-class).")
    print(f"   Ranked by bottleneck width (larger = more open channel).\n")
    print(f"{'#':>3}  {'Formula':<22}  {'BN (Å)':>7}  {'Ea floor':>9}  {'σ upper (mS/cm)':>16}")
    print("-" * 65)
    for i, c in enumerate(extrapolated_group, 1):
        print(f"{i:>3}. {c['formula']:<22}  {c['bottleneck_width_angstrom']:>7.3f}  "
              f"{c['ea_calibrated_ev']:>9.4f}  {c['conductivity_calibrated_ms_cm']:>16.4f}")

    print(f"\n── GROUP B: Within reference range (interpolated — model is predictive) ──")
    print(f"   Ea predicted by linear fit through LGPS, β-Li3PS4, Li6PS5Cl.\n")
    print(f"{'#':>3}  {'Formula':<22}  {'BN (Å)':>7}  {'Ea (eV)':>8}  "
          f"{'σ (mS/cm)':>11}  {'Rating'}")
    print("-" * 78)
    for i, c in enumerate(interpolated_group, 1):
        print(f"{i:>3}. {c['formula']:<22}  {c['bottleneck_width_angstrom']:>7.3f}  "
              f"{c['ea_calibrated_ev']:>8.4f}  {c['conductivity_calibrated_ms_cm']:>11.4f}  "
              f"{c['perf_rating_calibrated']}")

    print(f"\nSummary: {len(extrapolated_group)} extrapolated (≥LGPS-class), "
          f"{len(interpolated_group)} interpolated")

    # ── Step 4: Save ─────────────────────────────────────────────────
    output = {
        "artifact_type": "performance_calibration_v1",
        "calibration_references": [
            {k: v for k, v in r.items() if k != "note"}
            for r in valid_refs
        ],
        "calibration_params": params,
        "ea_floor_ev": EA_LGPS,
        "max_ref_bottleneck_angstrom": max_ref_bn,
        "model_equation": (
            f"Ea_eV = {params['a']:.4f} + ({params['b']:.4f}) * bottleneck_angstrom  "
            f"[clamped at {EA_LGPS} eV]"
        ),
        "conductivity_equation": (
            f"sigma_mS_cm = {params['A']:.1f} * exp(-Ea / (kB * T))"
        ),
        "rating_thresholds": {
            "viable_ms_cm": 1.0,
            "superionic_ms_cm": 5.0,
        },
        "extrapolated_count": len(extrapolated_group),
        "interpolated_count": len(interpolated_group),
        "group_a_extrapolated": extrapolated_group,
        "group_b_interpolated": interpolated_group,
        "calibrated_candidates": calibrated,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(output, indent=2) + "\n")
    print(f"\nCalibrated results saved to: {OUT_PATH}")


if __name__ == "__main__":
    main()
