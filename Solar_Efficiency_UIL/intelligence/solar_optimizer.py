import json

def find_best_solar():
    print("INTELLIGENCE LAYER: Optimizing for Non-Toxic Efficiency...")
    
    with open("ingestion/raw_solar_data.json", "r") as f:
        data = json.load(f)

    # Filter for non-toxic winners only
    winners = [d for d in data if not d['is_toxic']]
    
    # Sort by Stability (lowest formation energy)
    winners.sort(key=lambda x: x['stability'])

    print(f"\n--- TOP NON-TOXIC SOLAR DISCOVERIES ---")
    print(f"{'Formula':<15} | {'Band Gap':<10} | {'Stability'}")
    print("-" * 45)
    for w in winners[:5]:
        print(f"{w['formula']:<15} | {w['band_gap']:<10} eV | {w['stability']} eV")

if __name__ == "__main__":
    find_best_solar()
