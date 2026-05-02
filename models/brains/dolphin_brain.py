"""
Dolphin Brain — massive cortex, hemispheric switching, paralimbic lobe.
=======================================================================

Key biological features:
  - Encephalization quotient second only to humans
  - MASSIVE neocortex — more cortical neurons than humans in some areas
  - Unihemispheric slow-wave sleep — one hemisphere stays awake
  - Paralimbic lobe — unique structure for social/emotional processing
  - Echolocation processing — specialized auditory cortex
  - Very thin cortex but spread over huge surface area
  - Reduced hippocampus relative to cortex size

Architecture insight: the hemispheric switching is the key.
At any timestep, one hemisphere is "primary" (higher dt) and the
other is "standby" (lower dt). They alternate, creating a unique
temporal interleaving that no other brain has.

References (conceptual):
  - Marino 2002 — dolphin brain evolution
  - Ridgway 2002 — unihemispheric sleep
  - Pack & Herman 2006 — dolphin cognition
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


class DolphinBrain(nn.Module):
    """
    Dolphin brain — hemispheric switching + massive cortex + paralimbic.

    The unique feature: hemispheres ALTERNATE being primary vs standby.
    This creates temporal interleaving that naturally handles long sequences.

    Region allocation:
      Auditory cortex (echolocation): 10%  — specialized sonar processing
      Left hemisphere cortex:         18%  — analytical (alternates primary)
      Right hemisphere cortex:        18%  — spatial (alternates primary)
      Paralimbic lobe:                10%  — social/emotional (unique to dolphins)
      Hippocampus (reduced):           6%  — small relative to cortex
      Cerebellum:                     10%  — motor coordination (swimming)
      Brainstem (arousal):             6%  — sleep/wake regulation (hemispheric switching controller)
      Corpus callosum (thick):         8%  — strong inter-hemisphere bridge
      Motor cortex:                    8%  — output
      Sensory cortex:                  6%  — multimodal integration
    """

    def __init__(self, input_size=1, hidden_size=128, n_properties=2, dropout=0.1, dt=1.0):
        super().__init__()
        self.hidden_size = hidden_size
        self.dt = dt
        H = hidden_size

        def _sz(pct):
            return max(4, int(H * pct))

        sz = {
            "auditory": _sz(0.10),    # echolocation
            "left_ctx": _sz(0.18),    # left hemisphere cortex
            "right_ctx": _sz(0.18),   # right hemisphere cortex
            "paralimbic": _sz(0.10),  # social/emotional (dolphin unique)
            "hippo": _sz(0.06),       # reduced hippocampus
            "cerebellum": _sz(0.10),  # motor coordination
            "brainstem": _sz(0.06),   # arousal / hemispheric switch controller
            "callosum": _sz(0.08),    # thick corpus callosum
            "motor": _sz(0.08),       # output
            "sensory": _sz(0.06),     # multimodal
        }
        self.sz = sz

        self.input_proj = nn.Linear(input_size, sz["auditory"])

        # Auditory cortex — echolocation, fast
        self.auditory = Region(sz["auditory"], sz["auditory"], dt_scale=2.5, name="auditory_cortex")

        # Sensory — multimodal, receives auditory
        self.sensory = Region(sz["auditory"], sz["sensory"], dt_scale=1.5, name="sensory_cortex")

        # Brainstem — controls hemispheric switching
        bs_in = sz["auditory"] + sz["sensory"]
        self.brainstem = Region(bs_in, sz["brainstem"], dt_scale=2.0, name="brainstem")

        # Hemispheres — same input, different dt based on which is "primary"
        ctx_in = sz["sensory"] + sz["auditory"] + sz["brainstem"]
        self.left_ctx = Region(ctx_in, sz["left_ctx"], dt_scale=0.3,
                               self_loop=True, name="left_hemisphere")
        self.right_ctx = Region(ctx_in, sz["right_ctx"], dt_scale=0.3,
                                self_loop=True, name="right_hemisphere")

        # Corpus callosum — thick bridge
        cal_in = sz["left_ctx"] + sz["right_ctx"]
        self.callosum = Region(cal_in, sz["callosum"], dt_scale=1.0, name="corpus_callosum")

        # Paralimbic — unique dolphin structure, social/emotional
        para_in = sz["left_ctx"] + sz["right_ctx"] + sz["callosum"]
        self.paralimbic = Region(para_in, sz["paralimbic"], dt_scale=0.5,
                                 self_loop=True, name="paralimbic_lobe")

        # Hippocampus — small, receives cortex
        hippo_in = sz["left_ctx"] + sz["right_ctx"]
        self.hippo = Region(hippo_in, sz["hippo"], dt_scale=0.7,
                            self_loop=True, name="hippocampus")

        # Cerebellum — swimming coordination
        cer_in = sz["sensory"] + sz["left_ctx"]
        self.cerebellum = Region(cer_in, sz["cerebellum"], dt_scale=1.8, name="cerebellum")

        # Motor — output
        motor_in = sz["left_ctx"] + sz["right_ctx"] + sz["cerebellum"]
        self.motor = Region(motor_in, sz["motor"], dt_scale=1.5, name="motor_cortex")

        # Connections
        self.paralimbic_to_ctx = Axon(sz["paralimbic"], ctx_in)  # social modulation
        self.hippo_to_auditory = Axon(sz["hippo"], sz["auditory"])  # memory replay

        # Hemispheric switching gate — learned alternation
        self.switch_gate = nn.Linear(sz["brainstem"], 2)  # outputs [left_weight, right_weight]

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
        region_names = ["auditory", "sensory", "brainstem", "left_ctx", "right_ctx",
                        "callosum", "paralimbic", "hippo", "cerebellum", "motor"]

        states = {}
        for name, region in [
            ("auditory", self.auditory), ("sensory", self.sensory), ("brainstem", self.brainstem),
            ("left_ctx", self.left_ctx), ("right_ctx", self.right_ctx),
            ("callosum", self.callosum), ("paralimbic", self.paralimbic),
            ("hippo", self.hippo), ("cerebellum", self.cerebellum), ("motor", self.motor),
        ]:
            states[name] = region.initial_state(B, x.device)

        outputs = []
        traces = {k: [] for k in states}

        for t in range(T):
            inp = self.input_proj(x[:, t, :])

            # Auditory cortex — echolocation input + memory replay
            aud_in = inp
            if t > 0:
                aud_in = aud_in + 0.1 * self.hippo_to_auditory(states["hippo"])
            states["auditory"] = self.auditory.step(aud_in, states["auditory"], self.dt)

            # Sensory integration
            states["sensory"] = self.sensory.step(states["auditory"], states["sensory"], self.dt)

            # Brainstem — controls hemispheric switching
            bs_in = torch.cat([states["auditory"], states["sensory"]], dim=-1)
            states["brainstem"] = self.brainstem.step(bs_in, states["brainstem"], self.dt)

            # HEMISPHERIC SWITCHING — the dolphin's unique trick
            # Brainstem outputs a soft switch: which hemisphere is "primary"
            switch = torch.softmax(self.switch_gate(states["brainstem"]), dim=-1)  # [B, 2]
            left_dt_mult = 0.5 + switch[:, 0:1]   # primary hemisphere runs faster
            right_dt_mult = 0.5 + switch[:, 1:2]

            # Both hemispheres receive same input, different effective dt
            ctx_in = torch.cat([states["sensory"], states["auditory"], states["brainstem"]], dim=-1)
            if t > 0:
                ctx_in = ctx_in + 0.05 * self.paralimbic_to_ctx(states["paralimbic"])

            states["left_ctx"] = self.left_ctx.step(ctx_in, states["left_ctx"],
                                                     self.dt * float(left_dt_mult.detach().mean()))
            states["right_ctx"] = self.right_ctx.step(ctx_in, states["right_ctx"],
                                                       self.dt * float(right_dt_mult.detach().mean()))

            # Corpus callosum — bridge
            cal_in = torch.cat([states["left_ctx"], states["right_ctx"]], dim=-1)
            states["callosum"] = self.callosum.step(cal_in, states["callosum"], self.dt)

            # Paralimbic — social/emotional, unique to dolphins
            para_in = torch.cat([states["left_ctx"], states["right_ctx"], states["callosum"]], dim=-1)
            states["paralimbic"] = self.paralimbic.step(para_in, states["paralimbic"], self.dt)

            # Hippocampus
            hippo_in = torch.cat([states["left_ctx"], states["right_ctx"]], dim=-1)
            states["hippo"] = self.hippo.step(hippo_in, states["hippo"], self.dt)

            # Cerebellum
            cer_in = torch.cat([states["sensory"], states["left_ctx"]], dim=-1)
            states["cerebellum"] = self.cerebellum.step(cer_in, states["cerebellum"], self.dt)

            # Motor
            motor_in = torch.cat([states["left_ctx"], states["right_ctx"], states["cerebellum"]], dim=-1)
            states["motor"] = self.motor.step(motor_in, states["motor"], self.dt)

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
        for name in ["auditory", "sensory", "brainstem", "left_ctx", "right_ctx",
                      "callosum", "paralimbic", "hippo", "cerebellum", "motor"]:
            counts[name] = sum(p.numel() for p in getattr(self, name).parameters())
        counts["connections"] = (
            sum(p.numel() for p in self.paralimbic_to_ctx.parameters()) +
            sum(p.numel() for p in self.hippo_to_auditory.parameters()) +
            sum(p.numel() for p in self.switch_gate.parameters())
        )
        counts["total"] = sum(p.numel() for p in self.parameters())
        return counts
