"""
Brain Ensemble — meta-controller that routes to and blends multiple brains.
===========================================================================

After each brain trains independently, the ensemble learns HOW to combine
their outputs. This mimics what evolution does at the population level:
different species find different solutions, natural selection picks winners.

Modes:
  1. Voting — each brain produces predictions, weighted average
  2. Routing — a learned gate picks which brain(s) to trust per timestep
  3. Stacking — brains' hidden states concatenated, a meta-network decides

The ensemble can discover that:
  - The insect brain is best for fast pattern detection
  - The human brain excels at long-range dependencies
  - The dolphin brain handles alternating patterns
  - etc.

This is the "process together on a larger level" the user envisioned.
"""
from __future__ import annotations

import torch
from torch import nn
from typing import Dict, List, Optional


class BrainEnsemble(nn.Module):
    """
    Meta-controller that combines multiple trained brain architectures.

    Each brain runs independently, then a learned routing network
    decides how to blend their outputs at each timestep.
    """

    def __init__(self, brains: Dict[str, nn.Module], hidden_size: int = 128,
                 n_properties: int = 2, freeze_brains: bool = True):
        super().__init__()
        self.hidden_size = hidden_size
        self.brain_names = sorted(brains.keys())
        self.n_brains = len(self.brain_names)

        # Store brains as a ModuleDict so parameters are tracked
        self.brains = nn.ModuleDict(brains)

        # Optionally freeze individual brains (only train the router)
        if freeze_brains:
            for brain in self.brains.values():
                for p in brain.parameters():
                    p.requires_grad = False

        # Router — takes concatenated hidden states, outputs per-brain weights
        # Input: concatenation of all brains' hidden outputs at each timestep
        router_in = hidden_size * self.n_brains
        self.router = nn.Sequential(
            nn.Linear(router_in, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.GELU(),
            nn.Linear(hidden_size, self.n_brains),
        )

        # Meta-integration — projects blended signal to unified hidden
        self.meta_proj = nn.Linear(hidden_size, hidden_size)
        self.meta_norm = nn.LayerNorm(hidden_size)

        # Output heads (trained fresh on ensemble output)
        self.next_step_head = nn.Sequential(
            nn.LayerNorm(hidden_size), nn.Linear(hidden_size, 1))
        self.anomaly_head = nn.Sequential(
            nn.LayerNorm(hidden_size), nn.Linear(hidden_size, 1), nn.Sigmoid())
        self.property_head = nn.Sequential(
            nn.LayerNorm(hidden_size), nn.Linear(hidden_size, hidden_size // 2),
            nn.GELU(), nn.Linear(hidden_size // 2, n_properties))

    def forward(self, x, **kwargs):
        B, T, _ = x.shape

        # Run all brains independently
        brain_outputs = {}
        for name in self.brain_names:
            brain_outputs[name] = self.brains[name](x, **kwargs)

        # Collect hidden states from all brains [B, T, H] each
        all_hidden = []
        for name in self.brain_names:
            h = brain_outputs[name]["hidden"]  # [B, T, H_brain]
            # Project to common size if needed
            if h.shape[-1] != self.hidden_size:
                # Pad or truncate
                if h.shape[-1] < self.hidden_size:
                    pad = torch.zeros(B, T, self.hidden_size - h.shape[-1], device=x.device)
                    h = torch.cat([h, pad], dim=-1)
                else:
                    h = h[:, :, :self.hidden_size]
            all_hidden.append(h)

        # Concatenate for routing
        concat_hidden = torch.cat(all_hidden, dim=-1)  # [B, T, H * n_brains]

        # Router produces per-brain weights at each timestep
        weights = torch.softmax(self.router(concat_hidden), dim=-1)  # [B, T, n_brains]

        # Weighted blend
        stacked = torch.stack(all_hidden, dim=-1)  # [B, T, H, n_brains]
        blended = (stacked * weights.unsqueeze(2)).sum(dim=-1)  # [B, T, H]

        # Meta-integration
        hidden = self.meta_norm(self.meta_proj(blended))

        # Output heads
        predictions = self.next_step_head(hidden[:, :-1, :])
        anomaly_score = self.anomaly_head(hidden).squeeze(-1)
        surprise = ((predictions - x[:, 1:, :]) ** 2).mean(dim=-1)
        properties = self.property_head(hidden[:, -1, :])

        # Collect per-brain routing weights for analysis
        avg_weights = weights.detach().mean(dim=(0, 1))  # [n_brains]
        routing_info = {name: float(avg_weights[i]) for i, name in enumerate(self.brain_names)}

        return {
            "predictions": predictions, "hidden": hidden,
            "anomaly_score": anomaly_score, "surprise": surprise,
            "properties": properties,
            "routing_weights": routing_info,
            "per_brain_outputs": brain_outputs,
            "weight_timeline": weights.detach(),  # [B, T, n_brains] for visualization
        }

    def param_count(self):
        counts = {}
        for name in self.brain_names:
            counts[name] = sum(p.numel() for p in self.brains[name].parameters())
        counts["router"] = sum(p.numel() for p in self.router.parameters())
        counts["meta"] = (sum(p.numel() for p in self.meta_proj.parameters()) +
                          sum(p.numel() for p in self.meta_norm.parameters()))
        counts["heads"] = (sum(p.numel() for p in self.next_step_head.parameters()) +
                           sum(p.numel() for p in self.anomaly_head.parameters()) +
                           sum(p.numel() for p in self.property_head.parameters()))
        counts["total"] = sum(p.numel() for p in self.parameters())
        counts["trainable"] = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return counts
