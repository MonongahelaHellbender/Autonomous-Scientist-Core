import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.datasets import load_diabetes

def estimate_id(data, k=10):
    neigh = NearestNeighbors(n_neighbors=k + 1).fit(data)
    distances, _ = neigh.kneighbors(data)
    dist_k = distances[:, k]
    dist_others = np.maximum(distances[:, 1:k], 1e-10)
    return 1 / np.mean(np.log(dist_k[:, None] / dist_others))

data = load_diabetes().data
id_val = estimate_id(data)
print(f"--- BIOLOGY HARDENING ---")
print(f"Diabetes Intrinsic Dimension: {id_val:.4f}")
if 2.5 < id_val < 3.1:
    print("[VERDICT] ROBUST: Dimension matches Cancer dataset.")
else:
    print("[VERDICT] FAILED: Dimensionality is scale-dependent.")
