import pandas as pd
import numpy as np
from sklearn.datasets import load_breast_cancer

def run_composite_validation():
    print("--- UIL Quality Control: Composite Ratio Validation ---")
    
    data_bundle = load_breast_cancer()
    df = pd.DataFrame(data_bundle.data, columns=data_bundle.feature_names)
    
    # Define a Composite Feature: Symmetry / Smoothness
    df['composite_ratio'] = df['mean symmetry'] / df['mean smoothness']
    target = 'composite_ratio'
    
    jackknife_cvs = []
    for i in range(len(df)):
        resampled_df = df.drop(df.index[i])
        cv = resampled_df[target].std() / resampled_df[target].mean()
        jackknife_cvs.append(cv)
    
    std_jack_cv = np.std(jackknife_cvs)
    print(f"Composite Feature: Symmetry / Smoothness")
    print(f"Jackknife Std Dev: {std_jack_cv:.6e}")

    if std_jack_cv < 1e-4:
        print("\n[VERDICT] SUCCESS: Composite Ratio is a ROBUST Invariant.")
    else:
        print("\n[VERDICT] FAILURE: Still vulnerable to noise.")

if __name__ == "__main__":
    run_composite_validation()
