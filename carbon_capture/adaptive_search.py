from mp_api.client import MPRester
import json

API_KEY = "7bwxDCAscx0aaR8ROwmn95lDbtN4Gs7E"

def find_pore_ceiling():
    print("ADAPTIVE MISSION: Finding the 'Porosity Ceiling' for the Calcium Manifold...")
    
    SEARCH_ELEMENTS = ["Ca", "Si", "O"]

    with MPRester(API_KEY) as mpr:
        docs = mpr.materials.summary.search(
            elements=SEARCH_ELEMENTS,
            energy_above_hull=(0, 0.05),
            fields=["formula_pretty", "volume", "structure", "formation_energy_per_atom"]
        )

    results = []
    for d in docs:
        space_per_atom = d.volume / len(d.structure)
        results.append({
            "formula": d.formula_pretty,
            "pore_space": round(space_per_atom, 2),
            "stability": round(d.formation_energy_per_atom, 3)
        })

    # Sort by pore space to find the winner
    results.sort(key=lambda x: x['pore_space'], reverse=True)

    print(f"\nADAPTIVE BREAKTHROUGH: Found the top 3 most porous Calcium Silicates.")
    print(f"{'Formula':<15} | {'Pore Space':<12} | {'Stability'}")
    print("-" * 45)
    for res in results[:3]:
        print(f"{res['formula']:<15} | {res['pore_space']:<12} | {res['stability']} eV")
    
    return results

if __name__ == "__main__":
    winners = find_pore_ceiling()
    with open("carbon_capture/pore_ceiling_results.json", "w") as f:
        json.dump(winners, f, indent=4)
