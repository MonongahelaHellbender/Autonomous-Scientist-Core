import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.datasets import load_breast_cancer

def estimate_intrinsic_dimension(data, k=5):
    # MLE estimator for intrinsic dimensionality
    neigh = NearestNeighbors(n_neighbors=k + 1).fit(data)
    distances, _ = neigh.kneighbors(data)
    # Distance to k-th neighbor vs distance to others
    dist_k = distances[:, k]
    dist_others = distances[:, 1:k]
    
    # Avoid log(0)
    dist_others = np.maximum(dist_others, 1e-10)
    
    inv_id = np.mean(np.log(dist_k[:, None] / dist_others))
    return 1 / inv_id

def run_id_audit():
    print("--- UIL Quality Control: Intrinsic Dimensionality Audit ---")
    data = load_breast_cancer().data
    
    # Test stability across different neighbor counts (k)
    id_estimates = []
    for k_val in [5, 10, 15, 20]:
        id_val = estimate_intrinsic_dimension(data, k=k_val)
        id_estimates.append(id_val)
        print(f"Neighbors (k={k_val:2d}): Intrinsic Dimension = {id_val:.4f}")
    
    id_stability = np.std(id_estimates) / np.mean(id_estimates)
    print(f"\nID Stability (CV): {id_stability:.4f}")
    
    if id_stability < 0.10:
        print("[RESULT] VERIFIED: Intrinsic Dimension is a ROBUST Invariant.")
    else:
        print("[RESULT] FAILED: Dimensionality is unstable.")

if __name__ == "__main__":
    run_id_audit()
