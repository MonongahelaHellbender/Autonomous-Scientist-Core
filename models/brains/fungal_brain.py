"""
Fungal Brain (Mycelium Network) — purely distributed, no central processor.
============================================================================

Key biological features:
  - Mycelium networks have NO central brain whatsoever
  - Information flows through hyphae via chemical signaling
  - The "Wood Wide Web" connects entire forests through mycorrhizal networks
  - Nutrients and chemical signals diffuse through the network
  - Any node can become a hub — topology is emergent, not hardwired
  - Signaling is SLOW — chemical diffusion, not electrical impulses

Architecture insight: a fully connected mesh of equal nodes with
learned distance-decay weights governing chemical diffusion between them.
A shared nutrient pool aggregates resources from all nodes and feeds back.
No hierarchy, no motor region — output is the collective average.
"""
from __future__ import annotations

import torch
from torch import nn

from models.liquid_core import LiquidCell


class Region(nn.Module):
    def __init__(self, in_size: int, h_size: int, dt_scale: float = 1.0,
                 self_loop: bool = False, dropout: float = 0.0, name: str = "",
                 adaptive_dt: bool = False):
        super().__init__()
        self.name, self.h_size, self.dt_scale = name, h_size, dt_scale
        self.self_loop, self.adaptive_dt = self_loop, adaptive_dt
        eff_in = in_size + (h_size if self_loop else 0)
        self.cell = LiquidCell(eff_in, h_size, dropout=dropout)
        self.norm = nn.LayerNorm(h_size)
        if adaptive_dt:
            self.log_dt = nn.Parameter(torch.zeros(1))
        with torch.no_grad():
            if dt_scale < 0.5:
                self.cell.log_step.data -= 2.0
            elif dt_scale > 1.5:
                self.cell.log_step.data += 1.0

    def initial_state(self, B, device=None):
        return torch.zeros(B, self.h_size, device=device)

    def step(self, x, state, dt=1.0):
        if self.self_loop:
            x = torch.cat([x, state], dim=-1)
        if self.adaptive_dt:
            dt = dt * float(torch.sigmoid(self.log_dt).detach()) * 3.0
        else:
            dt = dt * self.dt_scale
        return self.norm(self.cell(x, state, dt=dt))


class Axon(nn.Module):
    def __init__(self, from_size, to_size, inhibitory=False):
        super().__init__()
        self.proj = nn.Linear(from_size, to_size)
        self.gate = nn.Linear(from_size, to_size)
        if inhibitory:
            with torch.no_grad():
                self.proj.bias.data -= 0.5

    def forward(self, x):
        return torch.sigmoid(self.gate(x)) * torch.tanh(self.proj(x))


class FungalBrain(nn.Module):
    """
    Fungal brain — distributed mycelium network with chemical diffusion.

    8 equal mycelium nodes (no hierarchy) + 1 nutrient pool.
    Chemical signals diffuse between all nodes via a learned distance matrix.
    All signaling is slow (dt_scale=0.3) — mycelium is patient.

    Region allocation:
      node_0 through node_7:  10% each = 80%  — equal mycelium nodes
      nutrient_pool:          10%              — shared resource aggregator
    """

    N_NODES = 8

    def __init__(self, input_size=1, hidden_size=128, n_properties=2, dropout=0.1, dt=1.0):
        super().__init__()
        self.hidden_size = hidden_size
        self.dt = dt
        H = hidden_size

        def _sz(pct):
            return max(4, int(H * pct))

        node_size = _sz(0.10)
        pool_size = _sz(0.10)

        sz = {f"node_{i}": node_size for i in range(self.N_NODES)}
        sz["nutrient_pool"] = pool_size
        self.sz = sz

        self.input_proj = nn.Linear(input_size, node_size)

        # Learned chemical diffusion matrix — soft connectivity between nodes
        # Softmaxed per row to represent chemical gradient distribution
        self.chemical_diffusion = nn.Parameter(torch.randn(8, 8) * 0.1)

        # Mycelium nodes — all slow (chemical signaling)
        # Each node receives: input + chemical signals from neighbors + nutrient pool feedback
        node_in = node_size + node_size + pool_size  # input + diffused signal + pool
        self.nodes = nn.ModuleList([
            Region(node_in, node_size, dt_scale=0.3, self_loop=True,
                   dropout=dropout, name=f"node_{i}")
            for i in range(self.N_NODES)
        ])

        # Nutrient pool — aggregates from all nodes, feeds back
        self.nutrient_pool = Region(node_size * self.N_NODES, pool_size,
                                    dt_scale=0.3, dropout=dropout, name="nutrient_pool")

        # Projection to compress diffused neighbor signals to node_size
        self.diffusion_proj = nn.Linear(node_size * self.N_NODES, node_size)

        # Output — collective average, no single motor region
        total = sum(sz.values())
        self.thalamus = nn.Sequential(nn.Linear(total, H), nn.LayerNorm(H), nn.Sigmoid())
        self.thalamic_proj = nn.Linear(total, H)

        self.next_step_head = nn.Sequential(nn.LayerNorm(H), nn.Linear(H, input_size))
        self.anomaly_head = nn.Sequential(nn.LayerNorm(H), nn.Linear(H, 1), nn.Sigmoid())
        self.property_head = nn.Sequential(
            nn.LayerNorm(H), nn.Linear(H, H // 2), nn.GELU(), nn.Linear(H // 2, n_properties))

    def forward(self, x, **kwargs):
        B, T, _ = x.shape
        sz = self.sz

        states = {}
        for i in range(self.N_NODES):
            states[f"node_{i}"] = self.nodes[i].initial_state(B, x.device)
        states["nutrient_pool"] = self.nutrient_pool.initial_state(B, x.device)

        outputs = []
        traces = {k: [] for k in states}

        region_names = [f"node_{i}" for i in range(self.N_NODES)] + ["nutrient_pool"]

        for t in range(T):
            inp = self.input_proj(x[:, t, :])

            # Chemical diffusion weights (softmaxed per row)
            diff_weights = torch.softmax(self.chemical_diffusion, dim=-1)  # [8, 8]

            # Stack all node states for diffusion
            all_nodes = torch.stack([states[f"node_{i}"] for i in range(self.N_NODES)], dim=1)  # [B, 8, h]

            # Update each node with chemical signals from neighbors
            for i in range(self.N_NODES):
                # Weighted sum of all node states using diffusion weights
                weights_i = diff_weights[i]  # [8]
                diffused = (all_nodes * weights_i.unsqueeze(0).unsqueeze(-1)).reshape(B, -1)  # [B, 8*h]
                chem_signal = self.diffusion_proj(diffused)  # [B, node_size]

                node_in = torch.cat([inp, chem_signal, states["nutrient_pool"]], dim=-1)
                states[f"node_{i}"] = self.nodes[i].step(node_in, states[f"node_{i}"], self.dt)

            # Nutrient pool — aggregates all nodes
            pool_in = torch.cat([states[f"node_{i}"] for i in range(self.N_NODES)], dim=-1)
            states["nutrient_pool"] = self.nutrient_pool.step(
                pool_in, states["nutrient_pool"], self.dt)

            # Integration — collective of all nodes
            all_regions = torch.cat([states[k] for k in region_names], dim=-1)
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
        for i in range(self.N_NODES):
            counts[f"node_{i}"] = sum(p.numel() for p in self.nodes[i].parameters())
        counts["nutrient_pool"] = sum(p.numel() for p in self.nutrient_pool.parameters())
        counts["chemical_diffusion"] = self.chemical_diffusion.numel()
        counts["total"] = sum(p.numel() for p in self.parameters())
        return counts
