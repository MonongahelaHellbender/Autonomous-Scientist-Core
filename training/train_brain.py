"""
Train the ScientistBrain model.
================================

Supports:
  - Sequence prediction (unsupervised, like Tasuke)
  - Anomaly detection (with Tasuke's benchmark suite)
  - Warm start from Tasuke checkpoints via bridge
  - Domain-aware training with curriculum
  - Background auto-train mode
"""
from __future__ import annotations

import json
import sys
import time
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from models.scientist_brain import ScientistBrain, DOMAIN_MAP
from models.bridge import (
    save_main_checkpoint, get_tasuke_generators,
    list_tasuke_checkpoints, transfer_tasuke_to_brain,
    MAIN_CHECKPOINT, MAIN_OUTPUT,
)

OUTPUT_DIR = MAIN_OUTPUT


@dataclass
class TrainConfig:
    # Model
    hidden_size: int = 64
    n_layers: int = 3
    n_domains: int = 4
    multi_scale: bool = True
    dropout: float = 0.1
    # Data
    seq_len: int = 80
    n_series: int = 120
    batch_size: int = 32
    # Training
    train_steps: int = 800
    learning_rate: float = 0.002
    seed: int = 0
    # Warm start
    warm_start: bool = True
    transfer_from_tasuke: bool = True
    tasuke_checkpoint: str = ""  # auto-select best if empty
    # Output
    protect_checkpoint: bool = True


# ── Data generation ───────────────────────────────────────────────────────────

def _local_generators() -> dict:
    """Built-in generators (no Tasuke dependency)."""
    def _sine_mix(rng, length):
        t = np.linspace(0, 4 * np.pi, length)
        n = rng.integers(1, 4)
        result = np.zeros(length, dtype=np.float32)
        for _ in range(n):
            result += rng.uniform(0.3, 1.5) * np.sin(rng.uniform(0.5, 3.0) * t + rng.uniform(0, 6.28))
        return result

    def _ar1(rng, length):
        phi = rng.uniform(0.7, 0.98)
        seq = np.zeros(length, dtype=np.float32)
        for i in range(1, length):
            seq[i] = phi * seq[i-1] + rng.normal(0, 0.15)
        return seq

    def _damped(rng, length):
        t = np.arange(length, dtype=np.float32) / length
        return (rng.uniform(0.5, 2) * np.exp(-rng.uniform(1, 4) * t) *
                np.sin(2 * np.pi * rng.uniform(4, 12) * t)).astype(np.float32)

    def _trend(rng, length):
        return (rng.uniform(-1, 1) + rng.uniform(-0.02, 0.02) * np.arange(length) +
                rng.normal(0, 0.08, length)).astype(np.float32)

    def _sawtooth(rng, length):
        p = rng.integers(15, 40)
        return (rng.uniform(0.5, 2) * ((np.arange(length) % p) / p - 0.5)).astype(np.float32)

    return {
        "sine_mix": _sine_mix, "ar1": _ar1, "damped": _damped,
        "trend": _trend, "sawtooth": _sawtooth,
    }


def get_all_generators() -> dict:
    """Merge local + Tasuke generators."""
    gens = _local_generators()
    tasuke_gens = get_tasuke_generators()
    gens.update(tasuke_gens)  # Tasuke overrides locals if same name
    return gens


def generate_batch(generators: dict, rng: np.random.Generator,
                   batch_size: int, seq_len: int) -> tuple[torch.Tensor, list[str]]:
    """Generate a batch of normalized sequences. Returns tensor [B, T, 1] and domain names."""
    gen_names = list(generators.keys())
    seqs = []
    domains = []
    for _ in range(batch_size):
        name = rng.choice(gen_names)
        seq = generators[name](rng, seq_len)
        mu, sigma = seq.mean(), max(seq.std(), 1e-8)
        seqs.append(((seq - mu) / sigma).astype(np.float32))
        domains.append(name)
    return torch.tensor(np.stack(seqs)).unsqueeze(-1), domains


# ── Training loop ─────────────────────────────────────────────────────────────

