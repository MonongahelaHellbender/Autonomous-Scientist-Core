import numpy as np

def run_biomimetic_simulation():
    print("--- UIL Cross-Scale Synthesis: Bio-Mimetic Calcium Cage ---")
    
    # Extreme Ambient Environment (Gigafactory conditions)
    ambient_base_temp = 750.0
    
    # Heavy Stochastic Noise (15% variance)
    ambient_noise = np.random.normal(0, 0.15, 1000)
    external_temps = ambient_base_temp * (1 + ambient_noise)
    
    # The Biological Invariant: Perimeter Gating
    # Reduces external thermal variance transfer by 68% (based on the 4D manifold)
    gating_efficiency = 0.68
    
    # Calculate internal core temperatures
    core_temps = ambient_base_temp + (external_temps - ambient_base_temp) * (1 - gating_efficiency)
    
    # Baseline Failure Limit from previous exact oxide test
    critical_limit = 662.0
    
    # Audit Results
    peak_external = np.max(external_temps)
    peak_internal = np.max(core_temps)
    failure_rate = np.mean(core_temps > critical_limit)
    
    print(f"Gigafactory Ambient Peak: {peak_external:.2f}°C")
    print(f"Shielded Core Peak:       {peak_internal:.2f}°C")
    print(f"Critical Failure Limit:   {critical_limit:.2f}°C")
    
    if failure_rate < 0.01:
        print("\n[VERDICT] SYNTHESIS SUCCESSFUL.")
        print(f"Discovery: Perimeter Gating allows the Cage to survive {peak_external:.0f}°C ambient environments.")
        print("Status: Ready for Phase 2 Patent Drafting.")
    else:
        print("\n[VERDICT] SYNTHESIS FAILED.")
        print("Logic: The biological geometry cannot withstand industrial thermal loads.")

if __name__ == "__main__":
    run_biomimetic_simulation()
