import pandas as pd
import numpy as np
from sklearn.datasets import load_breast_cancer, load_diabetes

def run_cross_audit():
    print("--- UIL Quality Control: Cross-Dataset Invariance Audit ---")
    
    # Load Dataset A (Cancer)
    cancer = load_breast_cancer()
    df_a = pd.DataFrame(cancer.data, columns=cancer.feature_names)
    
    # Load Dataset B (Diabetes)
    diabetes = load_diabetes()
    df_b = pd.DataFrame(diabetes.data, columns=diabetes.feature_names)
    
    # Calculate Stability across both
    cv_a = df_a.std() / df_a.mean()
    cv_b = df_b.std() / df_b.mean()
    
    print(f"Dataset A (Cancer) Mean Stability:   {cv_a.mean():.4f}")
    print(f"Dataset B (Diabetes) Mean Stability: {cv_b.mean():.4f}")
    
    # Conclusion: Is stability a universal biological trait?
    stability_diff = abs(cv_a.mean() - cv_b.mean())
    print(f"Variance between Domains: {stability_diff:.4f}")
    
    if stability_diff < 0.10:
        print("\n[VERDICT] IMPROVEMENT SUCCESS: Biological Stability is Domain-Agnostic.")
    else:
        print("\n[VERDICT] AUDIT FAILED: Biological 'Laws' are specific to the disease state.")

if __name__ == "__main__":
    run_cross_audit()
