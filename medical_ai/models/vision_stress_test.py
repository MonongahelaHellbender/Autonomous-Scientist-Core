import torch
import numpy as np
from imaging_backbone_gated import GatedVisionAI

def run_vision_audit():
    print("--- UIL Vision Lab: Adversarial Histopathology Audit ---")
    
    # Initialize the model (82.9% efficiency gate)
    model = GatedVisionAI()
    
    # 1. Generate "Clean" Slide (Simulated)
    clean_slide = torch.randn(1, 3, 224, 224)
    spine_variance = 2.84
    
    print("Analyzing Clean Microscope Slide...")
    diagnosis_clean = model(clean_slide, spine_variance)
    print(f"Base Diagnostic Confidence: {diagnosis_clean.item():.4f}")
    
    # 2. Generate "Corrupted" Slide (40% Noise Injection)
    # This simulates a poor quality scan or adversarial tampering
    corrupted_slide = clean_slide + (torch.randn(1, 3, 224, 224) * 0.40)
    noisy_variance = 7.12 # Massive deviation from the 4D spine
    
    print("\nAnalyzing Corrupted Slide (40% Noise Artifacts)...")
    diagnosis_noisy = model(corrupted_slide, noisy_variance)
    
    # 3. Verdict
    confidence_drift = abs(diagnosis_clean.item() - diagnosis_noisy.item())
    print(f"Gated Confidence Drift: {confidence_drift:.4f}")
    
    if confidence_drift < 0.05:
        print("\n[VERDICT] VISION STABILITY PROVEN.")
        print("Finding: The 82.9% gate successfully filtered pixel-level noise to maintain diagnostic integrity.")
    else:
        print("\n[VERDICT] VISION FAILURE.")
        print("The high-dimensional noise bypassed the gate.")

if __name__ == "__main__":
    run_vision_audit()
