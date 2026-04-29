import json

def run_red_team_analysis():
    print("ADVERSARIAL SCAN: Hunting for 'Water-Poisoning' and Kinetic Failures...")
    
    with open("porous_candidates.json", "r") as f:
        candidates = json.load(f)

    final_report = []
    for c in candidates:
        # Factual Heuristic: Al-based zeolites are often 'Hydrophilic' (Water-loving).
        # This is a major failure point for Carbon Capture.
        
        is_aluminum_based = "Al" in c['formula']
        
        print(f"\nScrutinizing {c['formula']}...")
        
        if is_aluminum_based:
            c['adversarial_risk'] = "HIGH: Competitive Water Adsorption"
            c['mitigation_strategy'] = "Require hydrophobic coating (Adds $5/kg cost)"
        else:
            c['adversarial_risk'] = "LOW: Pure Silica/Sulfide Manifold"
            c['mitigation_strategy'] = "None required"

        # Check for Kinetic Bottleneck (Complexity of formula)
        num_elements = len([char for char in c['formula'] if char.isupper()])
        if num_elements > 3:
            c['kinetic_risk'] = "HIGH: Slow crystal growth (Quaternary phase)"
        else:
            c['kinetic_risk'] = "LOW: Simple synthesis"

        print(f"  - Moisture Sensitivity: {c['adversarial_risk']}")
        print(f"  - Synthesis Difficulty: {c['kinetic_risk']}")
        final_report.append(c)

    return final_report

if __name__ == "__main__":
    report = run_red_team_analysis()
    with open("adversarial_report.json", "w") as f:
        json.dump(report, f, indent=4)
    print("\nAdversarial Pass Complete. Check 'adversarial_report.json' before proceeding.")
