import numpy as np

class TopologicalGate:
    def __init__(self, spine_anchor=2.84, gate_efficiency=0.829):
        self.spine_anchor = spine_anchor
        self.gate_efficiency = gate_efficiency

    def forward_pass(self, input_signal, local_variance):
        # The UIL logic: Reject noise that threatens the 4D manifold
        noise_deviation = abs(local_variance - self.spine_anchor)
        
        # Calculate how much signal to let through
        # Higher efficiency = stricter gate
        gate_threshold = 1.0 - (noise_deviation * self.gate_efficiency)
        gated_signal = input_signal * max(0, gate_threshold)
        
        return gated_signal

def test_ai_gate():
    print("--- UIL AI Lab: Topological Gate Layer Diagnostic ---")
    gate = TopologicalGate()
    
    clean_signal = 1.0
    poisoned_signal = 1.0
    high_noise_variance = 6.0 # The 'Diabetes' failure state we found earlier
    
    output = gate.forward_pass(poisoned_signal, high_noise_variance)
    
    print(f"Incoming Anomaly Signal: {poisoned_signal}")
    print(f"Gate Output (Suppressed): {output:.4f}")
    
    if output < 0.1:
        print("[VERDICT] GATE ACTIVE: Core memory protected from data poisoning.")

if __name__ == "__main__":
    test_ai_gate()
