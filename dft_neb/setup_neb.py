#!/usr/bin/env python3
"""
setup_neb.py
------------
Pulls the top 3 Group A candidates from MP, builds vacancy supercells,
and writes NEB image directories ready for VASP submission.

Candidates: Li2In2GeS6, Li2In2SiS6, LiInS2

Requirements:
  pip install pymatgen pymatgen-analysis-diffusion mp-api

Run:
  export MP_API_KEY='your_key'
  python setup_neb.py

Output layout (one per candidate):
  neb_Li2In2GeS6/
    bulk/              POSCAR of relaxed supercell
    vacancy_start/     POSCAR with one Li removed (migration source)
    vacancy_end/       POSCAR with Li at destination (migration sink)
    00/                Endpoint image (= vacancy_start)
    01/ ... 05/        Interpolated NEB images
    06/                Endpoint image (= vacancy_end)
    INCAR              copied from ../INCAR_neb
    KPOINTS            copied from ../KPOINTS
    POTCAR.spec        list of PAW potentials needed (assemble manually)
    path_info.json     migration path details (distance, estimated Ea class)
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

CANDIDATES = [
    {"label": "Li2In2GeS6", "formula": "Li2In2GeS6"},
    {"label": "Li2In2SiS6", "formula": "Li2In2SiS6"},
    {"label": "LiInS2",     "formula": "LiInS2"},
]

N_IMAGES = 5       # intermediate NEB images (total = N_IMAGES + 2 with endpoints)
SUPERCELL = [2, 2, 1]  # supercell expansion — adjust based on structure


def get_structure(formula: str, mpr) -> object:
    """Return the most stable MP structure for the given formula."""
    docs = list(mpr.materials.summary.search(
        formula=formula,
        fields=["structure", "energy_above_hull", "material_id"],
        energy_above_hull=(0, 0.05),
    ))
    if not docs:
        raise ValueError(f"No MP structure found for {formula}")
    docs.sort(key=lambda d: d.energy_above_hull or 999.0)
    print(f"  Using {docs[0].material_id} (E_hull={docs[0].energy_above_hull:.4f} eV)")
    return docs[0].structure


def build_neb_images_linear(start, end, n_images: int) -> list:
    """Linear interpolation between start and end structures."""
    from pymatgen.core import Structure
    images = []
    for i in range(1, n_images + 1):
        frac = i / (n_images + 1)
        interp_sites = []
        for s_site, e_site in zip(start, end):
            new_frac = s_site.frac_coords + frac * (e_site.frac_coords - s_site.frac_coords)
            interp_sites.append((s_site.species_string, new_frac))
        interp = Structure(start.lattice, [s for s, _ in interp_sites], [f for _, f in interp_sites])
        images.append(interp)
    return images


def find_migration_path(structure):
    """
    Find the shortest Li-Li hop in the structure as the NEB path.
    Returns (site_index_start, frac_coords_end, hop_distance_angstrom).
    Falls back to the two nearest Li sites.
    """
    from pymatgen.core import PeriodicSite
    import numpy as np

    li_sites = [(i, site) for i, site in enumerate(structure) if site.species_string == "Li"]
    if len(li_sites) < 2:
        raise ValueError("Need at least 2 Li sites to define a migration path")

    best = None
    best_dist = 1e10
    for i, (idx_a, site_a) in enumerate(li_sites):
        for idx_b, site_b in li_sites[i + 1:]:
            dist = structure.get_distance(idx_a, idx_b)
            if dist < best_dist:
                best_dist = dist
                best = (idx_a, idx_b, site_b.frac_coords, dist)

    return best  # (remove_idx, destination_idx, destination_frac, distance)


def setup_candidate(label: str, formula: str, mpr) -> dict:
    print(f"\n{'='*50}")
    print(f"Setting up NEB for {label}")
    print(f"{'='*50}")

    out_dir = ROOT / f"neb_{label}"
    out_dir.mkdir(exist_ok=True)

    # ── Get structure ───────────────────────────────────────────────
    structure = get_structure(formula, mpr)
    structure.make_supercell(SUPERCELL)
    n_li_total = sum(1 for s in structure if s.species_string == "Li")
    print(f"  Supercell: {SUPERCELL}, {len(structure)} atoms, {n_li_total} Li sites")

    # Save bulk supercell
    bulk_dir = out_dir / "bulk"
    bulk_dir.mkdir(exist_ok=True)
    structure.to(filename=str(bulk_dir / "POSCAR"))

    # ── Find migration path ─────────────────────────────────────────
    result = find_migration_path(structure)
    if result is None:
        print(f"  ERROR: Could not find Li migration path for {label}")
        return {}
    remove_idx, dest_idx, dest_frac, hop_dist = result
    print(f"  Shortest Li-Li hop: {hop_dist:.3f} Å (sites {remove_idx} → {dest_idx})")

    # ── Build endpoint structures ───────────────────────────────────
    # Start: remove Li at remove_idx (creates vacancy at source)
    start_struct = structure.copy()
    start_struct.remove_sites([remove_idx])

    # End: remove Li at dest_idx instead (vacancy now at destination)
    end_struct = structure.copy()
    end_struct.remove_sites([dest_idx])

    start_dir = out_dir / "vacancy_start"
    end_dir = out_dir / "vacancy_end"
    start_dir.mkdir(exist_ok=True)
    end_dir.mkdir(exist_ok=True)
    start_struct.to(filename=str(start_dir / "POSCAR"))
    end_struct.to(filename=str(end_dir / "POSCAR"))

    # ── Interpolate NEB images ──────────────────────────────────────
    images = build_neb_images_linear(start_struct, end_struct, N_IMAGES)
    all_images = [start_struct] + images + [end_struct]  # N_IMAGES+2 total

    for i, img in enumerate(all_images):
        img_dir = out_dir / f"{i:02d}"
        img_dir.mkdir(exist_ok=True)
        img.to(filename=str(img_dir / "POSCAR"))

    print(f"  Wrote {len(all_images)} image directories (00–{len(all_images)-1:02d})")

    # ── Copy VASP input files ───────────────────────────────────────
    for fname in ["INCAR_neb", "KPOINTS"]:
        src = ROOT / fname
        dst = out_dir / fname.replace("_neb", "")
        if src.exists():
            shutil.copy(src, dst)

    # ── POTCAR spec ────────────────────────────────────────────────
    elements = sorted(set(s.species_string for s in structure))
    potcar_spec = out_dir / "POTCAR.spec"
    potcar_spec.write_text(
        "# Assemble POTCAR manually from your VASP PAW library.\n"
        "# Recommended PAW potentials for Li-S electrolytes:\n"
        + "\n".join(f"  {el}: PAW_PBE/{el}_sv  (or {el})" for el in elements)
        + "\n\n# Command (adjust paths to your VASP library):\n"
        + "# cat " + " ".join(f"$VASP_PP/{el}_sv/POTCAR" for el in elements)
        + " > POTCAR\n"
    )

    # ── Path info JSON ─────────────────────────────────────────────
    path_info = {
        "formula": formula,
        "label": label,
        "supercell": SUPERCELL,
        "n_atoms_supercell": len(structure),
        "n_li_sites": n_li_total,
        "hop_distance_angstrom": round(hop_dist, 4),
        "n_images": N_IMAGES,
        "total_image_dirs": len(all_images),
        "note": (
            "Linear interpolation used. After VASP relaxation of endpoints, "
            "re-interpolate using relaxed POSCARs for better NEB convergence."
        ),
    }
    (out_dir / "path_info.json").write_text(json.dumps(path_info, indent=2))
    print(f"  Saved path_info.json")

    return path_info


def main():
    try:
        from mp_api.client import MPRester
    except ImportError:
        print("mp_api not found. Install with: pip install mp-api")
        return

    api_key = os.environ.get("MP_API_KEY")
    if not api_key:
        print("ERROR: MP_API_KEY not set.")
        return

    results = []
    with MPRester(api_key) as mpr:
        for c in CANDIDATES:
            try:
                info = setup_candidate(c["label"], c["formula"], mpr)
                results.append(info)
            except Exception as e:
                print(f"  ERROR for {c['label']}: {e}")

    print(f"\n{'='*50}")
    print(f"NEB setup complete for {len(results)} candidates.")
    print(f"Next steps:")
    print(f"  1. Assemble POTCAR in each neb_*/  directory")
    print(f"  2. Relax both endpoints:  vasp_std in 00/ and last image dir/")
    print(f"  3. Replace endpoint POSCARs with relaxed CONTCARs")
    print(f"  4. Re-interpolate images if needed (update setup_neb.py endpoints)")
    print(f"  5. Submit NEB: vasp_std in the parent neb_*/ directory")
    print(f"  6. Read Ea from OUTCAR or use vaspkit/nebresults.pl")


if __name__ == "__main__":
    main()
