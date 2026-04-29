from mp_api.client import MPRester
import json

API_KEY = "7bwxDCAscx0aaR8ROwmn95lDbtN4Gs7E"

def validate_synthesis():
    print("ANALYZING SYNTHESIS SUITABILITY (Energy Above Hull)...")
    
    with open("discovery_history_v2.json", "r") as f:
        candidates = json.load(f)

    with MPRester(API_KEY) as mpr:
        final_lab_candidates = []
        
        for c in candidates:
            # Query for the specific material's 'energy_above_hull'
            docs = mpr.materials.summary.search(
                formula=c['formula'],
                fields=["material_id", "energy_above_hull"]
            )
            
            if docs:
                # We take the most stable version of that formula
                min_ehull = min([d.energy_above_hull for d in docs])
                
                print(f"Checking {c['formula']}: E_hull = {min_ehull:.3f} eV/atom")
                
                # LAB CONSTRAINT: Only accept if very close to the stable hull
                if min_ehull < 0.03:
                    c['synthesis_status'] = "LAB-READY"
                    final_lab_candidates.append(c)
                else:
                    c['synthesis_status'] = "THEORETICAL-ONLY"

    print(f"\nVALIDATION COMPLETE: Found {len(final_lab_candidates)} Lab-Ready materials.")
    for res in final_lab_candidates:
        print(f"LAB CANDIDATE: {res['formula']} | Room: {res['room_per_atom']:.2f} Å³ | STATUS: {res['synthesis_status']}")
    
    return final_lab_candidates

if __name__ == "__main__":
    lab_ready = validate_synthesis()
    with open("lab_ready_candidates.json", "w") as f:
        json.dump(lab_ready, f, indent=4)
