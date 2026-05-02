"""
Self-Improvement Module — each brain can analyze its own weaknesses and evolve.
================================================================================

Evolution is mass trial-and-error. This module gives each brain that capability:

1. Diagnose — run eval, find which generators/patterns it struggles with
2. Prescribe — adjust training focus (oversample hard patterns)
3. Mutate — randomly perturb architecture hyperparameters (dt_scale, connections)
4. Select — keep mutations that improve, discard those that don't
5. Log — track evolutionary history so we can see the adaptation path

Each brain maintains its own evolution log. The ensemble can share
discoveries across brains (horizontal gene transfer).
"""
from __future__ import annotations

import json
import time
import copy
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[2]

import sys
sys.path.insert(0, str(ROOT))

from training.train_brain import get_all_generators, generate_batch


@dataclass
class EvolutionConfig:
    """Config for a self-improvement cycle."""
    train_steps: int = 200
    batch_size: int = 32
    seq_len: int = 80
    lr: float = 0.002
    mutation_rate: float = 0.1      # probability of mutating each region's dt
    mutation_strength: float = 0.2  # magnitude of dt perturbation
    n_candidates: int = 3           # mutations per generation
    elite_keep: int = 1             # best candidates kept


def diagnose(model: nn.Module, generators: dict, rng, batch_size=64, seq_len=80) -> Dict:
    """Find which patterns this brain struggles with."""
    model.eval()
    loss_fn = nn.MSELoss()
    per_gen = {}

    with torch.no_grad():
        for gen_name, gen_fn in list(generators.items())[:20]:
            gen_rng = np.random.default_rng(42 + hash(gen_name) % 10000)
            seqs = []
            for _ in range(16):
                seq = gen_fn(gen_rng, seq_len)
                mu, sigma = seq.mean(), max(seq.std(), 1e-8)
                seqs.append(((seq - mu) / sigma).astype(np.float32))
            batch = torch.tensor(np.stack(seqs)).unsqueeze(-1)
            out = model(batch)
            loss = float(loss_fn(out["predictions"], batch[:, 1:, :]).item())
            per_gen[gen_name] = loss

    # Sort by difficulty
    ranked = sorted(per_gen.items(), key=lambda x: x[1], reverse=True)
    weaknesses = [name for name, _ in ranked[:5]]
    strengths = [name for name, _ in ranked[-5:]]

    return {
        "per_generator": per_gen,
        "weaknesses": weaknesses,
        "strengths": strengths,
        "mean_loss": np.mean(list(per_gen.values())),
        "worst_loss": ranked[0][1] if ranked else 0,
        "best_loss": ranked[-1][1] if ranked else 0,
    }


def focused_train(model: nn.Module, generators: dict, weaknesses: List[str],
                  cfg: EvolutionConfig, rng) -> float:
    """Train with oversampling of weak patterns."""
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=0.01)
    loss_fn = nn.MSELoss()

    # Build weighted generator list — 3x weight on weaknesses
    weighted_gens = {}
    for name, fn in generators.items():
        weighted_gens[name] = fn
    for name in weaknesses:
        if name in generators:
            for i in range(2):  # add 2 extra copies
                weighted_gens[f"{name}_extra_{i}"] = generators[name]

    model.train()
    for step in range(cfg.train_steps):
        batch, _ = generate_batch(weighted_gens, rng, cfg.batch_size, cfg.seq_len)
        out = model(batch)
        loss = loss_fn(out["predictions"], batch[:, 1:, :])
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

    # Final eval loss
    model.eval()
    with torch.no_grad():
        eval_batch, _ = generate_batch(generators, rng, cfg.batch_size * 4, cfg.seq_len)
        eval_out = model(eval_batch)
        return float(loss_fn(eval_out["predictions"], eval_batch[:, 1:, :]).item())


def mutate_dt_scales(model: nn.Module, rate: float = 0.1, strength: float = 0.2):
    """Randomly perturb time constants of regions (evolutionary mutation)."""
    mutations = []
    with torch.no_grad():
        for name, module in model.named_modules():
            if hasattr(module, 'cell') and hasattr(module.cell, 'log_step'):
                if np.random.random() < rate:
                    delta = np.random.randn() * strength
                    module.cell.log_step.data += delta
                    mutations.append({"region": name, "delta": round(delta, 4)})
    return mutations


def self_improve_cycle(model: nn.Module, brain_name: str,
                       cfg: EvolutionConfig = None,
                       progress_cb=None) -> Dict:
    """
    One full self-improvement cycle:
    1. Diagnose weaknesses
    2. Create mutant candidates
    3. Focused-train each candidate on weaknesses
    4. Keep the best
    """
    if cfg is None:
        cfg = EvolutionConfig()

    generators = get_all_generators()
    rng = np.random.default_rng(int(time.time()) % 100000)

    # 1. Diagnose
    if progress_cb:
        progress_cb("diagnosing", 0, 1)
    diagnosis = diagnose(model, generators, rng)

    # 2. Create candidates (original + mutations)
    candidates = [("original", model, [])]
    for i in range(cfg.n_candidates):
        mutant = copy.deepcopy(model)
        mutations = mutate_dt_scales(mutant, cfg.mutation_rate, cfg.mutation_strength)
        candidates.append((f"mutant_{i}", mutant, mutations))

    # 3. Train each candidate with focus on weaknesses
    results = []
    for j, (label, candidate, mutations) in enumerate(candidates):
        if progress_cb:
            progress_cb(f"training {label}", j, len(candidates))
        eval_loss = focused_train(
            candidate, generators, diagnosis["weaknesses"],
            cfg, np.random.default_rng(rng.integers(0, 100000)))
        results.append({
            "label": label,
            "eval_loss": eval_loss,
            "mutations": mutations,
        })

    # 4. Select best
    results.sort(key=lambda x: x["eval_loss"])
    best = results[0]
    best_model = [c[1] for c in candidates if c[0] == best["label"]][0]

    # Copy best weights back to original model
    model.load_state_dict(best_model.state_dict())

    improvement = diagnosis["mean_loss"] - best["eval_loss"]

    return {
        "brain": brain_name,
        "before_loss": diagnosis["mean_loss"],
        "after_loss": best["eval_loss"],
        "improvement": improvement,
        "improvement_pct": round(improvement / max(diagnosis["mean_loss"], 1e-9) * 100, 2),
        "winner": best["label"],
        "mutations_applied": best["mutations"],
        "weaknesses_targeted": diagnosis["weaknesses"],
        "all_candidates": results,
        "diagnosis": diagnosis,
    }
