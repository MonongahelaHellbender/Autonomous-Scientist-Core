"""
Corvid Brain — dense nuclear clusters, no layered cortex.
==========================================================

Key biological features:
  - No neocortex! Uses dense pallial nuclei instead of layers
  - Nidopallium caudolaterale (NCL) = functional equivalent of prefrontal cortex
  - Extremely high neuron density — more neurons per gram than primates
  - Wulst = visual processing (homologous to V1)
  - Hippocampus is huge (spatial memory for caching food)
  - Mesopallium = associative processing
  - Arcopallium = motor planning/output
  - Cerebellum = timing (flight coordination)

Architecture insight: no layered hierarchy like mammals.
Instead, dense parallel clusters that communicate laterally.
Think of it as a "flat" organization with high connectivity,
not a deep hierarchy.

References (conceptual):
  - Olkowicz et al. 2016 — birds pack more neurons per volume
  - Güntürkün & Bugnyar 2016 — cognition without a cortex
  - Nieder et al. 2020 — corvid consciousness markers
"""
from __future__ import annotations

import torch
from torch import nn

from models.liquid_core import LiquidCell


class Nucleus(nn.Module):
    """Dense nuclear cluster — corvid equivalent of a brain region.

    Key difference from Region: every nucleus talks to every other nucleus
    through lateral connections (flat organization, not hierarchical).
    """

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


