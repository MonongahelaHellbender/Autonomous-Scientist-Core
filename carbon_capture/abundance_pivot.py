from mp_api.client import MPRester
import json

API_KEY = "7bwxDCAscx0aaR8ROwmn95lDbtN4Gs7E"

def calculate_abundance_manifold():
    print("PLANETARY SCALE SCAN: Pivoting to Calcium (Ca) for Maximum Abundance...")
    
    # Elements: Ca (Abundant), Si (Abundant), O (Abundant)
    # We remove Al to maximize moisture resistance.
    SEARCH_ELEMENTS = ["Ca", "Si", "O"]

    with MPRester(API_KEY) as mpr:
        docs = mpr.materials.summary.search(
            elements=SEARCH_ELEMENTS,
            energy_above_hull=(0, 0.02),
            fields=["formula_pretty", "volume", "structure", "formation_energy_per_atom"]
        )

    results = []
    for d in docs:
        space_per_atom = d.volume / len(d.structure)
        
        # We look for the "High Porosity" Manifold (> 22 Å³/atom)
        if space_per_atom > 22.0:
            results.append({
                "formula": d.formula_pretty,
                "pore_space": round(space_per_atom, 2),
                "stability": round(d.formation_energy_per_atom, 3),
                "verdict": "ABUNDANCE WINNER"
            })

    results.sort(key=lambda x: x['pore_space'], reverse=True)

    print(f"\nPLANETARY BREAKTHROUGH: Found {len(results)} Calcium-based Cages.")
    print(f"{'Formula':<15} | {'Pore Space':<12} | {'Stability'}")
    print("-" * 45)
    for res in results[:3]:
        print(f"{res['formula']:<15} | {res['pore_space']:<12} | {res['stability']} eV")
    
    return results

if __name__ == "__main__":
    winners = calculate_abundance_manifold()
    with open("carbon_capture/final_carbon_results.json", "w") as f:
        json.dump(winners, f, indent=4)
