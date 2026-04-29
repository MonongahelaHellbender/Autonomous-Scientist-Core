import json
import re
from datetime import date
from pathlib import Path

from cage_stress_test import write_json_output
from property_conditioned_stress_proxy import load_retained_candidates

OUTPUT_PATH = Path("carbon_capture/abundance_safe_subset_v1.json")

ABUNDANCE_EXCLUSION = {
    "Hf": "SCARCITY HEAVY (hafnium supply concentration)",
    "Ta": "SCARCITY HEAVY (tantalum supply concentration)",
    "Nb": "SCARCITY HEAVY (niobium supply concentration)",
    "Y": "SCARCITY HEAVY (yttrium supply concentration)",
    "La": "SCARCITY HEAVY (lanthanum supply concentration)",
    "Ce": "SCARCITY HEAVY (cerium supply concentration)",
    "Nd": "SCARCITY HEAVY (neodymium supply concentration)",
    "Dy": "SCARCITY HEAVY (dysprosium supply concentration)",
    "Er": "SCARCITY HEAVY (erbium supply concentration)",
    "Yb": "SCARCITY HEAVY (ytterbium supply concentration)",
    "Gd": "SCARCITY HEAVY (gadolinium supply concentration)",
    "Lu": "SCARCITY HEAVY (lutetium supply concentration)",
    "Tb": "SCARCITY HEAVY (terbium supply concentration)",
    "Eu": "SCARCITY HEAVY (europium supply concentration)",
    "Sm": "SCARCITY HEAVY (samarium supply concentration)",
    "Tm": "SCARCITY HEAVY (thulium supply concentration)",
    "Ho": "SCARCITY HEAVY (holmium supply concentration)",
}


def distinct_elements(formula):
    return sorted(set(re.findall(r"[A-Z][a-z]?", formula)))


def partition_candidates():
    retained = load_retained_candidates()
    candidates = []
    excluded = []

    for candidate in retained:
        elements = distinct_elements(candidate["formula"])
        scarcity_hits = [element for element in ABUNDANCE_EXCLUSION if element in elements]
        if scarcity_hits:
            excluded.append(
                {
                    "formula": candidate["formula"],
                    "scarcity_hits": scarcity_hits,
                    "reasons": [ABUNDANCE_EXCLUSION[element] for element in scarcity_hits],
                    "pore_space": candidate["pore_space"],
                    "stability": candidate["stability"],
                }
            )
            continue

        enriched = dict(candidate)
        enriched["abundance_safe_v1"] = True
        enriched["abundance_policy"] = "explicit scarcity-heavy exclusion set"
        enriched["abundance_exclusion_hits"] = []
        candidates.append(enriched)

    candidates.sort(key=lambda row: (-row["pore_space"], row["stability"], row["formula"]))
    excluded.sort(key=lambda row: (-row["pore_space"], row["stability"], row["formula"]))
    return retained, candidates, excluded


def build_artifact():
    retained, candidates, excluded = partition_candidates()
    return {
        "artifact_type": "abundance_safe_subset_v1",
        "created_on": str(date.today()),
        "source": "carbon_capture/vetted_carbon_results.json",
        "retained_input_count": len(retained),
        "abundance_safe_count": len(candidates),
        "excluded_count": len(excluded),
        "abundance_exclusion_policy": ABUNDANCE_EXCLUSION,
        "boundary_note": (
            "This abundance-safe v1 subset excludes explicit scarcity-heavy elements, "
            "but it is still a heuristic deployment screen rather than a full "
            "global resource model."
        ),
        "top_candidates_by_pore_space": candidates[:25],
        "candidates": candidates,
        "excluded_candidates": excluded,
    }


def main():
    artifact = build_artifact()
    print("--- Abundance-Safe Carbon Subset v1 ---")
    print(f"Retained Input Count:      {artifact['retained_input_count']}")
    print(f"Abundance-Safe Count:      {artifact['abundance_safe_count']}")
    print(f"Excluded Scarcity Count:   {artifact['excluded_count']}")
    print("")
    print(f"{'Rank':<5} {'Formula':<24} {'Pore Space':<12} {'Stability':<10}")
    print("-" * 70)
    for index, row in enumerate(artifact["top_candidates_by_pore_space"][:10], start=1):
        print(
            f"{index:<5} {row['formula']:<24} {row['pore_space']:<12.2f} "
            f"{row['stability']:<10.3f}"
        )

    write_json_output(OUTPUT_PATH, artifact)
    print("")
    print(f"Saved Artifact:            {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
