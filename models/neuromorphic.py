"""
Neuromorphic Liquid Network — brain-region-inspired architecture.
=================================================================

This module maps the human brain's regional architecture onto liquid
neural network components. Each "region" is a liquid cell with biologically
motivated time constants, connectivity patterns, and computational roles.

Brain regions modeled:

  SENSORY CORTEX (fast, feedforward)
    - Fastest time constants — reacts to input immediately
    - Extracts patterns from raw signal
    - Feeds forward to all other regions

  HIPPOCAMPUS (memory, sequence)
    - Medium time constants with self-recurrence
    - Maintains a compressed memory of recent sequence
    - Replays patterns back to cortex (feedback connection)

  PREFRONTAL CORTEX (slow, integrative)
    - Slowest time constants — accumulates evidence over time
    - Working memory: holds context across long spans
    - Integrates signals from all other regions before output

  CEREBELLUM (timing, error)
    - Fast but error-driven — adjusts based on surprise
    - Receives copy of sensory input + prefrontal plan
    - Outputs correction signal that modulates other regions

  THALAMIC GATE (routing)
    - Learned gating between regions — controls information flow
    - Analogous to basal ganglia + thalamus relay

Design principles:
  - Each region is a LiquidCell with region-specific time constant init
  - Connections between regions mirror known neuroanatomy
  - The whole system is still differentiable end-to-end
  - Can be compared against the flat deep-liquid architecture to see
    which internal structures emerge independently

References (conceptual, not implementation):
  - Hasani et al. 2021 — Liquid Time-Constant Networks (C. elegans inspired)
  - Sussillo & Abbott 2009 — Generating coherent patterns from RNNs
  - Murray et al. 2014 — Hierarchy of timescales in primate cortex
"""
from __future__ import annotations

import math
import torch
from torch import nn

from models.liquid_core import LiquidCell


class BrainRegion(nn.Module):
    """
    A single brain region — a LiquidCell with biologically motivated
    initialization and optional self-recurrence.

    dt_scale: multiplier on the base dt — lower = slower integration
    self_recurrent: if True, feeds own output back as additional input
    """

    def __init__(self, input_size: int, hidden_size: int,
                 dt_scale: float = 1.0, self_recurrent: bool = False,
                 dropout: float = 0.0, name: str = "region"):
        super().__init__()
        self.name = name
        self.dt_scale = dt_scale
        self.hidden_size = hidden_size
        self.self_recurrent = self_recurrent

        # If self-recurrent, input includes own previous output
        effective_input = input_size + (hidden_size if self_recurrent else 0)
        self.cell = LiquidCell(effective_input, hidden_size, dropout=dropout)
        self.norm = nn.LayerNorm(hidden_size)

        # Initialize time constants based on biological role
        with torch.no_grad():
            if dt_scale < 0.5:
                # Slow region (prefrontal) — small step sizes
                self.cell.log_step.data -= 2.0  # sigmoid(-2) ≈ 0.12
            elif dt_scale > 1.5:
                # Fast region (sensory/cerebellum) — large step sizes
                self.cell.log_step.data += 1.0  # sigmoid(1) ≈ 0.73
            # Medium regions keep default sigmoid(0) = 0.5

    def initial_state(self, batch_size: int, device=None) -> torch.Tensor:
        return torch.zeros(batch_size, self.hidden_size, device=device)

    def step(self, x_t: torch.Tensor, state: torch.Tensor, dt: float = 1.0) -> torch.Tensor:
        """Process one timestep. x_t: [B, input_size]"""
        if self.self_recurrent:
            x_t = torch.cat([x_t, state], dim=-1)
        new_state = self.cell(x_t, state, dt=dt * self.dt_scale)
        return self.norm(new_state)


