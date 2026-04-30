#!/usr/bin/env python3
"""
run_chgnet_md.py
----------------
Estimates Li+ diffusion coefficient and activation energy using
Machine Learning Molecular Dynamics (MLMD) with CHGNet.

Why MD instead of NEB:
  - NEB requires the migration path to be identified in advance.
    For layered Li2In2GeS6/SiS6/LiInS2, the nearest Li-Li distance is an
    interlayer hop through dense In/Ge/S slabs — NEB on that path gives
    unphysical barriers (66-480 eV). The correct intra-layer path requires
    crystallographic analysis beyond simple distance sorting.
  - MLMD avoids this entirely: Li migrates along whatever path the force field
    finds naturally at elevated temperature.

Method:
  1. Run NVT MD at 800K, 1000K, 1200K for each candidate (~30 min/temperature on MPS)
  2. Track Li+ positions, compute MSD with proper PBC unwrapping
  3. Extract diffusion coefficient D(T) from linear MSD slope
  4. Fit Arrhenius: ln(D) = ln(D0) - Ea/kT → get Ea
  5. Extrapolate D and ionic conductivity to 300K via Nernst-Einstein

Run:
  python run_chgnet_md.py

Output per candidate:
  neb_<formula>/md_<T>K/  — trajectory, log
  neb_<formula>/chgnet_md_results.json — D(T), Ea, σ(300K)
"""
from __future__ import annotations

import json
import time
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent

CANDIDATES = ["Li2In2GeS6", "Li2In2SiS6", "LiInS2"]

TEMPERATURES  = [800, 1000, 1200]    # K — elevated to see diffusion in ~100 ps
TIMESTEP_FS   = 2.0                  # fs
N_EQUIL       = 5_000                # equilibration steps (discard)
N_PROD        = 25_000               # production steps per temperature (~50 ps)
LOG_INTERVAL  = 10                   # record positions every N steps
KB            = 8.617e-5             # eV/K
Q_LI          = 1.602e-19            # C

warnings.filterwarnings("ignore", category=UserWarning)


def load_bulk_structure(neb_dir: Path):
    from pymatgen.core import Structure
    from pymatgen.io.ase import AseAtomsAdaptor
    struct = Structure.from_file(str(neb_dir / "bulk" / "POSCAR"))
    return AseAtomsAdaptor().get_atoms(struct)


def unwrap_positions(pos_frames: np.ndarray, cell: np.ndarray) -> np.ndarray:
    """
    Unwrap Li+ positions across periodic boundaries.
    pos_frames: (n_frames, n_li, 3) in Cartesian Å
    Returns unwrapped positions of same shape.
    """
    inv_cell = np.linalg.inv(cell)
    unwrapped = np.empty_like(pos_frames)
    unwrapped[0] = pos_frames[0]
    for i in range(1, len(pos_frames)):
        delta = pos_frames[i] - pos_frames[i - 1]
        frac  = delta @ inv_cell
        frac -= np.round(frac)           # minimum image
        unwrapped[i] = unwrapped[i - 1] + frac @ cell
    return unwrapped


def compute_msd_and_diffusivity(unwrapped: np.ndarray, dt_ps: float) -> tuple[np.ndarray, np.ndarray, float]:
    """
    Compute MSD vs lag time and fit D from the linear regime.
    Returns (lag_times_ps, msd_A2, D_A2_per_ps).
    """
    n_frames = len(unwrapped)
    max_lag  = n_frames // 3           # use first third for reliable statistics
    lag_times = np.arange(1, max_lag + 1) * dt_ps
    msd = np.array([
        np.mean(np.sum((unwrapped[lag:] - unwrapped[:-lag]) ** 2, axis=2))
        for lag in range(1, max_lag + 1)
    ])

    # Linear fit to MSD = 6Dt (3D diffusion); use middle 50% of lag range
    lo, hi = max_lag // 4, 3 * max_lag // 4
    slope, _ = np.polyfit(lag_times[lo:hi], msd[lo:hi], 1)
    D = max(slope / 6.0, 1e-20)        # Å²/ps, clamped away from zero
    return lag_times, msd, float(D)


