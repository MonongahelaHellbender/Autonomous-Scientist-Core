"""
Foundation Lab — unified app for all brains, training, evolution, and presence.
================================================================================
Single access point. Launch via Foundation Lab.app on Desktop.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st
import torch
from torch import nn

ROOT = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(ROOT))

from models.brains import ALL_BRAINS, BrainEnsemble
from models.brains.self_improve import self_improve_cycle, EvolutionConfig
from models.brains.companions import get_companion_css, get_companion_html, get_entity_css, get_entity_html
from models.presence import render_scientist_presence, _infer_state_from_model, _PRESENCE_HTML
from training.train_brain import get_all_generators, generate_batch
from models.scientist_brain import ScientistBrain
from models.neuromorphic import NeuromorphicBrain

# ─── Registry ───
FULL_REGISTRY = {
    **ALL_BRAINS,
    "foundation_core": ScientistBrain,
    "neuromorphic": NeuromorphicBrain,
}

BRAIN_META = {
    "human":           {"icon": "🧠", "color": "#60a5fa", "era": "2 MYA",   "neurons": "86B",   "tag": "Cortical hierarchy"},
    "octopus":         {"icon": "🐙", "color": "#f472b6", "era": "300 MYA", "neurons": "500M",  "tag": "Distributed arms"},
    "corvid":          {"icon": "🐦‍⬛", "color": "#a78bfa", "era": "150 MYA", "neurons": "1.2B",  "tag": "Dense nuclei"},
    "dolphin":         {"icon": "🐬", "color": "#22d3ee", "era": "50 MYA",  "neurons": "12B",   "tag": "Hemi-switching"},
    "insect":          {"icon": "🐝", "color": "#fbbf24", "era": "400 MYA", "neurons": "960K",  "tag": "Dual-track"},
    "alien":           {"icon": "👽", "color": "#34d399", "era": "—",       "neurons": "∞",     "tag": "No constraints"},
    "ultimate":        {"icon": "⚡", "color": "#f97316", "era": "Now",     "neurons": "∞",     "tag": "All tricks"},
    "fungal":          {"icon": "🍄", "color": "#a3e635", "era": "1.5 BYA", "neurons": "0",     "tag": "Mycelium network"},
    "reptile":         {"icon": "🦎", "color": "#84cc16", "era": "320 MYA","neurons": "10M",   "tag": "Brainstem dominant"},
    "jellyfish":       {"icon": "🪼", "color": "#c084fc", "era": "600 MYA","neurons": "5.6K",  "tag": "Nerve net"},
    "cat":             {"icon": "🐱", "color": "#f9a8d4", "era": "10 MYA", "neurons": "760M",  "tag": "Visual predator"},
    "dog":             {"icon": "🐕", "color": "#fdba74", "era": "15K YA", "neurons": "530M",  "tag": "Social olfactory"},
    "foundation_core": {"icon": "🔷", "color": "#818cf8", "era": "—",      "neurons": "—",     "tag": "Deep liquid"},
    "neuromorphic":    {"icon": "🔬", "color": "#fb923c", "era": "—",      "neurons": "—",     "tag": "4-region proto"},
}

SAVE_DIR = ROOT / "outputs" / "brain_zoo"


# ═══════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════
def _c(name): return BRAIN_META.get(name, {}).get("color", "#60a5fa")
def _i(name): return BRAIN_META.get(name, {}).get("icon", "🔹")
def _tag(name): return BRAIN_META.get(name, {}).get("tag", "")


def _normalize_output(model, x):
    out = model(x)
    if isinstance(out, dict):
        return out
    preds, states = out
    surprise = ((preds - x[:, 1:, :]) ** 2).mean(dim=-1)
    return {"predictions": preds, "hidden": states, "anomaly_score": surprise,
            "surprise": surprise, "properties": torch.zeros(x.shape[0], 2)}


def _loss_badge(loss):
    if loss < 0.03: return "#34d399", "OPTIMAL"
    if loss < 0.08: return "#60a5fa", "STRONG"
    if loss < 0.15: return "#fbbf24", "LEARNING"
    return "#ef4444", "EVOLVING"


BRAIN_TOPOLOGY = {
    "human": [("brainstem","v1"),("v1","v2"),("v2","sensory"),("sensory","amygdala"),
              ("sensory","hippo"),("hippo","left_pf"),("hippo","right_pf"),
              ("left_pf","callosum"),("right_pf","callosum"),("callosum","acc"),
              ("acc","insula"),("insula","cerebellum"),("cerebellum","motor")],
    "octopus": [("optic_l","central"),("optic_r","central"),("central","vertical"),
                ("vertical","frontal"),("frontal","subesoph")]
               + [(f"arm_{i}","subesoph") for i in range(8)],
    "corvid": [("wulst","mesopallium"),("tectum","mesopallium"),("mesopallium","ncl"),
               ("ncl","hippo"),("hippo","wulst"),("ncl","song"),
               ("song","arcopallium"),("arcopallium","cerebellum")],
    "dolphin": [("brainstem","auditory"),("brainstem","sensory"),("auditory","left_ctx"),
                ("sensory","right_ctx"),("left_ctx","callosum"),("right_ctx","callosum"),
                ("callosum","paralimbic"),("paralimbic","hippo"),("hippo","cerebellum"),
                ("cerebellum","motor")],
    "insect": [("antennal","mb_calyx"),("optic","mb_calyx"),("mb_calyx","mb_lobes"),
               ("antennal","lateral_horn"),("optic","lateral_horn"),
               ("lateral_horn","mb_lobes"),("mb_lobes","central_cx"),
               ("central_cx","protocerebrum"),("protocerebrum","seg")],
    "alien": [(f"r{i}","workspace") for i in range(8)] + [("workspace","selfmodel")],
    "ultimate": [("sensory","learned"),("sensory","innate"),("innate","learned"),
                 ("learned","left_h"),("innate","left_h"),("learned","right_h"),("innate","right_h"),
                 ("left_h","workspace"),("right_h","workspace"),
                 ("workspace","dist_a"),("workspace","dist_b"),("workspace","dist_c"),
                 ("dist_a","dense_hub"),("dist_b","dense_hub"),("dist_c","dense_hub"),
                 ("dense_hub","memory"),("dense_hub","selfmodel"),("memory","selfmodel"),
                 ("selfmodel","motor"),("memory","motor")],
    "fungal": [(f"node_{i}","nutrient_pool") for i in range(8)]
              + [(f"node_{i}",f"node_{(i+1)%8}") for i in range(8)],
    "reptile": [("olfactory","brainstem"),("optic_nerve","brainstem"),("brainstem","tectum"),
                ("tectum","striatum"),("striatum","pallium"),("pallium","brainstem"),
                ("hypothalamus","brainstem"),("striatum","cerebellum"),("cerebellum","motor"),
                ("optic_nerve","spinal"),("spinal","motor")],
    "jellyfish": [(f"rhopalium_{i}",f"rhopalium_{(i+1)%6}") for i in range(6)]
                 + [(f"rhopalium_{i}","nerve_net") for i in range(6)]
                 + [("nerve_net","motor_ring")],
    "cat": [("visual_cortex","thalamus_relay"),("auditory","thalamus_relay"),("olfactory","thalamus_relay"),
            ("whisker_cortex","thalamus_relay"),("thalamus_relay","brainstem"),("brainstem","amygdala"),
            ("amygdala","visual_cortex"),("amygdala","hippocampus"),("hippocampus","basal_ganglia"),
            ("basal_ganglia","prefrontal"),("prefrontal","cerebellum"),("cerebellum","motor")],
    "dog": [("olfactory_bulb","thalamus"),("auditory","thalamus"),("visual","thalamus"),
            ("thalamus","brainstem"),("brainstem","amygdala"),("amygdala","hippocampus"),
            ("hippocampus","caudate"),("social_cortex","caudate"),("caudate","prefrontal"),
            ("prefrontal","cerebellum"),("cerebellum","motor"),("social_cortex","prefrontal")],
    "foundation_core": [("layer_0","layer_1"),("layer_1","layer_2")],
    # neuromorphic uses the ring fallback in _build_brain_topology
}



def _hex_to_rgba(hex_color, alpha=1.0):
    """Convert #RRGGBB hex color to Plotly-safe rgba()."""
    if not isinstance(hex_color, str):
        return f"rgba(96,165,250,{alpha})"

    hex_color = hex_color.strip()

    if hex_color.startswith("rgba(") or hex_color.startswith("rgb("):
        return hex_color

    if not hex_color.startswith("#") or len(hex_color) != 7:
        return f"rgba(96,165,250,{alpha})"

    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return f"rgba({r},{g},{b},{alpha})"
    except ValueError:
        return f"rgba(96,165,250,{alpha})"

