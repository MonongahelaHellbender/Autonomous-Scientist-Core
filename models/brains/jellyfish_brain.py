"""
Jellyfish Brain (Nerve Net) — diffuse, radially symmetric, purely reactive.
============================================================================

Key biological features:
  - Jellyfish have NO brain — just a diffuse nerve net
  - Rhopalia are sensory clusters around the bell margin
  - Processing is radially symmetric — no left/right, no hierarchy
  - Signals propagate around a ring of sensory clusters
  - The nerve net is a slow mesh of interconnected neurons
  - Motor output is circular muscle pulsing for locomotion
  - Purely reactive — no learning, no memory (in biology)

Architecture insight: a ring topology of sensory clusters (rhopalia)
with signals propagating both around the ring AND inward to a central
nerve net. The nerve net is a slow integrator, not a decision-maker.
Learned coupling strengths between adjacent rhopalia control ring
propagation speed and strength.
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


class JellyfishBrain(nn.Module):
    """
    Jellyfish brain — diffuse nerve net with ring-topology rhopalia.

    6 rhopalium sensory clusters in a ring, each talking to its
    2 neighbors. A central nerve net slowly integrates all signals.
    Motor ring reads from the nerve net for pulsing locomotion.

    NO hierarchy — rhopalial signals propagate AROUND the ring
    AND inward to the nerve net simultaneously.

    Region allocation:
      rhopalium_0 through rhopalium_5:  12% each = 72%  — sensory ring
      nerve_net:                         16%             — diffuse integrator
      motor_ring:                        12%             — circular muscle
    """

    N_RHOPALIA = 6

    def __init__(self, input_size=1, hidden_size=128, n_properties=2, dropout=0.1, dt=1.0):
        super().__init__()
        self.hidden_size = hidden_size
        self.dt = dt
        H = hidden_size

        def _sz(pct):
            return max(4, int(H * pct))

        rhop_size = _sz(0.12)
        net_size = _sz(0.16)
        motor_size = _sz(0.12)

        sz = {f"rhopalium_{i}": rhop_size for i in range(self.N_RHOPALIA)}
        sz["nerve_net"] = net_size
        sz["motor_ring"] = motor_size
        self.sz = sz

        self.input_proj = nn.Linear(input_size, rhop_size)

        # Learned coupling strength between adjacent rhopalia in the ring
        self.ring_coupling = nn.Parameter(torch.ones(6) * 0.5)

        # Rhopalia — sensory clusters, each receives input + 2 neighbors
        # Input: sensory input + left neighbor + right neighbor
        rhop_in = rhop_size + rhop_size * 2  # input + 2 neighbors
        self.rhopalia = nn.ModuleList([
            Region(rhop_in, rhop_size, dt_scale=1.0, self_loop=True,
                   dropout=dropout, name=f"rhopalium_{i}")
            for i in range(self.N_RHOPALIA)
        ])

        # Axons for ring propagation (each rhopalium projects to its neighbors)
        self.ring_axons = nn.ModuleList([
            Axon(rhop_size, rhop_size) for _ in range(self.N_RHOPALIA)
        ])

        # Nerve net — slow diffuse integrator, receives all rhopalia
        nerve_in = rhop_size * self.N_RHOPALIA
        self.nerve_net = Region(nerve_in, net_size, dt_scale=0.5,
                                self_loop=True, dropout=dropout, name="nerve_net")

        # Motor ring — circular muscle coordination, reads from nerve net
        self.motor_ring = Region(net_size, motor_size, dt_scale=1.2,
                                 dropout=dropout, name="motor_ring")

        # Output
        total = sum(sz.values())
        self.thalamus = nn.Sequential(nn.Linear(total, H), nn.LayerNorm(H), nn.Sigmoid())
        self.thalamic_proj = nn.Linear(total, H)

        self.next_step_head = nn.Sequential(nn.LayerNorm(H), nn.Linear(H, input_size))
        self.anomaly_head = nn.Sequential(nn.LayerNorm(H), nn.Linear(H, 1), nn.Sigmoid())
        self.property_head = nn.Sequential(
            nn.LayerNorm(H), nn.Linear(H, H // 2), nn.GELU(), nn.Linear(H // 2, n_properties))

    def forward(self, x, **kwargs):
        B, T, _ = x.shape

        states = {}
        for i in range(self.N_RHOPALIA):
            states[f"rhopalium_{i}"] = self.rhopalia[i].initial_state(B, x.device)
        states["nerve_net"] = self.nerve_net.initial_state(B, x.device)
        states["motor_ring"] = self.motor_ring.initial_state(B, x.device)

        outputs = []
        traces = {k: [] for k in states}

        region_names = [f"rhopalium_{i}" for i in range(self.N_RHOPALIA)] + ["nerve_net", "motor_ring"]

        for t in range(T):
            inp = self.input_proj(x[:, t, :])

            # Coupling strengths (sigmoid to keep in [0, 1])
            coupling = torch.sigmoid(self.ring_coupling)

            # Ring propagation — each rhopalium receives from its 2 neighbors
            # Compute neighbor signals first (from previous states)
            neighbor_signals = []
            for i in range(self.N_RHOPALIA):
                left = (i - 1) % self.N_RHOPALIA
                right = (i + 1) % self.N_RHOPALIA
                left_signal = coupling[left] * self.ring_axons[left](states[f"rhopalium_{left}"])
                right_signal = coupling[i] * self.ring_axons[right](states[f"rhopalium_{right}"])
                neighbor_signals.append((left_signal, right_signal))

            # Update all rhopalia simultaneously
            for i in range(self.N_RHOPALIA):
                left_sig, right_sig = neighbor_signals[i]
                rhop_in = torch.cat([inp, left_sig, right_sig], dim=-1)
                states[f"rhopalium_{i}"] = self.rhopalia[i].step(
                    rhop_in, states[f"rhopalium_{i}"], self.dt)

            # Nerve net — slow integration of all rhopalia
            net_in = torch.cat([states[f"rhopalium_{i}"] for i in range(self.N_RHOPALIA)], dim=-1)
            states["nerve_net"] = self.nerve_net.step(net_in, states["nerve_net"], self.dt)

            # Motor ring — reads from nerve net
            states["motor_ring"] = self.motor_ring.step(
                states["nerve_net"], states["motor_ring"], self.dt)

            # Integration
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
        for i in range(self.N_RHOPALIA):
            counts[f"rhopalium_{i}"] = sum(p.numel() for p in self.rhopalia[i].parameters())
        counts["nerve_net"] = sum(p.numel() for p in self.nerve_net.parameters())
        counts["motor_ring"] = sum(p.numel() for p in self.motor_ring.parameters())
        counts["ring_coupling"] = self.ring_coupling.numel()
        counts["ring_axons"] = sum(
            sum(p.numel() for p in a.parameters()) for a in self.ring_axons)
        counts["total"] = sum(p.numel() for p in self.parameters())
        return counts