class CorvidBrain(nn.Module):
    """
    Corvid (crow/raven) brain — dense parallel nuclei, no cortical hierarchy.

    All nuclei are roughly equal in hierarchy (flat organization).
    High lateral connectivity — every cluster can influence every other.
    Extremely parameter-efficient due to density.

    Region allocation:
      Wulst (visual):              12%  — visual processing (like V1)
      Mesopallium (associative):   15%  — multimodal association
      Nidopallium (NCL, executive):18%  — decision/executive (like PFC)
      Hippocampus (spatial memory):15%  — massive for caching behavior
      Arcopallium (motor):         10%  — motor planning/output
      Cerebellum (timing):         12%  — flight timing
      Tectum (sensory relay):       8%  — sensory integration
      Song nuclei (vocal):         10%  — vocal learning (unique to birds)
    """

    def __init__(self, input_size=1, hidden_size=128, n_properties=2, dropout=0.1, dt=1.0):
        super().__init__()
        self.hidden_size = hidden_size
        self.dt = dt
        H = hidden_size

        def _sz(pct):
            return max(4, int(H * pct))

        sz = {
            "wulst": _sz(0.12),       # visual
            "mesopallium": _sz(0.15),  # associative
            "ncl": _sz(0.18),          # executive (nidopallium caudolaterale)
            "hippo": _sz(0.15),        # spatial memory
            "arcopallium": _sz(0.10),  # motor
            "cerebellum": _sz(0.12),   # timing
            "tectum": _sz(0.08),       # sensory relay
            "song": _sz(0.10),         # vocal learning
        }
        self.sz = sz

        self.input_proj = nn.Linear(input_size, sz["wulst"])

        # All nuclei — roughly parallel, not hierarchical
        self.wulst = Nucleus(sz["wulst"], sz["wulst"], dt_scale=2.0, name="wulst")
        self.tectum = Nucleus(sz["wulst"], sz["tectum"], dt_scale=2.0, name="tectum")

        # Mesopallium — associative, receives wulst + tectum
        meso_in = sz["wulst"] + sz["tectum"]
        self.mesopallium = Nucleus(meso_in, sz["mesopallium"], dt_scale=1.0,
                                   self_loop=True, name="mesopallium")

        # Hippocampus — huge, spatial memory, receives mesopallium
        self.hippo = Nucleus(sz["mesopallium"], sz["hippo"], dt_scale=0.6,
                             self_loop=True, name="hippocampus")

        # NCL (executive) — receives mesopallium + hippo + all lateral input
        ncl_in = sz["mesopallium"] + sz["hippo"]
        self.ncl = Nucleus(ncl_in, sz["ncl"], dt_scale=0.4,
                           self_loop=True, name="nidopallium_NCL")

        # Song nuclei — vocal learning, receives NCL + mesopallium
        song_in = sz["ncl"] + sz["mesopallium"]
        self.song = Nucleus(song_in, sz["song"], dt_scale=1.2,
                            self_loop=True, name="song_nuclei")

        # Cerebellum — timing, receives motor plan + sensory
        cer_in = sz["ncl"] + sz["wulst"]
        self.cerebellum = Nucleus(cer_in, sz["cerebellum"], dt_scale=1.8, name="cerebellum")

        # Arcopallium — motor, receives NCL + cerebellum
        arco_in = sz["ncl"] + sz["cerebellum"]
        self.arcopallium = Nucleus(arco_in, sz["arcopallium"], dt_scale=1.5, name="arcopallium")

        # Lateral connections (the corvid difference — flat, dense cross-talk)
        self.hippo_to_wulst = Axon(sz["hippo"], sz["wulst"])  # memory replay
        self.ncl_to_meso = Axon(sz["ncl"], meso_in)  # executive feedback
        self.song_to_arco = Axon(sz["song"], arco_in)  # vocal → motor

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
        regions = ["wulst", "tectum", "mesopallium", "hippo", "ncl", "song", "cerebellum", "arcopallium"]

        states = {}
        for name, region in [
            ("wulst", self.wulst), ("tectum", self.tectum),
            ("mesopallium", self.mesopallium), ("hippo", self.hippo),
            ("ncl", self.ncl), ("song", self.song),
            ("cerebellum", self.cerebellum), ("arcopallium", self.arcopallium),
        ]:
            states[name] = region.initial_state(B, x.device)

        outputs = []
        traces = {k: [] for k in states}

        for t in range(T):
            inp = self.input_proj(x[:, t, :])

            # Wulst — visual + memory replay from hippo
            w_in = inp
            if t > 0:
                w_in = w_in + 0.1 * self.hippo_to_wulst(states["hippo"])
            states["wulst"] = self.wulst.step(w_in, states["wulst"], self.dt)

            # Tectum — sensory relay
            states["tectum"] = self.tectum.step(states["wulst"], states["tectum"], self.dt)

            # Mesopallium — associative, receives wulst + tectum + NCL feedback
            meso_in = torch.cat([states["wulst"], states["tectum"]], dim=-1)
            if t > 0:
                meso_in = meso_in + 0.05 * self.ncl_to_meso(states["ncl"])
            states["mesopallium"] = self.mesopallium.step(meso_in, states["mesopallium"], self.dt)

            # Hippocampus — spatial memory
            states["hippo"] = self.hippo.step(states["mesopallium"], states["hippo"], self.dt)

            # NCL — executive decision
            ncl_in = torch.cat([states["mesopallium"], states["hippo"]], dim=-1)
            states["ncl"] = self.ncl.step(ncl_in, states["ncl"], self.dt)

            # Song nuclei — vocal learning
            song_in = torch.cat([states["ncl"], states["mesopallium"]], dim=-1)
            states["song"] = self.song.step(song_in, states["song"], self.dt)

            # Cerebellum — timing
            cer_in = torch.cat([states["ncl"], states["wulst"]], dim=-1)
            states["cerebellum"] = self.cerebellum.step(cer_in, states["cerebellum"], self.dt)

            # Arcopallium — motor output
            arco_in = torch.cat([states["ncl"], states["cerebellum"]], dim=-1)
            if t > 0:
                arco_in = arco_in + 0.05 * self.song_to_arco(states["song"])
            states["arcopallium"] = self.arcopallium.step(arco_in, states["arcopallium"], self.dt)

            # Integration
            all_regions = torch.cat([states[k] for k in regions], dim=-1)
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
        for name in ["wulst", "tectum", "mesopallium", "hippo", "ncl", "song", "cerebellum", "arcopallium"]:
            counts[name] = sum(p.numel() for p in getattr(self, name).parameters())
        counts["connections"] = sum(
            sum(p.numel() for p in m.parameters())
            for m in [self.hippo_to_wulst, self.ncl_to_meso, self.song_to_arco])
        counts["total"] = sum(p.numel() for p in self.parameters())
        return counts
