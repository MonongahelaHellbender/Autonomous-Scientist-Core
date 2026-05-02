"""
Foundation Core — the neural backbone of the Foundation AI system.
==================================================================

Pure deep liquid architecture. No transformers, no attention.
Every layer is continuous-time dynamics — the same architectural family
as the Liquid Lab (Tasuke), but deeper and more capable.

Architecture:

    Input → Projection → [Liquid Layer 1] → [Liquid Layer 2] → [Liquid Layer 3]
                              ↓ residual         ↓ residual         ↓
                           Domain Gate ──────────────────────────→ Heads
                                                                   ├─ next-step predictor
                                                                   ├─ anomaly scorer
                                                                   └─ property regressor

Each liquid layer is a MultiScaleLiquidCell (fast + slow lanes).
Residual connections between layers let gradients flow.
Layer normalization between layers keeps training stable at depth.

Why no attention:
  The whole project is "liquid networks earning trust from the bottom up."
  If this architecture hits a ceiling on long-range tasks later, attention
  can be added then — with evidence for why it was needed.
  For now, the system is one coherent architectural family end to end.
"""
from __future__ import annotations

import torch
from torch import nn

from models.liquid_core import LiquidCell, MultiScaleLiquidCell


class LiquidBlock(nn.Module):
    """
    One block of the deep liquid stack:
      MultiScaleLiquidCell → LayerNorm → residual add

    The residual connection means deeper stacks don't lose the signal.
    """

    def __init__(self, hidden_size: int, multi_scale: bool = True, dropout: float = 0.0):
        super().__init__()
        if multi_scale:
            self.cell = MultiScaleLiquidCell(hidden_size, hidden_size, dropout=dropout)
        else:
            self.cell = LiquidCell(hidden_size, hidden_size, dropout=dropout)
        self.norm = nn.LayerNorm(hidden_size)

    def forward(self, x_t: torch.Tensor, state: torch.Tensor, dt: float = 1.0) -> torch.Tensor:
        """Single timestep: returns new state with residual connection."""
        new_state = self.cell(x_t, state, dt=dt)
        return self.norm(state + new_state)  # residual + normalize

    def initial_state(self, batch_size: int, device=None) -> torch.Tensor:
        return self.cell.initial_state(batch_size, device)


class DomainGate(nn.Module):
    """
    Soft gating that weights hidden states differently per domain.

    n_domains: number of expert lanes (e.g., math=0, physics=1, real=2, materials=3)
    Each domain has a learned weighting vector over hidden dimensions.
    """

    def __init__(self, hidden_size: int, n_domains: int = 4):
        super().__init__()
        self.n_domains = n_domains
        self.gate_weights = nn.Parameter(torch.ones(n_domains, hidden_size))
        nn.init.normal_(self.gate_weights, mean=1.0, std=0.1)

    def forward(self, x: torch.Tensor, domain_id: int = 0) -> torch.Tensor:
        """Apply domain-specific soft gating. x: [B, T, H] or [B, H]"""
        gate = torch.sigmoid(self.gate_weights[domain_id])
        if x.dim() == 3:
            gate = gate.unsqueeze(0).unsqueeze(0)
        else:
            gate = gate.unsqueeze(0)
        return x * gate


DOMAIN_MAP = {
    "math": 0, "physics": 1, "real": 2, "materials": 3,
    # Tasuke-compatible aliases
    "math:arithmetic": 0, "math:geometric": 0, "math:polynomial": 0,
    "math:sine_mix": 0, "math:recurrence": 0, "math:modular": 0,
    "math:pendulum": 1, "math:lorenz_x": 1, "math:logistic_map": 1,
    "math:van_der_pol": 1, "math:damped_osc": 1, "math:wave_interference": 1,
    "math:prime_gaps": 0, "math:collatz": 0, "math:euler_totient": 0,
    "kepler": 2, "classical": 2, "dynamics": 2,
    "bridge": 2,
}


