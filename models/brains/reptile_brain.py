"""
Reptile Brain — ancient, brainstem-dominant, energy-efficient.
==============================================================

Key biological features:
  - Brainstem-dominant architecture — core survival processing
  - Minimal cortex (thin pallium) — just enough for basic learning
  - Powerful tectum for visual tracking (optic tectum)
  - Strong instinctual patterns via striatum
  - Cold-blooded = variable metabolic rate affects processing speed
  - Spinal reflex arc bypasses the brain entirely for fast reactions
  - Energy-efficient — no wasted computation

Architecture insight: a fast, reflexive system with a thin veneer of
"thought." The metabolic rate parameter modulates ALL processing speeds,
mimicking how temperature affects cold-blooded neural processing.
The spinal reflex arc provides an ultrafast bypass for immediate responses.
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


class ReptileBrain(nn.Module):
    """
    Reptile brain — brainstem-dominant, cold-blooded metabolic modulation.

    Ancient architecture optimized for survival, not cognition.
    A learned metabolic rate scalar modulates ALL dt values,
    mimicking temperature-dependent processing in cold-blooded animals.
    Spinal reflex arc bypasses the brain entirely.

    Region allocation:
      brainstem:      15%  — dominant survival processing, fast
      tectum:         15%  — visual tracking, fast
      pallium:        10%  — thin proto-cortex, slow
      striatum:       12%  — habit/reward, medium
      cerebellum:     10%  — motor coordination
      olfactory:       8%  — chemical sensing, fast
      hypothalamus:    8%  — thermoregulation, drives
      spinal:          8%  — reflexes, very fast
      motor:           7%  — output
      optic_nerve:     7%  — fast sensory input
    """

    def __init__(self, input_size=1, hidden_size=128, n_properties=2, dropout=0.1, dt=1.0):
        super().__init__()
        self.hidden_size = hidden_size
        self.dt = dt
        H = hidden_size

        def _sz(pct):
            return max(4, int(H * pct))

        sz = {
            "brainstem": _sz(0.15),
            "tectum": _sz(0.15),
            "pallium": _sz(0.10),
            "striatum": _sz(0.12),
            "cerebellum": _sz(0.10),
            "olfactory": _sz(0.08),
            "hypothalamus": _sz(0.08),
            "spinal": _sz(0.08),
            "motor": _sz(0.07),
            "optic_nerve": _sz(0.07),
        }
        self.sz = sz

        # Learned metabolic rate — modulates ALL dt values (cold-blooded)
        self.metabolic_rate = nn.Parameter(torch.zeros(1))

        self.input_proj = nn.Linear(input_size, sz["olfactory"])
        self.input_proj_optic = nn.Linear(input_size, sz["optic_nerve"])

        # Sensory input regions
        self.olfactory = Region(sz["olfactory"], sz["olfactory"], dt_scale=1.5,
                                dropout=dropout, name="olfactory")
        self.optic_nerve = Region(sz["optic_nerve"], sz["optic_nerve"], dt_scale=1.5,
                                  dropout=dropout, name="optic_nerve")

        # Brainstem — dominant, fast, receives sensory + hypothalamus modulation
        bs_in = sz["olfactory"] + sz["optic_nerve"] + sz["hypothalamus"]
        self.brainstem = Region(bs_in, sz["brainstem"], dt_scale=2.0,
                                self_loop=True, dropout=dropout, name="brainstem")

        # Tectum — visual tracking, fast
        tectum_in = sz["optic_nerve"] + sz["brainstem"]
        self.tectum = Region(tectum_in, sz["tectum"], dt_scale=1.8,
                             dropout=dropout, name="tectum")

        # Striatum — habit/reward
        striatum_in = sz["brainstem"] + sz["tectum"]
        self.striatum = Region(striatum_in, sz["striatum"], dt_scale=1.0,
                               self_loop=True, dropout=dropout, name="striatum")

        # Pallium — thin proto-cortex, slow feedback
        pallium_in = sz["striatum"] + sz["tectum"]
        self.pallium = Region(pallium_in, sz["pallium"], dt_scale=0.4,
                              self_loop=True, dropout=dropout, name="pallium")

        # Cerebellum — motor coordination
        cerebellum_in = sz["pallium"] + sz["brainstem"]
        self.cerebellum = Region(cerebellum_in, sz["cerebellum"], dt_scale=1.0,
                                 dropout=dropout, name="cerebellum")

        # Hypothalamus — thermoregulation, drives, modulates brainstem
        hypo_in = sz["brainstem"]
        self.hypothalamus = Region(hypo_in, sz["hypothalamus"], dt_scale=0.8,
                                   self_loop=True, dropout=dropout, name="hypothalamus")

        # Spinal — reflexes, very fast, bypasses brain
        spinal_in = sz["olfactory"] + sz["optic_nerve"]
        self.spinal = Region(spinal_in, sz["spinal"], dt_scale=3.0,
                             dropout=dropout, name="spinal")

        # Motor — output
        motor_in = sz["cerebellum"] + sz["spinal"]
        self.motor = Region(motor_in, sz["motor"], dt_scale=1.2,
                            dropout=dropout, name="motor")

        # Connections
        self.pallium_to_brainstem = Axon(sz["pallium"], bs_in)
        self.hypo_modulate = Axon(sz["hypothalamus"], sz["brainstem"])

        # Output
        total = sum(sz.values())
        self.thalamus = nn.Sequential(nn.Linear(total, H), nn.LayerNorm(H), nn.Sigmoid())
        self.thalamic_proj = nn.Linear(total, H)

        self.next_step_head = nn.Sequential(nn.LayerNorm(H), nn.Linear(H, input_size))
        self.anomaly_head = nn.Sequential(nn.LayerNorm(H), nn.Linear(H, 1), nn.Sigmoid())
        self.property_head = nn.Sequential(
            nn.LayerNorm(H), nn.Linear(H, H // 2), nn.GELU(), nn.Linear(H // 2, n_properties))

    def _metabolic_dt(self, dt):
        """Apply metabolic rate modulation to dt — cold-blooded processing speed."""
        rate = torch.sigmoid(self.metabolic_rate).detach().item() * 2.0 + 0.5  # range [0.5, 2.5]
        return dt * rate

    def forward(self, x, **kwargs):
        B, T, _ = x.shape
        region_names = ["olfactory", "optic_nerve", "brainstem", "tectum", "striatum",
                        "pallium", "cerebellum", "hypothalamus", "spinal", "motor"]

        states = {}
        for name in region_names:
            states[name] = getattr(self, name).initial_state(B, x.device)

        outputs = []
        traces = {k: [] for k in states}

        for t in range(T):
            mdt = self._metabolic_dt(self.dt)

            inp_olf = self.input_proj(x[:, t, :])
            inp_opt = self.input_proj_optic(x[:, t, :])

            # Sensory input
            states["olfactory"] = self.olfactory.step(inp_olf, states["olfactory"], mdt)
            states["optic_nerve"] = self.optic_nerve.step(inp_opt, states["optic_nerve"], mdt)

            # Spinal reflex arc — bypasses brain entirely, very fast
            spinal_in = torch.cat([states["olfactory"], states["optic_nerve"]], dim=-1)
            states["spinal"] = self.spinal.step(spinal_in, states["spinal"], mdt)

            # Hypothalamus — modulates brainstem metabolic state
            hypo_in = states["brainstem"]
            states["hypothalamus"] = self.hypothalamus.step(hypo_in, states["hypothalamus"], mdt)

            # Brainstem — dominant processing + hypothalamus modulation + pallium feedback
            bs_in = torch.cat([states["olfactory"], states["optic_nerve"],
                               states["hypothalamus"]], dim=-1)
            if t > 0:
                bs_in = bs_in + 0.1 * self.pallium_to_brainstem(states["pallium"])
            states["brainstem"] = self.brainstem.step(bs_in, states["brainstem"], mdt)

            # Tectum — visual tracking
            tectum_in = torch.cat([states["optic_nerve"], states["brainstem"]], dim=-1)
            states["tectum"] = self.tectum.step(tectum_in, states["tectum"], mdt)

            # Striatum — habit/reward
            striatum_in = torch.cat([states["brainstem"], states["tectum"]], dim=-1)
            states["striatum"] = self.striatum.step(striatum_in, states["striatum"], mdt)

            # Pallium — thin proto-cortex, slow
            pallium_in = torch.cat([states["striatum"], states["tectum"]], dim=-1)
            states["pallium"] = self.pallium.step(pallium_in, states["pallium"], mdt)

            # Cerebellum — motor coordination
            cerebellum_in = torch.cat([states["pallium"], states["brainstem"]], dim=-1)
            states["cerebellum"] = self.cerebellum.step(cerebellum_in, states["cerebellum"], mdt)

            # Motor output — cerebellum + spinal reflex
            motor_in = torch.cat([states["cerebellum"], states["spinal"]], dim=-1)
            states["motor"] = self.motor.step(motor_in, states["motor"], mdt)

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
        for name in ["olfactory", "optic_nerve", "brainstem", "tectum", "striatum",
                      "pallium", "cerebellum", "hypothalamus", "spinal", "motor"]:
            counts[name] = sum(p.numel() for p in getattr(self, name).parameters())
        counts["connections"] = sum(
            sum(p.numel() for p in m.parameters())
            for m in [self.pallium_to_brainstem, self.hypo_modulate])
        counts["metabolic_rate"] = self.metabolic_rate.numel()
        counts["total"] = sum(p.numel() for p in self.parameters())
        return counts
