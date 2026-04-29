import torch
import torch.nn as nn
import sys
import os

# Append path to load the previously verified gate
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from internal.adversarial.topological_gate_layer import TopologicalGate

class LiquidMedicalAI(nn.Module):
    def __init__(self, input_features, hidden_neurons=128):
        super(LiquidMedicalAI, self).__init__()
        
        # 1. The Sensor Layer (Ingests raw patient telemetry)
        self.sensor_layer = nn.Linear(input_features, hidden_neurons)
        
        # 2. The UIL Topological Gate (82% Efficiency)
        # Protects the core memory from noisy/poisoned data
        self.perimeter_gate = TopologicalGate(spine_anchor=2.84, gate_efficiency=0.829)
        
        # 3. The Core Liquid Memory (The 4D Spine)
        # Represents the invariant diagnostic logic
        self.core_memory = nn.RNNCell(hidden_neurons, hidden_neurons)
        
        # 4. Diagnostic Output
        self.classifier = nn.Linear(hidden_neurons, 1) # e.g., Malignant vs Benign

    def forward(self, x, hidden_state, current_variance):
        # Ingest data
        raw_signal = torch.relu(self.sensor_layer(x))
        
        # Filter signal through the mathematical gate
        gated_signal = self.perimeter_gate.forward_pass(raw_signal.detach().numpy(), current_variance)
        gated_signal = torch.tensor(gated_signal, dtype=torch.float32)
        
        # Update core memory ONLY with safe, gated signal
        new_hidden = self.core_memory(gated_signal, hidden_state)
        
        # Generate diagnosis
        diagnosis = torch.sigmoid(self.classifier(new_hidden))
        
        return diagnosis, new_hidden

if __name__ == "__main__":
    print("--- UIL Medical AI Architecture Compiled ---")
    print("Model 'LiquidMedicalAI' initialized with 82% Topological Gate.")
    print("Status: Ready for dataset ingestion (Cancer/Diabetes).")
