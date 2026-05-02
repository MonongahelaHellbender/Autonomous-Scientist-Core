"""
Bridge between Tasuke and the main assistant.
==============================================

Functions to:
  1. Load Tasuke's trained weights into the main model's liquid cell
  2. Transfer Tasuke's anomaly benchmark results as evaluation context
  3. Share training data generators between the two systems
  4. Sync improvements: if Tasuke improves on a domain, the main model can absorb it

The bridge is one-directional by default (Tasuke → Main) because the main model
is strictly more capable. But Tasuke can also benefit from the main model's
attention-enriched representations fed back as soft targets.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import torch

# Paths
MAIN_ROOT = Path(__file__).resolve().parents[1]
TASUKE_ROOT = MAIN_ROOT / "Tasuke"
TASUKE_SRC = TASUKE_ROOT / "src"
TASUKE_OUTPUT = TASUKE_ROOT / "output"
TASUKE_EXPERIMENTS = TASUKE_ROOT / "experiments"

MAIN_OUTPUT = MAIN_ROOT / "outputs" / "models"
MAIN_CHECKPOINT = MAIN_OUTPUT / "scientist_brain.pt"
MAIN_CHECKPOINT_META = MAIN_OUTPUT / "scientist_brain_meta.json"


def tasuke_available() -> bool:
    """Check if Tasuke project exists and has trained checkpoints."""
    return (TASUKE_ROOT / "src" / "liquid_cell.py").exists()


def list_tasuke_checkpoints() -> list[dict]:
    """List all Tasuke checkpoints with their metadata."""
    if not TASUKE_OUTPUT.exists():
        return []
    results = []
    for pt_file in sorted(TASUKE_OUTPUT.glob("ckpt_*.pt")):
        meta_file = pt_file.with_suffix(".json")
        meta = {}
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text())
            except Exception:
                pass
        results.append({
            "path": str(pt_file),
            "name": pt_file.stem,
            "size_kb": round(pt_file.stat().st_size / 1024, 1),
            "best_mse": meta.get("best_mse"),
            "domain": "math" if "math" in pt_file.stem else
                      "real" if "real" in pt_file.stem else
                      "bridge" if "bridge" in pt_file.stem else "unknown",
        })
    return results


def load_tasuke_weights(checkpoint_path: str | Path,
                        target_hidden_size: int = 64) -> dict[str, torch.Tensor]:
    """
    Load a Tasuke checkpoint and prepare weight mappings for the main model.

    Tasuke's LiquidTimeConstantCell has:
      - input_proj.weight/bias
      - recurrent_proj.weight
      - gate_proj.weight/bias
      - bias (cell bias)
      - log_step

    The main model's LiquidCell has the same + layer_norm.

    If hidden sizes differ, we pad or truncate to fit.
    """
    state = torch.load(str(checkpoint_path), map_location="cpu", weights_only=True)

    # Tasuke stores as model state dict with 'cell.' prefix
    cell_weights = {}
    for key, val in state.items():
        if key.startswith("cell."):
            cell_weights[key.replace("cell.", "")] = val

    if not cell_weights:
        # Maybe the checkpoint is already just cell weights
        cell_weights = state

    tasuke_hidden = cell_weights.get("log_step", torch.zeros(1)).shape[0]

    # If sizes match, return directly
    if tasuke_hidden == target_hidden_size:
        return cell_weights

    # Otherwise, pad or truncate
    adapted = {}
    for key, val in cell_weights.items():
        if val.dim() == 1:
            # 1D parameter: hidden_size
            if val.shape[0] < target_hidden_size:
                padded = torch.zeros(target_hidden_size)
                padded[:val.shape[0]] = val
                adapted[key] = padded
            else:
                adapted[key] = val[:target_hidden_size]
        elif val.dim() == 2:
            # 2D weight: [out, in] — adapt both dims if needed
            out_dim, in_dim = val.shape
            new_out = min(out_dim, target_hidden_size) if out_dim != 1 else out_dim
            new_in = min(in_dim, target_hidden_size) if in_dim != 1 else in_dim
            padded = torch.zeros(
                target_hidden_size if out_dim != 1 else 1,
                target_hidden_size if in_dim != 1 else 1,
            )
            padded[:new_out, :new_in] = val[:new_out, :new_in]
            adapted[key] = padded
        else:
            adapted[key] = val

    return adapted


def transfer_tasuke_to_brain(brain: torch.nn.Module,
                              checkpoint_path: str | Path,
                              target: str = "fast") -> dict:
    """
    Transfer Tasuke weights into the ScientistBrain's liquid cell.

    target: "fast" loads into the fast lane of MultiScaleLiquidCell,
            "slow" loads into the slow lane,
            "single" loads into a single-scale LiquidCell.

    Returns transfer report dict.
    """
    from models.scientist_brain import ScientistBrain

    hidden_size = brain.hidden_size
    cell_weights = load_tasuke_weights(checkpoint_path, hidden_size // 2 if target != "single" else hidden_size)

    loaded_keys = []
    skipped_keys = []

    if target == "single":
        prefix = "liquid."
    elif target == "fast":
        prefix = "liquid.fast_cell."
    else:
        prefix = "liquid.slow_cell."

    brain_state = brain.state_dict()
    for key, val in cell_weights.items():
        full_key = prefix + key
        if full_key in brain_state and brain_state[full_key].shape == val.shape:
            brain_state[full_key] = val
            loaded_keys.append(full_key)
        else:
            skipped_keys.append(full_key)

    brain.load_state_dict(brain_state, strict=False)

    return {
        "transferred": len(loaded_keys),
        "skipped": len(skipped_keys),
        "loaded_keys": loaded_keys,
        "skipped_keys": skipped_keys,
        "source": str(checkpoint_path),
        "target_lane": target,
    }


def get_tasuke_benchmark_results() -> list[dict]:
    """Load Tasuke's anomaly benchmark results for comparison."""
    results = []
    if not TASUKE_OUTPUT.exists():
        return results
    for f in sorted(TASUKE_OUTPUT.glob("anomaly_benchmark_*.json")):
        try:
            data = json.loads(f.read_text())
            results.append({
                "file": f.name,
                "created_at": data.get("created_at"),
                "aggregate": data.get("aggregate", {}),
                "per_scenario": data.get("per_scenario", {}),
            })
        except Exception:
            pass
    return results


