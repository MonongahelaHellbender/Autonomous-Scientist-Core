import json

def scrutinize_solar_v2():
    print("HARDENED ADVERSARIAL SCAN: Consolidating Toxicity, Scarcity, and Safety...")
    
    with open("ingestion/raw_solar_data.json", "r") as f:
        data = json.load(f)

    # The Master "Forbidden" Database
    FORBIDDEN = {
        # TOXICITY
        "Pb": "TOXIC (Lead-based, regulatory barriers)",
        "Hg": "TOXIC (Mercury-based, extreme hazard)",
        "As": "TOXIC (Arsenic-based, safety risk)",
        "Cd": "TOXIC (Cadmium-based, restricted)",
        # RADIOACTIVITY
        "Th": "RADIOACTIVE (Nuclear regulatory barriers)",
        "U":  "RADIOACTIVE (Strict handling required)",
        # SCARCITY / SUPPLY CHAIN
        "Gd": "RARE EARTH (Supply chain volatility)",
        "Yb": "RARE EARTH (High cost/Scarcity)",
        "Se": "BYPRODUCT (Limited global production)",
        "Te": "RARE (Tellurium scarcity)",
        "Ag": "PRECIOUS METAL (High cost for mass-scale)"
    }

    results = []
    print(f"{'Formula':<15} | {'Primary Risk'}")
    print("-" * 55)

    for d in data:
        formula = d['formula']
        # Detect all risky elements present in the formula
        risks_found = [FORBIDDEN[el] for el in FORBIDDEN if el in formula]
        
        if risks_found:
            d['adversarial_risk'] = risks_found[0] # Log the first major risk
            d['final_verdict'] = "REJECTED"
        else:
            d['adversarial_risk'] = "NONE"
            d['final_verdict'] = "APPROVED"
        
        if d['final_verdict'] == "APPROVED":
            print(f"\033[92m{formula:<15}\033[0m | {d['adversarial_risk']}")
        else:
            # We don't print all rejections to keep the log clean
            pass
            
        results.append(d)

    return results

if __name__ == "__main__":
    vetted = scrutinize_solar_v2()
    with open("adversarial/vetted_solar_results.json", "w") as f:
        json.dump(vetted, f, indent=4)
    
    # Filter for the actual winners
    winners = [v for v in vetted if v['final_verdict'] == "APPROVED"]
    print(f"\n--- HARDENED RESULTS ---")
    print(f"Total candidates passed: {len(winners)}")
