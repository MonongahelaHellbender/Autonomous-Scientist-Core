"""
Liquid core — the continuous-time recurrent cell and predictor.

This is the main assistant's own copy of the liquid architecture, extended
beyond Tasuke's version with:
  - Multi-scale time constants (fast + slow processing lanes)
  - Layer normalization for training stability
  - Residual connections for deeper stacking
  - Dropout for regularization
"""
from __future__ import annotations

import torch
from torch import nn


class LiquidCell(nn.Module):
    """
    Liquid time-constant cell with learned per-unit time scales.

    Improvement over Tasuke's cell:
      - LayerNorm on the gate input for stable training at larger hidden sizes
      - Optional residual connection when input_size == hidden_size
    """

    def __init__(self, input_size: int, hidden_size: int, dropout: float = 0.0):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.input_proj = nn.Linear(input_size, hidden_size)
        self.recurrent_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.gate_proj = nn.Linear(input_size + hidden_size, hidden_size)
        self.bias = nn.Parameter(torch.zeros(hidden_size))
        self.log_step = nn.Parameter(torch.zeros(hidden_size))
        self.layer_norm = nn.LayerNorm(input_size + hidden_size)
        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()
        self._residual = input_size == hidden_size

    def initial_state(self, batch_size: int, device: torch.device | None = None) -> torch.Tensor:
        return torch.zeros(batch_size, self.hidden_size, device=device)

    def forward(self, x_t: torch.Tensor, state: torch.Tensor, dt: float = 1.0) -> torch.Tensor:
        step_size = torch.sigmoid(self.log_step).unsqueeze(0)
        drive = self.input_proj(x_t) + self.recurrent_proj(torch.tanh(state)) + self.bias
        gate_input = self.layer_norm(torch.cat([x_t, state], dim=-1))
        gate = torch.sigmoid(self.gate_proj(gate_input))
        target = torch.tanh(drive)
        blend = torch.clamp(dt * step_size * gate, max=1.0)
        new_state = state + blend * (target - state)
        new_state = self.dropout(new_state)
        return new_state


class MultiScaleLiquidCell(nn.Module):
    """
    Two parallel liquid cells at different time scales — fast lane captures
    rapid dynamics, slow lane captures trends. Their outputs are concatenated
    and projected back to hidden_size.

    This is the key architectural advantage over Tasuke's single-scale cell.
    """

    def __init__(self, input_size: int, hidden_size: int, dropout: float = 0.0):
        super().__init__()
        fast_size = hidden_size // 2
        slow_size = hidden_size - fast_size
        self.fast_cell = LiquidCell(input_size, fast_size, dropout=dropout)
        self.slow_cell = LiquidCell(input_size, slow_size, dropout=dropout)
        self.merge = nn.Linear(hidden_size, hidden_size)
        self.hidden_size = hidden_size
        self._fast_size = fast_size
        self._slow_size = slow_size
        # Slow cell gets smaller time constants by default
        with torch.no_grad():
            self.slow_cell.log_step.data -= 1.5  # sigmoid(-1.5) ≈ 0.18 vs sigmoid(0) = 0.5

    def initial_state(self, batch_size: int, device: torch.device | None = None) -> torch.Tensor:
        return torch.zeros(batch_size, self.hidden_size, device=device)

    def forward(self, x_t: torch.Tensor, state: torch.Tensor, dt: float = 1.0) -> torch.Tensor:
        fast_state = state[:, :self._fast_size]
        slow_state = state[:, self._fast_size:]
        new_fast = self.fast_cell(x_t, fast_state, dt=dt)
        new_slow = self.slow_cell(x_t, slow_state, dt=dt * 0.3)  # slow lane runs at 0.3× speed
        merged = torch.cat([new_fast, new_slow], dim=-1)
        return self.merge(merged)


class LiquidPredictor(nn.Module):
    """
    Next-step predictor using multi-scale liquid cell.
    Drop-in replacement for Tasuke's LiquidNextStepPredictor with richer dynamics.
    """

    def __init__(self, input_size: int = 1, hidden_size: int = 64,
                 dt: float = 1.0, multi_scale: bool = True, dropout: float = 0.0):
        super().__init__()
        self.hidden_size = hidden_size
        self.dt = dt
        if multi_scale:
            self.cell = MultiScaleLiquidCell(input_size, hidden_size, dropout=dropout)
        else:
            self.cell = LiquidCell(input_size, hidden_size, dropout=dropout)
        self.readout = nn.Linear(hidden_size, input_size)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        B, T, _ = x.shape
        state = self.cell.initial_state(B, device=x.device)
        preds, states = [], []
        for t in range(T):
            state = self.cell(x[:, t, :], state, dt=self.dt)
            states.append(state)
            if t < T - 1:
                preds.append(self.readout(state))
        return torch.stack(preds, dim=1), torch.stack(states, dim=1)

    def surprise(self, x: torch.Tensor) -> torch.Tensor:
        """Per-timestep squared prediction error."""
        preds, _ = self.forward(x)
        return ((preds - x[:, 1:, :]) ** 2).mean(dim=-1)