def _build_brain_topology(brain_name, region_traces, color):
    """Render a plotly network graph of brain regions with activity-based sizing/coloring."""
    import math

    region_names = list(region_traces.keys())
    n = len(region_names)
    if n == 0:
        fig = go.Figure()
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="#060a13", height=350)
        return fig

    # Activity levels per region
    activities = {}
    for rn in region_names:
        t = region_traces[rn]
        activities[rn] = float(t[0, -1].abs().mean().item())
    max_act = max(activities.values()) if activities else 1.0
    if max_act < 1e-8:
        max_act = 1.0

    # Get edges first (layout depends on connectivity)
    if brain_name in BRAIN_TOPOLOGY:
        candidate_edges = [(a, b) for a, b in BRAIN_TOPOLOGY[brain_name]
                           if a in region_names and b in region_names]
    else:
        candidate_edges = [(region_names[i], region_names[(i + 1) % n]) for i in range(n)]

    # Hub-aware layout: nodes with high degree go in the center
    degree = {rn: 0 for rn in region_names}
    for a, b in candidate_edges:
        degree[a] += 1
        degree[b] += 1
    avg_deg = sum(degree.values()) / max(len(degree), 1)
    hubs = [rn for rn in region_names if degree[rn] >= max(3, avg_deg * 1.6)]
    periphery = [rn for rn in region_names if rn not in hubs]

    positions = {}
    # Place hubs near center in a small inner ring (or single point)
    if len(hubs) == 1:
        positions[hubs[0]] = (0.0, 0.0)
    else:
        for i, rn in enumerate(hubs):
            angle = 2 * math.pi * i / max(len(hubs), 1)
            positions[rn] = (0.35 * math.cos(angle), 0.35 * math.sin(angle))
    # Periphery nodes ring around
    for i, rn in enumerate(periphery):
        angle = 2 * math.pi * i / max(len(periphery), 1) - math.pi / 2
        positions[rn] = (math.cos(angle), math.sin(angle))

    edges = [(a, b) for a, b in candidate_edges if a in positions and b in positions]

    fig = go.Figure()

    # Draw edges
    for a, b in edges:
        x0, y0 = positions[a]
        x1, y1 = positions[b]
        fig.add_trace(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode="lines",
            line=dict(color=_hex_to_rgba(color, 0.18), width=1.5),
            hoverinfo="skip", showlegend=False))

    # Draw nodes
    node_x = [positions[rn][0] for rn in region_names]
    node_y = [positions[rn][1] for rn in region_names]
    node_sizes = [15 + 30 * (activities[rn] / max_act) for rn in region_names]

    # Color from dim to bright based on activity
    node_colors = []
    for rn in region_names:
        frac = activities[rn] / max_act
        # Interpolate opacity: dim (0.2) to bright (1.0)
        opacity = 0.2 + 0.8 * frac
        node_colors.append(_hex_to_rgba(color, opacity))

    fig.add_trace(go.Scatter(
        x=node_x, y=node_y, mode="markers+text",
        marker=dict(size=node_sizes, color=node_colors,
                    line=dict(width=1.5, color=_hex_to_rgba(color, 0.38))),
        text=[rn[:10] for rn in region_names],
        textposition="top center",
        textfont=dict(size=8, color="#94a3b8"),
        hovertext=[f"{rn}: {activities[rn]:.4f}" for rn in region_names],
        showlegend=False))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#060a13",
        height=350,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False, range=[-1.5, 1.5]),
        yaxis=dict(visible=False, range=[-1.5, 1.5], scaleanchor="x"),
    )
    return fig


def _save_results():
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    data = {}
    for name, r in st.session_state.results.items():
        data[name] = {k: v for k, v in r.items() if k != "model_state"}
    (SAVE_DIR / "results.json").write_text(json.dumps(data, indent=2, default=str))
    for name, r in st.session_state.results.items():
        if "model_state" in r:
            torch.save(r["model_state"], SAVE_DIR / f"{name}.pt")


def _load_results():
    path = SAVE_DIR / "results.json"
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text())
        for name, r in data.items():
            if name not in st.session_state.results:
                wp = SAVE_DIR / f"{name}.pt"
                if wp.exists():
                    r["model_state"] = torch.load(wp, weights_only=True)
                st.session_state.results[name] = r
    except Exception:
        pass


def _plot_defaults(fig, height=380, **kw):
    """Apply consistent futuristic theme to all plots."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0d1117",
        height=height,
        font=dict(family="SF Pro Display, -apple-system, sans-serif", color="#94a3b8"),
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)),
        xaxis=dict(gridcolor="#1e293b", zerolinecolor="#1e293b"),
        yaxis=dict(gridcolor="#1e293b", zerolinecolor="#1e293b"),
        **kw,
    )
    return fig


# ═══════════════════════════════════════════════════
# Page config + CSS
# ═══════════════════════════════════════════════════
st.set_page_config(page_title="Foundation Lab", page_icon="🔷", layout="wide")


st.markdown("""
<style>
/* ── Base ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
:root {
  --bg-deep: #060a13;
  --bg-card: #0d1220;
  --bg-card-hover: #111a2e;
  --border: #1a2744;
  --border-glow: #3b82f640;
  --text-primary: #e2e8f0;
  --text-secondary: #64748b;
  --text-muted: #475569;
  --accent: #60a5fa;
}
.stApp {
  background: var(--bg-deep);
  background-image:
    radial-gradient(ellipse at 20% 50%, rgba(59,130,246,0.04) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(139,92,246,0.03) 0%, transparent 50%);
  font-family: 'Inter', -apple-system, sans-serif;
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #080d19 0%, #0a1020 100%);
  border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { font-family: 'Inter', sans-serif !important; }

/* ── Hide streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Cards ── */
.f-card {
  background: linear-gradient(135deg, var(--bg-card) 0%, #111b30 100%);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px;
  margin: 10px 0;
  position: relative;
  overflow: hidden;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
.f-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--card-accent, var(--accent)), transparent);
  opacity: 0;
  transition: opacity 0.35s ease;
}
.f-card:hover {
  border-color: var(--border-glow);
  box-shadow: 0 4px 30px rgba(59,130,246,0.06), inset 0 1px 0 rgba(255,255,255,0.03);
  transform: translateY(-1px);
}
.f-card:hover::before { opacity: 1; }

