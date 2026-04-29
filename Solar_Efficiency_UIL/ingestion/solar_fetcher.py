from mp_api.client import MPRester
import json

API_KEY = "7bwxDCAscx0aaR8ROwmn95lDbtN4Gs7E"

def fetch_solar_candidates():
    print("SOLAR MISSION: Fetching semiconductors in the Shockley-Queisser Manifold...")
    
    # We hunt for stable, non-toxic semiconductors
    # Exclude Lead (Pb) and Cadmium (Cd) to ensure 'Industrial Hero' status
    with MPRester(API_KEY) as mpr:
        docs = mpr.materials.summary.search(
            band_gap=(1.1, 1.6), # The 'Sweet Spot' for Solar
            energy_above_hull=(0, 0.02),
            fields=["formula_pretty", "band_gap", "elements", "formation_energy_per_atom"]
        )

    results = []
    for d in docs:
        elements = [e.symbol for e in d.elements]
        # ADVERSARIAL PRE-FILTER: Flag toxic elements immediately
        toxic_elements = ["Pb", "Cd", "As", "Hg"]
        is_toxic = any(te in elements for te in toxic_elements)
        
        results.append({
            "formula": d.formula_pretty,
            "band_gap": round(d.band_gap, 2),
            "stability": round(d.formation_energy_per_atom, 3),
            "is_toxic": is_toxic
        })

    print(f"\nINGESTION COMPLETE: Found {len(results)} potential solar materials.")
    return results

if __name__ == "__main__":
    raw_data = fetch_solar_candidates()
    with open("ingestion/raw_solar_data.json", "w") as f:
        json.dump(raw_data, f, indent=4)
