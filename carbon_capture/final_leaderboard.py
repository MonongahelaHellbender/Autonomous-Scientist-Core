import json

def generate_leaderboard():
    print("FINAL RANKING: Searching for the most porous SAFE carbon cages...")
    
    with open("carbon_capture/vetted_carbon_results.json", "r") as f:
        data = json.load(f)

    # Filter for only Approved materials
    safe_candidates = [d for d in data if d['final_verdict'] == "APPROVED"]
    
    # Sort by pore space
    safe_candidates.sort(key=lambda x: x['pore_space'], reverse=True)

    print(f"\n--- SAFE CARBON CAPTURE LEADERBOARD ---")
    print(f"{'Rank':<5} | {'Formula':<15} | {'Pore Space':<12}")
    print("-" * 40)
    
    for i, res in enumerate(safe_candidates[:5]):
        print(f"{i+1:<5} | {res['formula']:<15} | {res['pore_space']:<12} Å³/atom")

if __name__ == "__main__":
    generate_leaderboard()
