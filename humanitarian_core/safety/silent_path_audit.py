import numpy as np

def run_passage_audit():
    print("--- UIL Humanitarian Lab: Safe Passage Navigation ---")
    
    # 0.0 = Perfectly Quiet | 10.0 = Maximum Combat Noise (Explosions/Speed)
    # We represent 10 blocks of a city
    city_entropy_map = [0.2, 0.5, 9.1, 8.4, 0.3, 0.1, 7.8, 0.4, 0.2, 9.5]
    
    print("Scanning City Manifold for 0.13-Coherence Path...")
    
    safe_route = []
    
    for street_id, entropy in enumerate(city_entropy_map):
        # We apply the 82.9% Gate to see if the 'Ground Truth' of peace is visible
        # Residual Noise = Raw_Entropy * (1 - Gate_Efficiency)
        residual_noise = entropy * (1 - 0.829)
        
        # Check against Melissa's 0.13 Safety Floor
        if residual_noise <= 0.13:
            status = "COHERENT [Safe]"
            safe_route.append(street_id)
        else:
            status = "CHAOTIC  [Danger]"
            
        print(f"Block {street_id}: Entropy {entropy:.1f} | Gated Noise {residual_noise:.4f} -> {status}")

    print("\n--- NAVIGATION VERDICT ---")
    if safe_route:
        print(f"Recommended Silent Path: {safe_route}")
        print("Finding: The 2.84 Spine of civil stability is preserved in these blocks.")
    else:
        print("[WARNING] NO SAFE MANIFOLD DETECTED. SHELTER IN PLACE.")

if __name__ == "__main__":
    run_passage_audit()