/* ── Brain card specific ── */
.brain-tile {
  --card-accent: var(--brain-color, var(--accent));
  background: linear-gradient(160deg, var(--bg-card) 0%, color-mix(in srgb, var(--brain-color) 4%, #0d1220) 100%);
  border-color: color-mix(in srgb, var(--brain-color) 15%, transparent);
  padding: 16px 18px;
  border-radius: 14px;
  margin: 6px 0;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}
.brain-tile:hover {
  border-color: color-mix(in srgb, var(--brain-color) 40%, transparent);
  box-shadow: 0 0 24px color-mix(in srgb, var(--brain-color) 10%, transparent);
}
.brain-tile .bt-icon {
  font-size: 1.8em;
  line-height: 1;
  margin-bottom: 6px;
}
.brain-tile .bt-name {
  font-weight: 800;
  font-size: 0.95em;
  color: var(--brain-color);
  margin-bottom: 2px;
}
.brain-tile .bt-tag {
  font-size: 0.72em;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.brain-tile .bt-stats {
  display: flex;
  gap: 12px;
  font-size: 0.72em;
}
.brain-tile .bt-stat-val {
  font-weight: 700;
  color: color-mix(in srgb, var(--brain-color) 80%, white);
}
.brain-tile .bt-stat-lbl {
  color: var(--text-muted);
  font-size: 0.88em;
}

/* ── Badges ── */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 0.62em;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  background: color-mix(in srgb, var(--badge-color) 15%, transparent);
  color: var(--badge-color);
  border: 1px solid color-mix(in srgb, var(--badge-color) 25%, transparent);
  margin-left: 8px;
  vertical-align: middle;
}

/* ── Glow orb indicator ── */
.glow-orb {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, var(--orb-inner), var(--orb-outer));
  border: 2px solid var(--orb-inner);
  box-shadow: 0 0 20px color-mix(in srgb, var(--orb-inner) 30%, transparent);
  animation: orbPulse 3s ease-in-out infinite;
  flex-shrink: 0;
}
@keyframes orbPulse {
  0%, 100% { box-shadow: 0 0 12px color-mix(in srgb, var(--orb-inner) 25%, transparent); transform: scale(1); }
  50% { box-shadow: 0 0 24px color-mix(in srgb, var(--orb-inner) 40%, transparent); transform: scale(1.05); }
}

/* ── Section headers ── */
.sec-header {
  font-size: 1.4em;
  font-weight: 900;
  color: var(--text-primary);
  margin: 0 0 4px 0;
  letter-spacing: -0.02em;
}
.sec-sub {
  font-size: 0.85em;
  color: var(--text-secondary);
  margin: 0 0 20px 0;
  line-height: 1.5;
}
.sec-line {
  height: 1px;
  background: linear-gradient(90deg, var(--border), transparent);
  margin: 28px 0;
}

/* ── Metric tiles ── */
.metric-tile {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  text-align: center;
}
.metric-tile .mt-val {
  font-size: 1.6em;
  font-weight: 900;
  color: var(--mt-color, var(--accent));
  line-height: 1.2;
}
.metric-tile .mt-lbl {
  font-size: 0.65em;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-top: 2px;
}
.metric-tile .mt-delta {
  font-size: 0.7em;
  color: var(--text-secondary);
  margin-top: 2px;
}

/* ── Rank list ── */
.rank-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  margin: 4px 0;
  transition: border-color 0.2s ease;
}
.rank-item:hover { border-color: var(--border-glow); }
.rank-num {
  font-size: 1.1em;
  font-weight: 900;
  color: var(--rank-color, var(--text-muted));
  width: 28px;
  text-align: center;
}
.rank-name { font-weight: 700; color: var(--text-primary); font-size: 0.88em; flex: 1; }
.rank-val { font-weight: 600; color: var(--text-secondary); font-size: 0.82em; font-family: 'SF Mono', monospace; }

/* Nav radio as vertical menu */
[data-testid="stSidebar"] .stRadio > div {
  flex-direction: column;
  gap: 2px;
}
[data-testid="stSidebar"] .stRadio > div > label {
  background: transparent;
  border: 1px solid transparent;
  border-radius: 10px;
  padding: 10px 14px;
  font-weight: 600;
  font-size: 0.88em;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s ease;
  margin: 0;
}
[data-testid="stSidebar"] .stRadio > div > label:hover {
  background: #111a2e;
  border-color: #1a2744;
  color: #e2e8f0;
}
[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"],
[data-testid="stSidebar"] .stRadio > div [data-testid="stMarkdownContainer"] {
  /* selected handled by streamlit */
}
div[data-testid="stSidebar"] .stRadio > label { display: none; }

/* ── Animated brain node ── */
.brain-node {
  width: 48px; height: 48px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, var(--node-color), color-mix(in srgb, var(--node-color) 20%, #060a13));
  border: 2px solid color-mix(in srgb, var(--node-color) 50%, transparent);
  box-shadow:
    0 0 16px color-mix(in srgb, var(--node-color) 20%, transparent),
    inset 0 0 12px color-mix(in srgb, var(--node-color) 10%, transparent);
  animation: nodeFloat var(--float-dur, 4s) ease-in-out infinite, orbPulse 3s ease-in-out infinite;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.4em;
  flex-shrink: 0;
}
@keyframes nodeFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

/* ── Scan line overlay for futuristic feel ── */
.scan-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  pointer-events: none;
  z-index: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(59,130,246,0.008) 2px,
    rgba(59,130,246,0.008) 4px
  );
  animation: scanDrift 8s linear infinite;
}
@keyframes scanDrift {
  0% { transform: translateY(0); }
  100% { transform: translateY(4px); }
}

/* ── Connection line ── */
.conn-line {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--line-color, #1e3a5f), transparent);
  margin: 2px 24px;
  opacity: 0.5;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #334155; }

/* ── Animated background grid ── */
.grid-bg {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  pointer-events: none;
  z-index: 0;
  background-image:
    linear-gradient(rgba(59,130,246,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(59,130,246,0.03) 1px, transparent 1px);
  background-size: 60px 60px;
  animation: gridDrift 20s linear infinite;
  mask-image: radial-gradient(ellipse at center, black 30%, transparent 70%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 70%);
}
@keyframes gridDrift {
  0% { transform: translate(0, 0); }
  100% { transform: translate(60px, 60px); }
}

/* ── Presence preview ── */
.presence-preview .sp-wrap {
  position: relative !important;
  top: auto !important;
  right: auto !important;
  z-index: 1 !important;
}

/* ── Buttons ── */
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #1d4ed8, #7c3aed) !important;
  border: none !important;
  font-weight: 700 !important;
  letter-spacing: 0.02em !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 4px 16px rgba(59,130,246,0.2) !important;
}
.stButton > button[kind="primary"]:hover {
  box-shadow: 0 6px 24px rgba(59,130,246,0.35) !important;
  transform: translateY(-1px) !important;
}
</style>
<div class="grid-bg"></div>
<div class="scan-overlay"></div>
""", unsafe_allow_html=True)

# Companion + Entity CSS
st.markdown(get_companion_css(), unsafe_allow_html=True)
st.markdown(get_entity_css(), unsafe_allow_html=True)

# ─── Presence ───
render_scientist_presence(mode="auto")

# ─── Session state ───
for key in ["results", "ensemble_result", "evo_logs"]:
    if key not in st.session_state:
        st.session_state[key] = {} if key != "ensemble_result" else None
if "hidden_size_used" not in st.session_state:
    st.session_state.hidden_size_used = 128
if not st.session_state.results:
    _load_results()

# ─── Sidebar ───
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 16px 0 8px 0;">
        <div style="font-size: 2.2em;">🔷</div>
        <div style="font-size: 1.1em; font-weight: 900; color: #e2e8f0; letter-spacing: -0.02em;">Foundation Lab</div>
        <div style="font-size: 0.7em; color: #475569; margin-top: 2px;">Liquid Neural Architecture Studio</div>
    </div>
    """, unsafe_allow_html=True)

    st.radio(
        "Navigation", options=[
            "🏠 Overview", "⚡ Train", "📊 Compare", "🔗 Ensemble",
            "🧬 Evolve", "💬 Query", "🪞 Presence", "🔧 Self-Improve",
        ], key="nav", label_visibility="collapsed",
    )

    st.markdown("---")

    # Status bar
    if st.session_state.results:
        n_trained = len(st.session_state.results)
        best = min(st.session_state.results.values(), key=lambda x: x.get("eval_loss", 999))
        gens = sum(len(v) for v in st.session_state.evo_logs.values())
        st.markdown("---")
        st.markdown(f"""
        <div style="font-size:0.72em; color:#64748b; line-height:1.8;">
            <span style="color:#34d399;">●</span> {n_trained} trained<br>
            <span style="color:#60a5fa;">●</span> best {best.get('eval_loss',0):.5f}<br>
            <span style="color:#a78bfa;">●</span> {gens} evolutions
        </div>""", unsafe_allow_html=True)


