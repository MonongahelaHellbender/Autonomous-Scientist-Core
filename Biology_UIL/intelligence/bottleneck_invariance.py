import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.datasets import load_breast_cancer

def analyze_information_bottleneck():
    print("--- UIL Biological Intelligence: Information Bottleneck ---")
    
    # 1. Load Data
    data = load_breast_cancer()
    df = pd.DataFrame(data.data, columns=data.feature_names)
    
    # 2. Normalize (Standardize to prevent scale bias)
    df_norm = (df - df.mean()) / df.std()
    
    # 3. Apply PCA
    pca = PCA()
    pca.fit(df_norm)
    
    # 4. Calculate Explained Variance (The Bottleneck)
    variance_ratio = pca.explained_variance_ratio_
    cumulative_variance = np.cumsum(variance_ratio)
    
    # How many components to reach 90% of the truth?
    bottleneck_size = np.argmax(cumulative_variance >= 0.90) + 1
    compression_ratio = bottleneck_size / len(df.columns)
    
    print(f"\n=== BOTTLENECK REPORT ===")
    print(f"Total Dimensions:      {len(df.columns)}")
    print(f"Dimensions for 90% Truth: {bottleneck_size}")
    print(f"Information Compression:  {compression_ratio:.2%}")
    print(f"Primary Component Signal: {variance_ratio[0]:.4f}")
    
    # 5. UIL Verdict
    # If the system can be compressed by more than 80%, a bottleneck invariant exists.
    if compression_ratio < 0.20:
        print("\n[VERDICT] SUCCESS: Information Bottleneck Discovered.")
        print(f"Logic: Biology preserves information through extreme compression.")
    else:
        print("\n[VERDICT] FAILURE: Information is too diffuse. No bottleneck found.")

if __name__ == "__main__":
    analyze_information_bottleneck()
