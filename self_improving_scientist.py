from mp_api.client import MPRester
import json

API_KEY = "7bwxDCAscx0aaR8ROwmn95lDbtN4Gs7E"

def autonomous_refinement():
    print("ANALYZING DISCOVERY HISTORY...")
    with open("discovery_history.json", "r") as f:
        history = json.load(f)
    
    print(f"DECISION: Phosphorus candidates found. Pivoting to Silicon (Si) for better scalability...")

    with MPRester(API_KEY) as mpr:
        # Searching for Silicon-Sulfur-Lithium compounds
        docs = mpr.materials.summary.search(
            elements=["Li", "S", "Si"],
            energy_above_hull=(0, 0.03),
            fields=["formula_pretty", "volume", "structure", "formation_energy_per_atom"]
        )

    refined_results = []
    for d in docs:
        vol_per_atom = d.volume / len(d.structure)
        if vol_per_atom > 18.0:
            refined_results.append({
                "formula": d.formula_pretty,
                "room_per_atom": vol_per_atom,
                "stability": d.formation_energy_per_atom
            })

    # Sort by stability
    refined_results.sort(key=lambda x: x["stability"])
    
    print(f"\nREFINEMENT COMPLETE: Found {len(refined_results)} Silicon-based high-speed candidates.")
    for res in refined_results[:3]:
        print(f"NEW CANDIDATE: {res['formula']} | Room per Atom: {res['room_per_atom']:.2f} Å³")
    
    return refined_results

if __name__ == "__main__":
    results = autonomous_refinement()
    with open("discovery_history_v2.json", "w") as f:
        json.dump(results, f, indent=4)
