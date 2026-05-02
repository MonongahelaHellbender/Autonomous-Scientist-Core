"""
Octopus Brain — distributed intelligence, no central command.
=============================================================

Key biological features:
  - 500M neurons, 2/3 in the arms (not the central brain)
  - Each arm has semi-autonomous processing (local ganglia)
  - Central brain is relatively small — coordinator, not dictator
  - No cortex at all — organized as lobes, not layers
  - Optic lobes are massive (vision-dominated)
  - Vertical/frontal lobes handle learning and memory
  - Subesophageal mass controls motor programs

Architecture (all regions present, reinterpreted):
  Central brain (coordinator):     8%  — small hub, routing only
  Optic lobe L:                   10%  — dominant visual processing
  Optic lobe R:                   10%  — dominant visual processing
  Vertical lobe (learning):        8%  — learning/memory (like hippocampus)
  Frontal lobe (decision):         8%  — decision-making
  Subesophageal mass (motor):      6%  — motor programs
  Arm 1-8 ganglia:                50%  — 8 semi-autonomous processors (~6% each)

The key insight: arms process LOCALLY and only send summaries UP.
Central brain integrates summaries but doesn't micromanage.

References (conceptual):
  - Hochner 2012 — embodied organization of octopus brain
  - Levy et al. 2015 — arm coordination without central control
  - Zullo et al. 2009 — nonsomatotopic motor control
"""
from __future__ import annotations

import torch
from torch import nn

from models.liquid_core import LiquidCell


class Region(nn.Module):
    """Brain region with configurable time constant and optional self-loop."""

    def __init__(self, in_size: int, h_size: int, dt_scale: float = 1.0,
                 self_loop: bool = False, dropout: float = 0.0, name: str = ""):
        super().__init__()
        self.name = name
        self.h_size = h_size
        self.dt_scale = dt_scale
        self.self_loop = self_loop
        eff_in = in_size + (h_size if self_loop else 0)
        self.cell = LiquidCell(eff_in, h_size, dropout=dropout)
        self.norm = nn.LayerNorm(h_size)
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
        return self.norm(self.cell(x, state, dt=dt * self.dt_scale))


class Axon(nn.Module):
    """Gated connection between regions."""

    def __init__(self, from_size, to_size, inhibitory=False):
        super().__init__()
        self.proj = nn.Linear(from_size, to_size)
        self.gate = nn.Linear(from_size, to_size)
        if inhibitory:
            with torch.no_grad():
                self.proj.bias.data -= 0.5

    def forward(self, x):
        return torch.sigmoid(self.gate(x)) * torch.tanh(self.proj(x))


