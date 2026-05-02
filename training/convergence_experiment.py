"""
Convergence Experiment — do different architectures discover the same structure?
================================================================================

Trains three variants on identical data and compares what they learn:

  1. Foundation Core (flat deep liquid — 3 stacked layers)
  2. Neuromorphic Brain (brain-region layout — sensory/hippo/prefrontal/cerebellum)
  3. Minimal Liquid (single-layer, Liquid Lab style — baseline control)

The question: when trained from scratch on the same sequences, do the
architectures converge on similar internal representations? If the
brain-layout version and the flat version develop similar hidden state
geometry, that tells us the structure is *necessary* — not just a human
design choice.

Metrics compared:
  - Eval loss (prediction quality)
  - Surprise distribution (anomaly sensitivity)
  - Hidden state geometry (PCA of internal states)
  - Per-generator performance (which architectures struggle where)
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from models.scientist_brain import ScientistBrain
from models.neuromorphic import NeuromorphicBrain
from models.liquid_core import LiquidPredictor
from training.train_brain import get_all_generators, generate_batch

OUTPUT_DIR = ROOT / "outputs" / "convergence"


@dataclass
class ConvergenceConfig:
    hidden_size: int = 64
    train_steps: int = 600
    batch_size: int = 32
    seq_len: int = 80
    learning_rate: float = 0.002
    seed: int = 42


def _normalize_output(model, x):
    """Ensure output is a dict regardless of model type."""
    out = model(x)
    if isinstance(out, dict):
        return out
    # LiquidPredictor returns (predictions, states)
    preds, states = out
    surprise = ((preds - x[:, 1:, :]) ** 2).mean(dim=-1)
    return {
        "predictions": preds,
        "hidden": states,
        "anomaly_score": surprise,  # use surprise as anomaly proxy
        "surprise": surprise,
        "properties": torch.zeros(x.shape[0], 2),
    }


def _train_model(model, generators, cfg, rng, label, progress_cb=None):
    """Train a model and return eval metrics."""
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.learning_rate, weight_decay=0.01)
    loss_fn = nn.MSELoss()
    loss_history = []

    model.train()
    t0 = time.time()
    for step in range(cfg.train_steps):
        batch, domains = generate_batch(generators, rng, cfg.batch_size, cfg.seq_len)
        out = _normalize_output(model, batch)
        loss = loss_fn(out["predictions"], batch[:, 1:, :])
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        if step % 50 == 0:
            loss_history.append({"step": step, "loss": float(loss.item())})
            if progress_cb:
                progress_cb(label, step, cfg.train_steps, float(loss.item()))
    train_time = time.time() - t0

    # Eval
    model.eval()
    per_generator = {}
    with torch.no_grad():
        # Overall eval
        eval_batch, _ = generate_batch(generators, rng, cfg.batch_size * 4, cfg.seq_len)
        eval_out = _normalize_output(model, eval_batch)
        eval_loss = float(loss_fn(eval_out["predictions"], eval_batch[:, 1:, :]).item())
        mean_surprise = float(eval_out["surprise"].mean().item())
        surprise_std = float(eval_out["surprise"].std().item())

        # Hidden state geometry — PCA variance ratios
        hidden = eval_out["hidden"][:, -1, :].numpy()  # final states
        if hidden.shape[1] > 3:
            centered = hidden - hidden.mean(axis=0)
            try:
                _, s, _ = np.linalg.svd(centered, full_matrices=False)
                variance_ratios = (s ** 2) / (s ** 2).sum()
                pca_top3 = float(variance_ratios[:3].sum())
                pca_top1 = float(variance_ratios[0])
            except Exception:
                pca_top3, pca_top1 = 0.0, 0.0
        else:
            pca_top3, pca_top1 = 1.0, 1.0

        # Per-generator eval
        gen_names = list(generators.keys())
        for gen_name in gen_names[:12]:  # sample of generators
            gen_rng = np.random.default_rng(cfg.seed + hash(gen_name) % 10000)
            seqs = []
            for _ in range(16):
                seq = generators[gen_name](gen_rng, cfg.seq_len)
                mu, sigma = seq.mean(), max(seq.std(), 1e-8)
                seqs.append(((seq - mu) / sigma).astype(np.float32))
            gen_batch = torch.tensor(np.stack(seqs)).unsqueeze(-1)
            gen_out = _normalize_output(model, gen_batch)
            gen_loss = float(loss_fn(gen_out["predictions"], gen_batch[:, 1:, :]).item())
            per_generator[gen_name] = round(gen_loss, 5)

    return {
        "label": label,
        "eval_loss": eval_loss,
        "mean_surprise": mean_surprise,
        "surprise_std": surprise_std,
        "pca_top1_ratio": pca_top1,
        "pca_top3_ratio": pca_top3,
        "train_time_sec": round(train_time, 2),
        "loss_history": loss_history,
        "per_generator": per_generator,
        "param_count": (model.param_count()["total"] if hasattr(model, "param_count")
                        else sum(p.numel() for p in model.parameters())),
    }


def run_convergence(cfg: ConvergenceConfig,
                    progress_cb: Optional[Callable] = None) -> dict:
    """Train all three variants and compare."""
    generators = get_all_generators()

    # Build models
    models = {
        "Foundation Core (deep liquid)": ScientistBrain(
            input_size=1, hidden_size=cfg.hidden_size, n_layers=3,
            multi_scale=True, dropout=0.1,
        ),
        "Neuromorphic Brain (brain regions)": NeuromorphicBrain(
            input_size=1, hidden_size=cfg.hidden_size, dropout=0.1,
        ),
        "Minimal Liquid (single layer)": LiquidPredictor(
            input_size=1, hidden_size=cfg.hidden_size, multi_scale=False, dropout=0.0,
        ),
    }

    results = {}
    for label, model in models.items():
        rng = np.random.default_rng(cfg.seed)  # same seed = same data
        results[label] = _train_model(model, generators, cfg, rng, label, progress_cb)

    # Compute convergence metrics
    labels = list(results.keys())
    gen_names = list(set().union(*(r["per_generator"].keys() for r in results.values())))

    # Where do architectures agree/disagree on difficulty?
    agreement = {}
    for gen_name in gen_names:
        losses = [results[l]["per_generator"].get(gen_name, 999) for l in labels]
        rankings = list(np.argsort(losses))
        agreement[gen_name] = {
            "losses": {l: results[l]["per_generator"].get(gen_name) for l in labels},
            "best": labels[rankings[0]],
            "spread": round(max(losses) - min(losses), 5),
        }

    # Hidden state geometry similarity
    geometry_note = (
        "If PCA top-3 ratios are similar across architectures, they're discovering "
        "similar low-dimensional structure despite different wiring."
    )

    output = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "experiment": "convergence_comparison",
        "config": asdict(cfg),
        "generator_count": len(generators),
        "models": results,
        "per_generator_agreement": agreement,
        "geometry_note": geometry_note,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"convergence_{cfg.seed}.json"
    out_path.write_text(json.dumps(output, indent=2) + "\n")

    return output


if __name__ == "__main__":
    print("Running convergence experiment...")
    cfg = ConvergenceConfig()

    def _cb(label, step, total, loss):
        print(f"  [{label[:20]:20s}] step {step}/{total}  loss={loss:.5f}")

    results = run_convergence(cfg, progress_cb=_cb)

    print("\n" + "=" * 70)
    print("CONVERGENCE RESULTS")
    print("=" * 70)
    for label, r in results["models"].items():
        print(f"\n{label}:")
        print(f"  Eval loss:    {r['eval_loss']:.5f}")
        print(f"  Surprise:     {r['mean_surprise']:.5f} (std={r['surprise_std']:.5f})")
        print(f"  PCA top-3:    {r['pca_top3_ratio']:.3f}")
        print(f"  Parameters:   {r['param_count']:,}")
        print(f"  Train time:   {r['train_time_sec']:.1f}s")
