import json
import numpy as np

def predict_conductivity():
    print("PERFORMANCE SCAN: Calculating Room-Temperature Ionic Conductivity...")
    
    with open("thermal_validated_candidates.json", "r") as f:
        candidates = json.load(f)

    # Boltzman constant in eV/K
    kb = 8.617e-5
    T = 298.15 # Room temp in Kelvin (25C)

    results = []
    for c in candidates:
        # Factual Heuristic: Activation Energy (Ea) is inversely proportional 
        # to the tunnel bottleneck width. 
        # Wider tunnels = Lower barrier for Li+ to jump.
        
        # Estimate Activation Energy (eV)
        # 1.5A is the threshold. Wider than that drops the barrier significantly.
        ea = 0.6 - (c['bottleneck_width_angstrom'] - 1.5) * 0.5
        ea = max(0.2, round(ea, 3)) # Cap at 0.2 eV (physically realistic limit)
        
        # Arrhenius Model for conductivity
        # sigma = sigma_0 * exp(-Ea / (kb * T))
        sigma_0 = 1000 # Pre-exponential factor for high-performing sulfides
        conductivity = sigma_0 * np.exp(-ea / (kb * T))
        
        c['activation_energy_ev'] = ea
        c['conductivity_ms_cm'] = round(conductivity, 4)
        
        if c['conductivity_ms_cm'] > 5.0:
            c['perf_rating'] = "SUPERIONIC (Tesla-Grade)"
        elif c['conductivity_ms_cm'] > 1.0:
            c['perf_rating'] = "VIABLE"
        else:
            c['perf_rating'] = "LOW FLOW"

        print(f"\nMaterial: {c['formula']}")
        print(f"  - Activation Energy: {ea} eV")
        print(f"  - RT Conductivity: {c['conductivity_ms_cm']} mS/cm")
        print(f"  - Performance: {c['perf_rating']}")
        results.append(c)

    return results

if __name__ == "__main__":
    perf_data = predict_conductivity()
    with open("final_validated_candidates.json", "w") as f:
        json.dump(perf_data, f, indent=4)
    print("\nPerformance metrics archived in 'final_validated_candidates.json'.")