class InterRegionConnection(nn.Module):
    """
    Learned projection between two brain regions.
    Models axonal connections (e.g., hippocampus → prefrontal).

    Can be excitatory (positive bias init) or inhibitory (negative bias init).
    """

    def __init__(self, from_size: int, to_size: int,
                 excitatory: bool = True):
        super().__init__()
        self.proj = nn.Linear(from_size, to_size)
        self.gate = nn.Linear(from_size, to_size)
        # Bias toward excitatory or inhibitory
        with torch.no_grad():
            if not excitatory:
                self.proj.bias.data -= 0.5

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Gated projection: gate * tanh(proj(x))"""
        return torch.sigmoid(self.gate(x)) * torch.tanh(self.proj(x))


class NeuromorphicBrain(nn.Module):
    """
    Brain-region-inspired liquid neural network.

    Architecture mirrors human cortical hierarchy:

        Input
          │
          ▼
      ┌─────────────┐
      │ Sensory      │ (fast, dt×2.0)
      │ Cortex       │
      └──┬──┬──┬─────┘
         │  │  │
         │  │  └──────────────────┐
         │  │                     │
         ▼  ▼                     ▼
      ┌─────────┐          ┌────────────┐
      │ Hippo-  │◄────────►│ Cerebellum │ (fast, error-driven)
      │ campus  │ (memory)  └──────┬─────┘
      └────┬────┘                  │
           │                       │
           ▼                       │
      ┌──────────────┐             │
      │ Prefrontal   │◄────────────┘
      │ Cortex       │ (slow, integrative)
      └──────┬───────┘
             │
             ▼
        Thalamic Gate
             │
             ▼
        Output Heads
    """

    def __init__(
        self,
        input_size: int = 1,
        hidden_size: int = 64,
        n_properties: int = 2,
        dropout: float = 0.1,
        dt: float = 1.0,
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.dt = dt

        # Distribute hidden size across regions (not equal — mirrors cortex ratios)
        # Sensory: 25%, Hippocampus: 20%, Prefrontal: 35%, Cerebellum: 20%
        self.sensory_size = hidden_size // 4
        self.hippo_size = hidden_size // 5
        self.prefrontal_size = hidden_size - self.sensory_size - self.hippo_size - (hidden_size // 5)
        self.cerebellum_size = hidden_size // 5

        # Input projection
        self.input_proj = nn.Linear(input_size, self.sensory_size)

        # ── Brain regions ──

        self.sensory = BrainRegion(
            self.sensory_size, self.sensory_size,
            dt_scale=2.0, self_recurrent=False, dropout=dropout,
            name="sensory_cortex",
        )

        self.hippocampus = BrainRegion(
            self.sensory_size, self.hippo_size,
            dt_scale=0.8, self_recurrent=True, dropout=dropout,
            name="hippocampus",
        )

        self.cerebellum = BrainRegion(
            self.sensory_size + self.prefrontal_size, self.cerebellum_size,
            dt_scale=1.8, self_recurrent=False, dropout=dropout,
            name="cerebellum",
        )

        self.prefrontal = BrainRegion(
            self.sensory_size + self.hippo_size + self.cerebellum_size,
            self.prefrontal_size,
            dt_scale=0.3, self_recurrent=True, dropout=dropout,
            name="prefrontal_cortex",
        )

        # ── Inter-region connections ──

        # Hippocampus → Sensory (memory replay / feedback)
        self.hippo_to_sensory = InterRegionConnection(
            self.hippo_size, self.sensory_size, excitatory=True,
        )

        # Cerebellum → Prefrontal (error correction)
        self.cerebellum_to_prefrontal = InterRegionConnection(
            self.cerebellum_size, self.prefrontal_size, excitatory=False,  # inhibitory correction
        )

        # ── Thalamic gate (routes integrated signal) ──
        total_size = self.sensory_size + self.hippo_size + self.prefrontal_size + self.cerebellum_size
        self.thalamus = nn.Sequential(
            nn.Linear(total_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.Sigmoid(),
        )
        self.thalamic_proj = nn.Linear(total_size, hidden_size)

        # ── Output heads ──
        self.next_step_head = nn.Sequential(
            nn.LayerNorm(hidden_size),
            nn.Linear(hidden_size, input_size),
        )
        self.anomaly_head = nn.Sequential(
            nn.LayerNorm(hidden_size),
            nn.Linear(hidden_size, 1),
            nn.Sigmoid(),
        )
        self.property_head = nn.Sequential(
            nn.LayerNorm(hidden_size),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.GELU(),
            nn.Linear(hidden_size // 2, n_properties),
        )

    def _init_states(self, B: int, device) -> dict:
        return {
            "sensory": self.sensory.initial_state(B, device),
            "hippo": self.hippocampus.initial_state(B, device),
            "prefrontal": self.prefrontal.initial_state(B, device),
            "cerebellum": self.cerebellum.initial_state(B, device),
        }

    def encode(self, x: torch.Tensor) -> tuple[torch.Tensor, dict]:
        """
        Run input through the brain-region pipeline.

        Returns:
            hidden: [B, T, hidden_size] — thalamic-gated output
            region_activity: dict of per-region state histories for visualization
        """
        B, T, _ = x.shape
        states = self._init_states(B, x.device)

        all_outputs = []
        region_traces = {r: [] for r in ["sensory", "hippo", "prefrontal", "cerebellum"]}

        for t in range(T):
            x_t = self.input_proj(x[:, t, :])  # [B, sensory_size]

            # 1. Sensory cortex processes raw input + hippocampal replay
            if t > 0:
                replay = self.hippo_to_sensory(states["hippo"])
                x_t = x_t + replay  # modulate input with memory
            states["sensory"] = self.sensory.step(x_t, states["sensory"], dt=self.dt)

            # 2. Hippocampus receives sensory output (with self-recurrence)
            states["hippo"] = self.hippocampus.step(
                states["sensory"], states["hippo"], dt=self.dt,
            )

            # 3. Cerebellum receives sensory + prefrontal (error computation)
            cerebellum_input = torch.cat([states["sensory"], states["prefrontal"]], dim=-1)
            states["cerebellum"] = self.cerebellum.step(
                cerebellum_input, states["cerebellum"], dt=self.dt,
            )

            # 4. Prefrontal integrates everything (slowest, with self-recurrence)
            #    + cerebellar correction signal
            pf_input = torch.cat([
                states["sensory"], states["hippo"], states["cerebellum"],
            ], dim=-1)
            correction = self.cerebellum_to_prefrontal(states["cerebellum"])
            states["prefrontal"] = self.prefrontal.step(
                pf_input, states["prefrontal"], dt=self.dt,
            )
            states["prefrontal"] = states["prefrontal"] + 0.1 * correction  # subtle correction

            # 5. Thalamic routing — gate and project
            all_regions = torch.cat([
                states["sensory"], states["hippo"],
                states["prefrontal"], states["cerebellum"],
            ], dim=-1)
            gate = self.thalamus(all_regions)
            output = gate * self.thalamic_proj(all_regions)

            all_outputs.append(output)

            # Record traces for visualization
            for name in region_traces:
                region_traces[name].append(states[name].detach())

        hidden = torch.stack(all_outputs, dim=1)  # [B, T, H]

        # Stack traces
        for name in region_traces:
            region_traces[name] = torch.stack(region_traces[name], dim=1)

        return hidden, region_traces

    def forward(self, x: torch.Tensor, **kwargs) -> dict[str, torch.Tensor]:
        """
        Full forward pass.

        Returns dict matching the same interface as ScientistBrain (FoundationCore).
        """
        hidden, region_traces = self.encode(x)

        predictions = self.next_step_head(hidden[:, :-1, :])
        anomaly_score = self.anomaly_head(hidden).squeeze(-1)
        surprise = ((predictions - x[:, 1:, :]) ** 2).mean(dim=-1)
        properties = self.property_head(hidden[:, -1, :])

        return {
            "predictions": predictions,
            "hidden": hidden,
            "anomaly_score": anomaly_score,
            "surprise": surprise,
            "properties": properties,
            "region_traces": region_traces,  # extra: per-region activity
        }

    def combined_anomaly_score(self, x: torch.Tensor, **kwargs) -> torch.Tensor:
        out = self.forward(x)
        def _norm(t):
            mn, mx = t.min(), t.max()
            return (t - mn) / (mx - mn + 1e-9)
        return (_norm(out["surprise"]) + out["anomaly_score"][:, 1:]) / 2.0

    def param_count(self) -> dict[str, int]:
        counts = {
            "sensory_cortex": sum(p.numel() for p in self.sensory.parameters()),
            "hippocampus": sum(p.numel() for p in self.hippocampus.parameters()),
            "prefrontal_cortex": sum(p.numel() for p in self.prefrontal.parameters()),
            "cerebellum": sum(p.numel() for p in self.cerebellum.parameters()),
            "inter_region": (
                sum(p.numel() for p in self.hippo_to_sensory.parameters()) +
                sum(p.numel() for p in self.cerebellum_to_prefrontal.parameters())
            ),
            "thalamic_gate": (
                sum(p.numel() for p in self.thalamus.parameters()) +
                sum(p.numel() for p in self.thalamic_proj.parameters())
            ),
            "output_heads": (
                sum(p.numel() for p in self.next_step_head.parameters()) +
                sum(p.numel() for p in self.anomaly_head.parameters()) +
                sum(p.numel() for p in self.property_head.parameters())
            ),
        }
        counts["total"] = sum(p.numel() for p in self.parameters())
        return counts

    def region_summary(self) -> str:
        """Human-readable summary of the brain architecture."""
        return (
            f"Neuromorphic Liquid Brain ({self.hidden_size}h)\n"
            f"  Sensory Cortex:    {self.sensory_size}h, dt×2.0 (fast)\n"
            f"  Hippocampus:       {self.hippo_size}h, dt×0.8, self-recurrent (memory)\n"
            f"  Prefrontal Cortex: {self.prefrontal_size}h, dt×0.3, self-recurrent (slow/planning)\n"
            f"  Cerebellum:        {self.cerebellum_size}h, dt×1.8 (timing/error)\n"
            f"  Thalamic Gate:     {self.hidden_size}h (routing)\n"
            f"  Connections: hippo→sensory (replay), cerebellum→prefrontal (correction)\n"
            f"  Total params: {self.param_count()['total']:,}"
        )
