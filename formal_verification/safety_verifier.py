import sympy as sp

def verify_safety_epsilon():
    print("--- UIL Formal Verification: Compositional Safety ---")
    
    x = sp.symbols('x')
    epsilon = sp.symbols('epsilon')
    
    # 1. Define a "Safe" Discovery (Linear/Smooth): f(x) = x^2
    safe_discovery = x**2
    
    # 2. Define an "Unsafe" Discovery (Fractured/Explosive): f(x) = 1/x
    # (A tiny change near zero causes an infinite result)
    unsafe_discovery = 1/x
    
    def test_stability(func, name):
        print(f"\nTesting {name}: {func}")
        # Calculate the difference when we add a tiny epsilon
        diff = sp.simplify(func.subs(x, x + epsilon) - func)
        print(f"Sensitivity to change: {diff}")
        
        # Take the limit as epsilon goes to zero
        stability_limit = sp.limit(diff/epsilon, epsilon, 0)
        print(f"Stability Gradient: {stability_limit}")
        
        if stability_limit.is_finite:
            print(f"[RESULT] {name} is COMPOSITIONALLY SAFE.")
        else:
            print(f"[RESULT] {name} is UNSTABLE / DANGEROUS.")

    test_stability(safe_discovery, "Discovery A (Standard)")
    test_stability(unsafe_discovery, "Discovery B (High-Risk)")

if __name__ == "__main__":
    verify_safety_epsilon()
