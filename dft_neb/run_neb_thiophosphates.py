#!/usr/bin/env python3
"""
run_neb_thiophosphates.py
--------------------------
CHGNet CI-NEB for 3D thiophosphate Li-S-X candidates using crystallographic
path-finding (DistinctPathFinder) instead of nearest-neighbor distance.

Why a separate script from run_chgnet_neb.py:
  - The In-containing layered structures (Li2In2GeS6, etc.) failed because
    the shortest Li-Li distance was an interlayer hop through dense In/Ge/S slabs.
  - 3D thiophosphates (LiZnPS4, LiAl(PS3)2, etc.) have isotropic PS4 networks
    where the crystallographically distinct short hop IS the intra-network hop.
  - DistinctPathFinder picks hops by crystallographic inequivalence + length,
    avoiding the accidental interlayer-path selection from bare distance sorting.

Run:
  python run_neb_thiophosphates.py

Output per candidate:
  neb_<formula>/                     — image dirs, path_info.json
  neb_<formula>/chgnet_neb_results.json
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent

CANDIDATES = [
    # Validation reference — experimental Ea = 0.35 eV; use to calibrate CHGNet accuracy
    {"label": "Li3PS4",        "mp_formula": "Li3PS4"},
    # Novel Group A candidates with confirmed 3D Li networks (DistinctPathFinder >1d)
    {"label": "Li9Nd2(PS4)5",  "mp_formula": "Li9Nd2(PS4)5"},   # shortest hop 3.335 Å
    {"label": "Li4Zn(PS4)2",   "mp_formula": "Li4Zn(PS4)2"},    # shortest hop 3.634 Å
    {"label": "Li6Zn3(PS4)4",  "mp_formula": "Li6Zn3(PS4)4"},   # shortest hop 3.641 Å
    # Excluded: LiAl(PS3)2 — no 3D Li network; LiZnPS4 — 5.82 Å hop (1D channel)
]

N_IMAGES   = 7       # intermediate images (total = 9 with endpoints)
NEB_FMAX   = 0.10    # eV/Å force convergence
NEB_STEPS  = 500


def get_structure_from_mp(formula: str):
    """Fetch lowest-hull structure from Materials Project."""
    from mp_api.client import MPRester
    api_key = os.environ.get("MP_API_KEY")
    if not api_key:
        raise EnvironmentError("MP_API_KEY not set")
    with MPRester(api_key) as mpr:
        docs = list(mpr.materials.summary.search(
            formula=formula,
            fields=["structure", "energy_above_hull", "material_id"],
            energy_above_hull=(0, 0.1),
        ))
    if not docs:
        raise ValueError(f"No MP structure for {formula}")
    docs.sort(key=lambda d: d.energy_above_hull or 999.0)
    best = docs[0]
    print(f"  Using {best.material_id} (E_hull={best.energy_above_hull:.4f} eV)")
    return best.structure


def find_shortest_distinct_hop(structure, max_length: float = 6.0):
    """
    Use DistinctPathFinder to get crystallographically distinct Li hops,
    return the shortest one (which is the intra-framework hop for thiophosphates).
    Tries percolating (>1d) first, falls back to all paths if none found.
    """
    from pymatgen.analysis.diffusion.neb.pathfinder import DistinctPathFinder
    for perc_mode in [">1d", "None"]:
        dpf = DistinctPathFinder(
            structure,
            migrating_specie="Li",
            max_path_length=max_length,
            symprec=0.1,
            perc_mode=perc_mode,
        )
        paths = dpf.get_paths()
        if paths:
            paths.sort(key=lambda p: p.length)
            print(f"    ({len(paths)} distinct paths, perc_mode={perc_mode})")
            return paths[0]
    raise ValueError(f"No Li migration paths found within {max_length} Å")


def rough_conductivity(ea_ev: float) -> str:
    import math
    sigma = 12.0 * math.exp(-(ea_ev - 0.22) / (8.617e-5 * 298.15))
    if sigma > 5.0:   return f"~{sigma:.3f} mS/cm (SUPERIONIC)"
    if sigma > 1.0:   return f"~{sigma:.3f} mS/cm (VIABLE)"
    if sigma > 0.1:   return f"~{sigma:.3f} mS/cm (MODERATE)"
    return f"~{sigma:.3f} mS/cm (LOW)"


def run_candidate(label: str, mp_formula: str) -> dict:
    try:
        from ase.mep.neb import NEB
    except ImportError:
        from ase.neb import NEB
    from ase.optimize import FIRE
    from chgnet.model import CHGNet
    from chgnet.model.dynamics import CHGNetCalculator
    from pymatgen.io.ase import AseAtomsAdaptor

    print(f"\n{'='*55}")
    print(f"  NEB: {label}")
    print(f"{'='*55}")

    out_dir = ROOT / f"neb_{label}"
    out_dir.mkdir(exist_ok=True)

    # ── Structure from MP ──────────────────────────────────────────
    print(f"  Fetching structure for {mp_formula}...")
    struct = get_structure_from_mp(mp_formula)
    n_li = sum(1 for s in struct if s.species_string == "Li")
    print(f"  Primitive cell: {len(struct)} atoms, {n_li} Li")

    # ── Find crystallographic Li hop ───────────────────────────────
    print("  Finding distinct Li hops via DistinctPathFinder...")
    hop = find_shortest_distinct_hop(struct)
    print(f"  Shortest distinct hop: {hop.length:.3f} Å")

    # ── Build supercell endpoint structures ────────────────────────
    print("  Building vacancy supercell (80–240 atoms)...", end=" ", flush=True)
    start_struct, end_struct, _ = hop.get_sc_structures(
        vac_mode=True,
        min_atoms=80,
        max_atoms=240,
        min_length=10.0,
    )
    n_atoms = len(start_struct)
    print(f"{n_atoms} atoms")

    # Save bulk (start) and endpoint POSCARs
    bulk_dir = out_dir / "bulk"
    bulk_dir.mkdir(exist_ok=True)
    start_struct.to(filename=str(bulk_dir / "POSCAR"))

    # ── Get interpolated NEB images ────────────────────────────────
    print(f"  Generating {N_IMAGES} interpolated images (IDPP)...", end=" ", flush=True)
    pymatgen_images = hop.get_structures(
        nimages=N_IMAGES,
        vac_mode=True,
        idpp=True,
    )
    print("done")

    adaptor = AseAtomsAdaptor()
    images = [adaptor.get_atoms(s) for s in pymatgen_images]

    # Write image directories
    for i, img_struct in enumerate(pymatgen_images):
        img_dir = out_dir / f"{i:02d}"
        img_dir.mkdir(exist_ok=True)
        img_struct.to(filename=str(img_dir / "POSCAR"))
    print(f"  Wrote {len(images)} image directories")

    # ── CHGNet NEB ─────────────────────────────────────────────────
    print("  Loading CHGNet model...", end=" ", flush=True)
    model = CHGNet.load()
    print("OK")

    for img in images:
        img.calc = CHGNetCalculator(model=model, use_device="cpu")

    e_start = float(images[0].get_potential_energy())
    e_end   = float(images[-1].get_potential_energy())
    print(f"  Endpoint energies: start={e_start:.4f} eV, end={e_end:.4f} eV")
    print(f"  Reaction energy: {e_end - e_start:.4f} eV")

    # Pre-run sanity check: IDPP images should be well-behaved for 3D networks
    pre_energies = [float(img.get_potential_energy()) for img in images[1:-1]]
    max_pre = max(pre_energies) - e_start
    print(f"  Max intermediate energy after IDPP: {max_pre:.3f} eV above start")
    if max_pre > 5.0:
        msg = (f"IDPP path has {max_pre:.1f} eV spike — "
               "unexpected for thiophosphate. Check structure.")
        print(f"  WARNING: {msg}")
        return {"label": label, "error": msg, "max_idpp_energy_eV": round(max_pre, 3)}

    neb = NEB(images, climb=False, method='improvedtangent')
    opt = FIRE(neb, logfile=str(out_dir / "chgnet_neb.log"))

    print("  Phase 1: relaxing band (no climbing, fmax=0.3)...")
    opt.run(fmax=0.3, steps=150)

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

    # ── Extract results ────────────────────────────────────────────
    energies = ([e_start]
                + [float(img.get_potential_energy()) for img in images[1:-1]]
                + [e_end])
    rel_energies = [e - e_start for e in energies]

    ea_forward  = float(max(rel_energies))
    ea_backward = float(max(rel_energies) - rel_energies[-1])
    saddle_idx  = int(np.argmax(rel_energies))

    print(f"\n  ── Results ──────────────────────────────────────")
    print(f"  Ea (forward):   {ea_forward:.4f} eV")
    print(f"  Ea (backward):  {ea_backward:.4f} eV")
    print(f"  Saddle at image {saddle_idx}/{len(images)-1}")
    print(f"  σ estimate:     {rough_conductivity(ea_forward)}")

    profile_path = out_dir / "chgnet_neb_energy_profile.txt"
    with open(profile_path, "w") as f:
        f.write("# image  rel_energy_eV\n")
        for i, e in enumerate(rel_energies):
            f.write(f"{i:4d}  {e:.6f}\n")

    result = {
        "label": label,
        "mp_formula": mp_formula,
        "n_atoms_supercell": n_atoms,
        "hop_length_angstrom": round(hop.length, 4),
        "n_images": len(images),
        "ea_forward_ev": round(ea_forward, 4),
        "ea_backward_ev": round(ea_backward, 4),
        "reaction_energy_ev": round(float(rel_energies[-1]), 4),
        "saddle_image_index": saddle_idx,
        "converged": converged,
        "elapsed_seconds": round(elapsed, 1),
        "energy_profile_ev": [round(float(e), 6) for e in rel_energies],
        "conductivity_estimate": rough_conductivity(ea_forward),
        "path_method": "DistinctPathFinder (crystallographic) + IDPP",
    }

    out_path = out_dir / "chgnet_neb_results.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n")
    print(f"  Saved to {out_path.name}")

    return result


def main():
    print("=" * 55)
    print("  CHGNet CI-NEB — Thiophosphate Candidates")
    print("  (DistinctPathFinder + IDPP — crystallographic paths)")
    print("=" * 55)

    try:
        import chgnet
        print(f"  CHGNet {chgnet.__version__}")
    except ImportError:
        print("ERROR: pip install chgnet"); return

    all_results = []
    for c in CANDIDATES:
        result = run_candidate(c["label"], c["mp_formula"])
        all_results.append(result)

    print("\n\n" + "=" * 55)
    print("  SUMMARY")
    print("=" * 55)
    print(f"{'Compound':<22}  {'Hop (Å)':>8}  {'Ea (eV)':>8}  {'σ estimate'}")
    print("-" * 65)
    for r in all_results:
        if "error" in r:
            print(f"  {r['label']:<20}  ERROR: {r['error'][:40]}")
            continue
        print(f"  {r['label']:<20}  {r['hop_length_angstrom']:>8.3f}  "
              f"{r['ea_forward_ev']:>8.4f}  {r['conductivity_estimate']}")

    summary_path = ROOT / "chgnet_neb_thiophosphate_summary.json"
    summary_path.write_text(json.dumps(all_results, indent=2) + "\n")
    print(f"\nFull results: {summary_path}")


if __name__ == "__main__":
    main()