def run_training(cfg: TrainConfig,
                 progress_cb: Optional[Callable] = None,
                 ) -> dict:
    """
    Train the ScientistBrain model.

    Returns results dict with loss history, metrics, and model info.
    """
    rng = np.random.default_rng(cfg.seed)
    device = torch.device("cpu")

    # Build model
    brain = ScientistBrain(
        input_size=1,
        hidden_size=cfg.hidden_size,
        n_layers=cfg.n_layers,
        n_domains=cfg.n_domains,
        multi_scale=cfg.multi_scale,
        dropout=cfg.dropout,
    )

    # Warm start
    transfer_report = None
    if cfg.warm_start and MAIN_CHECKPOINT.exists():
        try:
            state = torch.load(MAIN_CHECKPOINT, map_location=device, weights_only=True)
            brain.load_state_dict(state, strict=False)
        except Exception:
            pass

    # Transfer from Tasuke
    if cfg.transfer_from_tasuke:
        tasuke_ckpts = list_tasuke_checkpoints()
        if tasuke_ckpts:
            # Pick the best checkpoint (lowest MSE, or first if no MSE recorded)
            ckpt = cfg.tasuke_checkpoint
            if not ckpt:
                best = min(tasuke_ckpts,
                           key=lambda c: c.get("best_mse") or 999.0)
                ckpt = best["path"]
            try:
                transfer_report = transfer_tasuke_to_brain(brain, ckpt, target="fast")
            except Exception as e:
                transfer_report = {"error": str(e)}

    # Get generators
    generators = get_all_generators()
    gen_count = len(generators)

    optimizer = torch.optim.AdamW(brain.parameters(), lr=cfg.learning_rate, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=cfg.train_steps)
    loss_fn = nn.MSELoss()

    loss_history = []
    best_loss = float("inf")
    t0 = time.time()

    brain.train()
    for step in range(cfg.train_steps):
        batch, domains = generate_batch(generators, rng, cfg.batch_size, cfg.seq_len)
        batch = batch.to(device)

        # Use most common domain in batch for gating
        domain = max(set(domains), key=domains.count)

        out = brain(batch, domain=domain)
        pred_loss = loss_fn(out["predictions"], batch[:, 1:, :])

        optimizer.zero_grad()
        pred_loss.backward()
        torch.nn.utils.clip_grad_norm_(brain.parameters(), 1.0)
        optimizer.step()
        scheduler.step()

        if step % 25 == 0 or step == cfg.train_steps - 1:
            loss_val = float(pred_loss.item())
            loss_history.append({
                "step": step,
                "loss": loss_val,
                "lr": float(scheduler.get_last_lr()[0]),
            })
            if progress_cb:
                progress_cb(step, cfg.train_steps, loss_val)

    train_time = time.time() - t0

    # Eval
    brain.eval()
    with torch.no_grad():
        eval_batch, eval_domains = generate_batch(generators, rng, cfg.batch_size * 4, cfg.seq_len)
        eval_out = brain(eval_batch)
        eval_loss = float(loss_fn(eval_out["predictions"], eval_batch[:, 1:, :]).item())
        mean_surprise = float(eval_out["surprise"].mean().item())

    # Save checkpoint
    should_save = True
    if cfg.protect_checkpoint and MAIN_CHECKPOINT.exists():
        try:
            old_meta = json.loads(MAIN_CHECKPOINT.with_suffix(".json").read_text())
            if old_meta.get("eval_loss", float("inf")) <= eval_loss:
                should_save = False
        except Exception:
            pass

    if should_save:
        meta = {
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "eval_loss": eval_loss,
            "mean_surprise": mean_surprise,
            "config": asdict(cfg),
            "param_count": brain.param_count(),
            "generator_count": gen_count,
            "transfer_report": transfer_report,
        }
        save_main_checkpoint(brain, meta)

    results = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "experiment": "scientist_brain_training",
        "train_time_sec": round(train_time, 2),
        "eval_loss": eval_loss,
        "mean_surprise": mean_surprise,
        "loss_history": loss_history,
        "config": asdict(cfg),
        "param_count": brain.param_count(),
        "generator_count": gen_count,
        "generator_names": sorted(generators.keys()),
        "transfer_report": transfer_report,
        "checkpoint_saved": should_save,
    }

    # Save artifact
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"brain_training_{cfg.seed}.json"
    out_path.write_text(json.dumps(results, indent=2) + "\n")

    return results


# ── Auto-train (background) ──────────────────────────────────────────────────

def run_auto_train(stop_event: threading.Event,
                   status_cb: Callable[[str], None],
                   cfg: TrainConfig) -> None:
    """Run training rounds in a loop until stop_event is set."""
    round_num = 0
    while not stop_event.is_set():
        round_num += 1
        cfg_round = TrainConfig(**{
            **asdict(cfg),
            "seed": cfg.seed + round_num,
            "train_steps": min(cfg.train_steps, 400),  # shorter rounds for auto
        })
        status_cb(f"Round {round_num}: training {cfg_round.train_steps} steps...")
        try:
            results = run_training(cfg_round)
            status_cb(
                f"Round {round_num} done: loss={results['eval_loss']:.5f}, "
                f"saved={results['checkpoint_saved']}"
            )
        except Exception as e:
            status_cb(f"Round {round_num} error: {e}")
        if stop_event.wait(2.0):  # brief pause between rounds
            break


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Training ScientistBrain...")
    cfg = TrainConfig()
    results = run_training(cfg, progress_cb=lambda s, t, l: print(f"  step {s}/{t}  loss={l:.5f}"))
    print(f"\nEval loss: {results['eval_loss']:.5f}")
    print(f"Mean surprise: {results['mean_surprise']:.5f}")
    print(f"Architecture: pure deep liquid ({cfg.hidden_size}h × 3 layers, multi-scale)")
    print(f"Parameters: {results['param_count']}")
    print(f"Generators: {results['generator_count']} ({', '.join(results['generator_names'][:10])}...)")
    if results.get("transfer_report"):
        tr = results["transfer_report"]
        print(f"Tasuke transfer: {tr.get('transferred', 0)} weights loaded from {tr.get('source', '?')}")
