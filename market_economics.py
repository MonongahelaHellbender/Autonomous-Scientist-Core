import json

# Current Market Prices (USD per kg - Approx)
PRICES = {
    "Li": 25.0,  # Lithium
    "S": 0.20,   # Sulfur
    "Si": 2.50,  # Silicon
    "P": 3.00,   # Phosphorus
    "Sn": 25.0,  # Tin
    "In": 600.0, # Indium (RARE/EXPENSIVE)
    "Cl": 0.15,  # Chlorine
    "I": 30.0    # Iodine
}

def calculate_market_viability():
    print("\nECONOMIC SCAN: Calculating Cost per Kilogram...")
    
    try:
        with open("physics_validated_candidates.json", "r") as f:
            candidates = json.load(f)
    except FileNotFoundError:
        print("Error: physics_validated_candidates.json not found. Run tunnel_physics.py first.")
        return

    print(f"{'Formula':<15} | {'Cost/kg':<10} | {'Verdict'}")
    print("-" * 50)

    for c in candidates:
        total_element_cost = 0
        # Calculate raw material cost based on existence of symbols
        for el, price in PRICES.items():
            if el in c['formula']:
                total_element_cost += price
        
        c['estimated_cost_usd_kg'] = round(total_element_cost, 2)
        
        if total_element_cost < 60:
            verdict = "MASS MARKET READY"
        elif total_element_cost < 150:
            verdict = "PREMIUM/EV READY"
        else:
            verdict = "LAB PROTOTYPE ONLY (TOO EXPENSIVE)"
            
        print(f"{c['formula']:<15} | ${total_element_cost:<9.2f} | {verdict}")

if __name__ == "__main__":
    calculate_market_viability()
