"""
Insect Brain (Bee) — mushroom bodies, tiny but massively parallel.
==================================================================

Key biological features:
  - ~960,000 neurons (honeybee) — tiny but incredibly efficient
  - Mushroom bodies (MB) = associative learning centers, analogous to cortex
  - Antennal lobes = olfactory processing (primary sensory modality)
  - Optic lobes = visual processing
  - Central complex = navigation, spatial orientation, motor coordination
  - Lateral horn = innate behavioral responses (no learning)
  - Subesophageal ganglion = motor output
  - Key: parallel pathways for learned vs innate behavior

Architecture insight: two parallel tracks —
  1. Mushroom body pathway (learned, flexible, slower)
  2. Lateral horn pathway (innate, hardwired, fast)
Both converge at motor output. This is evolution's answer to
the explore/exploit tradeoff.

References (conceptual):
  - Menzel & Giurfa 2001 — cognitive architecture of honeybee
  - Aso et al. 2014 — mushroom body compartments
  - Webb 2012 — insect navigation circuits
"""
from __future__ import annotations

import torch
from torch import nn

from models.liquid_core import LiquidCell


class Region(nn.Module):
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
    def __init__(self, from_size, to_size, inhibitory=False):
        super().__init__()
        self.proj = nn.Linear(from_size, to_size)
        self.gate = nn.Linear(from_size, to_size)
        if inhibitory:
            with torch.no_grad():
                self.proj.bias.data -= 0.5

    def forward(self, x):
        return torch.sigmoid(self.gate(x)) * torch.tanh(self.proj(x))


