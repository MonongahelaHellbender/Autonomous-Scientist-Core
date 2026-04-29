import numpy as np

def optimize_gate():
    print("--- UIL Materials Lab: Critical Convergence Optimization ---")
    
    baseline_pores = 18.50
    target_pores = 17.82
    penalty_k = 1.12
    
    # 1. Solve for Max Dopant (D): 17.82 = 18.50 * e^(-D * 1.12)
    max_dopant = -np.log(target_pores / baseline_pores) / penalty_k
    
    # 2. Calculate the resulting Gate Efficiency (eff)
    # Formula: D = e^((eff - 0.45) / 0.3) / 100
    new_efficiency = (np.log(max_dopant * 100) * 0.3) + 0.45
    
    print(f"Optimized Dopant Limit: {max_dopant:.5f} mol/cm^3")
    print(f"Resulting Gate Efficiency: {new_efficiency*100:.2f}%")
    
    # 3. Survival Check (750C baseline)
    ambient_base = 750.0
    natural_core = 582.0
    critical_limit = 662.0
    
    # Simulate core temp with the new efficiency
    # We use a 3-sigma peak for the worst-case noise (15% noise)
    peak_ambient = ambient_base * (1 + (0.15 * 3))
    peak_core = natural_core + (peak_ambient - natural_core) * (1 - new_efficiency)
    
    print(f"Worst-Case Peak Core Temp: {peak_core:.2f}°C")
    
    if peak_core < critical_limit:
        print("\n[VERDICT] CRITICAL CONVERGENCE ACHIEVED.")
        print(f"The {new_efficiency*100:.1f}% gate is thin enough for pores and thick enough for heat.")
    else:
        print("\n[VERDICT] PHYSICS MISMATCH.")
        print(f"Core hits {peak_core:.1f}°C. We must either lower the Gigafactory temp or find a new dopant.")

if __name__ == "__main__":
    optimize_gate()
