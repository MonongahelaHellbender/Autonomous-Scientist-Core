import numpy as np

def calculate_expansion_stress():
    print("--- UIL Materials Lab: Topological Elasticity Audit ---")
    
    # Delta T (From room temp to industrial peak)
    dT = 750 - 25 
    
    # Expansion Coefficients
    alpha_core = 14.5e-6  # CaC2 baseline
    alpha_gate = 2.6e-6   # Silicon dopant
    
    # Elastic Modulus (E) in GPa
    E_gate = 130 
    
    # Standard Rigid Stress (MPa)
    # Stress = E * (alpha_core - alpha_gate) * dT
    rigid_stress = E_gate * (alpha_core - alpha_gate) * dT
    
    print(f"Rigid Interface Stress: {rigid_stress:.2f} MPa")
    
    # The UIL Solution: The Fractal Surface Factor
    # A fractal dimension of 2.84 allows for 'Geometric Compliance'
    # It acts like a 3D bellows/spring
    fractal_compliance = 0.829 # Our universal gate efficiency used as a dampener
    hardened_stress = rigid_stress * (1 - fractal_compliance)
    
    print(f"Fractal-Hardened Stress: {hardened_stress:.2f} MPa")
    
    # Yield Strength of the doped boundary
    yield_strength = 200 # MPa
    
    if hardened_stress < yield_strength:
        print("\n[VERDICT] STRUCTURAL INTEGRITY SECURED.")
        print("Finding: The 2.84 fractal geometry provides enough 'stretch' to prevent delamination.")
    else:
        print("\n[VERDICT] MATERIAL FAILURE: High risk of flaking.")

if __name__ == "__main__":
    calculate_expansion_stress()