# ─── Page Navigation ───
page = st.session_state.get("nav", "🏠 Overview")

# ─── Defaults (pages override inline) ───
_def_hidden = 128
_def_steps = 400
_def_batch = 32
_def_seq = 80
_def_lr = 0.002
_def_seed = 42


# ════════════════════════════════════════
# PAGE: Overview
# ════════════════════════════════════════
if page == "🏠 Overview":
    st.markdown("""
    <div style="padding: 10px 0 0 0;">
        <p class="sec-header">Foundation Lab</p>
        <p class="sec-sub">Nine liquid neural architectures. Each inspired by a different evolutionary solution.<br>
        Train them. Compare them. Evolve them. Query them. See which wins.</p>
    </div>""", unsafe_allow_html=True)

    # Quick stats if trained
    if st.session_state.results:
        res = st.session_state.results
        best_n = min(res, key=lambda n: res[n].get("eval_loss", 999))
        cols = st.columns(4)
        stats = [
            (f"{len(res)}", "Trained", "#34d399"),
            (f"{res[best_n].get('eval_loss',0):.4f}", f"Best ({best_n})", _c(best_n)),
            (f"{sum(r.get('params',0) for r in res.values()):,}", "Total Params", "#a78bfa"),
            (f"{sum(len(v) for v in st.session_state.evo_logs.values())}", "Evolutions", "#f97316"),
        ]
        for col, (val, lbl, color) in zip(cols, stats):
            col.markdown(f"""
            <div class="metric-tile" style="--mt-color:{color};">
                <div class="mt-val">{val}</div>
                <div class="mt-lbl">{lbl}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)

    # Brain grid
    cols = st.columns(3)
    for i, (name, Cls) in enumerate(FULL_REGISTRY.items()):
        color = _c(name)
        # Cached stats
        ck = f"_pc_{name}_{_def_hidden}"
        if ck not in st.session_state:
            m = Cls(input_size=1, hidden_size=_def_hidden)
            st.session_state[ck] = sum(p.numel() for p in m.parameters())
            try:
                o = m(torch.randn(1, 8, 1))
                st.session_state[f"_nr_{name}_{_def_hidden}"] = len(o.get("region_traces", {})) if isinstance(o, dict) else 0
            except: st.session_state[f"_nr_{name}_{_def_hidden}"] = 0
            del m
        pc = st.session_state[ck]
        nr = st.session_state.get(f"_nr_{name}_{_def_hidden}", 0)

        badge_html = ""
        if name in st.session_state.results:
            loss = st.session_state.results[name].get("eval_loss", 999)
            bc, bl = _loss_badge(loss)
            badge_html = f'<span class="badge" style="--badge-color:{bc};">{bl} {loss:.4f}</span>'

        brain_loss = st.session_state.results.get(name, {}).get("eval_loss", None)
        entity_html = get_entity_html(name, brain_loss)
        with cols[i % 3]:
            st.markdown(f"""
            <div class="brain-tile" style="--brain-color:{color};">
                {entity_html}
                <div style="text-align:center;margin-top:8px;">
                    <div class="bt-name">{name.replace('_',' ').title()}{badge_html}</div>
                    <div class="bt-tag">{_tag(name)}</div>
                </div>
                <div class="bt-stats" style="justify-content:center;">
                    <div><span class="bt-stat-val">{pc:,}</span> <span class="bt-stat-lbl">params</span></div>
                    <div><span class="bt-stat-val">{nr}</span> <span class="bt-stat-lbl">regions</span></div>
                    <div><span class="bt-stat-val">{BRAIN_META.get(name,{}).get('era','—')}</span> <span class="bt-stat-lbl">era</span></div>
                </div>
            </div>""", unsafe_allow_html=True)


    # Network topology — show brain interconnections
    st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
    st.markdown('<p class="sec-header" style="font-size:1.1em;">Architecture Topology</p>', unsafe_allow_html=True)

    # Build a 3D scatter showing brains as nodes positioned by their design philosophy
    positions = {
        "insect":          (-2, -2, 0),
        "octopus":         (-1, 1, -1),
        "corvid":          (0, -1, 1),
        "dolphin":         (1, 1, 0),
        "human":           (2, 0, 1),
        "neuromorphic":    (0, 0, 0),
        "foundation_core": (0, 2, 0),
        "alien":           (-1, 0, 2),
        "ultimate":        (1, -1, 2),
        "fungal":          (-2, 1, 1),
        "reptile":         (2, -2, -1),
        "jellyfish":       (-1, -1, -2),
        "cat":             (1, 2, -1),
        "dog":             (2, 1, -1),
    }
    topo_fig = go.Figure()
    for name in FULL_REGISTRY:
        px, py, pz = positions.get(name, (0, 0, 0))
        color = _c(name)
        topo_fig.add_trace(go.Scatter3d(
            x=[px], y=[py], z=[pz], mode="markers+text",
            marker=dict(size=12, color=color, opacity=0.9,
                        line=dict(width=1, color="#0d1117")),
            text=[f"{_i(name)}"], textposition="top center",
            textfont=dict(size=12), name=name,
            hovertext=f"{name} · {_tag(name)}",
            showlegend=False))
    # Connection lines between related brains
    connections = [
        ("human", "neuromorphic"), ("neuromorphic", "foundation_core"),
        ("human", "dolphin"), ("human", "corvid"),
        ("insect", "alien"), ("octopus", "alien"),
        ("alien", "ultimate"), ("human", "ultimate"),
        ("dolphin", "ultimate"), ("insect", "ultimate"),
        ("corvid", "ultimate"), ("octopus", "ultimate"),
        ("fungal", "alien"), ("fungal", "octopus"),
        ("reptile", "human"), ("reptile", "insect"),
        ("jellyfish", "octopus"), ("jellyfish", "insect"),
        ("cat", "human"), ("cat", "dolphin"),
        ("dog", "human"), ("dog", "cat"),
        ("fungal", "ultimate"), ("reptile", "ultimate"),
    ]
    for a, b in connections:
        if a in positions and b in positions:
            pa, pb = positions[a], positions[b]
            topo_fig.add_trace(go.Scatter3d(
                x=[pa[0], pb[0]], y=[pa[1], pb[1]], z=[pa[2], pb[2]],
                mode="lines", line=dict(color="#1e3a5f", width=2),
                showlegend=False, hoverinfo="skip"))
    topo_fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
            bgcolor="#060a13",
            camera=dict(eye=dict(x=1.8, y=1.8, z=1.2))),
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        height=420, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(topo_fig, use_container_width=True)


# ════════════════════════════════════════
# PAGE: Train
# ════════════════════════════════════════
elif page == "⚡ Train":
    st.markdown("""
    <p class="sec-header">Train Architectures</p>
    <p class="sec-sub">Pick which brains to train and how. Same data, same seed — a fair race.</p>
    """, unsafe_allow_html=True)

    # ── What to train ──
    train_mode = st.radio("What to train", ["🌐 All Brains", "✅ Pick Specific Brains"], horizontal=True, key="train_mode")

    if train_mode == "🌐 All Brains":
        active = list(FULL_REGISTRY.keys())
    else:
        tcols = st.columns(3)
        selected = {}
        for i, name in enumerate(FULL_REGISTRY):
            with tcols[i % 3]:
                selected[name] = st.checkbox(
                    f"{_i(name)} {name.replace('_',' ').title()}", value=(name in ALL_BRAINS), key=f"t_{name}")
        active = [n for n, v in selected.items() if v]

    # ── How to train ──
    with st.expander("⚙️ Training Settings", expanded=False):
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            hidden_size = st.slider("Hidden size", 32, 256, _def_hidden, 16, key="tr_hs")
            train_steps = st.slider("Train steps", 100, 2000, _def_steps, 100, key="tr_st")
        with sc2:
            batch_size = st.slider("Batch size", 8, 64, _def_batch, 8, key="tr_bs")
            seq_len = st.slider("Seq length", 20, 200, _def_seq, 10, key="tr_sl")
        with sc3:
            lr = st.number_input("Learning rate", 0.0001, 0.01, _def_lr, format="%.4f", key="tr_lr")
            seed = st.number_input("Seed", 0, 99999, _def_seed, key="tr_seed")

    st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        train_btn = st.button("🚀 Train Selected", type="primary", key="train_btn", disabled=not active)
    with col2:
        st.caption(f"{len(active)} brains · {train_steps} steps")

    if train_btn:
        generators = get_all_generators()
        loss_fn = nn.MSELoss()
        progress_bar = st.progress(0)
        total_work = len(active) * int(train_steps)
        done = 0

        for brain_name in active:
            Cls = FULL_REGISTRY[brain_name]
            model = Cls(input_size=1, hidden_size=hidden_size, dropout=0.1)
            optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
            rng = np.random.default_rng(int(seed))
            loss_history = []
            model.train()
            t0 = time.time()

            # Two-column layout: topology diagram + info panel
            col_topo, col_info = st.columns([2, 1])
            topo_container = col_topo.empty()
            info_container = col_info.empty()

            for step in range(int(train_steps)):
                batch, _ = generate_batch(generators, rng, int(batch_size), int(seq_len))
                out = _normalize_output(model, batch)
                loss = loss_fn(out["predictions"], batch[:, 1:, :])
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                if step % 25 == 0:
                    lv = float(loss.item())
                    loss_history.append({"step": step, "loss": lv})

                    color = _c(brain_name)
                    comp = get_companion_html(brain_name)

                    # Build topology figure
                    if isinstance(out, dict) and "region_traces" in out:
                        topo_fig = _build_brain_topology(brain_name, out["region_traces"], color)
                        topo_container.plotly_chart(topo_fig, use_container_width=True, key=f"topo_{brain_name}_{step}")

                    # Info panel with entity + loss
                    loss_bar_w = max(0, min(100, 100 - lv * 200))
                    ent_html = get_entity_html(brain_name, lv)
                    info_container.markdown(f"""
                    <div style="padding:12px;background:#0d1220;border:1px solid #1a2744;border-radius:12px;">
                        {ent_html}
                        <div style="font-weight:800;color:{color};font-size:0.95em;margin-bottom:4px;text-align:center;">
                            {_i(brain_name)} {brain_name}
                        </div>
                        <div style="font-size:0.7em;color:#475569;text-align:center;margin-bottom:8px;">
                            step {step}/{int(train_steps)}
                        </div>
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                            <div style="flex:1;height:8px;background:#1a2744;border-radius:4px;overflow:hidden;">
                                <div style="width:{loss_bar_w}%;height:100%;background:linear-gradient(90deg,{color},{color}80);border-radius:4px;transition:width 0.5s ease;"></div>
                            </div>
                            <div style="font-family:'SF Mono',monospace;font-size:0.75em;color:{color};font-weight:700;">{lv:.5f}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)
                done += 1
                progress_bar.progress(min(done / total_work, 1.0))

            train_time = time.time() - t0
            model.eval()
            with torch.no_grad():
                eb, _ = generate_batch(generators, rng, int(batch_size)*4, int(seq_len))
                eo = _normalize_output(model, eb)
                el = float(loss_fn(eo["predictions"], eb[:, 1:, :]).item())
                h = eo["hidden"][:, -1, :].numpy()
                pca3 = 0.0
                if h.shape[1] > 3:
                    try:
                        _, s, _ = np.linalg.svd(h - h.mean(axis=0), full_matrices=False)
                        vr = (s**2)/(s**2).sum()
                        pca3 = float(vr[:3].sum())
                    except: pass
                else: pca3 = 1.0
                n_reg = len(eo.get("region_traces", {})) if isinstance(eo, dict) else 0

            st.session_state.results[brain_name] = {
                "eval_loss": el, "pca_top3": pca3, "train_time": round(train_time, 1),
                "loss_history": loss_history, "params": sum(p.numel() for p in model.parameters()),
                "regions": n_reg, "model_state": model.state_dict(), "hidden_size": hidden_size,
            }

        st.session_state.hidden_size_used = hidden_size
        _save_results()
        progress_bar.progress(1.0)
        st.success("✅ All trained and saved!")

    # Results
    if st.session_state.results:
        st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
        res = st.session_state.results
        sorted_res = sorted(res.items(), key=lambda x: x[1].get("eval_loss", 999))

        # Ranking cards
        for rank, (name, r) in enumerate(sorted_res, 1):
            bc, bl = _loss_badge(r.get("eval_loss", 999))
            medals = {1: ("🥇", "#fbbf24"), 2: ("🥈", "#94a3b8"), 3: ("🥉", "#b45309")}
            m_icon, m_color = medals.get(rank, (f"#{rank}", "#475569"))
            st.markdown(f"""
            <div class="rank-item" style="--rank-color:{m_color};">
                <div class="rank-num">{m_icon}</div>
                <div style="font-size:1.2em;">{_i(name)}</div>
                <div class="rank-name" style="color:{_c(name)};">{name.replace('_',' ').title()}</div>
                <span class="badge" style="--badge-color:{bc};">{bl}</span>
                <div class="rank-val">{r.get('eval_loss',0):.5f}</div>
                <div style="font-size:0.72em;color:#475569;">{r.get('params',0):,}p · {r.get('train_time',0)}s</div>
            </div>""", unsafe_allow_html=True)

        # Loss curves
        st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
        fig = go.Figure()
        for name, r in res.items():
            if "loss_history" not in r: continue
            fig.add_trace(go.Scatter(
                x=[h["step"] for h in r["loss_history"]],
                y=[h["loss"] for h in r["loss_history"]],
                mode="lines", name=f"{_i(name)} {name}",
                line=dict(color=_c(name), width=2.5)))
        _plot_defaults(fig, 420, title="Training Loss Curves", yaxis_type="log",
                       xaxis_title="Step", yaxis_title="Loss")
        st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════