def arrhenius_fit(temperatures: list[float], D_values: list[float]) -> tuple[float, float]:
    """
    Fit ln(D) = ln(D0) - Ea/(kB*T) to get Ea (eV) and D0 (Å²/ps).
    Returns (Ea_eV, D0_A2_per_ps).
    """
    inv_T = np.array([1.0 / T for T in temperatures])
    ln_D  = np.array([np.log(max(D, 1e-30)) for D in D_values])
    slope, intercept = np.polyfit(inv_T, ln_D, 1)
    Ea  = -slope * KB          # eV
    D0  = np.exp(intercept)    # Å²/ps
    return float(Ea), float(D0)


def nernst_einstein_conductivity(D_A2ps: float, n_li: int, vol_A3: float, T_K: float) -> float:
    """
    σ = n_Li * q² * D / (kB * T)   in mS/cm
    D in m²/s, n in m⁻³
    """
    D_m2s  = D_A2ps * 1e-20 / 1e-12   # Å²/ps → m²/s
    n_m3   = n_li / (vol_A3 * 1e-30)  # atoms/Å³ → atoms/m³
    sigma  = n_m3 * (Q_LI ** 2) * D_m2s / (KB * T_K * Q_LI)  # S/m
    return float(sigma * 0.1)         # S/m → mS/cm


def run_md_temperature(atoms, model, T_K: int, out_dir: Path) -> dict:
    from chgnet.model.dynamics import MolecularDynamics

    out_dir.mkdir(parents=True, exist_ok=True)
    traj_file = str(out_dir / "md.traj")
    log_file  = str(out_dir / "md.log")

    # Equilibration
    print(f"    Equilibrating at {T_K}K ({N_EQUIL} steps)...", end=" ", flush=True)
    md_equil = MolecularDynamics(
        atoms=atoms,
        model=model,
        ensemble="nvt",
        temperature=T_K,
        timestep=TIMESTEP_FS,
        trajectory=None,
        logfile=str(out_dir / "equil.log"),
        loginterval=500,
        use_device="mps",
    )
    md_equil.run(N_EQUIL)
    print("done")

    # Production
    print(f"    Production at {T_K}K ({N_PROD} steps, log every {LOG_INTERVAL})...",
          end=" ", flush=True)
    t0 = time.time()
    md_prod = MolecularDynamics(
        atoms=atoms,
        model=model,
        ensemble="nvt",
        temperature=T_K,
        timestep=TIMESTEP_FS,
        trajectory=traj_file,
        logfile=log_file,
        loginterval=LOG_INTERVAL,
        use_device="mps",
    )
    md_prod.run(N_PROD)
    elapsed = time.time() - t0
    print(f"done ({elapsed:.0f}s)")

    # Load trajectory and compute MSD
    from ase.io.trajectory import Trajectory as AseTraj
    traj  = AseTraj(traj_file)
    cell  = traj[0].cell.array

    li_idx = [i for i, sym in enumerate(traj[0].get_chemical_symbols()) if sym == "Li"]
    pos_frames = np.array([frame.positions[li_idx] for frame in traj])  # (frames, n_li, 3)

    unwrapped = unwrap_positions(pos_frames, cell)
    dt_ps     = TIMESTEP_FS * LOG_INTERVAL / 1000.0
    lag_t, msd, D = compute_msd_and_diffusivity(unwrapped, dt_ps)

    rmsd_final = float(np.sqrt(msd[-1]))
    print(f"    D({T_K}K) = {D:.4e} Å²/ps  |  RMSD at end = {rmsd_final:.2f} Å")

    if rmsd_final < 0.5:
        print(f"    WARNING: RMSD < 0.5 Å — Li barely moved at {T_K}K. "
              "D estimate may be unreliable. Consider higher T.")

    np.savetxt(str(out_dir / "msd.txt"),
               np.column_stack([lag_t, msd]),
               header="lag_time_ps  msd_A2")

    return {
        "temperature_K": T_K,
        "D_A2_per_ps": D,
        "rmsd_final_A": rmsd_final,
        "n_frames": len(pos_frames),
        "elapsed_s": round(elapsed, 1),
    }


