from mp_api.client import MPRester
import json

API_KEY = "7bwxDCAscx0aaR8ROwmn95lDbtN4Gs7E"

# We target Earth-Abundant elements + Sulfur
# Elements: Li(3), P(15), S(16), Si(14), Fe(26)
SEARCH_ELEMENTS = ["Li", "S", "P"]

print("Autonomous Mission: Searching for 'Open Channel' Sulfide Electrolytes...")

with MPRester(API_KEY) as mpr:
    # Querying for stable Sulfides containing Lithium and Phosphorus
    docs = mpr.materials.summary.search(
        elements=SEARCH_ELEMENTS,
        energy_above_hull=(0, 0.03),
        fields=["formula_pretty", "volume", "structure", "formation_energy_per_atom"]
    )

results = []
for d in docs:
    vol_per_atom = d.volume / len(d.structure)
    if vol_per_atom > 17.0: # Targeting extremely open frameworks
        results.append({
            "formula": d.formula_pretty,
            "room_per_atom": vol_per_atom,
            "stability": d.formation_energy_per_atom
        })

# Sort by stability (most stable first)
results.sort(key=lambda x: x["stability"])

print(f"\nSCREENING COMPLETE: Found {len(results)} High-Speed Candidates.")
for i, res in enumerate(results[:5]):
    print(f"{i+1}. {res['formula']} | Room per Atom: {res['room_per_atom']:.2f} Å³ | Stability: {res['stability']:.2f} eV")

# Log to discovery file
with open("discovery_history.json", "a") as f:
    json.dump(results[:5], f, indent=4)
