import numpy as np

def find_tipping_point():
    print("--- UIL Physics Fix: Searching for Viable Gating Efficiency ---")
    
    ambient_base = 750.0
    natural_core_baseline = 582.0 
    critical_limit = 662.0
    noise_level = 0.15  # 15% noise
    
    # Generate the harsh external gigafactory environment
    noise_vector = np.random.normal(0, noise_level, 5000)
    external_temps = ambient_base * (1 + noise_vector)
    
    print(f"Testing survival for Ambient Base: {ambient_base}°C")
    print(f"Goal: Find Efficiency where Failure Rate < 1%\n")
    
    # Test efficiencies from 10% to 99%
    for eff in np.arange(0.10, 1.0, 0.01):
        # The gate insulates the core's natural baseline from the harsh outside temps
        core_temps = natural_core_baseline + (external_temps - natural_core_baseline) * (1 - eff)
        failure_rate = np.mean(core_temps > critical_limit)
        
        if failure_rate < 0.01:
            print(f"[FOUND] Efficiency: {eff:.2f} | Failure Rate: {failure_rate:.2%}")
            print(f"VERDICT: To survive 750°C, the bio-mimetic gate must be {eff*100:.0f}% efficient.")
            return eff
            
    print("[FAILED] No survivable efficiency found.")
    return None

if __name__ == "__main__":
    find_tipping_point()
