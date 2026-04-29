import numpy as np

def audit_pore_utility():
    print("--- UIL Materials Lab: Pore Space Utility Audit ---")
    
    # Baseline Pore Space for pure CaC2
    baseline_pores = 18.50 
    
    # Silicon Doping Concentration (mol/cm^3)
    si_doping = 0.0343
    
    # Mathematical Penalty: Doping reduces volume by a factor of atomic radius displacement
    # UIL Model: Volume_Final = Volume_Base * e^(-Doping * constant)
    volometric_penalty_constant = 1.12
    final_pores = baseline_pores * np.exp(-si_doping * volometric_penalty_constant)
    
    target_metric = 17.82
    
    print(f"Silicon Doping Level:  {si_doping} mol/cm^3")
    print(f"Calculated Pore Space: {final_pores:.2f} Å³/atom")
    print(f"Target Industry Spec: {target_metric} Å³/atom")
    
    if final_pores >= target_metric:
        print("\n[VERDICT] UTILITY PRESERVED.")
        print("The 82% efficiency gate is achieved without sacrificing carbon capture capacity.")
    else:
        print("\n[VERDICT] OVER-DOPED.")
        print(f"Utility loss of {baseline_pores - final_pores:.2f} Å³ exceeds tolerance.")

if __name__ == "__main__":
    audit_pore_utility()
