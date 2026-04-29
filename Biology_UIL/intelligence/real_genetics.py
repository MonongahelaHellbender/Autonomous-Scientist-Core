import pandas as pd
import numpy as np
from sklearn.datasets import load_breast_cancer

def analyze_real_biological_data():
    print("--- UIL Biological Intelligence: Real Biological Invariants ---")
    
    # 1. Load real-world dataset
    data_bundle = load_breast_cancer()
    df = pd.DataFrame(data_bundle.data, columns=data_bundle.feature_names)
    
    print(f"Dataset Loaded: {len(df)} samples, {len(df.columns)} biological features.")
    
    # 2. Calculate Invariance Metrics
    # CV = Standard Deviation / Mean
    mean_signal = df.mean()
    std_noise = df.std()
    cv = std_noise / mean_signal
    
    # 3. Rank Features by Invariance
    invariants = pd.DataFrame({
        'Biological_Feature': cv.index,
        'Variability_CV': cv.values,
        'Mean_Value': mean_signal.values
    }).sort_values(by='Variability_CV')

    # 4. Output Results
    print("\n=== TOP 5 BIOLOGICAL INVARIANTS (STABLE STRUCTURES) ===")
    print(invariants.head(5).to_string(index=False))
    
    print("\n=== TOP 5 VARIABLE FEATURES (ADAPTIVE/SENSITIVE) ===")
    print(invariants.tail(5).to_string(index=False))
    
    # UIL Logic Pass
    threshold = 0.20
    stable_features = invariants[invariants['Variability_CV'] < threshold]
    print(f"\n[UIL VERDICT] Identified {len(stable_features)} invariants below {threshold} CV.")
    print("These features represent the geometric 'Spine' of the biological system.")

if __name__ == "__main__":
    analyze_real_biological_data()
