"""
Cat Brain — visual predator with exceptional motor coordination.
================================================================

Key biological features:
  - ~760M neurons — mid-sized mammalian brain
  - Exceptional visual cortex — night vision specialist, tapetum lucidum
  - Large auditory cortex — can hear ultrasonic frequencies (up to 64 kHz)
  - Powerful cerebellum — why they always land on their feet
  - Huge whisker barrel cortex — somatosensory map of whisker field
  - Strong amygdala-driven predatory instinct circuits
  - Small prefrontal cortex — independent, not very trainable
  - Large olfactory bulb relative to brain size

Architecture insight: sensory-heavy, motor-precise, planning-light.
The cat brain is optimized for ambush predation: detect, stalk, pounce.
Amygdala feeds back into visual cortex to sharpen attention during
prey detection (pupil dilation, enhanced visual processing).

References (conceptual):
  - Hubel & Wiesel 1962 — cat visual cortex columns
  - Stein & Meredith 1993 — superior colliculus, multisensory integration
  - Bhatt et al. 2013 — feline cerebellar coordination
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


class CatBrain(nn.Module):
    """
    Cat brain — visual predator with exceptional motor coordination.

    Sensory-dominant architecture with strong cerebellum and fast
    amygdala-driven predatory circuits. Small prefrontal = independent,
    not very trainable (classic cat behavior).

    Region allocation:
      visual_cortex:    14%  — DOMINANT, night vision specialist
      auditory:         10%  — ultrasonic hearing
      olfactory:         8%  — chemical sensing
      brainstem:         6%  — survival basics
      thalamus_relay:    6%  — sensory gating
      amygdala:          8%  — fear/predatory response
      hippocampus:       8%  — spatial memory (3D navigation)
      cerebellum:       12%  — LARGE, exceptional motor coordination
      basal_ganglia:     6%  — habit/stalking patterns
      prefrontal:        4%  — SMALL, cats aren't planners
      motor:             8%  — precise movement
      whisker_cortex:   10%  — somatosensory barrel cortex
    """

    def __init__(self, input_size=1, hidden_size=128, n_properties=2, dropout=0.1, dt=1.0):
        super().__init__()
        self.hidden_size = hidden_size
        self.dt = dt
        H = hidden_size

        def _sz(pct):
            return max(4, int(H * pct))

        sz = {
            "visual_cortex":  _sz(0.14),
            "auditory":       _sz(0.10),
            "olfactory":      _sz(0.08),
            "brainstem":      _sz(0.06),
            "thalamus_relay": _sz(0.06),
            "amygdala":       _sz(0.08),
            "hippocampus":    _sz(0.08),
            "cerebellum":     _sz(0.12),
            "basal_ganglia":  _sz(0.06),
            "prefrontal":     _sz(0.04),
            "motor":          _sz(0.08),
            "whisker_cortex": _sz(0.10),
        }
        self.sz = sz

        # Input projection to olfactory (cats sniff first)
        self.input_proj = nn.Linear(input_size, sz["olfactory"])

        # Sensory regions — fast
        self.olfactory = Region(sz["olfactory"], sz["olfactory"], dt_scale=1.0, name="olfactory")
        self.visual_cortex = Region(sz["olfactory"], sz["visual_cortex"], dt_scale=1.8, name="visual_cortex")
        self.auditory = Region(sz["olfactory"], sz["auditory"], dt_scale=2.0, name="auditory")
        self.whisker_cortex = Region(sz["olfactory"], sz["whisker_cortex"], dt_scale=2.5, name="whisker_cortex")

        # Thalamus relay — sensory convergence
        thal_in = sz["olfactory"] + sz["visual_cortex"] + sz["auditory"] + sz["whisker_cortex"]
        self.thalamus_relay = Region(thal_in, sz["thalamus_relay"], dt_scale=1.0, name="thalamus_relay")

        # Brainstem — survival basics
        self.brainstem = Region(sz["thalamus_relay"], sz["brainstem"], dt_scale=1.0, name="brainstem")

        # Amygdala — predatory detection, fast
        self.amygdala = Region(sz["brainstem"], sz["amygdala"], dt_scale=2.2, name="amygdala")

        # Hippocampus — spatial mapping
        self.hippocampus = Region(sz["amygdala"], sz["hippocampus"], dt_scale=1.0,
                                  self_loop=True, name="hippocampus")

        # Basal ganglia — stalking patterns
        self.basal_ganglia = Region(sz["hippocampus"], sz["basal_ganglia"], dt_scale=1.0, name="basal_ganglia")

        # Prefrontal — minimal planning
        self.prefrontal = Region(sz["basal_ganglia"], sz["prefrontal"], dt_scale=0.8,
                                 self_loop=True, name="prefrontal")

        # Cerebellum — precise coordination
        self.cerebellum = Region(sz["prefrontal"], sz["cerebellum"], dt_scale=1.0,
                                 self_loop=True, name="cerebellum")

        # Motor — precise movement
        self.motor = Region(sz["cerebellum"], sz["motor"], dt_scale=1.5, name="motor")

        # Unique: predatory gate — amygdala enhances visual attention
        self.predatory_gate = nn.Linear(sz["amygdala"], sz["visual_cortex"])

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
        region_names = list(sz.keys())

        states = {}
        for name, region in [
            ("olfactory", self.olfactory), ("visual_cortex", self.visual_cortex),
            ("auditory", self.auditory), ("whisker_cortex", self.whisker_cortex),
            ("thalamus_relay", self.thalamus_relay), ("brainstem", self.brainstem),
            ("amygdala", self.amygdala), ("hippocampus", self.hippocampus),
            ("basal_ganglia", self.basal_ganglia), ("prefrontal", self.prefrontal),
            ("cerebellum", self.cerebellum), ("motor", self.motor),
        ]:
            states[name] = region.initial_state(B, x.device)

        outputs = []
        traces = {k: [] for k in states}

        for t in range(T):
            inp = self.input_proj(x[:, t, :])

            # Sensory regions
            states["olfactory"] = self.olfactory.step(inp, states["olfactory"], self.dt)
            states["visual_cortex"] = self.visual_cortex.step(inp, states["visual_cortex"], self.dt)
            states["auditory"] = self.auditory.step(inp, states["auditory"], self.dt)
            states["whisker_cortex"] = self.whisker_cortex.step(inp, states["whisker_cortex"], self.dt)

            # Predatory gate: amygdala modulates visual cortex (pupil dilation effect)
            if t > 0:
                pred_mod = torch.sigmoid(self.predatory_gate(states["amygdala"]))
                states["visual_cortex"] = states["visual_cortex"] * (1.0 + 0.3 * pred_mod)

            # Thalamus relay — convergence
            thal_in = torch.cat([states["olfactory"], states["visual_cortex"],
                                 states["auditory"], states["whisker_cortex"]], dim=-1)
            states["thalamus_relay"] = self.thalamus_relay.step(thal_in, states["thalamus_relay"], self.dt)

            # Brainstem
            states["brainstem"] = self.brainstem.step(states["thalamus_relay"], states["brainstem"], self.dt)

            # Amygdala — predatory detection
            states["amygdala"] = self.amygdala.step(states["brainstem"], states["amygdala"], self.dt)

            # Hippocampus — spatial mapping
            states["hippocampus"] = self.hippocampus.step(states["amygdala"], states["hippocampus"], self.dt)

            # Basal ganglia — stalking patterns
            states["basal_ganglia"] = self.basal_ganglia.step(states["hippocampus"], states["basal_ganglia"], self.dt)

            # Prefrontal — minimal planning
            states["prefrontal"] = self.prefrontal.step(states["basal_ganglia"], states["prefrontal"], self.dt)

            # Cerebellum — precise coordination
            states["cerebellum"] = self.cerebellum.step(states["prefrontal"], states["cerebellum"], self.dt)

            # Motor — output
            states["motor"] = self.motor.step(states["cerebellum"], states["motor"], self.dt)

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
        for name in ["olfactory", "visual_cortex", "auditory", "whisker_cortex",
                      "thalamus_relay", "brainstem", "amygdala", "hippocampus",
                      "basal_ganglia", "prefrontal", "cerebellum", "motor"]:
            counts[name] = sum(p.numel() for p in getattr(self, name).parameters())
        counts["predatory_gate"] = sum(p.numel() for p in self.predatory_gate.parameters())
        counts["total"] = sum(p.numel() for p in self.parameters())
        return counts
