from mp_api.client import MPRester
import json

API_KEY = "7bwxDCAscx0aaR8ROwmn95lDbtN4Gs7E"

def search_robust_cages():
    print("MISSION: Discovering 'Water-Resistant' Manifolds for Carbon Capture...")
    
    # Elements for cheap, global-scale DAC
    SEARCH_ELEMENTS = ["Al", "Si", "O"]

    with MPRester(API_KEY) as mpr:
        docs = mpr.materials.summary.search(
            elements=SEARCH_ELEMENTS,
            energy_above_hull=(0, 0.04),
            fields=["formula_pretty", "density", "volume", "structure", "formation_energy_per_atom"]
        )

    results = []
    for d in docs:
        space_per_atom = d.volume / len(d.structure)
        
        # --- ADVERSARIAL FILTER START ---
        # 1. Moisture Risk: Al-rich zeolites are notorious for water-clogging.
        # We penalize high Aluminum ratios.
        al_count = d.formula_pretty.count('Al')
        si_count = d.formula_pretty.count('Si')
        hydrophilicity_penalty = 0
        if al_count > si_count:
            hydrophilicity_penalty = 15.0 # Significant reduction in pore effectiveness
            
        # 2. Kinetic Risk: Complex formulas (4+ elements) take too long to synthesize.
        # This is already restricted by our SEARCH_ELEMENTS, but we check stoichiometry.
        complexity_penalty = len(d.structure) * 0.1
        
        # --- ROBUSTNESS CALCULATION ---
        # Robust Score = Pore Space - Penalties
        robust_pore_score = space_per_atom - hydrophilicity_penalty - complexity_penalty
        # --- ADVERSARIAL FILTER END ---

        if space_per_atom > 18.0:
            results.append({
                "formula": d.formula_pretty,
                "pore_space": round(space_per_atom, 2),
                "robustness_score": round(robust_pore_score, 2),
                "adversarial_verdict": "SECURE" if robust_pore_score > 15 else "VULNERABLE"
            })

    # Sort by Robustness Score (The "Survives the Real World" Metric)
    results.sort(key=lambda x: x['robustness_score'], reverse=True)

    print(f"\nSCREENING COMPLETE: Found {len(results)} candidates.")
    print(f"{'Formula':<15} | {'Pore Space':<10} | {'Robustness':<10} | {'Verdict'}")
    print("-" * 55)
    for i, res in enumerate(results[:5]):
        print(f"{res['formula']:<15} | {res['pore_space']:<10} | {res['robustness_score']:<10} | {res['adversarial_verdict']}")

    return results

if __name__ == "__main__":
    candidates = search_robust_cages()
    with open("carbon_capture/robust_candidates.json", "w") as f:
        json.dump(candidates, f, indent=4)