def get_tasuke_generators():
    """
    Import Tasuke's sequence generators so the main model can train on the same data.

    Returns dict of generator functions, or empty dict if Tasuke not available.
    """
    if not tasuke_available():
        return {}

    if str(TASUKE_EXPERIMENTS) not in sys.path:
        sys.path.insert(0, str(TASUKE_EXPERIMENTS))
    if str(TASUKE_SRC) not in sys.path:
        sys.path.insert(0, str(TASUKE_SRC))

    generators = {}
    try:
        from train_unsupervised import (
            _gen_arithmetic, _gen_geometric, _gen_polynomial, _gen_sine_mix,
            _gen_recurrence, _gen_modular, _gen_mixed,
            _gen_pendulum, _gen_damped_oscillator, _gen_lorenz_x,
            _gen_logistic_map, _gen_van_der_pol, _gen_wave_interference,
            _gen_prime_gaps, _gen_collatz, _gen_euler_totient,
            _gen_partial_zeta, _gen_chebyshev, _gen_farey_fractions,
        )
        generators = {
            # Math
            "arithmetic": _gen_arithmetic, "geometric": _gen_geometric,
            "polynomial": _gen_polynomial, "sine_mix": _gen_sine_mix,
            "recurrence": _gen_recurrence, "modular": _gen_modular,
            "mixed": _gen_mixed,
            # Physics
            "pendulum": _gen_pendulum, "damped_osc": _gen_damped_oscillator,
            "lorenz_x": _gen_lorenz_x, "logistic_map": _gen_logistic_map,
            "van_der_pol": _gen_van_der_pol, "wave_interference": _gen_wave_interference,
            # Number theory
            "prime_gaps": _gen_prime_gaps, "collatz": _gen_collatz,
            "euler_totient": _gen_euler_totient, "partial_zeta": _gen_partial_zeta,
            "chebyshev": _gen_chebyshev, "farey_fractions": _gen_farey_fractions,
        }
    except ImportError:
        pass
    return generators


def save_main_checkpoint(brain: torch.nn.Module, meta: dict) -> Path:
    """Save the main model checkpoint with metadata sidecar."""
    MAIN_OUTPUT.mkdir(parents=True, exist_ok=True)
    torch.save(brain.state_dict(), MAIN_CHECKPOINT)
    MAIN_CHECKPOINT_META.write_text(json.dumps(meta, indent=2) + "\n")
    return MAIN_CHECKPOINT