# PAGE: Compare / Convergence
# ════════════════════════════════════════
elif page == "📊 Compare":
    st.markdown("""
    <p class="sec-header">Convergence Analysis</p>
    <p class="sec-sub">Do different brain architectures discover the same structure when given the same data?<br>
    If they converge — the structure is <b>necessary</b>. If they diverge — wiring <b>matters</b>.</p>
    """, unsafe_allow_html=True)

    if st.session_state.results and len(st.session_state.results) >= 2:
        res = st.session_state.results
        names = list(res.keys())

        # Verdict first (most important info up top)
        losses = [res[n]["eval_loss"] for n in names]
        spread = max(losses) - min(losses)
        pcas = [res[n].get("pca_top3", 0) for n in names]
        pca_spread = max(pcas) - min(pcas)

        vc1, vc2 = st.columns(2)
        with vc1:
            if spread < 0.01:
                st.success("🎯 **Strong convergence** — architecture barely matters.")
            elif spread < 0.05:
                st.info("📊 **Moderate convergence** — similar range, some wiring helps.")
            else:
                st.warning("🔀 **Divergence** — architectures find different solutions.")
        with vc2:
            if pca_spread < 0.15:
                st.success("🧬 **Same geometry** — hidden states land in similar space.")
            else:
                st.info(f"🧬 PCA spread: {pca_spread:.3f}")

        st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            sn = sorted(names, key=lambda n: res[n].get("eval_loss", 999))
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[f"{_i(n)} {n}" for n in sn],
                y=[res[n]["eval_loss"] for n in sn],
                marker_color=[_c(n) for n in sn],
                marker_line=dict(width=0)))
            _plot_defaults(fig, 360, title="Eval Loss (ranked)")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[res[n]["params"] for n in names],
                y=[res[n]["eval_loss"] for n in names],
                mode="markers+text",
                text=[f"{_i(n)}" for n in names],
                textposition="top center",
                marker=dict(size=16, color=[_c(n) for n in names],
                            line=dict(width=1.5, color="#0d1117")),
                textfont=dict(size=14),
                hovertext=[f"{n}: {res[n]['eval_loss']:.5f}" for n in names]))
            _plot_defaults(fig, 360, title="Efficiency Frontier",
                           xaxis_title="Parameters", yaxis_title="Loss")
            st.plotly_chart(fig, use_container_width=True)

        # Radar
        if len(names) >= 3:
            st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
            cats = ["Efficiency", "Accuracy", "Complexity", "Speed", "Geometry"]
            fig = go.Figure()
            for name in names:
                r = res[name]
                raw = [50000/max(r["params"],1), 1/max(r["eval_loss"],0.001),
                       r.get("regions",0)/15.0, 1/max(r.get("train_time",1),0.1), r.get("pca_top3",0)]
                mx = max(raw) if max(raw)>0 else 1
                v = [x/mx for x in raw] + [raw[0]/mx]
                fig.add_trace(go.Scatterpolar(
                    r=v, theta=cats+[cats[0]], fill="toself",
                    name=f"{_i(name)} {name}", opacity=0.2,
                    line=dict(color=_c(name), width=2)))
            fig.update_layout(
                polar=dict(bgcolor="#0d1117",
                           radialaxis=dict(visible=True, color="#334155", gridcolor="#1a2744"),
                           angularaxis=dict(color="#94a3b8")),
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                title="Capabilities Radar", height=500)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Train at least 2 architectures to see convergence analysis.")


