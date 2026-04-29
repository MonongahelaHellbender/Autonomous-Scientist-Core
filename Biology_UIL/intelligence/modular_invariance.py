import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.datasets import load_breast_cancer

def analyze_modular_invariance():
    print("--- UIL Biological Intelligence: Modular Invariance ---")
    
    # 1. Load Data
    data_bundle = load_breast_cancer()
    df = pd.DataFrame(data_bundle.data, columns=data_bundle.feature_names)
    
    # 2. Cluster the Features (Transpose the DF to group features, not samples)
    # We ask: Which features consistently group together?
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(df.T)
    
    feature_groups = pd.DataFrame({
        'Feature': df.columns,
        'Module_ID': clusters
    }).sort_values(by='Module_ID')
    
    print("\n=== FUNCTIONAL BIOLOGICAL MODULES ===")
    for i in range(3):
        module = feature_groups[feature_groups['Module_ID'] == i]['Feature'].tolist()
        print(f"Module {i} Size: {len(module)} features.")
        print(f"Sample Features: {module[:3]}...")

    # 3. Quality Control: Module Stability
    # A Module is an Invariant if the features within it have high mutual correlation
    module_0_corr = df[feature_groups[feature_groups['Module_ID'] == 0]['Feature']].corr().mean().mean()
    
    print(f"\nModule 0 Internal Cohesion: {module_0_corr:.4f}")
    
    if module_0_corr > 0.70:
        print("\n[VERDICT] SUCCESS: Modular Invariant Detected.")
        print("Conclusion: Biology uses 'Islands of Stability' rather than a single spine.")
    else:
        print("\n[VERDICT] FAILURE: System is truly chaotic.")

if __name__ == "__main__":
    analyze_modular_invariance()
