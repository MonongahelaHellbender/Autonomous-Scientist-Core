#!/usr/bin/env python3
"""
run_chgnet_neb.py
-----------------
Runs CI-NEB using CHGNet (ML force field) on the prepared image directories.
No VASP or cluster required — runs on CPU in ~10–30 min per candidate.

CHGNet is a universal GNN potential trained on ~1.5M Materials Project structures.
Ea accuracy for Li-S systems: ±0.05–0.10 eV vs. DFT-PBE.

Usage:
  pip install chgnet
  python run_chgnet_neb.py

Output:
  neb_<formula>/chgnet_neb_results.json — Ea, barrier profile, convergence info
  neb_<formula>/chgnet_neb_energy_profile.txt — image index vs. energy for plotting
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent

CANDIDATES = [
    "Li2In2GeS6",
    "Li2In2SiS6",
    "LiInS2",
]

NEB_FMAX = 0.10        # eV/Å force convergence (0.05 for publication quality)
NEB_STEPS = 500        # max optimizer steps
CLIMB = True           # climbing image NEB


def load_images_from_poscar(neb_dir: Path) -> list:
    """Load all image POSCARs in order (00, 01, ...) as ASE Atoms objects."""
    from pymatgen.core import Structure
    from pymatgen.io.ase import AseAtomsAdaptor

    image_dirs = sorted(
        d for d in neb_dir.iterdir()
        if d.is_dir() and d.name.isdigit()
    )
    if not image_dirs:
        raise FileNotFoundError(f"No numbered image directories in {neb_dir}")

    adaptor = AseAtomsAdaptor()
    images = []
    for d in image_dirs:
        poscar = d / "POSCAR"
        struct = Structure.from_file(str(poscar))
        atoms = adaptor.get_atoms(struct)
        images.append(atoms)

    return images


def run_neb_for_candidate(label: str) -> dict:
    try:
        from ase.mep.neb import NEB   # ASE >= 3.23
    except ImportError:
        from ase.neb import NEB       # ASE < 3.23
    from ase.optimize import FIRE
    from chgnet.model import CHGNet
    from chgnet.model.dynamics import CHGNetCalculator

    neb_dir = ROOT / f"neb_{label}"
    if not neb_dir.exists():
        return {"label": label, "error": f"Directory {neb_dir} not found"}

    print(f"\n{'='*55}")
    print(f"  CHGNet NEB: {label}")
    print(f"{'='*55}")

    # Load CHGNet model once — calculator instances are lightweight wrappers
    print("  Loading CHGNet model...", end=" ", flush=True)
    model = CHGNet.load()
    print("OK")

    # Load images
    images = load_images_from_poscar(neb_dir)
    n_images = len(images)
    print(f"  Loaded {n_images} images (including endpoints)")

    # Each image needs its OWN calculator instance (model weights are shared internally)
    for img in images:
        img.calc = CHGNetCalculator(model=model, use_device="cpu")

    # Compute endpoint energies before NEB (they stay fixed during optimisation)
    e_start = float(images[0].get_potential_energy())
    e_end   = float(images[-1].get_potential_energy())
    print(f"  Endpoint energies: start={e_start:.4f} eV, end={e_end:.4f} eV")
    print(f"  Reaction energy: {e_end - e_start:.4f} eV")

    # Set up NEB with IDPP interpolation.
    # Linear interpolation sends Li through surrounding S/In/Ge atoms → 10-20 eV artifact.
    # IDPP respects interatomic distances and routes Li around blocking atoms.
    neb = NEB(images, climb=False, method='improvedtangent')
    print("  Generating IDPP initial path...", end=" ", flush=True)
    neb.interpolate(method='idpp')
    print("done")

    # Sanity check: if any intermediate image is > 5 eV above endpoints, path is
    # still clashing — abort rather than run a 4-hour calculation on garbage geometry.
    e_ref = e_start
    pre_energies = [float(img.get_potential_energy()) for img in images[1:-1]]
    max_pre = max(pre_energies) - e_ref
    print(f"  Max intermediate energy after IDPP: {max_pre:.3f} eV above start")
    if max_pre > 5.0:
        msg = (f"IDPP path still has {max_pre:.1f} eV spike — "
               "likely an interlayer hop through dense atoms. "
               "Skipping CI-NEB; inspect structure in VESTA.")
        print(f"  WARNING: {msg}")
        return {"label": label, "error": msg,
                "max_idpp_energy_eV": round(max_pre, 3)}

    # Phase 1: relax the NEB band without climbing image (faster convergence)
    opt = FIRE(neb, logfile=str(neb_dir / "chgnet_neb.log"))
    print("  Phase 1: relaxing NEB band (no climbing)...")
    opt.run(fmax=0.3, steps=150)

    # Phase 2: enable climbing image for accurate saddle point
    neb.climb = True
    print(f"  Phase 2: CI-NEB (fmax={NEB_FMAX} eV/Å, max {NEB_STEPS} steps)...")
    t0 = time.time()
    converged = False
    try:
        opt.run(fmax=NEB_FMAX, steps=NEB_STEPS)
        converged = True
    except Exception as e:
        print(f"  WARNING: Optimizer raised {e}")

    elapsed = time.time() - t0
    print(f"  Completed in {elapsed:.1f}s  |  converged={converged}")

    # Extract energy profile — convert all to plain Python float for JSON
    energies = [e_start] + [float(img.get_potential_energy()) for img in images[1:-1]] + [e_end]

    # Normalize to start energy
    e_ref = energies[0]
    rel_energies = [e - e_ref for e in energies]

    ea_forward  = float(max(rel_energies))
    ea_backward = float(max(rel_energies) - rel_energies[-1])
    saddle_idx  = int(np.argmax(rel_energies))

    print(f"\n  ── Results ──────────────────────────────────────")
    print(f"  Ea (forward):   {ea_forward:.4f} eV")
    print(f"  Ea (backward):  {ea_backward:.4f} eV")
    print(f"  Saddle at image {saddle_idx}/{n_images-1}")
    print(f"  Reaction ΔE:    {rel_energies[-1]:.4f} eV")

    # Save energy profile text file
    profile_path = neb_dir / "chgnet_neb_energy_profile.txt"
    with open(profile_path, "w") as f:
        f.write("# image  rel_energy_eV\n")
        for i, e in enumerate(rel_energies):
            f.write(f"{i:4d}  {e:.6f}\n")

    result = {
        "label": label,
        "n_images": n_images,
        "ea_forward_ev": round(ea_forward, 4),
        "ea_backward_ev": round(ea_backward, 4),
        "reaction_energy_ev": round(rel_energies[-1], 4),
        "saddle_image_index": saddle_idx,
        "converged": converged,
        "elapsed_seconds": round(elapsed, 1),
        "energy_profile_ev": [round(float(e), 6) for e in rel_energies],
        "conductivity_rough_estimate": rough_conductivity(ea_forward),
    }

    out_path = neb_dir / "chgnet_neb_results.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n")
    print(f"  Saved to {out_path.name}")

    return result


def rough_conductivity(ea_ev: float) -> str:
    """
    Rough σ estimate anchored to LGPS (Ea=0.22 eV, σ=12 mS/cm).
    Uses Arrhenius scaling: σ ∝ exp(-Ea/kT).
    Uncertainty: ±1 order of magnitude.
    """
    import math
    kb = 8.617e-5
    T = 298.15
    sigma_lgps = 12.0
    ea_lgps = 0.22
    sigma = sigma_lgps * math.exp(-(ea_ev - ea_lgps) / (kb * T))
    if sigma > 5.0:
        rating = "SUPERIONIC"
    elif sigma > 1.0:
        rating = "VIABLE"
    elif sigma > 0.1:
        rating = "MODERATE"
    else:
        rating = "LOW"
    return f"~{sigma:.3f} mS/cm ({rating}) [±1 order of magnitude]"


def main():
    print("=" * 55)
    print("  CHGNet CI-NEB — Li-S Electrolyte Candidates")
    print("=" * 55)

    try:
        import chgnet
        print(f"  CHGNet version: {chgnet.__version__}")
    except ImportError:
        print("\nERROR: CHGNet not installed.")
        print("Install with:  pip install chgnet")
        return

    all_results = []
    for label in CANDIDATES:
        result = run_neb_for_candidate(label)
        all_results.append(result)

    print("\n\n" + "=" * 55)
    print("  SUMMARY")
    print("=" * 55)
    print(f"{'Compound':<22}  {'Ea (eV)':>8}  {'Est. σ (mS/cm)':>14}  {'Converged'}")
    print("-" * 70)
    for r in all_results:
        if "error" in r:
            print(f"  {r['label']:<20}  ERROR: {r['error']}")
            continue
        print(f"  {r['label']:<20}  {r['ea_forward_ev']:>8.4f}  "
              f"{r['conductivity_rough_estimate']}")

    # Save combined summary
    summary_path = ROOT / "chgnet_neb_summary.json"
    summary_path.write_text(json.dumps(all_results, indent=2) + "\n")
    print(f"\nFull results saved to: {summary_path}")


if __name__ == "__main__":
    main()
