import json

def generate_global_ledger():
    total_dividend = 987.0e9 # $987 Billion
    
    allocations = {
        "Infrastructure_Maintenance": 0.40,
        "Prairie_Restoration_Texas": 0.15,
        "Amazonian_Protection_Vision": 0.15,
        "Saharan_Solar_Expansion": 0.20,
        "Citizen_Climate_Dividend": 0.10
    }
    
    print("--- UIL Global Governor: Dividend Allocation Ledger ---")
    final_report = {}
    for sector, pct in allocations.items():
        amount = total_dividend * pct
        final_report[sector] = f"${amount/1e9:.2f} Billion"
        print(f"{sector:.<30} {final_report[sector]}")
    
    with open("internal/governor/dividend_final_allocation.json", "w") as f:
        json.dump(final_report, f, indent=4)
        
    print("\n[SUCCESS] Global Ledger locked. Economic entropy neutralized.")

if __name__ == "__main__":
    generate_global_ledger()
