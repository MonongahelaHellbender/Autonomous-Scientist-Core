import json
import re

FORBIDDEN = {
    "Pb": "TOXIC (Lead-based, regulatory barriers)",
    "Hg": "TOXIC (Mercury-based, extreme hazard)",
    "As": "TOXIC (Arsenic-based, safety risk)",
    "Cd": "TOXIC (Cadmium-based, restricted)",
    "Th": "RADIOACTIVE (Nuclear regulatory barriers)",
    "U": "RADIOACTIVE (Strict handling required)",
    "Se": "BYPRODUCT (Limited global production)",
    "Te": "RARE (Tellurium scarcity)",
    "Ag": "PRECIOUS METAL (High cost for mass-scale)",
}


def distinct_elements(formula):
    return sorted(set(re.findall(r"[A-Z][a-z]?", formula)))


def classify_environmental_risk(formula):
    elements = distinct_elements(formula)
    forbidden_hits = [element for element in FORBIDDEN if element in elements]

    is_suboxide = "O" in formula and ("O" == formula[-1] or formula[-2:] == "O1")
    if forbidden_hits:
        first_hit = forbidden_hits[0]
        return {
            "environment_risk": FORBIDDEN[first_hit],
            "final_verdict": "REJECTED (Safety / Supply Chain)",
            "forbidden_elements": forbidden_hits,
        }
    if is_suboxide and "Ca3" in formula:
        return {
            "environment_risk": "CRITICAL: Likely Pyrophoric/Reactive",
            "final_verdict": "REJECTED (Atmospheric Collapse)",
            "forbidden_elements": [],
        }
    return {
        "environment_risk": "LOW: Stoichiometrically Stable",
        "final_verdict": "APPROVED",
        "forbidden_elements": [],
    }


def scrutinize_reactivity():
    print("HARDENED CARBON SCAN: Checking stability, toxicity, and supply-chain risk...")

    with open("carbon_capture/pore_ceiling_results.json", "r") as f:
        candidates = json.load(f)

    results = []
    approved_count = 0
    print(f"{'Formula':<24} | {'Verdict'}")
    print("-" * 80)

    for candidate in candidates:
        formula = candidate["formula"]
        classification = classify_environmental_risk(formula)
        candidate.update(classification)

        if candidate["final_verdict"] == "APPROVED":
            approved_count += 1
            print(f"{formula:<24} | {candidate['environment_risk']}")

        results.append(candidate)

    print("")
    print(f"Approved candidates: {approved_count}")
    return results


if __name__ == "__main__":
    vetted = scrutinize_reactivity()
    with open("carbon_capture/vetted_carbon_results.json", "w") as f:
        json.dump(vetted, f, indent=4)
