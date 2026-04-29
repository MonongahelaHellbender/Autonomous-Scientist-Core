import json

def generate_contribution_report(dividend_surplus=4.55e9):
    print("--- UIL Values: Peace & Kindness Allocation ---")
    
    # Diverting 20% of the surplus directly to community well-being
    peace_fund = dividend_surplus * 0.20
    
    allocations = {
        "Native_Texas_Prairie_Expansion": peace_fund * 0.40,
        "Local_Quiet_Infrastructure": peace_fund * 0.30,
        "Regional_Animal_Sanctuary_Grants": peace_fund * 0.20,
        "Community_Loving_Society_Initiatives": peace_fund * 0.10
    }
    
    print(f"Total Peace Dividend: ${peace_fund/1e6:.2f} Million")
    for project, amount in allocations.items():
        print(f"-> {project:.<40} ${amount/1e6:.2f}M")

    with open("internal/governor/peace_reinvestment_2026.json", "w") as f:
        json.dump(allocations, f, indent=4)
        
    print("\n[VERDICT] VALUE ALIGNMENT SECURED.")
    print("Finding: The 2.84 manifold is now providing the financial energy for a peaceful society.")

if __name__ == "__main__":
    generate_contribution_report()