class ScientistBrain(nn.Module):
    """
    Pure deep liquid neural network.

    Stacked multi-scale liquid cells with residual connections,
    domain gating, and three output heads.

    Capabilities:
      1. Next-step prediction (unsupervised sequence learning)
      2. Anomaly detection (surprise from prediction error + learned anomaly head)
      3. Property regression (conductivity, activation energy, etc.)
    """

    def __init__(
        self,
        input_size: int = 1,
        hidden_size: int = 64,
        n_layers: int = 3,
        n_domains: int = 4,
        n_properties: int = 2,
        multi_scale: bool = True,
        dropout: float = 0.1,
        dt: float = 1.0,
        # kept for backward compat but unused in pure liquid mode
        n_attention_heads: int = 4,
        max_seq_len: int = 512,
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.n_layers = n_layers
        self.dt = dt

        # Input projection
        self.input_proj = nn.Linear(input_size, hidden_size)

        # Stacked liquid layers
        self.layers = nn.ModuleList([
            LiquidBlock(hidden_size, multi_scale=multi_scale, dropout=dropout)
            for _ in range(n_layers)
        ])

        # Domain gating (applied after the full stack)
        self.domain_gate = DomainGate(hidden_size, n_domains)

        # Output heads
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

    def encode(self, x: torch.Tensor, domain: str = "math") -> torch.Tensor:
        """
        Run input through the full liquid stack.

        Args:
            x: [B, T, input_size]
            domain: domain string for gating

        Returns:
            hidden: [B, T, hidden_size] — full hidden state sequence
        """
        B, T, _ = x.shape
        domain_id = DOMAIN_MAP.get(domain, 0)

        # Project input
        x_proj = self.input_proj(x)  # [B, T, H]

        # Initialize state for each layer
        layer_states = [layer.initial_state(B, device=x.device) for layer in self.layers]

        all_states = []
        for t in range(T):
            h = x_proj[:, t, :]  # input to first layer at this timestep

            for i, layer in enumerate(self.layers):
                layer_states[i] = layer(h, layer_states[i], dt=self.dt)
                h = layer_states[i]  # output of this layer feeds next layer

            all_states.append(h)

        hidden = torch.stack(all_states, dim=1)  # [B, T, H]

        # Domain gating
        hidden = self.domain_gate(hidden, domain_id)

        return hidden

    def forward(self, x: torch.Tensor, domain: str = "math") -> dict[str, torch.Tensor]:
        """
        Full forward pass with all heads.

        Returns dict with:
            predictions:    [B, T-1, input_size] — next-step predictions
            hidden:         [B, T, hidden_size]
            anomaly_score:  [B, T] — learned anomaly probability
            surprise:       [B, T-1] — prediction error (MSE per step)
            properties:     [B, n_properties] — from final hidden state
        """
        hidden = self.encode(x, domain)

        # Next-step prediction (from t to predict t+1)
        predictions = self.next_step_head(hidden[:, :-1, :])

        # Anomaly score (learned head)
        anomaly_score = self.anomaly_head(hidden).squeeze(-1)

        # Surprise (prediction error — the liquid network's native anomaly signal)
        surprise = ((predictions - x[:, 1:, :]) ** 2).mean(dim=-1)

        # Property prediction from final state
        properties = self.property_head(hidden[:, -1, :])

        return {
            "predictions": predictions,
            "hidden": hidden,
            "anomaly_score": anomaly_score,
            "surprise": surprise,
            "properties": properties,
        }

    def combined_anomaly_score(self, x: torch.Tensor, domain: str = "math") -> torch.Tensor:
        """
        Fused anomaly signal: surprise + learned anomaly head.
        Returns [B, T-1] combined score (higher = more anomalous).
        """
        out = self.forward(x, domain)

        def _norm(t):
            mn, mx = t.min(), t.max()
            return (t - mn) / (mx - mn + 1e-9)

        surprise_n = _norm(out["surprise"])
        anomaly_n = out["anomaly_score"][:, 1:]  # align with surprise length

        return (surprise_n + anomaly_n) / 2.0

    def param_count(self) -> dict[str, int]:
        """Return parameter counts per component."""
        counts = {
            "liquid_stack": sum(
                sum(p.numel() for p in layer.parameters())
                for layer in self.layers
            ),
            "domain_gate": sum(p.numel() for p in self.domain_gate.parameters()),
            "next_step_head": sum(p.numel() for p in self.next_step_head.parameters()),
            "anomaly_head": sum(p.numel() for p in self.anomaly_head.parameters()),
            "property_head": sum(p.numel() for p in self.property_head.parameters()),
            "input_proj": sum(p.numel() for p in self.input_proj.parameters()),
        }
        counts["total"] = sum(p.numel() for p in self.parameters())
        return counts


# Canonical name + backward-compatible alias
FoundationCore = ScientistBrain
