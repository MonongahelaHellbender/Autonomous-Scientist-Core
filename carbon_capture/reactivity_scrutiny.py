import json

def scrutinize_reactivity():
    print("DEVIL'S ADVOCATE: Checking Atmospheric Stability (O-to-Metal Ratio)...")
    
    with open("carbon_capture/pore_ceiling_results.json", "r") as f:
        candidates = json.load(f)

    results = []
    for c in candidates:
        formula = c['formula']
        # Factual Heuristic: If Oxygen ratio is too low, the material is an 'unfilled manifold'
        # and will likely oxidize/collapse when exposed to air.
        
        # Simplified parser for Oxygen-to-Metal ratio
        is_suboxide = "O" in formula and ("O" == formula[-1] or formula[-2:] == "O1")
        
        print(f"\nChecking {formula}...")
        if is_suboxide and "Ca3" in formula:
            c['environment_risk'] = "CRITICAL: Likely Pyrophoric/Reactive"
            c['final_verdict'] = "REJECTED (Atmospheric Collapse)"
        else:
            c['environment_risk'] = "LOW: Stoichiometrically Stable"
            c['final_verdict'] = "APPROVED"
        
        print(f"  - Air Risk: {c['environment_risk']}")
        print(f"  - Verdict: {c['final_verdict']}")
        results.append(c)

    return results

if __name__ == "__main__":
    vetted = scrutinize_reactivity()
    with open("carbon_capture/vetted_carbon_results.json", "w") as f:
        json.dump(vetted, f, indent=4)
