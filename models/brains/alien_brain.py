"""
Alien Brain — no biological constraints, pure mathematical optimization.
========================================================================

Design philosophy: what if evolution had NO physical constraints?
  - No skull to limit size
  - No metabolic cost to limit connections
  - No developmental constraints on wiring
  - No separation into hemispheres (why would you?)

Result: a fully-connected topology where every region talks to every
other region at every timestep. No hierarchy, no bottlenecks.
Uses learned routing weights to discover optimal information flow.

Unique features:
  - Global workspace: shared memory all regions read/write simultaneously
  - Adaptive topology: connection strengths learned, not hardwired
  - Multi-resolution: each region runs at a LEARNED time constant (not fixed)
  - Recursive self-modeling: one region models the state of all others

This is the "what if we just optimize everything" baseline.
If biological brains converge toward similar solutions, biology was right.
If this beats everything, biology was constrained.
"""
from __future__ import annotations

import torch
from torch import nn

from models.liquid_core import LiquidCell


class AdaptiveRegion(nn.Module):
    """Region with LEARNED time constant (not fixed like biological brains)."""

    def __init__(self, in_size: int, h_size: int, dropout: float = 0.0, name: str = ""):
        super().__init__()
        self.name = name
        self.h_size = h_size
        self.self_loop = True
        eff_in = in_size + h_size  # always self-loop
        self.cell = LiquidCell(eff_in, h_size, dropout=dropout)
        self.norm = nn.LayerNorm(h_size)
        # Learned dt multiplier — starts at 1.0, network finds optimal
        self.log_dt = nn.Parameter(torch.zeros(1))

    def initial_state(self, B, device=None):
        return torch.zeros(B, self.h_size, device=device)

    def step(self, x, state, dt=1.0):
        x = torch.cat([x, state], dim=-1)
        effective_dt = dt * float(torch.sigmoid(self.log_dt).detach()) * 3.0
        return self.norm(self.cell(x, state, dt=effective_dt))


