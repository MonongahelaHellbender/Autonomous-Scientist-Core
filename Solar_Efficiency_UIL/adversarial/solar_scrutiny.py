import json

def scrutinize_solar():
    print("DEVIL'S ADVOCATE: Checking Radioactivity and Element Scarcity...")
    
    with open("ingestion/raw_solar_data.json", "r") as f:
        data = json.load(f)

    # Scarcity/Risk Database
    RISKY_ELEMENTS = {
        "Th": "RADIOACTIVE (Nuclear regulatory barriers)",
        "Gd": "RARE EARTH (Supply chain volatility)",
        "Yb": "RARE EARTH (High cost/Scarcity)",
        "Se": "BYPRODUCT (Limited global production)"
    }

    results = []
    for d in data:
        formula = d['formula']
        risks = [RISKY_ELEMENTS[el] for el in RISKY_ELEMENTS if el in formula]
        
        print(f"\nScrutinizing {formula}...")
        if risks:
            d['adversarial_risk'] = " | ".join(risks)
            d['final_verdict'] = "REJECTED (Scale/Safety Risk)"
        else:
            d['adversarial_risk'] = "NONE"
            d['final_verdict'] = "APPROVED (Ready for Gigafactory)"
        
        print(f"  - Risks: {d['adversarial_risk']}")
        print(f"  - Verdict: {d['final_verdict']}")
        results.append(d)

    return results

if __name__ == "__main__":
    vetted = scrutinize_solar()
    with open("adversarial/vetted_solar_results.json", "w") as f:
        json.dump(vetted, f, indent=4)
