import torch
import torch.nn as nn
import sys
import os

# Load our synchronized gate
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from internal.adversarial.topological_gate_layer import TopologicalGate

class GatedVisionAI(nn.Module):
    def __init__(self, hidden_dim=256):
        super(GatedVisionAI, self).__init__()
        
        # 1. Vision Backbone (Extracts patterns from microscope pixels)
        self.backbone = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Flatten()
        )
        
        # 2. The UIL Gate (Now at 82.9% efficiency)
        self.gate = TopologicalGate(spine_anchor=2.84, gate_efficiency=0.829)
        
        # 3. Decision Core
        self.decision_core = nn.Linear(32 * 112 * 112, hidden_dim) # Assuming 224x224 input
        self.classifier = nn.Linear(hidden_dim, 1)

    def forward(self, x, current_variance):
        # Extract features
        features = self.backbone(x)
        
        # UIL Protection: Filter the feature map before the decision
        gated_features = self.gate.forward_pass(features.detach().numpy(), current_variance)
        gated_features = torch.tensor(gated_features, dtype=torch.float32)
        
        # Decision
        hidden = torch.relu(self.decision_core(gated_features))
        return torch.sigmoid(self.classifier(hidden))

if __name__ == "__main__":
    print("--- UIL Gated Vision AI Compiled ---")
    print("Ready for Histopathology Scaling. Gate efficiency locked at 82.9%.")