def run_candidate(label: str) -> dict:
    from chgnet.model import CHGNet

    neb_dir = ROOT / f"neb_{label}"
    if not neb_dir.exists():
        return {"label": label, "error": f"neb_{label}/ not found"}

    print(f"\n{'='*55}")
    print(f"  MLMD: {label}")
    print(f"{'='*55}")

    model = CHGNet.load()
    atoms = load_bulk_structure(neb_dir)
    n_li  = sum(1 for s in atoms.get_chemical_symbols() if s == "Li")
    vol   = atoms.get_volume()
    print(f"  Supercell: {len(atoms)} atoms, {n_li} Li, volume={vol:.1f} Å³")

    T_results = []
    for T_K in TEMPERATURES:
        # Work on a fresh copy of atoms each temperature
        from copy import deepcopy
        atoms_copy = deepcopy(atoms)
        out_dir = neb_dir / f"md_{T_K}K"
        res = run_md_temperature(atoms_copy, model, T_K, out_dir)
        T_results.append(res)

    # Arrhenius fit
    valid = [(r["temperature_K"], r["D_A2_per_ps"])
             for r in T_results if r["rmsd_final_A"] > 0.3]

    if len(valid) < 2:
        print("  WARNING: Fewer than 2 reliable D values — Arrhenius fit skipped.")
        Ea, D0 = None, None
        D_300K = None
        sigma_300K = None
    else:
        Ts, Ds = zip(*valid)
        Ea, D0 = arrhenius_fit(list(Ts), list(Ds))
        D_300K = D0 * np.exp(-Ea / (KB * 300))
        sigma_300K = nernst_einstein_conductivity(D_300K, n_li, vol, 300)

        print(f"\n  ── Arrhenius fit ────────────────────────────────")
        print(f"  Ea  = {Ea:.3f} eV")
        print(f"  D0  = {D0:.3e} Å²/ps")
        print(f"  D(300K) = {D_300K:.3e} Å²/ps")
        print(f"  σ(300K) = {sigma_300K:.4f} mS/cm")

        if sigma_300K > 5:
            rating = "SUPERIONIC"
        elif sigma_300K > 1:
            rating = "VIABLE"
        elif sigma_300K > 0.1:
            rating = "MODERATE"
        else:
            rating = "LOW FLOW"
        print(f"  Rating: {rating}")

    result = {
        "label": label,
        "n_li": n_li,
        "volume_A3": round(vol, 2),
        "temperature_results": T_results,
        "ea_ev": round(Ea, 4) if Ea else None,
        "D0_A2_per_ps": D0,
        "D_300K_A2_per_ps": D_300K,
        "sigma_300K_ms_cm": round(sigma_300K, 4) if sigma_300K else None,
        "note": ("Nernst-Einstein σ assumes all Li are mobile. "
                 "Real σ may be lower if Li sublattice has partial disorder."),
    }
    (neb_dir / "chgnet_md_results.json").write_text(json.dumps(result, indent=2))
    return result


def main():
    print("=" * 55)
    print("  CHGNet MLMD — Li-S Electrolyte Candidates")
    print(f"  Temperatures: {TEMPERATURES} K")
    print(f"  Production: {N_PROD} steps × {TIMESTEP_FS} fs = "
          f"{N_PROD * TIMESTEP_FS / 1000:.0f} ps per temperature")
    print("=" * 55)

    try:
        import chgnet
        print(f"  CHGNet {chgnet.__version__}  |  device: mps (Apple Silicon)\n")
    except ImportError:
        print("ERROR: pip install chgnet"); return

    all_results = []
    for label in CANDIDATES:
        result = run_candidate(label)
        all_results.append(result)

    print("\n\n" + "=" * 55)
    print("  FINAL SUMMARY")
    print("=" * 55)
    print(f"{'Compound':<22}  {'Ea (eV)':>8}  {'σ 300K (mS/cm)':>16}")
    print("-" * 52)
    for r in all_results:
        if "error" in r:
            print(f"  {r['label']:<20}  ERROR"); continue
        ea  = f"{r['ea_ev']:.3f}"  if r["ea_ev"]  else "N/A"
        sig = f"{r['sigma_300K_ms_cm']:.4f}" if r["sigma_300K_ms_cm"] else "N/A"
        print(f"  {r['label']:<20}  {ea:>8}  {sig:>16}")

    summary_path = ROOT / "chgnet_md_summary.json"
    summary_path.write_text(json.dumps(all_results, indent=2))
    print(f"\nFull results: {summary_path}")


if __name__ == "__main__":
    main()
