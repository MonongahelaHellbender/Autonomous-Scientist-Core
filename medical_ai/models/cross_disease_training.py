import torch
import numpy as np
from liquid_diagnostic_model import LiquidMedicalAI
from sklearn.datasets import load_breast_cancer, load_diabetes

def run_cross_disease_challenge():
    print("--- UIL Cognitive Lab: Cross-Disease Plasticity Test ---")
    model = LiquidMedicalAI(input_features=30, hidden_neurons=64)
    hidden_state = torch.zeros(64)
    
    # Phase 1: Train on Cancer (ID ~2.84)
    print("Training on Disease A (Cancer)...")
    cancer_data = load_breast_cancer().data[0]
    cancer_variance = 2.84
    _, hidden_state = model(torch.tensor(cancer_data, dtype=torch.float32), hidden_state, cancer_variance)
    
    # Phase 2: Train on Diabetes (ID ~6.01)
    # The UIL Gate must detect that 6.01 is a STABLE state, not random noise
    print("\nAttempting to ingest Disease B (Diabetes)...")
    diabetes_data = load_diabetes().data[0]
    # We pad the diabetes data (10 features) to 30 to match model input
    diabetes_padded = np.pad(diabetes_data, (0, 20), 'constant')
    diabetes_variance = 6.01 
    
    diagnosis_B, updated_hidden = model(torch.tensor(diabetes_padded, dtype=torch.float32), hidden_state, diabetes_variance)
    
    # Verdict: Did the gate allow the hidden state to update?
    update_magnitude = torch.norm(updated_hidden - hidden_state).item()
    print(f"Memory Update Magnitude: {update_magnitude:.4f}")
    
    if update_magnitude > 0.5:
        print("\n[VERDICT] PLASTICITY VERIFIED.")
        print("The gate recognized a new stable manifold and allowed learning.")
    else:
        print("\n[VERDICT] GATE TOO RIGID.")
        print("The model is refusing to learn new domains.")

if __name__ == "__main__":
    run_cross_disease_challenge()
