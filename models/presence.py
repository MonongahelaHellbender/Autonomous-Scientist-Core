"""
Foundation Presence — adaptive AI visual identity.
===================================================

A living visual entity that Foundation determines how to present based on
its own internal state. Unlike the Liquid Lab's orb which reads from a JSON
file, this one derives its state FROM the model itself:
  - Surprise level → animation speed
  - Training loss → color temperature
  - Domain active → shape morphology

States:
  idle      — Deep blue nebula, slow drift, calm particles
  learning  — Electric cyan, fast rings, data particles streaming
  analyzing — Amber-gold, pulsing core, attention ripples
  alert     — Red-shift, erratic morphing, warning pulse
  ready     — Emerald bloom, stable geometry, confident glow
  genesis   — Violet-deep, cosmic, first-light animation

The entity is hexagonal-based (vs Tasuke's circular orb) to visually
distinguish the main assistant as a more structured intelligence.
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]


def _infer_state_from_model(checkpoint_meta_path: Path) -> tuple[str, str, str]:
    """
    Derive visual state from the model's own metrics.
    This is how the AI 'decides' how to present itself.
    """
    if not checkpoint_meta_path.exists():
        return "genesis", "Scientist awakening", "No trained model yet"

    try:
        meta = json.loads(checkpoint_meta_path.read_text())
    except Exception:
        return "alert", "State read error", "Could not parse model metadata"

    eval_loss = meta.get("eval_loss", 999)
    mean_surprise = meta.get("mean_surprise", 999)
    mean_surprise = meta.get("mean_surprise", 999)
    param_count = meta.get("param_count", {}).get("total", 0)

    # The AI decides its presentation based on its own performance
    if eval_loss < 0.05:
        return "ready", "High confidence", f"Loss: {eval_loss:.4f} | Sharp attention"
    elif eval_loss < 0.15:
        return "analyzing", "Processing patterns", f"Loss: {eval_loss:.4f} | {param_count:,} params active"
    elif eval_loss < 0.30:
        return "learning", "Building understanding", f"Loss: {eval_loss:.4f} | Learning in progress"
    elif eval_loss < 0.50:
        return "idle", "Scientist online", f"Loss: {eval_loss:.4f} | Ready for more training"
    else:
        return "idle", "Early stage", f"Loss: {eval_loss:.4f} | Needs training"


_PRESENCE_HTML = """
<style>
/* ── Wrapper ── */
.sp-wrap {
  position: fixed;
  top: 1.1rem;
  right: 1.1rem;
  z-index: 99999;
  pointer-events: none;
  width: 272px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.sp-card {
  pointer-events: auto;
  display: flex;
  align-items: center;
  gap: .9rem;
  padding: .55rem .75rem .55rem .55rem;
  border-radius: 20px;
  background: rgba(3, 8, 22, 0.93);
  border: 1px solid rgba(96, 165, 250, 0.18);
  box-shadow:
    inset 0 0 0 1px rgba(255,255,255,.04),
    0 20px 48px rgba(0,0,0,.50),
    0 0 56px var(--sp-card-glow);
  backdrop-filter: blur(18px) saturate(1.5);
  -webkit-backdrop-filter: blur(18px) saturate(1.5);
  transition: box-shadow .6s ease;
}

/* ── Hexagonal stage ── */
.sp-stage {
  position: relative;
  width: 68px;
  height: 68px;
  flex: 0 0 68px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Outer hex frame */
.sp-hex-frame {
  position: absolute;
  inset: -2px;
  clip-path: polygon(50% 0%, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%);
  border: 1.5px solid var(--sp-frame-color);
  animation: spRotate var(--sp-r1) linear infinite;
  pointer-events: none;
}
.sp-hex-frame::before {
  content: '';
  position: absolute;
  inset: 0;
  clip-path: polygon(50% 0%, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%);
  border: 1.5px solid var(--sp-frame-color);
  opacity: .5;
}

/* Inner hex ring — counter-rotate */
.sp-hex-inner {
  position: absolute;
  inset: 8px;
  clip-path: polygon(50% 0%, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%);
  border: 1px solid var(--sp-accent);
  animation: spRotateRev var(--sp-r2) linear infinite;
  opacity: .60;
  pointer-events: none;
}

/* Data stream particles */
.sp-particle {
  position: absolute;
  width: 2.5px;
  height: 2.5px;
  border-radius: 50%;
  background: var(--sp-accent);
  box-shadow: 0 0 8px 1px var(--sp-accent);
  top: 50%; left: 50%;
  margin: -1.25px 0 0 -1.25px;
  animation: spOrbit var(--sp-orbit) linear infinite;
  opacity: var(--sp-dot-alpha);
  pointer-events: none;
}
.sp-particle:nth-child(2) { animation-delay: calc(var(--sp-orbit) * -.25); }
.sp-particle:nth-child(3) { animation-delay: calc(var(--sp-orbit) * -.5); }
.sp-particle:nth-child(4) { animation-delay: calc(var(--sp-orbit) * -.75); }
.sp-particle.sp-particle-b {
  background: var(--sp-frame-color);
  box-shadow: 0 0 6px 1px var(--sp-frame-color);
  width: 2px; height: 2px;
  animation-duration: calc(var(--sp-orbit) * 1.5);
  animation-delay: calc(var(--sp-orbit) * -.15);
}

/* Core — the living center */
.sp-core {
  position: relative;
  z-index: 2;
  width: 38px;
  height: 38px;
  clip-path: polygon(50% 2%, 91% 27%, 91% 73%, 50% 98%, 9% 73%, 9% 27%);
  background:
    radial-gradient(circle at 30% 25%, rgba(255,255,255,.90), transparent 20%),
    radial-gradient(circle at 65% 60%, var(--sp-hot), transparent 35%),
    radial-gradient(circle at 30% 70%, var(--sp-cool), transparent 35%),
    linear-gradient(135deg, var(--sp-a), var(--sp-b), var(--sp-c));
  box-shadow:
    0 0 24px var(--sp-glow-a),
    0 0 52px var(--sp-glow-b);
  animation:
    spPulse var(--sp-pulse) ease-in-out infinite,
    spShift var(--sp-morph) ease-in-out infinite;
}

/* Neural web overlay on core */
.sp-core::after {
  content: '';
  position: absolute;
  inset: 0;
  clip-path: polygon(50% 2%, 91% 27%, 91% 73%, 50% 98%, 9% 73%, 9% 27%);
  background:
    linear-gradient(60deg, transparent 48%, rgba(255,255,255,.08) 49%, transparent 51%),
    linear-gradient(120deg, transparent 48%, rgba(255,255,255,.06) 49%, transparent 51%),
    linear-gradient(0deg, transparent 48%, rgba(255,255,255,.04) 49%, transparent 51%);
  animation: spGrid var(--sp-morph) linear infinite;
  opacity: .5;
}

/* Ambient glow behind everything */
.sp-glow {
  position: absolute;
  inset: -14px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--sp-glow-a) 0%, transparent 65%);
  animation: spBreath var(--sp-pulse) ease-in-out infinite;
  opacity: .45;
  pointer-events: none;
}