# ════════════════════════════════════════
# PAGE: Ensemble
# ════════════════════════════════════════
elif page == "🔗 Ensemble":
    st.markdown("""
    <p class="sec-header">Brain Ensemble</p>
    <p class="sec-sub">Group think — all brains process the same input, a learned router picks who to trust.</p>
    """, unsafe_allow_html=True)

    trained_brains = [n for n in st.session_state.results if n in ALL_BRAINS and "model_state" in st.session_state.results[n]]
    if len(trained_brains) >= 2:
        st.markdown(f"**{len(trained_brains)} brains available:** " + ", ".join(f"{_i(n)} {n}" for n in trained_brains))
        with st.expander("⚙️ Ensemble Settings", expanded=False):
            ec1, ec2 = st.columns(2)
            ens_steps = ec1.slider("Router train steps", 50, 1000, _def_steps // 2, 50, key="ens_st")
            ens_lr = ec2.number_input("Learning rate", 0.0001, 0.01, _def_lr, format="%.4f", key="ens_lr")
        if st.button("🔗 Train Ensemble Router", type="primary", key="ens_btn"):
            generators = get_all_generators()
            loss_fn = nn.MSELoss()
            hs = st.session_state.hidden_size_used
            brains = {}
            for n in trained_brains:
                m = ALL_BRAINS[n](input_size=1, hidden_size=hs, dropout=0.0)
                m.load_state_dict(st.session_state.results[n]["model_state"])
                brains[n] = m
            ens = BrainEnsemble(brains, hidden_size=hs, freeze_brains=True)
            opt = torch.optim.AdamW([p for p in ens.parameters() if p.requires_grad], lr=ens_lr)
            rng = np.random.default_rng(_def_seed)
            es = int(ens_steps)
            prog = st.progress(0); stat = st.empty(); hist = []
            ens.train()
            for step in range(es):
                batch, _ = generate_batch(generators, rng, _def_batch, _def_seq)
                out = ens(batch)
                loss = loss_fn(out["predictions"], batch[:, 1:, :])
                opt.zero_grad(); loss.backward()
                torch.nn.utils.clip_grad_norm_(ens.parameters(), 1.0); opt.step()
                if step % 25 == 0:
                    hist.append({"step": step, "loss": float(loss.item())})
                    stat.text(f"🔗 step {step}/{es} · loss {loss.item():.5f}")
                prog.progress((step+1)/es)
            ens.eval()
            with torch.no_grad():
                eb, _ = generate_batch(generators, rng, _def_batch*4, _def_seq)
                eo = ens(eb)
                el = float(loss_fn(eo["predictions"], eb[:, 1:, :]).item())
            st.session_state.ensemble_result = {
                "eval_loss": el, "routing": eo["routing_weights"],
                "loss_history": hist, "params": ens.param_count()}
            prog.progress(1.0); stat.success("✅ Ensemble trained!")

        if st.session_state.ensemble_result:
            r = st.session_state.ensemble_result
            st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)

            col1, col2 = st.columns([1, 2])
            with col1:
                sc, _ = _loss_badge(r["eval_loss"])
                st.markdown(f"""
                <div class="metric-tile" style="--mt-color:{sc};">
                    <div class="mt-val">{r['eval_loss']:.5f}</div>
                    <div class="mt-lbl">Ensemble Loss</div>
                </div>""", unsafe_allow_html=True)

                if st.session_state.results:
                    best_n, best_r = min(st.session_state.results.items(), key=lambda x: x[1].get("eval_loss", 999))
                    imp = (best_r["eval_loss"] - r["eval_loss"]) / max(best_r["eval_loss"], 1e-9) * 100
                    if imp > 0:
                        st.success(f"Beats **{best_n}** by **{imp:.1f}%**")
                    else:
                        st.info(f"**{best_n}** still leads by {-imp:.1f}%")

            with col2:
                routing = r["routing"]
                fig = go.Figure(data=[go.Pie(
                    labels=[f"{_i(n)} {n}" for n in routing],
                    values=list(routing.values()),
                    marker=dict(colors=[_c(n) for n in routing], line=dict(color="#0d1117", width=2)),
                    hole=0.5, textinfo="label+percent", textfont=dict(size=11))])
                fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                                  title="Who Does the Ensemble Trust?", height=380,
                                  font=dict(color="#94a3b8"))
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Train at least 2 brain-zoo architectures first.")