class InsectBrain(nn.Module):
    """
    Insect (bee) brain — dual-track: learned (mushroom body) vs innate (lateral horn).

    Extremely parameter-efficient. The smallest brain in the zoo,
    but with sophisticated parallel processing.

    Region allocation:
      Antennal lobe (olfactory):     10%  — primary sensory
      Optic lobe (visual):           12%  — visual processing
      Mushroom body calyx:           15%  — sensory convergence for learning
      Mushroom body lobes:           15%  — learned associations, memory
      Lateral horn (innate):         10%  — hardwired responses, fast
      Central complex:               15%  — navigation, spatial, motor planning
      Subesophageal ganglion:        10%  — motor output
      Protocerebrum (integration):   13%  — higher integration
    """

    def __init__(self, input_size=1, hidden_size=128, n_properties=2, dropout=0.1, dt=1.0):
        super().__init__()
        self.hidden_size = hidden_size
        self.dt = dt
        H = hidden_size

        def _sz(pct):
            return max(4, int(H * pct))

        sz = {
            "antennal": _sz(0.10),     # olfactory
            "optic": _sz(0.12),        # visual
            "mb_calyx": _sz(0.15),     # mushroom body input
            "mb_lobes": _sz(0.15),     # mushroom body output/memory
            "lateral_horn": _sz(0.10), # innate responses
            "central_cx": _sz(0.15),   # navigation/spatial
            "seg": _sz(0.10),          # subesophageal ganglion (motor)
            "protocerebrum": _sz(0.13),# higher integration
        }
        self.sz = sz

        self.input_proj = nn.Linear(input_size, sz["antennal"])

        # Sensory lobes — fast
        self.antennal = Region(sz["antennal"], sz["antennal"], dt_scale=2.5, name="antennal_lobe")
        self.optic = Region(sz["antennal"], sz["optic"], dt_scale=2.5, name="optic_lobe")

        # TRACK 1: Mushroom body pathway (learned, flexible)
        mb_calyx_in = sz["antennal"] + sz["optic"]
        self.mb_calyx = Region(mb_calyx_in, sz["mb_calyx"], dt_scale=1.0, name="mushroom_body_calyx")
        self.mb_lobes = Region(sz["mb_calyx"], sz["mb_lobes"], dt_scale=0.5,
                               self_loop=True, name="mushroom_body_lobes")

        # TRACK 2: Lateral horn pathway (innate, fast, no learning)
        lh_in = sz["antennal"] + sz["optic"]
        self.lateral_horn = Region(lh_in, sz["lateral_horn"], dt_scale=2.0, name="lateral_horn")

        # Central complex — navigation, receives both tracks
        cc_in = sz["mb_lobes"] + sz["lateral_horn"]
        self.central_cx = Region(cc_in, sz["central_cx"], dt_scale=0.8,
                                 self_loop=True, name="central_complex")

        # Protocerebrum — higher integration
        proto_in = sz["mb_lobes"] + sz["lateral_horn"] + sz["central_cx"]
        self.protocerebrum = Region(proto_in, sz["protocerebrum"], dt_scale=0.6,
                                    self_loop=True, name="protocerebrum")

        # Subesophageal ganglion — motor output, receives protocerebrum + central complex
        seg_in = sz["protocerebrum"] + sz["central_cx"]
        self.seg = Region(seg_in, sz["seg"], dt_scale=1.8, name="subesophageal_ganglion")

        # Connections
        # Mushroom body → antennal (learned feedback modulates sensory)
        self.mb_to_antennal = Axon(sz["mb_lobes"], sz["antennal"])
        # Lateral horn inhibits mushroom body (innate overrides learned in danger)
        self.lh_inhibit_mb = Axon(sz["lateral_horn"], mb_calyx_in, inhibitory=True)

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
        sz = self.sz
        region_names = ["antennal", "optic", "mb_calyx", "mb_lobes",
                        "lateral_horn", "central_cx", "protocerebrum", "seg"]

        states = {}
        for name, region in [
            ("antennal", self.antennal), ("optic", self.optic),
            ("mb_calyx", self.mb_calyx), ("mb_lobes", self.mb_lobes),
            ("lateral_horn", self.lateral_horn), ("central_cx", self.central_cx),
            ("protocerebrum", self.protocerebrum), ("seg", self.seg),
        ]:
            states[name] = region.initial_state(B, x.device)

        outputs = []
        traces = {k: [] for k in states}

        for t in range(T):
            inp = self.input_proj(x[:, t, :])

            # Antennal lobe — olfactory + learned feedback
            ant_in = inp
            if t > 0:
                ant_in = ant_in + 0.1 * self.mb_to_antennal(states["mb_lobes"])
            states["antennal"] = self.antennal.step(ant_in, states["antennal"], self.dt)

            # Optic lobe — visual
            states["optic"] = self.optic.step(states["antennal"], states["optic"], self.dt)

            # TRACK 1: Mushroom body calyx (learned track)
            mb_in = torch.cat([states["antennal"], states["optic"]], dim=-1)
            # Lateral horn can inhibit mushroom body (innate override)
            if t > 0:
                mb_in = mb_in + 0.1 * self.lh_inhibit_mb(states["lateral_horn"])
            states["mb_calyx"] = self.mb_calyx.step(mb_in, states["mb_calyx"], self.dt)
            states["mb_lobes"] = self.mb_lobes.step(states["mb_calyx"], states["mb_lobes"], self.dt)

            # TRACK 2: Lateral horn (innate track — fast, no memory)
            lh_in = torch.cat([states["antennal"], states["optic"]], dim=-1)
            states["lateral_horn"] = self.lateral_horn.step(lh_in, states["lateral_horn"], self.dt)

            # Central complex — navigation, convergence
            cc_in = torch.cat([states["mb_lobes"], states["lateral_horn"]], dim=-1)
            states["central_cx"] = self.central_cx.step(cc_in, states["central_cx"], self.dt)

            # Protocerebrum — higher integration
            proto_in = torch.cat([states["mb_lobes"], states["lateral_horn"], states["central_cx"]], dim=-1)
            states["protocerebrum"] = self.protocerebrum.step(proto_in, states["protocerebrum"], self.dt)

            # Subesophageal ganglion — motor
            seg_in = torch.cat([states["protocerebrum"], states["central_cx"]], dim=-1)
            states["seg"] = self.seg.step(seg_in, states["seg"], self.dt)

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
        for name in ["antennal", "optic", "mb_calyx", "mb_lobes",
                      "lateral_horn", "central_cx", "protocerebrum", "seg"]:
            counts[name] = sum(p.numel() for p in getattr(self, name).parameters())
        counts["connections"] = sum(
            sum(p.numel() for p in m.parameters())
            for m in [self.mb_to_antennal, self.lh_inhibit_mb])
        counts["total"] = sum(p.numel() for p in self.parameters())
        return counts
