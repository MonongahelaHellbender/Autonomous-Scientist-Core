"""
Multi-head temporal attention for time series.

The liquid cell processes sequences step-by-step (local context).
This module adds global context — each timestep can attend to all others.

Applied AFTER the liquid cell, so the attention operates on hidden states
that already encode continuous-time dynamics.
"""
from __future__ import annotations

import math
import torch
from torch import nn


class MultiHeadTimeAttention(nn.Module):
    """
    Self-attention over a sequence of hidden states.

    Input:  [batch, time, hidden_size]
    Output: [batch, time, hidden_size]

    Features beyond standard attention:
      - Causal mask (optional) so the model can't peek at future timesteps
      - Attention entropy output for anomaly scoring
      - Relative position bias
    """

    def __init__(self, hidden_size: int, n_heads: int = 4,
                 dropout: float = 0.0, causal: bool = True,
                 max_seq_len: int = 512):
        super().__init__()
        assert hidden_size % n_heads == 0, f"hidden_size {hidden_size} must be divisible by n_heads {n_heads}"
        self.hidden_size = hidden_size
        self.n_heads = n_heads
        self.head_dim = hidden_size // n_heads
        self.causal = causal

        self.qkv = nn.Linear(hidden_size, 3 * hidden_size)
        self.out_proj = nn.Linear(hidden_size, hidden_size)
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(hidden_size)

        # Relative position bias (learned, per head)
        self.rel_pos_bias = nn.Parameter(torch.zeros(n_heads, 2 * max_seq_len - 1))
        nn.init.trunc_normal_(self.rel_pos_bias, std=0.02)
        self._max_seq_len = max_seq_len

    def _get_rel_pos(self, seq_len: int) -> torch.Tensor:
        """Return [n_heads, seq_len, seq_len] relative position bias."""
        positions = torch.arange(seq_len, device=self.rel_pos_bias.device)
        rel = positions.unsqueeze(0) - positions.unsqueeze(1)  # [T, T]
        rel = rel + self._max_seq_len - 1  # shift to non-negative
        rel = rel.clamp(0, 2 * self._max_seq_len - 2)
        return self.rel_pos_bias[:, rel]  # [n_heads, T, T]

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            output: [B, T, hidden_size]
            attn_entropy: [B, T] — per-timestep attention entropy (high = uncertain = anomalous)
        """
        B, T, D = x.shape
        residual = x
        x = self.layer_norm(x)

        qkv = self.qkv(x).reshape(B, T, 3, self.n_heads, self.head_dim)
        q, k, v = qkv.unbind(dim=2)  # each [B, T, n_heads, head_dim]
        q = q.transpose(1, 2)  # [B, n_heads, T, head_dim]
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)

        scale = math.sqrt(self.head_dim)
        attn = torch.matmul(q, k.transpose(-2, -1)) / scale  # [B, n_heads, T, T]

        # Add relative position bias
        if T <= self._max_seq_len:
            attn = attn + self._get_rel_pos(T).unsqueeze(0)

        # Causal mask
        if self.causal:
            mask = torch.triu(torch.ones(T, T, device=x.device, dtype=torch.bool), diagonal=1)
            attn = attn.masked_fill(mask.unsqueeze(0).unsqueeze(0), float('-inf'))

        attn_weights = torch.softmax(attn, dim=-1)  # [B, n_heads, T, T]
        attn_weights = self.dropout(attn_weights)

        out = torch.matmul(attn_weights, v)  # [B, n_heads, T, head_dim]
        out = out.transpose(1, 2).reshape(B, T, D)
        out = self.out_proj(out)
        out = residual + out

        # Attention entropy: -sum(p * log(p)) averaged over heads
        # Clamp to avoid log(0)
        p = attn_weights.clamp(min=1e-9)
        entropy = -(p * p.log()).sum(dim=-1).mean(dim=1)  # [B, T]

        return out, entropy