# ════════════════════════════════════════
# PAGE: Evolution
# ════════════════════════════════════════
elif page == "🧬 Evolve":
    st.markdown("""
    <p class="sec-header">Evolutionary View</p>
    <p class="sec-sub">Evolution is mass trial-and-error learning. Humans aren't the goal — just one solution.<br>
    Every species won its own niche. Each brain's visual identity reflects its performance.</p>
    """, unsafe_allow_html=True)

    if st.session_state.results:
        evo_order = ["jellyfish","fungal","insect","reptile","octopus","corvid","dolphin","cat","dog","human","neuromorphic","foundation_core","alien","ultimate"]
        for name in evo_order:
            if name not in st.session_state.results: continue
            r = st.session_state.results[name]
            meta = BRAIN_META.get(name, {})
            loss = r.get("eval_loss", 999)
            sc, sl = _loss_badge(loss)
            color = _c(name)
            evo_n = len(st.session_state.evo_logs.get(name, []))

            comp = get_companion_html(name)
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:16px;padding:14px 18px;
                 background:linear-gradient(135deg,var(--bg-card),color-mix(in srgb,{color} 3%,#0d1220));
                 border:1px solid color-mix(in srgb,{color} 18%,transparent);border-radius:14px;margin:6px 0;
                 transition:all 0.3s ease;" onmouseover="this.style.borderColor='{color}40'" onmouseout="this.style.borderColor=''">
                {comp}
                <div style="flex:1;min-width:0;">
                    <div style="font-weight:800;color:{color};font-size:0.95em;">
                        {_i(name)} {name.replace('_',' ').title()}
                        <span class="badge" style="--badge-color:{sc};">{sl}</span>
                    </div>
                    <div style="font-size:0.72em;color:#64748b;margin-top:2px;">
                        {meta.get('era','—')} · {meta.get('neurons','—')} neurons · {_tag(name)}
                    </div>
                </div>
                <div style="text-align:right;font-family:'SF Mono',monospace;">
                    <div style="font-size:1.1em;font-weight:800;color:{sc};">{loss:.5f}</div>
                    <div style="font-size:0.65em;color:#475569;">{r.get('params',0):,}p · {r.get('train_time',0)}s{f' · gen {evo_n}' if evo_n else ''}</div>
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("Train brains to see the evolutionary view.")


# ════════════════════════════════════════
# PAGE: Query
# ════════════════════════════════════════
elif page == "💬 Query":
    st.markdown("""
    <p class="sec-header">Query Brains</p>
    <p class="sec-sub">Feed a signal in. See how brains predict, where they're surprised, who wins.</p>
    """, unsafe_allow_html=True)

    # ── Who to query ──
    query_scope = st.radio("Who to ask", ["🌐 All Trained Brains", "🎯 Specific Brain"], horizontal=True, key="qscope")

    trained_with_state = [n for n in st.session_state.results if "model_state" in st.session_state.results[n]]

    query_targets = trained_with_state
    if query_scope == "🎯 Specific Brain" and trained_with_state:
        chosen = st.selectbox("Pick a brain",
            trained_with_state,
            format_func=lambda n: f"{_i(n)} {n.replace('_',' ').title()}",
            key="q_brain")
        query_targets = [chosen]

    st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)

    # ── Input ──
    qmode = st.radio("Input type", ["Text", "Numbers", "Generator"], horizontal=True, key="qm")

    codes = None
    if qmode == "Text":
        txt = st.text_input("Type anything:", value="hello world", key="qt")
        if txt:
            codes = np.array([ord(c) for c in txt], dtype=np.float32)
            codes = (codes - codes.mean()) / max(codes.std(), 1e-8)
    elif qmode == "Numbers":
        nums = st.text_input("Comma-separated:", value="1,2,3,5,8,13,21,34,55", key="qn")
        try:
            codes = np.array([float(x.strip()) for x in nums.split(",")], dtype=np.float32)
            codes = (codes - codes.mean()) / max(codes.std(), 1e-8)
        except: codes = None
    else:
        gens = get_all_generators()
        gc = st.selectbox("Generator", list(gens.keys()), key="qg")
        gl = st.slider("Length", 10, 200, 60, key="ql")
        raw = gens[gc](np.random.default_rng(_def_seed), gl)
        codes = ((raw - raw.mean()) / max(raw.std(), 1e-8)).astype(np.float32)

    if st.button("🧠 Process", type="primary", key="qb", disabled=not query_targets):
        if codes is not None and len(codes) >= 3:
            x = torch.tensor(codes).unsqueeze(0).unsqueeze(-1)
            st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)

            # Input
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=codes, mode="lines+markers",
                                     line=dict(color="#e2e8f0", width=1.5),
                                     marker=dict(size=3, color="#60a5fa")))
            _plot_defaults(fig, 180, title="Input Signal")
            st.plotly_chart(fig, use_container_width=True)

            all_preds, all_surp = {}, {}
            for name in query_targets:
                hs = st.session_state.results[name].get("hidden_size", _def_hidden)
                Cls = FULL_REGISTRY[name]
                model = Cls(input_size=1, hidden_size=hs, dropout=0.0)
                model.load_state_dict(st.session_state.results[name]["model_state"])
                model.eval()
                with torch.no_grad():
                    out = _normalize_output(model, x)
                    all_preds[name] = out["predictions"][0,:,0].numpy()
                    all_surp[name] = out["surprise"][0].numpy() if "surprise" in out else np.zeros(len(all_preds[name]))

            # Predictions overlay
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=codes[1:], mode="lines", name="Actual",
                                     line=dict(color="#e2e8f0", width=2.5, dash="dot")))
            for n, p in all_preds.items():
                fig.add_trace(go.Scatter(y=p[:len(codes)-1], mode="lines",
                                         name=f"{_i(n)} {n}", line=dict(color=_c(n), width=1.8)))
            _plot_defaults(fig, 350, title="Predictions vs Actual")
            st.plotly_chart(fig, use_container_width=True)

            # Surprise
            fig = go.Figure()
            for n, s in all_surp.items():
                fig.add_trace(go.Bar(y=[float(s.mean())], x=[f"{_i(n)} {n}"],
                                     marker_color=_c(n), marker_line=dict(width=0)))
            _plot_defaults(fig, 280, title="Average Surprise (lower = better)")
            st.plotly_chart(fig, use_container_width=True)

            # Neural activity heatmaps — show which regions activate
            st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
            st.markdown("### Region Activity Heatmaps")
            hm_cols = st.columns(min(3, len(query_targets)))
            for idx, name in enumerate(query_targets[:6]):
                hs_n = st.session_state.results[name].get("hidden_size", _def_hidden)
                Cls_n = FULL_REGISTRY[name]
                model_n = Cls_n(input_size=1, hidden_size=hs_n, dropout=0.0)
                model_n.load_state_dict(st.session_state.results[name]["model_state"])
                model_n.eval()
                with torch.no_grad():
                    out_n = _normalize_output(model_n, x)
                    traces = out_n.get("region_traces", {})
                if traces:
                    # Build heatmap: regions × time
                    region_names = list(traces.keys())[:12]
                    activity = []
                    for rn in region_names:
                        t = traces[rn]  # [B, T, H]
                        activity.append(t[0].abs().mean(dim=-1).numpy())  # avg activation per timestep
                    if activity:
                        act_matrix = np.stack(activity)  # [regions, T]
                        with hm_cols[idx % len(hm_cols)]:
                            fig = go.Figure(data=go.Heatmap(
                                z=act_matrix,
                                y=region_names,
                                colorscale=[[0, "#060a13"], [0.3, _hex_to_rgba(_c(name), 0.25)], [1, _c(name)]],
                                showscale=False))
                            fig.update_layout(
                                title=f"{_i(name)} {name}", template="plotly_dark",
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0d1117",
                                height=220, margin=dict(l=80, r=10, t=35, b=20),
                                font=dict(size=9, color="#64748b"),
                                xaxis=dict(title="", gridcolor="#1a2744"),
                                yaxis=dict(title="", gridcolor="#1a2744"))
                            st.plotly_chart(fig, use_container_width=True)

            # Ranking
            st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
            ranking = sorted(all_preds.keys(),
                             key=lambda n: np.mean((all_preds[n][:len(codes)-1] - codes[1:])**2))
            for rank, name in enumerate(ranking, 1):
                mse = np.mean((all_preds[name][:len(codes)-1] - codes[1:])**2)
                medals = {1: ("🥇", "#fbbf24"), 2: ("🥈", "#94a3b8"), 3: ("🥉", "#b45309")}
                mi, mc = medals.get(rank, (f"#{rank}", "#475569"))
                st.markdown(f"""
                <div class="rank-item" style="--rank-color:{mc};">
                    <div class="rank-num">{mi}</div>
                    <div style="font-size:1.1em;">{_i(name)}</div>
                    <div class="rank-name" style="color:{_c(name)};">{name.replace('_',' ').title()}</div>
                    <div class="rank-val">{mse:.6f}</div>
                </div>""", unsafe_allow_html=True)

    elif not query_targets:
        st.info("Train brains first.")