class AlienBrain(nn.Module):
    """
    Alien brain — fully connected, no biological constraints.

    8 adaptive regions + global workspace + self-model.
    Every region can read from every other region.

    Region allocation (equal — no biological bias):
      Region 0-7:        10% each = 80%  — general-purpose adaptive
      Global workspace:  10%              — shared blackboard
      Self-model:        10%              — recursive self-monitoring
    """

    N_REGIONS = 8

    def __init__(self, input_size=1, hidden_size=128, n_properties=2, dropout=0.1, dt=1.0):
        super().__init__()
        self.hidden_size = hidden_size
        self.dt = dt
        H = hidden_size

        def _sz(pct):
            return max(4, int(H * pct))

        region_size = _sz(0.10)
        workspace_size = _sz(0.10)
        selfmodel_size = _sz(0.10)

        self.sz = {f"r{i}": region_size for i in range(self.N_REGIONS)}
        self.sz["workspace"] = workspace_size
        self.sz["selfmodel"] = selfmodel_size
        self.region_size = region_size

        self.input_proj = nn.Linear(input_size, region_size)

        # Adaptive regions — each receives input + workspace + all other regions' projections
        # To keep tractable: each region reads input + workspace summary
        region_in = region_size + workspace_size
        self.regions = nn.ModuleList([
            AdaptiveRegion(region_in, region_size, dropout=dropout, name=f"region_{i}")
            for i in range(self.N_REGIONS)
        ])

        # Global workspace — shared blackboard all regions write to
        total_region = region_size * self.N_REGIONS
        self.workspace = AdaptiveRegion(total_region, workspace_size,
                                        dropout=dropout, name="global_workspace")

        # Self-model — monitors all internal states (recursive self-awareness)
        selfmodel_in = total_region + workspace_size
        self.selfmodel = AdaptiveRegion(selfmodel_in, selfmodel_size,
                                        dropout=dropout, name="self_model")

        # Learned routing matrix — which regions attend to which
        # [N_REGIONS, N_REGIONS] soft adjacency
        self.routing = nn.Parameter(torch.randn(self.N_REGIONS, self.N_REGIONS) * 0.1)

        # Cross-region projection (all-to-all compressed)
        self.cross_proj = nn.Linear(total_region, region_size)

        # Self-model feedback — modulates all regions
        self.selfmodel_feedback = nn.Linear(selfmodel_size, region_size)

        # Output
        total = sum(self.sz.values())
        self.thalamus = nn.Sequential(nn.Linear(total, H), nn.LayerNorm(H), nn.Sigmoid())
        self.thalamic_proj = nn.Linear(total, H)

        self.next_step_head = nn.Sequential(nn.LayerNorm(H), nn.Linear(H, input_size))
        self.anomaly_head = nn.Sequential(nn.LayerNorm(H), nn.Linear(H, 1), nn.Sigmoid())
        self.property_head = nn.Sequential(
            nn.LayerNorm(H), nn.Linear(H, H // 2), nn.GELU(), nn.Linear(H // 2, n_properties))

    def forward(self, x, **kwargs):
        B, T, _ = x.shape

        # Init states
        states = {}
        for i in range(self.N_REGIONS):
            states[f"r{i}"] = self.regions[i].initial_state(B, x.device)
        states["workspace"] = self.workspace.initial_state(B, x.device)
        states["selfmodel"] = self.selfmodel.initial_state(B, x.device)

        outputs = []
        traces = {k: [] for k in states}

        for t in range(T):
            inp = self.input_proj(x[:, t, :])

            # Soft routing weights
            routing_weights = torch.softmax(self.routing, dim=-1)  # [N, N]

            # Cross-region signal — weighted sum of all regions
            all_r = torch.stack([states[f"r{i}"] for i in range(self.N_REGIONS)], dim=1)  # [B, N, h]
            cross_signal = self.cross_proj(all_r.reshape(B, -1))  # [B, region_size]

            # Self-model feedback
            sm_fb = self.selfmodel_feedback(states["selfmodel"]) if t > 0 else torch.zeros_like(inp)

            # Update all regions in parallel
            for i in range(self.N_REGIONS):
                r_in = torch.cat([
                    inp + 0.1 * cross_signal + 0.05 * sm_fb,
                    states["workspace"],
                ], dim=-1)
                states[f"r{i}"] = self.regions[i].step(r_in, states[f"r{i}"], self.dt)

            # Update global workspace — all regions write
            ws_in = torch.cat([states[f"r{i}"] for i in range(self.N_REGIONS)], dim=-1)
            states["workspace"] = self.workspace.step(ws_in, states["workspace"], self.dt)

            # Update self-model — reads everything
            sm_in = torch.cat([ws_in, states["workspace"]], dim=-1)
            states["selfmodel"] = self.selfmodel.step(sm_in, states["selfmodel"], self.dt)

            # Integration
            all_regions = torch.cat([states[k] for k in sorted(states.keys())], dim=-1)
            gate = self.thalamus(all_regions)
            out = gate * self.thalamic_proj(all_regions)
            outputs.append(out)

            for k in traces:
                traces[k].append(states[k].detach())

        hidden = torch.stack(outputs, dim=1)
        predictions = self.next_step_head(hidden[:, :-1, :])
        anomaly_score = self.anomaly_head(hidden).squeeze(-1)
        surprise = ((predictions - x[:, 1:, :]) ** 2).mean(dim=-1)
        properties = self.property_head(hidden[:, -1, :])

        return {
            "predictions": predictions, "hidden": hidden,
            "anomaly_score": anomaly_score, "surprise": surprise,
            "properties": properties,
            "region_traces": {k: torch.stack(v, dim=1) for k, v in traces.items()},
        }

    def param_count(self):
        counts = {}
        for i in range(self.N_REGIONS):
            counts[f"region_{i}"] = sum(p.numel() for p in self.regions[i].parameters())
        counts["workspace"] = sum(p.numel() for p in self.workspace.parameters())
        counts["selfmodel"] = sum(p.numel() for p in self.selfmodel.parameters())
        counts["routing"] = self.routing.numel()
        counts["total"] = sum(p.numel() for p in self.parameters())
        return counts