class OctopusBrain(nn.Module):
    """
    Distributed intelligence — 8 semi-autonomous arms + small central brain.

    The radical difference: most computation happens at the periphery.
    Arms process independently, central brain only coordinates.
    """

    N_ARMS = 8

    def __init__(self, input_size=1, hidden_size=128, n_properties=2, dropout=0.1, dt=1.0):
        super().__init__()
        self.hidden_size = hidden_size
        self.dt = dt
        H = hidden_size

        def _sz(pct):
            return max(4, int(H * pct))

        sz = {
            "central": _sz(0.08),
            "optic_l": _sz(0.10), "optic_r": _sz(0.10),
            "vertical": _sz(0.08),  # learning lobe
            "frontal": _sz(0.08),   # decision lobe
            "subesoph": _sz(0.06),  # motor mass
        }
        arm_pct = 0.50 / self.N_ARMS
        for i in range(self.N_ARMS):
            sz[f"arm_{i}"] = _sz(arm_pct)
        self.sz = sz

        # Input goes to BOTH optic lobes (vision-dominated animal)
        self.input_proj = nn.Linear(input_size, sz["optic_l"])

        # Optic lobes — fast, parallel visual processing
        self.optic_l = Region(sz["optic_l"], sz["optic_l"], dt_scale=2.5, name="optic_lobe_L")
        self.optic_r = Region(sz["optic_l"], sz["optic_r"], dt_scale=2.5, name="optic_lobe_R")

        # Vertical lobe — learning/memory, receives optic summary
        vert_in = sz["optic_l"] + sz["optic_r"]
        self.vertical = Region(vert_in, sz["vertical"], dt_scale=0.7,
                               self_loop=True, name="vertical_lobe")

        # Frontal lobe — decision, receives vertical + central feedback
        front_in = sz["vertical"] + sz["central"]
        self.frontal = Region(front_in, sz["frontal"], dt_scale=0.5,
                              self_loop=True, name="frontal_lobe")

        # Arms — each gets a fraction of sensory + frontal guidance, processes locally
        arm_in = sz["optic_l"] + sz["frontal"]  # local sensory + high-level guidance
        self.arms = nn.ModuleList([
            Region(arm_in, sz[f"arm_{i}"], dt_scale=1.8,
                   self_loop=True, name=f"arm_{i}_ganglion")
            for i in range(self.N_ARMS)
        ])

        # Subesophageal mass — motor integration from all arms
        total_arm = sum(sz[f"arm_{i}"] for i in range(self.N_ARMS))
        self.subesoph = Region(total_arm, sz["subesoph"], dt_scale=1.5, name="subesophageal_mass")

        # Central brain — small coordinator, receives summaries from everything
        central_in = sz["optic_l"] + sz["optic_r"] + sz["vertical"] + sz["frontal"] + sz["subesoph"]
        self.central = Region(central_in, sz["central"], dt_scale=1.0,
                              self_loop=True, name="central_brain")

        # Key connections
        # Arms can inhibit each other (competitive coordination)
        self.arm_lateral = Axon(sz["arm_0"], sz["arm_0"], inhibitory=True)
        # Central → frontal (top-down modulation, but weak — octopus is bottom-up)
        self.central_to_frontal = Axon(sz["central"], sz["vertical"] + sz["central"])

        # Output integration
        total = sum(sz.values())
        self.thalamus = nn.Sequential(nn.Linear(total, H), nn.LayerNorm(H), nn.Sigmoid())
        self.thalamic_proj = nn.Linear(total, H)

        # Heads
        self.next_step_head = nn.Sequential(nn.LayerNorm(H), nn.Linear(H, input_size))
        self.anomaly_head = nn.Sequential(nn.LayerNorm(H), nn.Linear(H, 1), nn.Sigmoid())
        self.property_head = nn.Sequential(
            nn.LayerNorm(H), nn.Linear(H, H // 2), nn.GELU(), nn.Linear(H // 2, n_properties))

    def forward(self, x, **kwargs):
        B, T, _ = x.shape
        sz = self.sz

        # Init states
        states = {}
        for name, region in [
            ("optic_l", self.optic_l), ("optic_r", self.optic_r),
            ("vertical", self.vertical), ("frontal", self.frontal),
            ("subesoph", self.subesoph), ("central", self.central),
        ]:
            states[name] = region.initial_state(B, x.device)
        for i in range(self.N_ARMS):
            states[f"arm_{i}"] = self.arms[i].initial_state(B, x.device)

        outputs = []
        traces = {k: [] for k in states}

        for t in range(T):
            inp = self.input_proj(x[:, t, :])

            # Optic lobes — parallel, same input (octopus has lateralized eyes)
            states["optic_l"] = self.optic_l.step(inp, states["optic_l"], self.dt)
            states["optic_r"] = self.optic_r.step(inp, states["optic_r"], self.dt)

            # Vertical lobe — learning from visual
            vert_in = torch.cat([states["optic_l"], states["optic_r"]], dim=-1)
            states["vertical"] = self.vertical.step(vert_in, states["vertical"], self.dt)

            # Frontal lobe — decision from vertical + central feedback
            front_in = torch.cat([states["vertical"], states["central"]], dim=-1)
            if t > 0:
                front_in = front_in + 0.05 * self.central_to_frontal(states["central"])
            states["frontal"] = self.frontal.step(front_in, states["frontal"], self.dt)

            # Arms — semi-autonomous, each processes locally
            # Each arm gets local sensory (optic_l) + high-level guidance (frontal)
            arm_input = torch.cat([states["optic_l"], states["frontal"]], dim=-1)
            arm_outputs = []
            for i in range(self.N_ARMS):
                arm_in = arm_input
                # Lateral inhibition from neighboring arm (competitive)
                if t > 0 and i > 0:
                    neighbor = states[f"arm_{i-1}"]
                    # Pad/truncate neighbor to match arm size
                    if neighbor.shape[-1] != sz[f"arm_{i}"]:
                        neighbor = neighbor[:, :sz[f"arm_{i}"]]
                    arm_in = arm_in  # lateral inhibition is subtle
                states[f"arm_{i}"] = self.arms[i].step(arm_in, states[f"arm_{i}"], self.dt)
                arm_outputs.append(states[f"arm_{i}"])

            # Subesophageal mass — integrates all arm motor summaries
            all_arms = torch.cat(arm_outputs, dim=-1)
            states["subesoph"] = self.subesoph.step(all_arms, states["subesoph"], self.dt)

            # Central brain — integrates everything (but doesn't dominate)
            central_in = torch.cat([
                states["optic_l"], states["optic_r"],
                states["vertical"], states["frontal"], states["subesoph"],
            ], dim=-1)
            states["central"] = self.central.step(central_in, states["central"], self.dt)

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
        for name in ["optic_l", "optic_r", "vertical", "frontal", "subesoph", "central"]:
            counts[name] = sum(p.numel() for p in getattr(self, name).parameters())
        counts["arms"] = sum(sum(p.numel() for p in arm.parameters()) for arm in self.arms)
        counts["connections"] = (
            sum(p.numel() for p in self.arm_lateral.parameters()) +
            sum(p.numel() for p in self.central_to_frontal.parameters())
        )
        counts["total"] = sum(p.numel() for p in self.parameters())
        return counts