# ════════════════════════════════════════
# PAGE: Presence
# ════════════════════════════════════════
elif page == "🪞 Presence":
    st.markdown("""
    <p class="sec-header">AI Presence</p>
    <p class="sec-sub">The AI decides how to present itself based on its own internal state.</p>
    """, unsafe_allow_html=True)

    meta_path = ROOT / "outputs" / "models" / "scientist_brain_meta.json"
    mode, label, detail = _infer_state_from_model(meta_path)

    st.markdown(f"""
    <div class="f-card" style="--card-accent: var(--accent);">
        <div style="font-weight:800;color:#e2e8f0;">Current: <span style="color:#60a5fa;">{mode.upper()}</span></div>
        <div style="font-size:0.85em;color:#94a3b8;margin-top:4px;">{label} — {detail}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
    st.markdown("### All States")

    states = {"genesis": "Awakening", "idle": "Online", "learning": "Building understanding",
              "analyzing": "Processing patterns", "ready": "High confidence", "alert": "Needs attention"}
    for state, lbl in states.items():
        html = (_PRESENCE_HTML.replace("__MODE__", state).replace("__LABEL__", lbl)
                .replace("__DETAIL__", state)
                .replace("position: fixed;", "position: relative;")
                .replace("top: 1.1rem;", "").replace("right: 1.1rem;", "")
                .replace("z-index: 99999;", "z-index: 1;"))
        st.markdown(f'<div class="presence-preview">{html}</div>', unsafe_allow_html=True)


# ════════════════════════════════════════
# PAGE: Self-Improve
# ════════════════════════════════════════
elif page == "🔧 Self-Improve":
    st.markdown("""
    <p class="sec-header">Self-Improvement</p>
    <p class="sec-sub">Each brain diagnoses its weaknesses, mutates its time constants, trains on hard patterns,
    and keeps only the fittest version. Evolution at the neuron level.</p>
    """, unsafe_allow_html=True)

    trained_with_state = [n for n in st.session_state.results if "model_state" in st.session_state.results[n]]
    if trained_with_state:
        brain_to_improve = st.selectbox("Select brain to evolve", trained_with_state,
                                         format_func=lambda n: f"{_i(n)} {n.replace('_',' ').title()}", key="si_sel")

        col1, col2 = st.columns(2)
        with col1:
            evo_steps = st.slider("Steps per candidate", 50, 500, 200, 50, key="es")
            n_mut = st.slider("Mutation candidates", 1, 6, 3, key="nm")
        with col2:
            mut_rate = st.slider("Mutation rate", 0.05, 0.5, 0.15, 0.05, key="mr")
            mut_str = st.slider("Mutation strength", 0.05, 0.5, 0.2, 0.05, key="ms")

        if st.button("🧬 Evolve", type="primary", key="si_btn"):
            hs = st.session_state.results[brain_to_improve].get("hidden_size", _def_hidden)
            Cls = FULL_REGISTRY[brain_to_improve]
            model = Cls(input_size=1, hidden_size=hs, dropout=0.1)
            model.load_state_dict(st.session_state.results[brain_to_improve]["model_state"])
            cfg = EvolutionConfig(train_steps=evo_steps, batch_size=_def_batch, seq_len=_def_seq,
                                  lr=_def_lr, mutation_rate=mut_rate, mutation_strength=mut_str, n_candidates=n_mut)
            prog = st.progress(0); stat = st.empty()
            def _cb(phase, i, total):
                stat.text(f"🧬 {brain_to_improve}: {phase}")
                if total > 0: prog.progress(min((i+1)/total, 1.0))
            result = self_improve_cycle(model, brain_to_improve, cfg, progress_cb=_cb)
            prog.progress(1.0)

            st.session_state.results[brain_to_improve]["model_state"] = model.state_dict()
            st.session_state.results[brain_to_improve]["eval_loss"] = result["after_loss"]
            _save_results()

            if brain_to_improve not in st.session_state.evo_logs:
                st.session_state.evo_logs[brain_to_improve] = []
            st.session_state.evo_logs[brain_to_improve].append(result)
            stat.success(f"✅ Winner: {result['winner']} · {result['improvement_pct']:+.1f}%")

            # Results
            st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
            cols = st.columns(3)
            cols[0].markdown(f'<div class="metric-tile"><div class="mt-val">{result["before_loss"]:.5f}</div><div class="mt-lbl">Before</div></div>', unsafe_allow_html=True)
            cols[1].markdown(f'<div class="metric-tile" style="--mt-color:#34d399;"><div class="mt-val">{result["after_loss"]:.5f}</div><div class="mt-lbl">After</div></div>', unsafe_allow_html=True)
            imp = result["improvement_pct"]
            ic = "#34d399" if imp > 0 else "#ef4444"
            cols[2].markdown(f'<div class="metric-tile" style="--mt-color:{ic};"><div class="mt-val">{imp:+.1f}%</div><div class="mt-lbl">Change</div></div>', unsafe_allow_html=True)

            if result["mutations_applied"]:
                for mut in result["mutations_applied"]:
                    d = "⬆" if mut["delta"] > 0 else "⬇"
                    st.caption(f"{d} `{mut['region']}` dt shifted by {mut['delta']:+.4f}")

        # History
        if st.session_state.evo_logs:
            has_data = any(logs for logs in st.session_state.evo_logs.values())
            if has_data:
                st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
                fig = go.Figure()
                for bname, logs in st.session_state.evo_logs.items():
                    if not logs: continue
                    fig.add_trace(go.Scatter(
                        x=list(range(1, len(logs)+1)),
                        y=[l["after_loss"] for l in logs],
                        mode="lines+markers", name=f"{_i(bname)} {bname}",
                        line=dict(color=_c(bname), width=2.5),
                        marker=dict(size=8, line=dict(width=1.5, color="#0d1117"))))
                _plot_defaults(fig, 380, title="Evolution Progress",
                               xaxis_title="Generation", yaxis_title="Loss")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Train brains first, then evolve them here.")
