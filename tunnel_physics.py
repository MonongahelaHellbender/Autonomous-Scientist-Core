from mp_api.client import MPRester
import json

API_KEY = "7bwxDCAscx0aaR8ROwmn95lDbtN4Gs7E"

def analyze_tunnels():
    print("PHYSICS SCAN: Mapping Ion Tunnels via Bottleneck Analysis...")
    
    try:
        with open("lab_ready_candidates.json", "r") as f:
            candidates = json.load(f)
    except FileNotFoundError:
        print("Error: lab_ready_candidates.json not found. Run previous scripts first.")
        return []

    results = []
    with MPRester(API_KEY) as mpr:
        for c in candidates:
            # Fixed API Call: Search for formula and get structure directly
            docs = mpr.materials.summary.search(
                formula=c['formula'], 
                fields=["structure", "volume"]
            )
            
            if docs:
                struct = docs[0].structure
                vol = docs[0].volume
                # Approximate packing density
                # (Atomic radii sum / unit cell volume)
                atomic_rad_sum = sum([getattr(site.specie, 'atomic_radius', 1.0) for site in struct])
                packing_fraction = atomic_rad_sum / vol
                
                # UIL Heuristic: Bottleneck width
                bottleneck_width = (c['room_per_atom'] / 10.0) * (1 - packing_fraction)
                c['bottleneck_width_angstrom'] = round(bottleneck_width, 3)
                
                if bottleneck_width > 1.2:
                    c['speed_rating'] = "ULTRA-FAST (5-min charge)"
                elif bottleneck_width > 0.9:
                    c['speed_rating'] = "FAST (15-min charge)"
                else:
                    c['speed_rating'] = "STANDARD"
                    
                results.append(c)
                print(f"Mapped {c['formula']}: Bottleneck = {c['bottleneck_width_angstrom']} Å | {c['speed_rating']}")

    return results

if __name__ == "__main__":
    physics_results = analyze_tunnels()
    with open("physics_validated_candidates.json", "w") as f:
        json.dump(physics_results, f, indent=4)
    print("\nPhysics validation saved to 'physics_validated_candidates.json'.")