/* ── Text ── */
.sp-text { flex: 1 1 auto; min-width: 0; overflow: hidden; }
.sp-eyebrow {
  font-size: .58rem;
  letter-spacing: .20rem;
  text-transform: uppercase;
  color: rgba(148, 195, 255, .72);
  font-weight: 700;
  margin-bottom: .15rem;
}
.sp-label {
  font-size: .72rem;
  font-weight: 800;
  color: #eef4ff;
  line-height: 1.2;
  margin-bottom: .12rem;
}
.sp-detail {
  font-size: .62rem;
  color: rgba(148, 195, 240, .60);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── State palettes ── */
.sp-idle {
  --sp-a: rgba(30,58,138,.95); --sp-b: rgba(59,130,246,.88); --sp-c: rgba(147,51,234,.80);
  --sp-hot: rgba(147,51,234,.85); --sp-cool: rgba(59,130,246,.90);
  --sp-glow-a: rgba(59,130,246,.30); --sp-glow-b: rgba(147,51,234,.15);
  --sp-frame-color: rgba(96,165,250,.50); --sp-accent: rgba(147,197,253,.55);
  --sp-card-glow: rgba(59,130,246,.10);
  --sp-morph: 10s; --sp-pulse: 4s;
  --sp-r1: 20s; --sp-r2: 30s; --sp-orbit: 12s;
  --sp-dot-alpha: .35;
}

.sp-learning {
  --sp-a: rgba(6,182,212,.95); --sp-b: rgba(59,130,246,.90); --sp-c: rgba(16,185,129,.82);
  --sp-hot: rgba(52,211,153,.92); --sp-cool: rgba(6,182,212,.95);
  --sp-glow-a: rgba(6,182,212,.48); --sp-glow-b: rgba(52,211,153,.24);
  --sp-frame-color: rgba(34,211,238,.72); --sp-accent: rgba(52,211,153,.70);
  --sp-card-glow: rgba(6,182,212,.16);
  --sp-morph: 3s; --sp-pulse: 1.8s;
  --sp-r1: 4s; --sp-r2: 6s; --sp-orbit: 2.5s;
  --sp-dot-alpha: .80;
}

.sp-analyzing {
  --sp-a: rgba(180,83,9,.92); --sp-b: rgba(245,158,11,.90); --sp-c: rgba(252,211,77,.84);
  --sp-hot: rgba(252,211,77,.95); --sp-cool: rgba(245,158,11,.90);
  --sp-glow-a: rgba(245,158,11,.42); --sp-glow-b: rgba(252,211,77,.22);
  --sp-frame-color: rgba(251,191,36,.68); --sp-accent: rgba(252,211,77,.65);
  --sp-card-glow: rgba(245,158,11,.14);
  --sp-morph: 4.5s; --sp-pulse: 2.2s;
  --sp-r1: 6s; --sp-r2: 9s; --sp-orbit: 4s;
  --sp-dot-alpha: .65;
}

.sp-alert {
  --sp-a: rgba(185,28,28,.94); --sp-b: rgba(239,68,68,.90); --sp-c: rgba(248,113,113,.82);
  --sp-hot: rgba(252,165,165,.94); --sp-cool: rgba(239,68,68,.88);
  --sp-glow-a: rgba(239,68,68,.52); --sp-glow-b: rgba(185,28,28,.28);
  --sp-frame-color: rgba(248,113,113,.72); --sp-accent: rgba(252,165,165,.70);
  --sp-card-glow: rgba(239,68,68,.18);
  --sp-morph: 1.5s; --sp-pulse: 0.9s;
  --sp-r1: 2.5s; --sp-r2: 3.5s; --sp-orbit: 1.5s;
  --sp-dot-alpha: .90;
}

.sp-ready {
  --sp-a: rgba(5,150,105,.92); --sp-b: rgba(16,185,129,.88); --sp-c: rgba(52,211,153,.84);
  --sp-hot: rgba(110,231,183,.92); --sp-cool: rgba(16,185,129,.90);
  --sp-glow-a: rgba(16,185,129,.38); --sp-glow-b: rgba(52,211,153,.18);
  --sp-frame-color: rgba(52,211,153,.58); --sp-accent: rgba(110,231,183,.55);
  --sp-card-glow: rgba(16,185,129,.12);
  --sp-morph: 7s; --sp-pulse: 3.2s;
  --sp-r1: 16s; --sp-r2: 24s; --sp-orbit: 9s;
  --sp-dot-alpha: .45;
}

.sp-genesis {
  --sp-a: rgba(109,40,217,.95); --sp-b: rgba(139,92,246,.90); --sp-c: rgba(6,182,212,.82);
  --sp-hot: rgba(196,181,253,.94); --sp-cool: rgba(103,232,249,.90);
  --sp-glow-a: rgba(139,92,246,.44); --sp-glow-b: rgba(6,182,212,.22);
  --sp-frame-color: rgba(167,139,250,.64); --sp-accent: rgba(103,232,249,.60);
  --sp-card-glow: rgba(139,92,246,.14);
  --sp-morph: 5s; --sp-pulse: 2.8s;
  --sp-r1: 8s; --sp-r2: 12s; --sp-orbit: 6s;
  --sp-dot-alpha: .55;
}

/* ── Keyframes ── */
@keyframes spRotate    { to { transform: rotate(360deg); } }
@keyframes spRotateRev { to { transform: rotate(-360deg); } }
@keyframes spBreath {
  0%, 100% { opacity: .35; transform: scale(1); }
  50%      { opacity: .60; transform: scale(1.08); }
}
@keyframes spPulse {
  0%, 100% { transform: scale(1);    filter: brightness(1); }
  50%      { transform: scale(1.05); filter: brightness(1.15); }
}
@keyframes spShift {
  0%   { clip-path: polygon(50% 2%, 91% 27%, 91% 73%, 50% 98%, 9% 73%, 9% 27%); }
  33%  { clip-path: polygon(52% 3%, 90% 28%, 92% 72%, 48% 97%, 8% 74%, 10% 26%); }
  66%  { clip-path: polygon(48% 1%, 92% 26%, 90% 74%, 52% 99%, 10% 72%, 8% 28%); }
  100% { clip-path: polygon(50% 2%, 91% 27%, 91% 73%, 50% 98%, 9% 73%, 9% 27%); }
}
@keyframes spGrid {
  0%   { transform: translateY(0); }
  100% { transform: translateY(20px); }
}
@keyframes spOrbit {
  0%   { transform: rotate(0deg)   translateX(32px) rotate(0deg); }
  100% { transform: rotate(360deg) translateX(32px) rotate(-360deg); }
}

@media (prefers-reduced-motion: reduce) {
  .sp-core, .sp-hex-frame, .sp-hex-inner, .sp-particle, .sp-glow, .sp-core::after {
    animation: none !important;
  }
}
</style>

<div class="sp-wrap">
  <div class="sp-card sp-__MODE__">
    <div class="sp-stage">
      <div class="sp-glow"></div>
      <div class="sp-hex-frame"></div>
      <div class="sp-hex-inner"></div>
      <div class="sp-particle"></div>
      <div class="sp-particle"></div>
      <div class="sp-particle"></div>
      <div class="sp-particle sp-particle-b"></div>
      <div class="sp-core"></div>
    </div>
    <div class="sp-text">
      <div class="sp-eyebrow">Scientist</div>
      <div class="sp-label">__LABEL__</div>
      <div class="sp-detail">__DETAIL__</div>
    </div>
  </div>
</div>
"""


def render_scientist_presence(mode: str = "auto") -> None:
    """
    Inject the Scientist presence widget.

    mode: "auto" infers state from model metrics, or pass a literal:
          "idle" | "learning" | "analyzing" | "alert" | "ready" | "genesis"
    """
    meta_path = ROOT / "outputs" / "models" / "scientist_brain_meta.json"

    if mode == "auto":
        mode, label, detail = _infer_state_from_model(meta_path)
    else:
        _labels = {
            "idle": "Scientist online",
            "learning": "Building understanding",
            "analyzing": "Processing patterns",
            "alert": "Needs attention",
            "ready": "High confidence",
            "genesis": "Scientist awakening",
        }
        label = _labels.get(mode, "Scientist online")
        detail = "Autonomous Scientist Core"

    html = (
        _PRESENCE_HTML
        .replace("__MODE__", mode)
        .replace("__LABEL__", label)
        .replace("__DETAIL__", str(detail)[:52])
    )
    st.markdown(html, unsafe_allow_html=True)
