import pandas as pd
import numpy as np
from sklearn.datasets import load_breast_cancer

def run_jackknife_validation():
    print("--- UIL Quality Control: Jackknife Invariant Validation ---")
    
    # 1. Load Data
    data_bundle = load_breast_cancer()
    df = pd.DataFrame(data_bundle.data, columns=data_bundle.feature_names)
    target_feature = 'mean fractal dimension'
    
    print(f"Targeting Feature: {target_feature}")
    print(f"Original CV: {df[target_feature].std() / df[target_feature].mean():.6f}")

    # 2. Jackknife Resampling
    # Remove one sample at a time and recalculate CV
    jackknife_cvs = []
    for i in range(len(df)):
        resampled_df = df.drop(df.index[i])
        cv = resampled_df[target_feature].std() / resampled_df[target_feature].mean()
        jackknife_cvs.append(cv)
    
    # 3. Statistical Analysis of Results
    mean_jack_cv = np.mean(jackknife_cvs)
    std_jack_cv = np.std(jackknife_cvs)
    bias = (len(df) - 1) * (mean_jack_cv - (df[target_feature].std() / df[target_feature].mean()))
    
    print("\n=== ADVERSARIAL STATISTICAL REPORT ===")
    print(f"Resampling Iterations: {len(jackknife_cvs)}")
    print(f"Mean Jackknife CV:    {mean_jack_cv:.6f}")
    print(f"Jackknife Std Dev:    {std_jack_cv:.6e}")
    print(f"Calculated Bias:      {bias:.6e}")

    # 4. Final Verdict
    if std_jack_cv < 1e-4:
        print("\n[VERDICT] ROBUST: Invariant is independent of individual samples.")
    else:
        print("\n[VERDICT] VULNERABLE: Invariant is sensitive to outliers.")

if __name__ == "__main__":
    run_jackknife_validation()
