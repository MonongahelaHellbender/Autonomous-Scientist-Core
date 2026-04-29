import pandas as pd
import numpy as np
from sklearn.datasets import load_breast_cancer, load_diabetes

def run_robust_audit():
    print("--- UIL Quality Control: Robust Biological Audit ---")
    
    # Load Datasets
    d1 = load_breast_cancer(); df1 = pd.DataFrame(d1.data)
    d2 = load_diabetes(); df2 = pd.DataFrame(d2.data)
    
    # Logic Pass: Use Median Absolute Deviation (MAD) instead of Std Dev
    # This ignores zeros and outliers.
    def get_robust_stability(df):
        median = df.median()
        mad = (df - median).abs().median()
        # Filter out features where median is 0 to prevent explosion
        mad_filtered = mad[median != 0]
        median_filtered = median[median != 0]
        return (mad_filtered / median_filtered).mean()

    stability1 = get_robust_stability(df1)
    stability2 = get_robust_stability(df2)
    
    print(f"Dataset 1 Robust Stability: {stability1:.4f}")
    print(f"Dataset 2 Robust Stability: {stability2:.4f}")
    
    diff = abs(stability1 - stability2)
    print(f"Variance between Domains: {diff:.4f}")

    if diff < 0.20:
        print("\n[VERDICT] IMPROVEMENT SUCCESS: Found Stable Biological Baseline.")
    else:
        print("\n[VERDICT] AUDIT FAILED: Biological noise is too inconsistent.")

if __name__ == "__main__":
    run_robust_audit()
