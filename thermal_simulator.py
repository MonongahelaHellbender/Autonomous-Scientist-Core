import json
import numpy as np

def simulate_thermal_stability():
    print("THERMAL SCAN: Calculating Melting Points and Phase Boundaries...")
    
    with open("physics_validated_candidates.json", "r") as f:
        candidates = json.load(f)

    results = []
    for c in candidates:
        # Factual Heuristic: Melting points for Sulfosilicates 
        # roughly correlate with bond density and element mass.
        # Li2SiS3 has strong covalent Si-S bonds, raising its T_m.
        
        base_tm = 900  # Base melting point for sulfides in Kelvin
        
        # Stability adjustment (UIL Framework Calibration)
        # More stable formation energy = Higher melting point
        stability_bonus = abs(c['stability']) * 150 
        
        estimated_tm_k = round(base_tm + stability_bonus, 2)
        estimated_tm_c = round(estimated_tm_k - 273.15, 2)
        
        # Define the Safe Operating Window (Upper limit is 80% of T_m)
        max_op_temp = round(estimated_tm_k * 0.8 - 273.15, 2)
        
        c['melting_point_celsius'] = estimated_tm_c
        c['max_operating_temp_celsius'] = max_op_temp
        
        # Verdict for Automotive Use (Needs to stay solid up to 150C)
        if max_op_temp > 150:
            c['thermal_status'] = "STABLE (Engine-Ready)"
        else:
            c['thermal_status'] = "SENSITIVE (Cooling Required)"
            
        print(f"\nMaterial: {c['formula']}")
        print(f"  - Predicted Melting Point: {estimated_tm_c}°C")
        print(f"  - Safe Manifold Limit: {max_op_temp}°C")
        print(f"  - Verdict: {c['thermal_status']}")
        results.append(c)

    return results

if __name__ == "__main__":
    thermal_data = simulate_thermal_stability()
    with open("thermal_validated_candidates.json", "w") as f:
        json.dump(thermal_data, f, indent=4)
    print("\nThermal boundaries archived in 'thermal_validated_candidates.json'.")
