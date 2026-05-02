"""
Human Brain — full cortical hierarchy with 12 regions.
=======================================================

Goes beyond the initial neuromorphic prototype with:
  - Amygdala (urgency/salience detection)
  - Visual cortex (hierarchical feature extraction, 2 sub-layers)
  - Motor cortex (output sequencing)
  - Anterior cingulate cortex (conflict monitoring)
  - Insula (self-monitoring / metacognition)
  - Brainstem (arousal regulation / baseline)
  - Corpus callosum (inter-hemisphere bridge)
  - Left/Right hemisphere split for prefrontal

Connectivity based on known human neuroanatomy:
  - Visual cortex → Sensory cortex (feedforward)
  - Sensory cortex → Everything (broadcast)
  - Amygdala ↔ Hippocampus (emotional memory)
  - Amygdala → Prefrontal (urgency signal)
  - Hippocampus → Prefrontal (memory recall)
  - Cerebellum → Motor cortex (timing correction)
  - Anterior cingulate monitors conflict between hemispheres
  - Insula reads internal state and modulates arousal
  - Brainstem sets baseline activation for all regions
  - Corpus callosum bridges left and right prefrontal

Neuroscience references (conceptual):
  - Murray et al. 2014 — cortical timescale hierarchy
  - Chaudhuri et al. 2015 — large-scale cortical dynamics
  - Felleman & Van Essen 1991 — hierarchical visual processing
  - LeDoux 1996 — amygdala fear circuits
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
        # Biologically motivated time constant init
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
    """Gated connection between regions. Can be excitatory or inhibitory."""

    def __init__(self, from_size, to_size, inhibitory=False):
        super().__init__()
        self.proj = nn.Linear(from_size, to_size)
        self.gate = nn.Linear(from_size, to_size)
        if inhibitory:
            with torch.no_grad():
                self.proj.bias.data -= 0.5

    def forward(self, x):
        return torch.sigmoid(self.gate(x)) * torch.tanh(self.proj(x))


class HumanBrain(nn.Module):
    """
    Full human brain architecture — 12 regions, biologically connected.

    Region allocation (% of hidden_size):
      Brainstem:          5%   — baseline arousal
      Visual cortex V1:   8%   — low-level features
      Visual cortex V2:   6%   — higher features
      Sensory cortex:    10%   — multimodal integration
      Amygdala:           6%   — salience/urgency
      Hippocampus:       10%   — memory, self-recurrent
      Cerebellum:         8%   — timing/error, fast
      Left prefrontal:   14%   — analytical reasoning, slow
      Right prefrontal:  14%   — pattern/creative reasoning, slow
      Corpus callosum:    5%   — inter-hemisphere bridge
      Anterior cingulate: 6%   — conflict monitoring
      Insula:             4%   — self-monitoring
      Motor cortex:       4%   — output sequencing
    """

    def __init__(self, input_size=1, hidden_size=128, n_properties=2, dropout=0.1, dt=1.0):
        super().__init__()
        self.hidden_size = hidden_size
        self.dt = dt
        H = hidden_size

        # Region sizes (percentages → absolute, minimum 4 each)
        def _sz(pct):
            return max(4, int(H * pct))

        sz = {
            "brainstem": _sz(0.05), "v1": _sz(0.08), "v2": _sz(0.06),
            "sensory": _sz(0.10), "amygdala": _sz(0.06), "hippo": _sz(0.10),
            "cerebellum": _sz(0.08), "left_pf": _sz(0.14), "right_pf": _sz(0.14),
            "callosum": _sz(0.05), "acc": _sz(0.06), "insula": _sz(0.04),
            "motor": _sz(0.04),
        }
        self.sz = sz

        # Input
        self.input_proj = nn.Linear(input_size, sz["v1"])

        # ── Regions ──

        # Brainstem — sets arousal baseline, fastest, always on
        self.brainstem = Region(sz["v1"], sz["brainstem"], dt_scale=3.0, name="brainstem")

        # Visual cortex — hierarchical, fast
        self.v1 = Region(sz["v1"], sz["v1"], dt_scale=2.5, name="visual_V1")
        self.v2 = Region(sz["v1"], sz["v2"], dt_scale=2.0, name="visual_V2")

        # Sensory cortex — integrates visual + brainstem arousal
        self.sensory = Region(sz["v2"] + sz["brainstem"], sz["sensory"], dt_scale=1.5, name="sensory")

        # Amygdala — fast salience detector, receives sensory
        self.amygdala = Region(sz["sensory"], sz["amygdala"], dt_scale=2.0,
                               self_loop=True, name="amygdala")

        # Hippocampus — memory, receives sensory + amygdala (emotional memory)
        self.hippo = Region(sz["sensory"] + sz["amygdala"], sz["hippo"], dt_scale=0.8,
                            self_loop=True, name="hippocampus")

        # Cerebellum — timing/error, fast, receives sensory + motor plan
        self.cerebellum = Region(sz["sensory"] + sz["left_pf"], sz["cerebellum"],
                                 dt_scale=1.8, name="cerebellum")

        # Left prefrontal — analytical, slow, receives sensory + hippo + amygdala
        pf_input = sz["sensory"] + sz["hippo"] + sz["amygdala"]
        self.left_pf = Region(pf_input, sz["left_pf"], dt_scale=0.25,
                              self_loop=True, name="left_prefrontal")

        # Right prefrontal — pattern/holistic, slow, same inputs
        self.right_pf = Region(pf_input, sz["right_pf"], dt_scale=0.3,
                               self_loop=True, name="right_prefrontal")

        # Corpus callosum — bridges the two hemispheres
        self.callosum = Region(sz["left_pf"] + sz["right_pf"], sz["callosum"],
                               dt_scale=1.2, name="corpus_callosum")

        # Anterior cingulate — conflict monitor, reads both PF + callosum
        self.acc = Region(sz["left_pf"] + sz["right_pf"] + sz["callosum"], sz["acc"],
                          dt_scale=0.6, name="anterior_cingulate")

        # Insula — self-monitoring, reads internal state summary
        insula_in = sz["brainstem"] + sz["amygdala"] + sz["acc"]
        self.insula = Region(insula_in, sz["insula"], dt_scale=0.5,
                             self_loop=True, name="insula")

        # Motor cortex — output sequencing, receives PF + cerebellum correction
        motor_in = sz["left_pf"] + sz["right_pf"] + sz["cerebellum"]
        self.motor = Region(motor_in, sz["motor"], dt_scale=1.5, name="motor_cortex")

        # ── Key axonal connections ──

        # Hippocampus → V1 (memory replay / imagination)
        self.hippo_to_v1 = Axon(sz["hippo"], sz["v1"])
        # Amygdala → Prefrontal (urgency signal, inhibitory — narrows focus)
        self.amygdala_to_pf = Axon(sz["amygdala"], sz["left_pf"], inhibitory=True)
        # Cerebellum → Motor (timing correction)
        self.cerebellum_to_motor = Axon(sz["cerebellum"], sz["motor"])
        # Insula → Brainstem (arousal modulation — matches brainstem input size)
        self.insula_to_brainstem = Axon(sz["insula"], sz["v1"])
        # ACC → both PF (conflict resolution signal — matches PF input size)
        self.acc_to_left = Axon(sz["acc"], pf_input)
        self.acc_to_right = Axon(sz["acc"], pf_input)

        # ── Output integration ──
        total = sum(sz.values())
        self.thalamus = nn.Sequential(nn.Linear(total, H), nn.LayerNorm(H), nn.Sigmoid())
        self.thalamic_proj = nn.Linear(total, H)

        # ── Heads ──
        self.next_step_head = nn.Sequential(nn.LayerNorm(H), nn.Linear(H, input_size))
        self.anomaly_head = nn.Sequential(nn.LayerNorm(H), nn.Linear(H, 1), nn.Sigmoid())
        self.property_head = nn.Sequential(
            nn.LayerNorm(H), nn.Linear(H, H // 2), nn.GELU(), nn.Linear(H // 2, n_properties))

    def forward(self, x, **kwargs):
        B, T, _ = x.shape
        sz = self.sz

        # Init all states
        S = {name: getattr(self, name.replace("left_pf", "left_pf").replace("right_pf", "right_pf"))
             for name in []}  # placeholder
        states = {}
        for name, region in [
            ("brainstem", self.brainstem), ("v1", self.v1), ("v2", self.v2),
            ("sensory", self.sensory), ("amygdala", self.amygdala), ("hippo", self.hippo),
            ("cerebellum", self.cerebellum), ("left_pf", self.left_pf), ("right_pf", self.right_pf),
            ("callosum", self.callosum), ("acc", self.acc), ("insula", self.insula), ("motor", self.motor),
        ]:
            states[name] = region.initial_state(B, x.device)

        outputs = []
        traces = {k: [] for k in states}

        for t in range(T):
            inp = self.input_proj(x[:, t, :])

            # Brainstem — baseline arousal + insula feedback
            if t > 0:
                inp_bs = inp + 0.1 * self.insula_to_brainstem(states["insula"])
            else:
                inp_bs = inp
            states["brainstem"] = self.brainstem.step(inp_bs, states["brainstem"], self.dt)

            # Visual V1 — raw features + hippocampal replay
            v1_in = inp
            if t > 0:
                v1_in = v1_in + 0.1 * self.hippo_to_v1(states["hippo"])
            states["v1"] = self.v1.step(v1_in, states["v1"], self.dt)

            # Visual V2 — higher features from V1
            states["v2"] = self.v2.step(states["v1"], states["v2"], self.dt)

            # Sensory integration — V2 + brainstem arousal
            sens_in = torch.cat([states["v2"], states["brainstem"]], dim=-1)
            states["sensory"] = self.sensory.step(sens_in, states["sensory"], self.dt)

            # Amygdala — salience from sensory
            states["amygdala"] = self.amygdala.step(states["sensory"], states["amygdala"], self.dt)

            # Hippocampus — memory from sensory + emotional tag
            hippo_in = torch.cat([states["sensory"], states["amygdala"]], dim=-1)
            states["hippo"] = self.hippo.step(hippo_in, states["hippo"], self.dt)

            # Prefrontal input — sensory + hippo + amygdala
            pf_in = torch.cat([states["sensory"], states["hippo"], states["amygdala"]], dim=-1)

            # Left PF — analytical + ACC conflict signal + amygdala urgency
            left_in = pf_in
            if t > 0:
                left_in = pf_in + 0.05 * self.acc_to_left(states["acc"])
            states["left_pf"] = self.left_pf.step(left_in, states["left_pf"], self.dt)
            states["left_pf"] = states["left_pf"] + 0.05 * self.amygdala_to_pf(states["amygdala"])

            # Right PF — holistic/pattern + ACC signal
            right_in = pf_in
            if t > 0:
                right_in = pf_in + 0.05 * self.acc_to_right(states["acc"])
            states["right_pf"] = self.right_pf.step(right_in, states["right_pf"], self.dt)

            # Corpus callosum — bridge hemispheres
            cal_in = torch.cat([states["left_pf"], states["right_pf"]], dim=-1)
            states["callosum"] = self.callosum.step(cal_in, states["callosum"], self.dt)

            # Anterior cingulate — conflict monitor
            acc_in = torch.cat([states["left_pf"], states["right_pf"], states["callosum"]], dim=-1)
            states["acc"] = self.acc.step(acc_in, states["acc"], self.dt)

            # Insula — self-monitoring
            ins_in = torch.cat([states["brainstem"], states["amygdala"], states["acc"]], dim=-1)
            states["insula"] = self.insula.step(ins_in, states["insula"], self.dt)

            # Cerebellum — timing, receives sensory + left PF plan
            cer_in = torch.cat([states["sensory"], states["left_pf"]], dim=-1)
            states["cerebellum"] = self.cerebellum.step(cer_in, states["cerebellum"], self.dt)

            # Motor cortex — output, both PFs + cerebellum correction
            motor_in = torch.cat([states["left_pf"], states["right_pf"], states["cerebellum"]], dim=-1)
            states["motor"] = self.motor.step(motor_in, states["motor"], self.dt)
            states["motor"] = states["motor"] + 0.1 * self.cerebellum_to_motor(states["cerebellum"])

            # Thalamic integration
            all_regions = torch.cat([states[k] for k in [
                "brainstem", "v1", "v2", "sensory", "amygdala", "hippo",
                "cerebellum", "left_pf", "right_pf", "callosum", "acc", "insula", "motor",
            ]], dim=-1)
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
        for name in ["brainstem", "v1", "v2", "sensory", "amygdala", "hippo",
                      "cerebellum", "left_pf", "right_pf", "callosum", "acc", "insula", "motor"]:
            counts[name] = sum(p.numel() for p in getattr(self, name).parameters())
        counts["connections"] = sum(
            sum(p.numel() for p in m.parameters())
            for m in [self.hippo_to_v1, self.amygdala_to_pf, self.cerebellum_to_motor,
                      self.insula_to_brainstem, self.acc_to_left, self.acc_to_right]
        )
        counts["thalamus"] = (sum(p.numel() for p in self.thalamus.parameters()) +
                              sum(p.numel() for p in self.thalamic_proj.parameters()))
        counts["heads"] = (sum(p.numel() for p in self.next_step_head.parameters()) +
                           sum(p.numel() for p in self.anomaly_head.parameters()) +
                           sum(p.numel() for p in self.property_head.parameters()))
        counts["total"] = sum(p.numel() for p in self.parameters())
        return counts
