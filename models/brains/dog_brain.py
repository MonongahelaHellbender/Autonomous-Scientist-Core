"""
Dog Brain — social olfactory specialist with strong reward processing.
=====================================================================

Key biological features:
  - ~530M neurons — smaller than cat but differently allocated
  - Massive olfactory bulb — 40x more scent receptors than humans
  - Specialized social cognition — 10,000+ years co-evolving with humans
  - Large caudate nucleus — reward processing (they LOVE treats)
  - Good auditory cortex, adequate visual cortex
  - Larger prefrontal than cats — more trainable, social planning
  - Strong motor cortex — endurance runners

Architecture insight: olfaction-dominant, socially wired, reward-driven.
The dog brain is optimized for social bonding and scent tracking.
Social cortex feeds into caudate (reward), explaining why dogs get
euphoric seeing their humans — social bonding IS the reward.

References (conceptual):
  - Berns et al. 2012 — caudate activation in dogs (fMRI)
  - Andics et al. 2016 — voice-sensitive regions in dog temporal cortex
  - Horowitz 2009 — olfactory cognition in domestic dogs
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


class DogBrain(nn.Module):
    """
    Dog brain — social olfactory specialist with strong reward circuits.

    Olfaction-dominant with unique social cortex for reading human cues.
    Large caudate for reward processing — dogs are trainable because
    social bonding directly activates reward pathways.

    Region allocation:
      olfactory_bulb:  14%  — DOMINANT, dogs live in a world of smell
      auditory:         8%  — good hearing
      visual:           6%  — adequate but not exceptional
      brainstem:        6%  — survival
      thalamus:         6%  — relay
      amygdala:         6%  — emotional response
      hippocampus:      8%  — spatial + associative memory
      caudate:         10%  — LARGE reward processing
      prefrontal:       8%  — larger than cat, trainable
      social_cortex:   10%  — UNIQUE, reading human cues
      cerebellum:       8%  — motor coordination
      motor:           10%  — locomotion, endurance runner
    """

    def __init__(self, input_size=1, hidden_size=128, n_properties=2, dropout=0.1, dt=1.0):
        super().__init__()
        self.hidden_size = hidden_size
        self.dt = dt
        H = hidden_size

        def _sz(pct):
            return max(4, int(H * pct))

        sz = {
            "olfactory_bulb": _sz(0.14),
            "auditory":       _sz(0.08),
            "visual":         _sz(0.06),
            "brainstem":      _sz(0.06),
            "thalamus":       _sz(0.06),
            "amygdala":       _sz(0.06),
            "hippocampus":    _sz(0.08),
            "caudate":        _sz(0.10),
            "prefrontal":     _sz(0.08),
            "social_cortex":  _sz(0.10),
            "cerebellum":     _sz(0.08),
            "motor":          _sz(0.10),
        }
        self.sz = sz

        # Input projection to olfactory bulb (dogs sniff everything)
        self.input_proj = nn.Linear(input_size, sz["olfactory_bulb"])

        # Sensory regions
        self.olfactory_bulb = Region(sz["olfactory_bulb"], sz["olfactory_bulb"], dt_scale=2.0, name="olfactory_bulb")
        self.auditory = Region(sz["olfactory_bulb"], sz["auditory"], dt_scale=1.5, name="auditory")
        self.visual = Region(sz["olfactory_bulb"], sz["visual"], dt_scale=1.0, name="visual")

        # Thalamus — sensory convergence
        thal_in = sz["olfactory_bulb"] + sz["auditory"] + sz["visual"]
        self.thalamus = Region(thal_in, sz["thalamus"], dt_scale=1.0, name="thalamus")

        # Brainstem
        self.brainstem = Region(sz["thalamus"], sz["brainstem"], dt_scale=1.0, name="brainstem")

        # Amygdala — emotional
        self.amygdala = Region(sz["brainstem"], sz["amygdala"], dt_scale=1.5, name="amygdala")

        # Hippocampus — spatial + associative memory
        self.hippocampus = Region(sz["amygdala"], sz["hippocampus"], dt_scale=1.0,
                                  self_loop=True, name="hippocampus")

        # Caudate — reward evaluation
        self.caudate = Region(sz["hippocampus"], sz["caudate"], dt_scale=1.5, name="caudate")

        # Social cortex — reading human cues
        self.social_cortex = Region(sz["caudate"], sz["social_cortex"], dt_scale=1.0,
                                    self_loop=True, name="social_cortex")

        # Unique: social-reward link — social bonding enhances reward
        # Projects from social_cortex into the caudate input stream (matched to hippocampus size)
        self.social_reward_link = Axon(sz["social_cortex"], sz["hippocampus"])

        # Prefrontal — planning/obedience
        self.prefrontal = Region(sz["social_cortex"], sz["prefrontal"], dt_scale=0.8,
                                 self_loop=True, name="prefrontal")

        # Cerebellum — motor coordination
        self.cerebellum = Region(sz["prefrontal"], sz["cerebellum"], dt_scale=1.0,
                                 self_loop=True, name="cerebellum")

        # Motor — locomotion
        self.motor = Region(sz["cerebellum"], sz["motor"], dt_scale=1.5, name="motor")

        # Output
        total = sum(sz.values())
        self.thalamus_gate = nn.Sequential(nn.Linear(total, H), nn.LayerNorm(H), nn.Sigmoid())
        self.thalamic_proj = nn.Linear(total, H)

        self.next_step_head = nn.Sequential(nn.LayerNorm(H), nn.Linear(H, input_size))
        self.anomaly_head = nn.Sequential(nn.LayerNorm(H), nn.Linear(H, 1), nn.Sigmoid())
        self.property_head = nn.Sequential(
            nn.LayerNorm(H), nn.Linear(H, H // 2), nn.GELU(), nn.Linear(H // 2, n_properties))

    def forward(self, x, **kwargs):
        B, T, _ = x.shape
        sz = self.sz
        region_names = list(sz.keys())

        states = {}
        for name, region in [
            ("olfactory_bulb", self.olfactory_bulb), ("auditory", self.auditory),
            ("visual", self.visual), ("thalamus", self.thalamus),
            ("brainstem", self.brainstem), ("amygdala", self.amygdala),
            ("hippocampus", self.hippocampus), ("caudate", self.caudate),
            ("social_cortex", self.social_cortex), ("prefrontal", self.prefrontal),
            ("cerebellum", self.cerebellum), ("motor", self.motor),
        ]:
            states[name] = region.initial_state(B, x.device)

        outputs = []
        traces = {k: [] for k in states}

        for t in range(T):
            inp = self.input_proj(x[:, t, :])

            # Sensory regions
            states["olfactory_bulb"] = self.olfactory_bulb.step(inp, states["olfactory_bulb"], self.dt)
            states["auditory"] = self.auditory.step(inp, states["auditory"], self.dt)
            states["visual"] = self.visual.step(inp, states["visual"], self.dt)

            # Thalamus — convergence
            thal_in = torch.cat([states["olfactory_bulb"], states["auditory"],
                                 states["visual"]], dim=-1)
            states["thalamus"] = self.thalamus.step(thal_in, states["thalamus"], self.dt)

            # Brainstem
            states["brainstem"] = self.brainstem.step(states["thalamus"], states["brainstem"], self.dt)

            # Amygdala
            states["amygdala"] = self.amygdala.step(states["brainstem"], states["amygdala"], self.dt)

            # Hippocampus
            states["hippocampus"] = self.hippocampus.step(states["amygdala"], states["hippocampus"], self.dt)

            # Caudate — reward evaluation + social reward enhancement
            caudate_in = states["hippocampus"]
            if t > 0:
                caudate_in = caudate_in + 0.2 * self.social_reward_link(states["social_cortex"])
            states["caudate"] = self.caudate.step(caudate_in, states["caudate"], self.dt)

            # Social cortex — reading human cues
            states["social_cortex"] = self.social_cortex.step(states["caudate"], states["social_cortex"], self.dt)

            # Prefrontal — planning/obedience
            states["prefrontal"] = self.prefrontal.step(states["social_cortex"], states["prefrontal"], self.dt)

            # Cerebellum
            states["cerebellum"] = self.cerebellum.step(states["prefrontal"], states["cerebellum"], self.dt)

            # Motor
            states["motor"] = self.motor.step(states["cerebellum"], states["motor"], self.dt)

            # Integration
            all_regions = torch.cat([states[k] for k in region_names], dim=-1)
            gate = self.thalamus_gate(all_regions)
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
        for name in ["olfactory_bulb", "auditory", "visual", "thalamus",
                      "brainstem", "amygdala", "hippocampus", "caudate",
                      "social_cortex", "prefrontal", "cerebellum", "motor"]:
            counts[name] = sum(p.numel() for p in getattr(self, name).parameters())
        counts["social_reward_link"] = sum(p.numel() for p in self.social_reward_link.parameters())
        counts["total"] = sum(p.numel() for p in self.parameters())
        return counts
