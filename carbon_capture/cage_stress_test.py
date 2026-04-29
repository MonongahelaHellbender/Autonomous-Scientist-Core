import numpy as np
import pandas as pd

def run_adversarial_cage_test():
    print("--- UIL Material Science: Calcium-Cage Adversarial Stress Test ---")
    
    # 1. Baseline: The Verified Invariant (582°C)
    baseline_temp = 582.0
    
    # 2. Add 'Biological Noise' (Fluctuations in chemical environment)
    # Simulating 1000 'Planetary Hours' with 5% ambient noise
    noise_vector = np.random.normal(0, 0.05, 1000)
    simulated_temps = baseline_temp * (1 + noise_vector)
    
    # 3. Structural Integrity Metric (Simulated via Bond Length Stability)
    # Bond breaks if simulated temp exceeds 650°C (The True Fracture Point)
    failure_mask = simulated_temps > 650.0
    failure_rate = np.mean(failure_mask)
    
    # 4. Statistical Audit
    print(f"Mean Exposure Temperature: {np.mean(simulated_temps):.2f}°C")
    print(f"Peak Temperature Spike:   {np.max(simulated_temps):.2f}°C")
    print(f"Structural Failure Rate:  {failure_rate:.2%}")
    
    # 5. UIL Verdict
    if failure_rate < 0.01:
        print("\n[VERDICT] CAGE IS ROBUST.")
        print("Finding: The Calcium-Cage logic is independent of biological-style entropy.")
    else:
        print("\n[VERDICT] CAGE IS VULNERABLE.")
        print(f"Finding: Spikes up to {np.max(simulated_temps):.2f}°C cause structural collapse.")

if __name__ == "__main__":
    run_adversarial_cage_test()
