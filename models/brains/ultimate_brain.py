"""
Ultimate Brain — chimera combining the best features from all brains.
=====================================================================

Takes the winning design choices from each species:
  - Human: cortical hierarchy with slow/fast timescales
  - Octopus: distributed peripheral processing (arm modules)
  - Corvid: dense flat connectivity (no wasted hierarchy)
  - Dolphin: hemispheric switching (temporal interleaving)
  - Insect: dual-track learned vs innate pathways
  - Alien: global workspace + self-model + adaptive dt

Architecture:
  Sensory → [learned track / innate track] →
  Left hemisphere ←switch→ Right hemisphere (dolphin-style) →
  Global workspace (alien-style) →
  Distributed processors (octopus-style arms) →
  Self-model (alien-style recursive monitoring) →
  Dense cross-talk layer (corvid-style flat connectivity) →
  Motor output

This is the "if evolution could start over with all the tricks" brain.
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
        self.name = name
        self.h_size = h_size
        self.dt_scale = dt_scale
        self.self_loop = self_loop
        self.adaptive_dt = adaptive_dt
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


class UltimateBrain(nn.Module):
    """
    Chimera brain — best features from all species + alien optimizations.

    Region allocation:
      Sensory (fast):            8%   — input processing
      Learned track (insect):    8%   — flexible learned pathway
      Innate track (insect):     6%   — fast hardwired pathway
      Left hemisphere (human):  10%   — analytical
      Right hemisphere (human): 10%   — pattern/spatial
      Global workspace (alien):  8%   — shared blackboard
      Distributed A (octopus):   6%   — peripheral processor 1
      Distributed B (octopus):   6%   — peripheral processor 2
      Distributed C (octopus):   6%   — peripheral processor 3
      Dense hub (corvid):       10%   — flat cross-talk center
      Self-model (alien):        6%   — recursive self-monitoring
      Memory (human hippo):      8%   — episodic memory
      Motor (output):            8%   — sequencing
    """

    def __init__(self, input_size=1, hidden_size=128, n_properties=2, dropout=0.1, dt=1.0):
        super().__init__()
        self.hidden_size = hidden_size
        self.dt = dt
        H = hidden_size

        def _sz(pct):
            return max(4, int(H * pct))

        sz = {
            "sensory": _sz(0.08),
            "learned": _sz(0.08),     # insect mushroom body analog
            "innate": _sz(0.06),      # insect lateral horn analog
            "left_h": _sz(0.10),      # human hemisphere
            "right_h": _sz(0.10),     # human hemisphere
            "workspace": _sz(0.08),   # alien global workspace
            "dist_a": _sz(0.06),      # octopus distributed
            "dist_b": _sz(0.06),
            "dist_c": _sz(0.06),
            "dense_hub": _sz(0.10),   # corvid flat connectivity
            "selfmodel": _sz(0.06),   # alien self-model
            "memory": _sz(0.08),      # human hippocampus
            "motor": _sz(0.08),       # output
        }
        self.sz = sz

        self.input_proj = nn.Linear(input_size, sz["sensory"])

        # Sensory — fast
        self.sensory = Region(sz["sensory"], sz["sensory"], dt_scale=2.5, name="sensory")

        # INSECT DUAL TRACK
        dual_in = sz["sensory"]
        self.learned = Region(dual_in, sz["learned"], dt_scale=0.7,
                              self_loop=True, name="learned_track")
        self.innate = Region(dual_in, sz["innate"], dt_scale=2.5, name="innate_track")

        # Innate inhibits learned (danger override)
        self.innate_inhibit = Axon(sz["innate"], sz["learned"], inhibitory=True)

        # DOLPHIN HEMISPHERIC SWITCHING
        hemi_in = sz["learned"] + sz["innate"] + sz["sensory"]
        self.left_h = Region(hemi_in, sz["left_h"], dt_scale=0.3,
                             self_loop=True, name="left_hemisphere")
        self.right_h = Region(hemi_in, sz["right_h"], dt_scale=0.3,
                              self_loop=True, name="right_hemisphere")
        self.switch_gate = nn.Linear(sz["sensory"], 2)

        # ALIEN GLOBAL WORKSPACE
        ws_in = sz["left_h"] + sz["right_h"]
        self.workspace = Region(ws_in, sz["workspace"], adaptive_dt=True,
                                self_loop=True, name="global_workspace")

        # OCTOPUS DISTRIBUTED PROCESSORS
        dist_in = sz["workspace"] + sz["sensory"]
        self.dist_a = Region(dist_in, sz["dist_a"], dt_scale=1.8,
                             self_loop=True, name="distributed_A")
        self.dist_b = Region(dist_in, sz["dist_b"], dt_scale=1.8,
                             self_loop=True, name="distributed_B")
        self.dist_c = Region(dist_in, sz["dist_c"], dt_scale=1.8,
                             self_loop=True, name="distributed_C")

        # CORVID DENSE HUB — reads everything, flat cross-talk
        total_dist = sz["dist_a"] + sz["dist_b"] + sz["dist_c"]
        hub_in = sz["workspace"] + total_dist + sz["left_h"] + sz["right_h"]
        self.dense_hub = Region(hub_in, sz["dense_hub"], adaptive_dt=True,
                                self_loop=True, name="dense_hub")

        # HUMAN MEMORY
        mem_in = sz["sensory"] + sz["dense_hub"]
        self.memory = Region(mem_in, sz["memory"], dt_scale=0.6,
                             self_loop=True, name="episodic_memory")

        # ALIEN SELF-MODEL
        sm_in = sz["workspace"] + sz["dense_hub"] + sz["memory"]
        self.selfmodel = Region(sm_in, sz["selfmodel"], adaptive_dt=True,
                                self_loop=True, name="self_model")

        # Motor output
        motor_in = sz["dense_hub"] + sz["selfmodel"] + sz["memory"]
        self.motor = Region(motor_in, sz["motor"], dt_scale=1.5, name="motor")

        # Feedback connections
        self.memory_replay = Axon(sz["memory"], sz["sensory"])
        self.selfmodel_fb = Axon(sz["selfmodel"], ws_in)

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
        region_names = sorted(sz.keys())

        states = {}
        for name, region in [
            ("sensory", self.sensory), ("learned", self.learned), ("innate", self.innate),
            ("left_h", self.left_h), ("right_h", self.right_h), ("workspace", self.workspace),
            ("dist_a", self.dist_a), ("dist_b", self.dist_b), ("dist_c", self.dist_c),
            ("dense_hub", self.dense_hub), ("memory", self.memory),
            ("selfmodel", self.selfmodel), ("motor", self.motor),
        ]:
            states[name] = region.initial_state(B, x.device)

        outputs = []
        traces = {k: [] for k in states}

        for t in range(T):
            inp = self.input_proj(x[:, t, :])

            # Sensory + memory replay
            s_in = inp
            if t > 0:
                s_in = s_in + 0.1 * self.memory_replay(states["memory"])
            states["sensory"] = self.sensory.step(s_in, states["sensory"], self.dt)

            # Dual track (insect)
            states["innate"] = self.innate.step(states["sensory"], states["innate"], self.dt)
            l_in = states["sensory"]
            if t > 0:
                l_in = l_in + 0.1 * self.innate_inhibit(states["innate"])
            states["learned"] = self.learned.step(l_in, states["learned"], self.dt)

            # Hemispheric switching (dolphin)
            hemi_in = torch.cat([states["learned"], states["innate"], states["sensory"]], dim=-1)
            switch = torch.softmax(self.switch_gate(states["sensory"]), dim=-1)
            states["left_h"] = self.left_h.step(hemi_in, states["left_h"],
                                                 self.dt * float(0.5 + switch[:, 0].detach().mean()))
            states["right_h"] = self.right_h.step(hemi_in, states["right_h"],
                                                   self.dt * float(0.5 + switch[:, 1].detach().mean()))

            # Global workspace (alien)
            ws_in = torch.cat([states["left_h"], states["right_h"]], dim=-1)
            if t > 0:
                ws_in_state = ws_in + 0.05 * self.selfmodel_fb(states["selfmodel"])
                # Pad/truncate to match expected size
                if ws_in_state.shape[-1] != ws_in.shape[-1]:
                    ws_in = ws_in
                else:
                    ws_in = ws_in_state
            states["workspace"] = self.workspace.step(ws_in, states["workspace"], self.dt)

            # Distributed processors (octopus)
            dist_in = torch.cat([states["workspace"], states["sensory"]], dim=-1)
            states["dist_a"] = self.dist_a.step(dist_in, states["dist_a"], self.dt)
            states["dist_b"] = self.dist_b.step(dist_in, states["dist_b"], self.dt)
            states["dist_c"] = self.dist_c.step(dist_in, states["dist_c"], self.dt)

            # Dense hub (corvid)
            all_dist = torch.cat([states["dist_a"], states["dist_b"], states["dist_c"]], dim=-1)
            hub_in = torch.cat([states["workspace"], all_dist,
                                states["left_h"], states["right_h"]], dim=-1)
            states["dense_hub"] = self.dense_hub.step(hub_in, states["dense_hub"], self.dt)

            # Memory
            mem_in = torch.cat([states["sensory"], states["dense_hub"]], dim=-1)
            states["memory"] = self.memory.step(mem_in, states["memory"], self.dt)

            # Self-model (alien)
            sm_in = torch.cat([states["workspace"], states["dense_hub"], states["memory"]], dim=-1)
            states["selfmodel"] = self.selfmodel.step(sm_in, states["selfmodel"], self.dt)

            # Motor
            motor_in = torch.cat([states["dense_hub"], states["selfmodel"], states["memory"]], dim=-1)
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
        for name in sorted(self.sz.keys()):
            attr = name
            if hasattr(self, attr):
                counts[name] = sum(p.numel() for p in getattr(self, attr).parameters())
        counts["total"] = sum(p.numel() for p in self.parameters())
        return counts
