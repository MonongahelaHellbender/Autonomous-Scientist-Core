import torch
import numpy as np

def check_matrix_health(weight_matrix, threshold=0.13):
    print("--- UIL Safety Lab: Weight Matrix Singularity Audit ---")
    
    # Calculate Singular Value Decomposition (SVD) to detect manifold collapse
    U, S, V = torch.svd(weight_matrix)
    
    spectral_norm = torch.max(S).item()
    coherence_score = (torch.max(S) / torch.min(S)).item()
    
    print(f"Spectral Norm: {spectral_norm:.4f}")
    print(f"Manifold Coherence: {coherence_score:.4f}")
    print(f"Safety Benchmark: {threshold}")

    if coherence_score > 50.0: 
        print("[WARNING] NEAR-SINGULARITY DETECTED.")
        return "TRIGGER_RESET"
    
    return "STABLE"

if __name__ == "__main__":
    # Test with a healthy 128-neuron matrix
    test_weights = torch.randn(128, 128)
    status = check_matrix_health(test_weights)
    print(f"Current System State: {status}")
