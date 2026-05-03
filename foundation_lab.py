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

# ─── Registry (10 brains — each tests a genuinely different wiring hypothesis) ───
FULL_REGISTRY = {
    **ALL_BRAINS,
    "foundation_core": ScientistBrain,
}

BRAIN_META = {
    "jellyfish":       {"icon": "🪼", "color": "#c084fc", "era": "600 MYA","neurons": "5.6K",  "tag": "Nerve net",
                        "why": "The simplest possible 'brain' — a ring of nerves with no center. Tests whether any central control is needed at all."},
    "fungal":          {"icon": "🍄", "color": "#a3e635", "era": "1.5 BYA", "neurons": "0",     "tag": "Mycelium network",
                        "why": "No neurons whatsoever. Information flows through chemical-like diffusion across a mesh. Tests whether neuron-based wiring is even necessary."},
    "insect":          {"icon": "🐝", "color": "#fbbf24", "era": "400 MYA", "neurons": "960K",  "tag": "Dual-track",
                        "why": "Two parallel systems: one learns from experience, one is hardwired instinct. The instinct track can override the learned one. Tests whether splitting fast/slow processing helps."},
    "octopus":         {"icon": "🐙", "color": "#f472b6", "era": "300 MYA", "neurons": "500M",  "tag": "Distributed arms",
                        "why": "8 semi-independent processors with a tiny coordinator. Most of the thinking happens locally. Tests whether distributed intelligence beats centralized."},
    "corvid":          {"icon": "🐦‍⬛", "color": "#a78bfa", "era": "150 MYA", "neurons": "1.2B",  "tag": "Dense nuclei",
                        "why": "Crows are as smart as primates but have no cortex — just dense clusters of neurons wired laterally. Tests whether you need layers or just density."},
    "dolphin":         {"icon": "🐬", "color": "#22d3ee", "era": "50 MYA",  "neurons": "12B",   "tag": "Hemi-switching",
                        "why": "Two brain halves that take turns being active — one sleeps while the other works. Tests whether redundancy and alternation improve robustness."},
    "human":           {"icon": "🧠", "color": "#60a5fa", "era": "2 MYA",   "neurons": "86B",   "tag": "Cortical hierarchy",
                        "why": "The full stack: brainstem for survival, cortex for abstraction, prefrontal for planning, all connected by a massive corpus callosum. The 'throw everything at it' approach."},
    "alien":           {"icon": "👽", "color": "#34d399", "era": "—",       "neurons": "∞",     "tag": "No constraints",
                        "why": "What if there were no skull, no energy budget, no evolutionary history? Every region talks to every other. Tests how much biology was constraint vs. design."},
    "ultimate":        {"icon": "⚡", "color": "#f97316", "era": "Now",     "neurons": "∞",     "tag": "All tricks",
                        "why": "A chimera — the best architectural feature from every species stitched together. If evolution could start over with all the tricks, what would it build?"},
    "foundation_core": {"icon": "🔷", "color": "#818cf8", "era": "—",      "neurons": "—",     "tag": "Deep liquid",
                        "why": "Clean engineering baseline with no biological inspiration. Three stacked liquid layers. If this beats the biology-inspired brains, evolution was just noise."},
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


def _linear_cka(X, Y):
    """
    Linear CKA between two activation matrices.

    X, Y: [N, D_x], [N, D_y] — N samples, D dimensions each.
    Returns scalar in [0, 1]: 1 = identical representations, 0 = orthogonal.

    Reference: Kornblith et al. 2019, "Similarity of Neural Network
    Representations Revisited."
    """
    X = X - X.mean(axis=0, keepdims=True)
    Y = Y - Y.mean(axis=0, keepdims=True)
    # Frobenius norm of cross-covariance, squared
    xy = float(np.linalg.norm(X.T @ Y, ord="fro") ** 2)
    xx = float(np.linalg.norm(X.T @ X, ord="fro"))
    yy = float(np.linalg.norm(Y.T @ Y, ord="fro"))
    if xx < 1e-10 or yy < 1e-10:
        return 0.0
    return xy / (xx * yy)


def _compute_cka_matrix(hidden_states):
    """Pairwise linear CKA between brains.

    hidden_states: dict[name -> np.ndarray of shape [N, D_name]]
    Returns: (names, matrix) where matrix[i,j] = CKA(brain_i, brain_j).
    """
    names = list(hidden_states.keys())
    n = len(names)
    M = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            try:
                cka = _linear_cka(hidden_states[names[i]], hidden_states[names[j]])
            except Exception:
                cka = 0.0
            M[i, j] = M[j, i] = cka
    return names, M


def _welch_t_test(a, b):
    """Two-sample Welch's t-test. Returns (t_stat, p_value_approx)."""
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return 0.0, 1.0
    ma, mb = np.mean(a), np.mean(b)
    va, vb = np.var(a, ddof=1), np.var(b, ddof=1)
    se = np.sqrt(va/na + vb/nb)
    if se < 1e-12:
        return 0.0, 1.0
    t = (ma - mb) / se
    # Welch-Satterthwaite df
    num = (va/na + vb/nb)**2
    den = (va/na)**2/(na-1) + (vb/nb)**2/(nb-1)
    df = num / max(den, 1e-12)
    # Approx p-value using normal (good enough for df > 5)
    from math import erfc, sqrt
    p = erfc(abs(t) / sqrt(2))
    return float(t), float(p)


def _cohens_d(a, b):
    """Cohen's d effect size between two groups."""
    na, nb = len(a), len(b)
    pooled_std = np.sqrt(((na-1)*np.var(a, ddof=1) + (nb-1)*np.var(b, ddof=1)) / max(na+nb-2, 1))
    if pooled_std < 1e-12:
        return 0.0
    return float((np.mean(a) - np.mean(b)) / pooled_std)


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
    "jellyfish": [(f"rhopalium_{i}",f"rhopalium_{(i+1)%6}") for i in range(6)]
                 + [(f"rhopalium_{i}","nerve_net") for i in range(6)]
                 + [("nerve_net","motor_ring")],
    "foundation_core": [("layer_0","layer_1"),("layer_1","layer_2")],
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

    # Draw edges — width and brightness scale with activity of connected nodes
    for a, b in edges:
        x0, y0 = positions[a]
        x1, y1 = positions[b]
        edge_act = (activities.get(a, 0) + activities.get(b, 0)) / (2 * max_act)
        edge_w = 1.0 + 3.0 * edge_act
        edge_alpha = 0.1 + 0.5 * edge_act
        fig.add_trace(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode="lines",
            line=dict(color=_hex_to_rgba(color, edge_alpha), width=edge_w),
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
    except Exception as e:
        st.session_state["_load_warning"] = f"Could not parse results.json: {e}"
        return

    failed = []
    for name, r in data.items():
        if name not in st.session_state.results:
            wp = SAVE_DIR / f"{name}.pt"
            if wp.exists():
                try:
                    r["model_state"] = torch.load(wp, weights_only=True)
                except Exception as e:
                    failed.append(f"{name} ({e})")
                    continue
            st.session_state.results[name] = r
    if failed:
        st.session_state["_load_warning"] = f"Failed to load weights for: {', '.join(failed)}"


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
            "📋 Report", "🔄 Auto-Loop",
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

        with st.expander("🗑️ Manage saved", expanded=False):
            if st.button("Archive current run", key="snapshot_btn",
                         help="Save current results as a named snapshot you can compare against later"):
                from datetime import datetime
                snap_name = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                snap_dir = SAVE_DIR / "snapshots" / snap_name
                snap_dir.mkdir(parents=True, exist_ok=True)
                snap_data = {n: {k: v for k, v in r.items() if k != "model_state"}
                             for n, r in st.session_state.results.items()}
                (snap_dir / "results.json").write_text(json.dumps(snap_data, indent=2, default=str))
                st.success(f"Archived: `{snap_name}`")
            if st.button("Clear all results", key="clear_btn", type="secondary",
                         help="Clear current session — saved snapshots are kept"):
                st.session_state.results = {}
                st.session_state.evo_logs = {}
                st.session_state.ensemble_result = None
                st.rerun()


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
        <p class="sec-sub">Ten liquid neural architectures. Each tests a genuinely different wiring hypothesis.<br>
        Train them. Compare them. Evolve them. Query them. See which wins.</p>
    </div>""", unsafe_allow_html=True)

    if st.session_state.get("_load_warning"):
        st.warning(f"⚠️ {st.session_state['_load_warning']}")

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
        why_text = BRAIN_META.get(name, {}).get("why", "")
        with cols[i % 3]:
            st.markdown(f"""
            <div class="brain-tile" style="--brain-color:{color};">
                {entity_html}
                <div style="text-align:center;margin-top:8px;">
                    <div class="bt-name">{name.replace('_',' ').title()}{badge_html}</div>
                    <div class="bt-tag">{_tag(name)}</div>
                </div>
                <div style="font-size:0.68em;color:#64748b;text-align:center;margin:6px 0 8px 0;line-height:1.5;padding:0 4px;">
                    {why_text}
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
        "jellyfish":       (-2, -1, -2),
        "fungal":          (-2, 1, 1),
        "insect":          (-1, -2, 0),
        "octopus":         (-1, 1, -1),
        "corvid":          (0, -1, 1),
        "dolphin":         (1, 1, 0),
        "human":           (2, 0, 1),
        "foundation_core": (0, 2, 0),
        "alien":           (-1, 0, 2),
        "ultimate":        (1, -1, 2),
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
            hovertext=f"<b>{name}</b><br>{_tag(name)}<br><i>{BRAIN_META.get(name,{}).get('why','')[:80]}...</i>",
            showlegend=False))
    # Connection lines between related brains
    connections = [
        ("human", "foundation_core"),
        ("human", "dolphin"), ("human", "corvid"),
        ("insect", "alien"), ("octopus", "alien"),
        ("alien", "ultimate"), ("human", "ultimate"),
        ("dolphin", "ultimate"), ("insect", "ultimate"),
        ("corvid", "ultimate"), ("octopus", "ultimate"),
        ("fungal", "alien"), ("fungal", "octopus"),
        ("jellyfish", "octopus"), ("jellyfish", "insect"),
        ("jellyfish", "fungal"),
        ("fungal", "ultimate"),
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

    with st.expander("💡 What do the results mean?", expanded=False):
        st.markdown("""
**Loss** = how wrong the brain's predictions are. Lower is better. A loss of 0.03 means the brain is predicting sequences almost perfectly. A loss of 0.15 means it's still struggling.

**What's happening during training:** Each brain receives random patterns — sine waves, noise, copied signals, regime switches — and tries to predict the next value. The training loop adjusts the brain's internal wiring until it gets better at guessing what comes next.

**Why loss curves matter:** A loss curve that drops fast then levels off means the brain learned quickly and hit its ceiling. A curve that keeps dropping slowly means it's still improving and might get better with more training steps. If two brains reach the same final loss but one got there in 2 seconds and the other in 10, the fast one is more *efficient* — it extracts more learning per computation.

**Multi-seed training (2+ seeds):** Single training runs are noisy — the same brain can get lucky or unlucky depending on its random starting point. Running 3+ seeds and averaging gives you reliable numbers. The ± value after the loss is the standard deviation — smaller means more consistent.

**Parameters:** Total learnable weights. Fewer parameters achieving the same loss = more efficient architecture. This matters in real applications where compute and memory are limited.
""")


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
            n_seeds = st.slider("Seeds (avg)", 1, 5, 1, 1, key="tr_seeds",
                                help="Train N times with different seeds. Reports mean ± std. "
                                     "Single-seed results are noisy.")

    st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        train_btn = st.button("🚀 Train Selected", type="primary", key="train_btn", disabled=not active)
    with col2:
        n_runs_label = f"× {n_seeds} seeds" if n_seeds > 1 else ""
        st.caption(f"{len(active)} brains · {train_steps} steps {n_runs_label}")

    if train_btn:
        generators = get_all_generators()
        loss_fn = nn.MSELoss()
        progress_bar = st.progress(0)
        total_work = len(active) * int(train_steps) * int(n_seeds)
        done = 0

        # ── Pre-generate shared batches for fairness across seeds (upgrade #5) ──
        shared_rng = np.random.default_rng(int(seed))
        pre_batches = []
        for step in range(int(train_steps)):
            b, _ = generate_batch(generators, shared_rng, int(batch_size), int(seq_len))
            pre_batches.append(b)
        # Pre-generate eval batch too
        pre_eval_batch, _ = generate_batch(generators, shared_rng, int(batch_size)*4, int(seq_len))

        # ── Quick benchmark for time estimate (upgrade #5) ──
        bench_model = list(FULL_REGISTRY.values())[0](input_size=1, hidden_size=hidden_size, dropout=0.1)
        bench_opt = torch.optim.AdamW(bench_model.parameters(), lr=lr, weight_decay=0.01)
        bench_t0 = time.time()
        for _bs in range(min(10, int(train_steps))):
            out_b = _normalize_output(bench_model, pre_batches[_bs])
            bl = loss_fn(out_b["predictions"], pre_batches[_bs][:, 1:, :])
            bench_opt.zero_grad(); bl.backward()
            torch.nn.utils.clip_grad_norm_(bench_model.parameters(), 1.0); bench_opt.step()
        bench_per_step = (time.time() - bench_t0) / min(10, int(train_steps))
        est_total = bench_per_step * int(train_steps) * int(n_seeds) * len(active)
        del bench_model, bench_opt
        st.caption(f"⏱️ Estimated total time: ~{est_total:.0f}s ({est_total/60:.1f}m) based on 10-step benchmark")

        for brain_name in active:
            Cls = FULL_REGISTRY[brain_name]
            color = _c(brain_name)

            # Three-column layout: topology + info + seed progress
            if int(n_seeds) > 1:
                col_topo, col_info, col_seeds = st.columns([2, 1, 1])
            else:
                col_topo, col_info = st.columns([2, 1])
                col_seeds = None
            topo_container = col_topo.empty()
            info_container = col_info.empty()
            seeds_container = col_seeds.empty() if col_seeds is not None else None

            # Per-seed accumulation
            per_seed_eval = []
            per_seed_pca = []
            per_seed_loss_history = []
            per_seed_train_time = []
            best_model_state = None
            best_loss = float("inf")
            n_reg = 0
            param_count = 0

            for seed_idx in range(int(n_seeds)):
                run_seed = int(seed) + seed_idx
                model = Cls(input_size=1, hidden_size=hidden_size, dropout=0.1)
                optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
                torch.manual_seed(run_seed)
                rng = np.random.default_rng(run_seed)
                loss_history = []
                model.train()
                t0 = time.time()

                for step in range(int(train_steps)):
                    batch = pre_batches[step]
                    out = _normalize_output(model, batch)
                    loss = loss_fn(out["predictions"], batch[:, 1:, :])
                    optimizer.zero_grad()
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    optimizer.step()
                    if step % 25 == 0:
                        lv = float(loss.item())
                        loss_history.append({"step": step, "loss": lv})

                        # Build topology figure
                        if isinstance(out, dict) and "region_traces" in out:
                            topo_fig = _build_brain_topology(brain_name, out["region_traces"], color)
                            topo_container.plotly_chart(topo_fig, use_container_width=True,
                                                        key=f"topo_{brain_name}_{seed_idx}_{step}")

                        # Info panel with entity + loss + seed indicator
                        loss_bar_w = max(0, min(100, 100 - lv * 200))
                        ent_html = get_entity_html(brain_name, lv)
                        seed_pill = (f'<div style="font-size:0.65em;color:{color};text-align:center;'
                                     f'margin-bottom:4px;font-weight:700;">SEED {seed_idx+1}/{int(n_seeds)}</div>'
                                     if int(n_seeds) > 1 else "")
                        info_container.markdown(f"""
                        <div style="padding:12px;background:#0d1220;border:1px solid #1a2744;border-radius:12px;">
                            {ent_html}
                            <div style="font-weight:800;color:{color};font-size:0.95em;margin-bottom:4px;text-align:center;">
                                {_i(brain_name)} {brain_name}
                            </div>
                            {seed_pill}
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
                    eb = pre_eval_batch
                    eo = _normalize_output(model, eb)
                    el = float(loss_fn(eo["predictions"], eb[:, 1:, :]).item())
                    h = eo["hidden"][:, -1, :].numpy()
                    pca3 = 0.0
                    if h.shape[1] > 3:
                        try:
                            _, s, _ = np.linalg.svd(h - h.mean(axis=0), full_matrices=False)
                            vr = (s**2) / (s**2).sum()
                            pca3 = float(vr[:3].sum())
                        except: pass
                    else: pca3 = 1.0
                    n_reg = len(eo.get("region_traces", {})) if isinstance(eo, dict) else 0

                per_seed_eval.append(el)
                per_seed_pca.append(pca3)
                per_seed_loss_history.append(loss_history)
                per_seed_train_time.append(train_time)
                param_count = sum(p.numel() for p in model.parameters())
                if el < best_loss:
                    best_loss = el
                    best_model_state = model.state_dict()

                # ── Live multi-seed progress chart (upgrade #4) ──
                if seeds_container is not None and len(per_seed_eval) >= 1:
                    fig_seeds = go.Figure()
                    xs = list(range(1, len(per_seed_eval) + 1))
                    ys = per_seed_eval
                    mean_val = float(np.mean(ys))
                    fig_seeds.add_trace(go.Scatter(
                        x=xs, y=ys, mode="markers",
                        marker=dict(size=10, color=color, line=dict(width=1, color="#0d1117")),
                        name="Per-seed loss", showlegend=False))
                    if len(ys) >= 2:
                        std_val = float(np.std(ys))
                        fig_seeds.add_trace(go.Scatter(
                            x=xs, y=[mean_val]*len(xs), mode="lines",
                            line=dict(color=color, width=2, dash="dash"),
                            name=f"Mean: {mean_val:.5f}", showlegend=True))
                        # Error band
                        fig_seeds.add_trace(go.Scatter(
                            x=xs + xs[::-1],
                            y=[mean_val + std_val]*len(xs) + [mean_val - std_val]*len(xs),
                            fill="toself", fillcolor=_hex_to_rgba(color, 0.15),
                            line=dict(width=0), showlegend=False, hoverinfo="skip"))
                    fig_seeds.update_layout(
                        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="#0d1117", height=250,
                        margin=dict(l=30, r=10, t=30, b=30),
                        title=dict(text=f"Seeds: {mean_val:.5f}" + (f" ± {float(np.std(ys)):.5f}" if len(ys) > 1 else ""),
                                   font=dict(size=11)),
                        xaxis=dict(title="Seed", dtick=1, gridcolor="#1e293b"),
                        yaxis=dict(title="Eval Loss", gridcolor="#1e293b"),
                        legend=dict(font=dict(size=9)))
                    seeds_container.plotly_chart(fig_seeds, use_container_width=True,
                                                 key=f"seeds_{brain_name}_{seed_idx}")

            # Aggregate across seeds
            mean_loss = float(np.mean(per_seed_eval))
            std_loss = float(np.std(per_seed_eval)) if len(per_seed_eval) > 1 else 0.0
            mean_pca = float(np.mean(per_seed_pca))
            mean_time = float(np.mean(per_seed_train_time))

            st.session_state.results[brain_name] = {
                "eval_loss": mean_loss,           # mean across seeds
                "eval_loss_std": std_loss,
                "n_seeds": int(n_seeds),
                "per_seed_loss": per_seed_eval,
                "pca_top3": mean_pca,
                "train_time": round(mean_time, 1),
                "loss_history": per_seed_loss_history[0],   # show first-seed curve
                "all_loss_histories": per_seed_loss_history,  # all seeds for plotting
                "params": param_count,
                "regions": n_reg,
                "model_state": best_model_state,    # save the best of N seeds
                "hidden_size": hidden_size,
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
            n_s = r.get("n_seeds", 1)
            std = r.get("eval_loss_std", 0)
            loss_display = (f"{r.get('eval_loss',0):.5f} ± {std:.5f}" if n_s > 1
                            else f"{r.get('eval_loss',0):.5f}")
            seed_chip = (f'<span style="font-size:0.65em;color:#a78bfa;background:#1a2744;'
                         f'padding:2px 6px;border-radius:8px;margin-left:6px;">{n_s} seeds</span>'
                         if n_s > 1 else "")
            st.markdown(f"""
            <div class="rank-item" style="--rank-color:{m_color};">
                <div class="rank-num">{m_icon}</div>
                <div style="font-size:1.2em;">{_i(name)}</div>
                <div class="rank-name" style="color:{_c(name)};">{name.replace('_',' ').title()}{seed_chip}</div>
                <span class="badge" style="--badge-color:{bc};">{bl}</span>
                <div class="rank-val">{loss_display}</div>
                <div style="font-size:0.72em;color:#475569;">{r.get('params',0):,}p · {r.get('train_time',0)}s</div>
            </div>""", unsafe_allow_html=True)

        # Loss curves — show all seeds as faint lines + mean as bold
        st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
        fig = go.Figure()
        for name, r in res.items():
            if "loss_history" not in r: continue
            color = _c(name)
            # If we have multi-seed histories, show them all faintly + mean bold
            histories = r.get("all_loss_histories") or [r["loss_history"]]
            if len(histories) > 1:
                # Per-seed faint lines
                for hi, hist in enumerate(histories):
                    fig.add_trace(go.Scatter(
                        x=[h["step"] for h in hist],
                        y=[h["loss"] for h in hist],
                        mode="lines", line=dict(color=color, width=1),
                        opacity=0.25, showlegend=False, hoverinfo="skip"))
                # Compute mean curve over seeds (assume same step grid)
                all_steps = sorted({h["step"] for hist in histories for h in hist})
                mean_y = []
                for s in all_steps:
                    vals = [h["loss"] for hist in histories for h in hist if h["step"] == s]
                    if vals:
                        mean_y.append(np.mean(vals))
                    else:
                        mean_y.append(None)
                fig.add_trace(go.Scatter(
                    x=all_steps, y=mean_y, mode="lines",
                    name=f"{_i(name)} {name}",
                    line=dict(color=color, width=2.8)))
            else:
                fig.add_trace(go.Scatter(
                    x=[h["step"] for h in histories[0]],
                    y=[h["loss"] for h in histories[0]],
                    mode="lines", name=f"{_i(name)} {name}",
                    line=dict(color=color, width=2.5)))
        _plot_defaults(fig, 420, title="Training Loss Curves (faint = individual seeds, bold = mean)",
                       yaxis_type="log", xaxis_title="Step", yaxis_title="Loss")
        st.plotly_chart(fig, use_container_width=True)

        # ── Learning Dynamics Heatmap ──
        st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
        st.markdown('<p class="sec-header" style="font-size:1.05em;">Learning Dynamics</p>', unsafe_allow_html=True)
        st.markdown('<p class="sec-sub">Each row is a brain, each column is a training checkpoint. '
                    'Color shows loss at that moment — darker = lower loss = better. '
                    'Watch for brains that learn in bursts vs. steady declines.</p>', unsafe_allow_html=True)

        # Build heatmap data: rows=brains, cols=steps
        hm_names = []
        hm_data = []
        for name, r in sorted_res:
            histories = r.get("all_loss_histories") or [r.get("loss_history", [])]
            if not histories or not histories[0]:
                continue
            # Use mean across seeds
            all_steps = sorted({h["step"] for hist in histories for h in hist})
            mean_vals = []
            for s in all_steps:
                vals = [h["loss"] for hist in histories for h in hist if h["step"] == s]
                mean_vals.append(np.mean(vals) if vals else 0)
            if mean_vals:
                hm_names.append(f"{_i(name)} {name}")
                hm_data.append(mean_vals)

        if hm_data and len(hm_data) >= 2:
            hm_matrix = np.array(hm_data)
            # Log-scale for better color differentiation
            hm_log = np.log10(np.clip(hm_matrix, 1e-6, None))
            fig = go.Figure(data=go.Heatmap(
                z=hm_log,
                y=hm_names,
                x=[str(s) for s in all_steps],
                colorscale=[[0, "#34d399"], [0.3, "#1d4ed8"], [0.6, "#7c3aed"], [1, "#ef4444"]],
                text=[[f"{v:.4f}" for v in row] for row in hm_matrix],
                texttemplate="%{text}",
                textfont=dict(size=8, color="#e2e8f0"),
                colorbar=dict(title="log₁₀(loss)"),
                hovertemplate="Brain: %{y}<br>Step %{x}<br>Loss: %{text}<extra></extra>"))
            _plot_defaults(fig, height=max(280, 35 * len(hm_names) + 80),
                           title="Loss Heatmap Over Training")
            fig.update_layout(xaxis_title="Training Step", yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)

            # Learning speed analysis
            st.markdown("""
            <div style="padding:12px 16px;background:#0d1220;border:1px solid #1a2744;border-radius:10px;margin:8px 0;">
                <div style="font-weight:700;color:#e2e8f0;font-size:0.85em;margin-bottom:6px;">🔍 Reading this heatmap</div>
                <div style="font-size:0.75em;color:#94a3b8;line-height:1.6;">
                    <b style="color:#34d399;">Green</b> = low loss (brain has learned well at this point)<br>
                    <b style="color:#ef4444;">Red</b> = high loss (still struggling)<br>
                    A row that goes from red→green quickly = fast learner<br>
                    A row that stays red = architecture struggling with this task<br>
                    Columns where ALL rows turn green = easy part of training (all brains handle it)<br>
                    Columns where rows diverge = where architectural differences show up
                </div>
            </div>""", unsafe_allow_html=True)

        # ── Efficiency analysis ──
        if len(sorted_res) >= 3:
            st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
            st.markdown('<p class="sec-header" style="font-size:1.05em;">Efficiency Report</p>', unsafe_allow_html=True)
            best_name, best_r = sorted_res[0]
            worst_name, worst_r = sorted_res[-1]
            best_eff = sorted(sorted_res, key=lambda x: x[1].get("eval_loss", 999) * x[1].get("params", 1))
            eff_name, eff_r = best_eff[0]

            e1, e2, e3 = st.columns(3)
            e1.markdown(f"""
            <div class="metric-tile" style="--mt-color:#34d399;">
                <div class="mt-val">{_i(best_name)}</div>
                <div class="mt-lbl">Most Accurate</div>
                <div class="mt-delta">{best_r.get('eval_loss',0):.5f} loss · {best_r.get('params',0):,}p</div>
            </div>""", unsafe_allow_html=True)
            e2.markdown(f"""
            <div class="metric-tile" style="--mt-color:#60a5fa;">
                <div class="mt-val">{_i(eff_name)}</div>
                <div class="mt-lbl">Most Efficient</div>
                <div class="mt-delta">{eff_r.get('eval_loss',0):.5f} loss · {eff_r.get('params',0):,}p</div>
            </div>""", unsafe_allow_html=True)
            e3.markdown(f"""
            <div class="metric-tile" style="--mt-color:#ef4444;">
                <div class="mt-val">{_i(worst_name)}</div>
                <div class="mt-lbl">Needs Evolution</div>
                <div class="mt-delta">{worst_r.get('eval_loss',0):.5f} loss · {worst_r.get('params',0):,}p</div>
            </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════
# PAGE: Compare / Convergence
# ════════════════════════════════════════
elif page == "📊 Compare":
    st.markdown("""
    <p class="sec-header">Convergence Analysis</p>
    <p class="sec-sub">Do different brain architectures discover the same structure when given the same data?<br>
    If they converge — the structure is <b>necessary</b>. If they diverge — wiring <b>matters</b>.</p>
    """, unsafe_allow_html=True)

    with st.expander("💡 Reading the convergence analysis", expanded=False):
        st.markdown("""
**The core question:** If you give 10 completely different brain architectures the same training data, do they all end up learning the same thing inside? Or does their internal wiring push them toward genuinely different solutions?

**Eval Loss bar chart:** Ranks brains by prediction accuracy. If all bars are roughly the same height, architecture doesn't matter much for this task. If there's a big spread, some wiring strategies are genuinely better.

**Efficiency Frontier:** Plots accuracy (y-axis) vs size (x-axis). Brains in the bottom-left corner are the winners — small and accurate. A brain that's huge but no more accurate than a smaller one is *wasteful*. This is the chart that matters most for practical applications.

**CKA Similarity Matrix:** Goes deeper than "who scored best" to ask "are they thinking the same way?" CKA compares the actual internal representations (hidden states) of different brains. A value of 0.9 between jellyfish and human means they arrived at nearly identical internal geometry despite totally different wiring. A value of 0.3 means they found genuinely different solutions.

**Radar chart:** Five axes comparing brains on different dimensions. A brain that dominates all axes is universally better. More commonly, each brain wins on different axes — the octopus might be most efficient while the human is most accurate. This shows the *tradeoffs* between architectural choices.

**Statistical significance (multi-seed only):** With enough seeds, you can ask "is the difference between brain A and brain B real, or just noise?" Green cells in the p-value matrix mean the difference is statistically significant — you can trust that ranking. Red cells mean the difference could be random.
""")


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
        # ── CKA representational similarity matrix ──
        trained_with_state = [n for n in names if "model_state" in res[n]]
        if len(trained_with_state) >= 2:
            st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
            st.markdown('<p class="sec-header" style="font-size:1.1em;">Representational Similarity (CKA)</p>', unsafe_allow_html=True)
            st.markdown('<p class="sec-sub">Are the brains learning the same internal representations? '
                        '1.0 = identical, 0.0 = orthogonal. High off-diagonal values mean architecture '
                        "doesn't matter for this task — they all converge to similar geometry.</p>",
                        unsafe_allow_html=True)

            with st.spinner("Computing pairwise CKA..."):
                generators_cka = get_all_generators()
                rng_cka = np.random.default_rng(_def_seed)
                eval_batch, _ = generate_batch(generators_cka, rng_cka, 16, 64)

                hidden_states = {}
                for n in trained_with_state:
                    hs_n = res[n].get("hidden_size", _def_hidden)
                    Cls_n = FULL_REGISTRY[n]
                    m_n = Cls_n(input_size=1, hidden_size=hs_n, dropout=0.0)
                    try:
                        m_n.load_state_dict(res[n]["model_state"])
                        m_n.eval()
                        with torch.no_grad():
                            o_n = _normalize_output(m_n, eval_batch)
                            # Flatten [B, T, H] → [B*T, H] for CKA
                            h = o_n["hidden"].detach().cpu().numpy()
                            hidden_states[n] = h.reshape(-1, h.shape[-1])
                    except Exception:
                        continue

                if len(hidden_states) >= 2:
                    cka_names, cka_M = _compute_cka_matrix(hidden_states)

                    # Plot heatmap
                    labels = [f"{_i(n)} {n}" for n in cka_names]
                    fig = go.Figure(data=go.Heatmap(
                        z=cka_M,
                        x=labels, y=labels,
                        colorscale=[[0, "#0d1220"], [0.3, "#1d4ed8"],
                                    [0.6, "#a78bfa"], [0.85, "#f472b6"], [1, "#fbbf24"]],
                        zmin=0, zmax=1,
                        text=[[f"{cka_M[i,j]:.2f}" for j in range(len(cka_names))]
                              for i in range(len(cka_names))],
                        texttemplate="%{text}",
                        textfont=dict(size=10, color="#e2e8f0"),
                        colorbar=dict(title="CKA", tickcolor="#64748b"),
                        hovertemplate="%{y} vs %{x}: <b>%{z:.3f}</b><extra></extra>"))
                    _plot_defaults(fig, height=max(360, 40 * len(cka_names) + 80),
                                   title="Pairwise Hidden-State Similarity")
                    st.plotly_chart(fig, use_container_width=True)

                    # Verdict
                    off_diag = cka_M[np.triu_indices(len(cka_names), k=1)]
                    mean_cka = float(off_diag.mean())
                    min_cka = float(off_diag.min())
                    max_cka = float(off_diag.max())
                    vc1, vc2, vc3 = st.columns(3)
                    vc1.metric("Mean CKA", f"{mean_cka:.3f}")
                    vc2.metric("Most aligned pair", f"{max_cka:.3f}")
                    vc3.metric("Least aligned pair", f"{min_cka:.3f}")

                    if mean_cka > 0.85:
                        st.success("🎯 **Strong representational convergence** — different architectures find essentially the same geometry. The task is the constraint, not the wiring.")
                    elif mean_cka > 0.6:
                        st.info("📊 **Moderate convergence** — overlapping representations with architectural variation.")
                    else:
                        st.warning("🔀 **Representational divergence** — brains are finding genuinely different solutions to the same task.")

        # ── Statistical Significance (multi-seed only) ──
        multi_seed_brains = [n for n in names if res[n].get("n_seeds", 1) > 1 and len(res[n].get("per_seed_loss", [])) > 1]
        if len(multi_seed_brains) >= 2:
            st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
            st.markdown('<p class="sec-header" style="font-size:1.1em;">Statistical Significance</p>', unsafe_allow_html=True)
            st.markdown('<p class="sec-sub">Pairwise Welch\'s t-test on per-seed eval losses. '
                        'Green = significant (p&lt;0.05), yellow = marginal (p&lt;0.10), red = not significant.</p>',
                        unsafe_allow_html=True)

            msb = multi_seed_brains
            n_msb = len(msb)
            p_matrix = np.ones((n_msb, n_msb))
            d_matrix = np.zeros((n_msb, n_msb))
            sig_count = 0
            total_pairs = 0
            for i in range(n_msb):
                for j in range(i + 1, n_msb):
                    a = np.array(res[msb[i]]["per_seed_loss"])
                    b = np.array(res[msb[j]]["per_seed_loss"])
                    _, p = _welch_t_test(a, b)
                    d = _cohens_d(a, b)
                    p_matrix[i, j] = p_matrix[j, i] = p
                    d_matrix[i, j] = d
                    d_matrix[j, i] = -d
                    total_pairs += 1
                    if p < 0.05:
                        sig_count += 1

            # Significance heatmap
            sig_labels = [f"{_i(n)} {n}" for n in msb]
            # Color: green for p<0.05, yellow for p<0.10, red for p>=0.10
            # Use a custom colorscale: 0=green (sig), 0.5=yellow, 1=red
            fig_sig = go.Figure(data=go.Heatmap(
                z=p_matrix,
                x=sig_labels, y=sig_labels,
                colorscale=[[0, "#059669"], [0.05, "#059669"], [0.10, "#eab308"], [0.5, "#ef4444"], [1, "#ef4444"]],
                zmin=0, zmax=1,
                text=[[f"p={p_matrix[i,j]:.3f}\nd={d_matrix[i,j]:.2f}" if i != j else "—"
                       for j in range(n_msb)] for i in range(n_msb)],
                texttemplate="%{text}",
                textfont=dict(size=9, color="#e2e8f0"),
                colorbar=dict(title="p-value", tickcolor="#64748b"),
                hovertemplate="%{y} vs %{x}: <b>p=%{z:.4f}</b><extra></extra>"))
            _plot_defaults(fig_sig, height=max(360, 40 * n_msb + 80),
                           title="Pairwise Statistical Significance (p-values)")
            st.plotly_chart(fig_sig, use_container_width=True)

            st.markdown(f"**{sig_count} of {total_pairs}** pairs show statistically significant differences (p < 0.05)")

            # Effect size summary
            with st.expander("Effect sizes (Cohen's d)", expanded=False):
                for i in range(n_msb):
                    for j in range(i + 1, n_msb):
                        d = d_matrix[i, j]
                        mag = "negligible" if abs(d) < 0.2 else "small" if abs(d) < 0.5 else "medium" if abs(d) < 0.8 else "large"
                        st.caption(f"{_i(msb[i])} {msb[i]} vs {_i(msb[j])} {msb[j]}: d = {d:.3f} ({mag})")

        if len(names) >= 3:
            st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
            cats = ["Efficiency", "Accuracy", "Complexity", "Speed", "Geometry"]
            # Compute raw scores per brain
            raw_scores = {}
            for name in names:
                r = res[name]
                raw_scores[name] = [
                    50000 / max(r["params"], 1),
                    1 / max(r["eval_loss"], 0.001),
                    r.get("regions", 0) / 15.0,
                    1 / max(r.get("train_time", 1), 0.1),
                    r.get("pca_top3", 0),
                ]
            # Normalize across brains per metric (so each axis is comparable)
            per_axis_max = [max(raw_scores[n][i] for n in names) or 1.0 for i in range(len(cats))]
            fig = go.Figure()
            for name in names:
                v = [raw_scores[name][i] / per_axis_max[i] for i in range(len(cats))]
                v.append(v[0])
                fig.add_trace(go.Scatterpolar(
                    r=v, theta=cats + [cats[0]], fill="toself",
                    name=f"{_i(name)} {name}", opacity=0.18,
                    line=dict(color=_c(name), width=2)))
            fig.update_layout(
                polar=dict(bgcolor="#0d1117",
                           radialaxis=dict(visible=True, color="#334155", gridcolor="#1a2744", range=[0, 1]),
                           angularaxis=dict(color="#94a3b8")),
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                title="Capabilities Radar (each axis normalized across brains)", height=500)
            st.plotly_chart(fig, use_container_width=True)

        # ── Task Affinity — per-generator performance per brain ──
        trained_with_state_ta = [n for n in names if "model_state" in res[n]]
        if len(trained_with_state_ta) >= 2:
            st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
            st.markdown('<p class="sec-header" style="font-size:1.1em;">Task Affinity</p>', unsafe_allow_html=True)
            st.markdown('<p class="sec-sub">Which brain handles which generator type best? '
                        'Lower MSE = better fit for that task.</p>', unsafe_allow_html=True)

            with st.spinner("Computing per-task affinity..."):
                generators_ta = get_all_generators()
                gen_names = list(generators_ta.keys())
                loss_fn_ta = nn.MSELoss()
                rng_ta = np.random.default_rng(_def_seed)
                task_mse = {}  # {brain_name: {gen_name: mse}}

                for bname in trained_with_state_ta:
                    hs_b = res[bname].get("hidden_size", _def_hidden)
                    Cls_b = FULL_REGISTRY[bname]
                    m_b = Cls_b(input_size=1, hidden_size=hs_b, dropout=0.0)
                    try:
                        m_b.load_state_dict(res[bname]["model_state"])
                    except Exception:
                        continue
                    m_b.eval()
                    task_mse[bname] = {}
                    for gname in gen_names:
                        single_gen = {gname: generators_ta[gname]}
                        rng_g = np.random.default_rng(_def_seed)
                        try:
                            tb, _ = generate_batch(single_gen, rng_g, 32, int(_def_seq))
                            with torch.no_grad():
                                to = _normalize_output(m_b, tb)
                                task_mse[bname][gname] = float(loss_fn_ta(to["predictions"], tb[:, 1:, :]).item())
                        except Exception:
                            task_mse[bname][gname] = float("nan")

                if task_mse:
                    ta_brains = list(task_mse.keys())
                    ta_gens = gen_names
                    z_ta = np.array([[task_mse[b].get(g, float("nan")) for g in ta_gens] for b in ta_brains])
                    ta_labels_y = [f"{_i(b)} {b}" for b in ta_brains]

                    fig_ta = go.Figure(data=go.Heatmap(
                        z=z_ta, x=ta_gens, y=ta_labels_y,
                        colorscale=[[0, "#059669"], [0.3, "#22d3ee"], [0.6, "#eab308"], [1, "#ef4444"]],
                        text=[[f"{z_ta[i,j]:.4f}" for j in range(len(ta_gens))] for i in range(len(ta_brains))],
                        texttemplate="%{text}",
                        textfont=dict(size=9, color="#e2e8f0"),
                        colorbar=dict(title="MSE", tickcolor="#64748b"),
                        hovertemplate="%{y} on %{x}: <b>MSE=%{z:.5f}</b><extra></extra>"))
                    _plot_defaults(fig_ta, height=max(300, 40 * len(ta_brains) + 80),
                                   title="Per-Task MSE (lower = better)")
                    st.plotly_chart(fig_ta, use_container_width=True)

                    # Best brain per task
                    st.markdown("**Best brain per task:**")
                    for gi, gname in enumerate(ta_gens):
                        col_vals = z_ta[:, gi]
                        best_idx = int(np.nanargmin(col_vals))
                        st.caption(f"  {gname}: {_i(ta_brains[best_idx])} **{ta_brains[best_idx]}** (MSE {col_vals[best_idx]:.5f})")

                    # Best task per brain
                    st.markdown("**Best task per brain:**")
                    for bi, bname in enumerate(ta_brains):
                        row_vals = z_ta[bi, :]
                        best_gi = int(np.nanargmin(row_vals))
                        st.caption(f"  {_i(bname)} {bname}: **{ta_gens[best_gi]}** (MSE {row_vals[best_gi]:.5f})")

                    # Store for Report page
                    st.session_state["task_affinity"] = {
                        "brains": ta_brains, "generators": ta_gens, "mse_matrix": z_ta.tolist()
                    }

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

    with st.expander("💡 Understanding ensemble results", expanded=False):
        st.markdown("""
**What the ensemble does:** Instead of picking one brain, it runs ALL trained brains on every input and learns a "router" that decides how much to trust each brain's prediction. The router itself is a small neural network that adapts in real time.

**When the ensemble beats every individual:** This means the brains are *complementary* — each one is good at different things, and the router learns to switch between them. This is the most interesting outcome, because it means no single architecture is sufficient.

**When one brain dominates the routing:** The pie chart shows one brain getting 80%+ of the trust. This means that brain is just better at everything, and the ensemble degrades to "just use the best brain." The others aren't contributing.

**Routing timeline:** This is the most revealing chart. If the routing weights shift dramatically over the course of a sequence, it means different brains are better at different *parts* of the pattern. Early timesteps might favor the insect brain (fast instinct), while later timesteps favor the human brain (slow deliberation). If the routing is flat, one brain dominates throughout.

**Does it matter?** If the ensemble significantly beats the best individual, it suggests real-world AI systems should use *mixtures of architectures* rather than scaling up a single one. This is an active research question.
""")


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
                # Average the per-timestep weights across the batch for the timeline chart
                # weight_timeline: [B, T, n_brains]
                wt = eo["weight_timeline"]
                wt_mean = wt.mean(dim=0).cpu().numpy()  # [T, n_brains]
            st.session_state.ensemble_result = {
                "eval_loss": el, "routing": eo["routing_weights"],
                "loss_history": hist, "params": ens.param_count(),
                "weight_timeline": wt_mean,
                "brain_order": list(brains.keys()),
            }
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
                                  title="Who Does the Ensemble Trust? (Average)", height=380,
                                  font=dict(color="#94a3b8"))
                st.plotly_chart(fig, use_container_width=True)

            # ── Live routing timeline — stacked area chart of weights per timestep ──
            if "weight_timeline" in r:
                st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
                st.markdown('<p class="sec-header" style="font-size:1.05em;">Routing Timeline</p>', unsafe_allow_html=True)
                st.markdown('<p class="sec-sub">How does the ensemble shift its trust over time? '
                            'Each band shows that brain\'s influence at each timestep.</p>',
                            unsafe_allow_html=True)
                wt = r["weight_timeline"]  # [T, n_brains]
                brain_order = r.get("brain_order", list(routing.keys()))
                fig = go.Figure()
                for i, bn in enumerate(brain_order):
                    fig.add_trace(go.Scatter(
                        x=list(range(wt.shape[0])),
                        y=wt[:, i],
                        mode="lines",
                        stackgroup="one", groupnorm="fraction",
                        name=f"{_i(bn)} {bn}",
                        line=dict(width=0.5, color=_c(bn)),
                        fillcolor=_hex_to_rgba(_c(bn), 0.7)))
                _plot_defaults(fig, 320, title="Per-Timestep Routing Weights",
                               xaxis_title="Timestep", yaxis_title="Trust fraction")
                fig.update_layout(yaxis=dict(range=[0, 1], gridcolor="#1e293b"))
                st.plotly_chart(fig, use_container_width=True)

                # Also: most-trusted brain per step (winner-take-all view)
                winners = wt.argmax(axis=1)
                winner_counts = {brain_order[i]: int((winners == i).sum()) for i in range(len(brain_order))}
                winner_counts = {k: v for k, v in winner_counts.items() if v > 0}
                if winner_counts:
                    fig2 = go.Figure(data=[go.Bar(
                        x=[f"{_i(n)} {n}" for n in winner_counts],
                        y=list(winner_counts.values()),
                        marker_color=[_c(n) for n in winner_counts],
                        marker_line=dict(width=0))])
                    _plot_defaults(fig2, 240, title="Timesteps Won (winner-take-all)",
                                   yaxis_title="# steps")
                    st.plotly_chart(fig2, use_container_width=True)
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
        evo_order = ["jellyfish","fungal","insect","octopus","corvid","dolphin","human","foundation_core","alien","ultimate"]
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

    with st.expander("💡 What the query results tell you", expanded=False):
        st.markdown("""
**Predictions vs Actual:** The dotted line is the real signal. Each colored line is a brain's guess for what comes next. Brains that track the dotted line closely are good at this pattern. Watch for moments where one brain nails a transition that others miss.

**Surprise:** How unexpected the signal was for each brain. Low surprise = the brain predicted well. A brain with low loss during training but high surprise on your specific query is revealing: it learned general patterns but your input doesn't match them.

**Region Activity Heatmaps:** Each row is a brain region, each column is a timestep. Bright spots show which parts of the brain activate at which moments. Look for:
- **Focused activation:** Only a few regions light up → the brain is specialized
- **Broad activation:** Many regions active → the brain uses distributed processing
- **Temporal patterns:** Regions that activate in sequence → information flowing through the architecture

**Anomaly Score Timeline:** How "suspicious" each brain finds each part of your input. Spikes mean "I've never seen anything like this." If all brains spike at the same point, that part of your signal is genuinely unusual. If only one brain spikes, that brain's architecture makes it blind to that pattern.

**Try this:** Feed the same text to all brains and see which ones find human language patterns most surprising. Then try a pure sine wave — the rankings will flip.
""")


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

            all_preds, all_surp, all_anom = {}, {}, {}
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
                    if "anomaly_score" in out:
                        try:
                            all_anom[name] = out["anomaly_score"][0].numpy()
                        except Exception:
                            pass

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
            n_cols = 4 if len(query_targets) > 6 else min(3, len(query_targets))
            hm_cols = st.columns(n_cols)
            for idx, name in enumerate(query_targets[:12]):
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

            # ── Anomaly score timeline (confidence) ──
            if all_anom:
                st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
                fig = go.Figure()
                for n, a in all_anom.items():
                    fig.add_trace(go.Scatter(
                        y=a, mode="lines", name=f"{_i(n)} {n}",
                        line=dict(color=_c(n), width=1.6)))
                _plot_defaults(fig, 260, title="Anomaly Score Per Timestep (higher = brain is suspicious)",
                               xaxis_title="Timestep", yaxis_title="Anomaly")
                fig.update_layout(yaxis=dict(range=[0, 1]))
                st.plotly_chart(fig, use_container_width=True)

            # Ranking — by MSE, plus surprise + anomaly summary
            st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
            ranking = sorted(all_preds.keys(),
                             key=lambda n: np.mean((all_preds[n][:len(codes)-1] - codes[1:])**2))
            for rank, name in enumerate(ranking, 1):
                mse = float(np.mean((all_preds[name][:len(codes)-1] - codes[1:])**2))
                surprise = float(all_surp[name].mean()) if name in all_surp else 0.0
                anom = float(all_anom[name].mean()) if name in all_anom else None
                medals = {1: ("🥇", "#fbbf24"), 2: ("🥈", "#94a3b8"), 3: ("🥉", "#b45309")}
                mi, mc = medals.get(rank, (f"#{rank}", "#475569"))
                anom_chip = (f'<span style="font-size:0.7em;color:#475569;margin-left:8px;">'
                             f'anom <b style="color:{"#ef4444" if anom > 0.5 else "#34d399"};">{anom:.2f}</b>'
                             f'</span>' if anom is not None else "")
                st.markdown(f"""
                <div class="rank-item" style="--rank-color:{mc};">
                    <div class="rank-num">{mi}</div>
                    <div style="font-size:1.1em;">{_i(name)}</div>
                    <div class="rank-name" style="color:{_c(name)};">{name.replace('_',' ').title()}{anom_chip}</div>
                    <div class="rank-val">MSE {mse:.5f}</div>
                    <div style="font-size:0.72em;color:#475569;">surprise {surprise:.4f}</div>
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

    with st.expander("💡 How self-improvement works", expanded=False):
        st.markdown("""
**The process:** Pick a trained brain. The system creates N mutant copies, each with slightly different internal time constants (how fast each region processes information). All candidates retrain on the patterns the original brain struggled with most. The best-performing mutant survives. Repeat for as many generations as you want.

**What's actually mutating:** Each brain region has a "dt" parameter — its internal clock speed. A region with high dt reacts quickly (like reflexes). Low dt means the region is slow and deliberate (like planning). Mutation nudges these values randomly, then selection keeps only improvements.

**Mutation rate:** Fraction of regions that get mutated each generation. Higher = more exploration, but also more chance of breaking what already works. Start with 0.15 and increase if evolution stalls.

**Improvement %:** Positive means the mutant is better than the parent. Even small improvements (1-3%) compound over generations. If you see 0% repeatedly, the brain may have hit its architectural ceiling — it can't get better without changing the wiring itself, only the timing.

**When this matters:** If a brain performs poorly after normal training, evolution can sometimes rescue it by finding better timing. If it's already near-optimal, evolution will plateau. This tells you whether the architecture has *untapped potential* or has been fully exploited.
""")


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

                # ── Tabs: lineage + classic line chart ──
                ev_tab1, ev_tab2 = st.tabs(["🌳 Lineage", "📈 Loss curves"])

                with ev_tab1:
                    st.markdown('<p class="sec-sub">Each generation is a node — color = brain, '
                                'size = improvement, label = winner mutation.</p>',
                                unsafe_allow_html=True)
                    fig = go.Figure()
                    for bname, logs in st.session_state.evo_logs.items():
                        if not logs: continue
                        color = _c(bname)
                        # Plot as a path of nodes — gen number on x, loss on y (log-ish)
                        xs = list(range(0, len(logs) + 1))
                        ys = [logs[0]["before_loss"]] + [l["after_loss"] for l in logs]
                        # Lines
                        fig.add_trace(go.Scatter(
                            x=xs, y=ys, mode="lines",
                            line=dict(color=color, width=2),
                            opacity=0.6, showlegend=False, hoverinfo="skip"))
                        # Nodes
                        node_sizes = [12]
                        for l in logs:
                            imp = max(0, l.get("improvement_pct", 0))
                            node_sizes.append(12 + min(imp * 0.8, 28))
                        hover_texts = [f"<b>{bname}</b><br>Gen 0 (initial)<br>Loss: {logs[0]['before_loss']:.5f}"]
                        for gi, l in enumerate(logs, 1):
                            hover_texts.append(
                                f"<b>{bname}</b><br>Gen {gi}<br>"
                                f"Loss: {l['after_loss']:.5f}<br>"
                                f"Δ: {l.get('improvement_pct', 0):+.1f}%<br>"
                                f"Winner: {l.get('winner', '?')}<br>"
                                f"Mutations: {len(l.get('mutations_applied', []))}"
                            )
                        fig.add_trace(go.Scatter(
                            x=xs, y=ys, mode="markers+text",
                            marker=dict(size=node_sizes, color=color,
                                        line=dict(width=1.5, color="#0d1117")),
                            text=[_i(bname)] + [str(i+1) for i in range(len(logs))],
                            textposition="middle center",
                            textfont=dict(size=10, color="#0d1117"),
                            name=f"{_i(bname)} {bname}",
                            hovertext=hover_texts, hoverinfo="text"))
                    _plot_defaults(fig, 420, title="Brain Lineage — each generation is a step",
                                   xaxis_title="Generation", yaxis_title="Loss")
                    st.plotly_chart(fig, use_container_width=True)

                    # Summary stats
                    sc1, sc2, sc3 = st.columns(3)
                    total_gens = sum(len(logs) for logs in st.session_state.evo_logs.values())
                    sc1.metric("Total generations", total_gens)
                    # Best improvement
                    all_imps = [l.get("improvement_pct", 0)
                                for logs in st.session_state.evo_logs.values()
                                for l in logs]
                    if all_imps:
                        sc2.metric("Best single-gen jump", f"{max(all_imps):+.1f}%")
                    # Brains evolved
                    sc3.metric("Brains evolved", len([logs for logs in st.session_state.evo_logs.values() if logs]))

                with ev_tab2:
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


# ════════════════════════════════════════
# PAGE: Report
# ════════════════════════════════════════
elif page == "📋 Report":
    st.markdown("""
    <p class="sec-header">Experiment Report</p>
    <p class="sec-sub">Auto-generated summary of your training run — copy-paste ready.</p>
    """, unsafe_allow_html=True)

    if st.session_state.results:
        res = st.session_state.results
        names = list(res.keys())
        sorted_names = sorted(names, key=lambda n: res[n].get("eval_loss", 999))
        from datetime import datetime

        lines = []
        lines.append(f"# Foundation Lab — Experiment Report")
        lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**Brains trained:** {len(names)}")
        if names:
            sample = res[names[0]]
            lines.append(f"**Hidden size:** {sample.get('hidden_size', '?')}")
            lines.append(f"**Seeds per brain:** {sample.get('n_seeds', 1)}")
        lines.append("")

        # Convergence summary
        losses = [res[n]["eval_loss"] for n in names]
        spread = max(losses) - min(losses)
        converged = [n for n in names if res[n].get("eval_loss_std", 0) < 0.01]
        diverged = [n for n in names if res[n].get("eval_loss_std", 0) >= 0.01]
        lines.append("## Convergence")
        if spread < 0.01:
            lines.append(f"**Strong convergence** — loss spread = {spread:.5f}")
        elif spread < 0.05:
            lines.append(f"**Moderate convergence** — loss spread = {spread:.5f}")
        else:
            lines.append(f"**Divergence detected** — loss spread = {spread:.5f}")
        if converged:
            lines.append(f"Converged (std < 0.01): {', '.join(converged)}")
        if diverged:
            lines.append(f"Higher variance: {', '.join(diverged)}")
        lines.append("")

        # CKA summary (reuse session_state if available)
        lines.append("## CKA Representational Similarity")
        trained_with_state_rpt = [n for n in names if "model_state" in res[n]]
        if len(trained_with_state_rpt) >= 2:
            try:
                generators_rpt = get_all_generators()
                rng_rpt = np.random.default_rng(_def_seed)
                eval_batch_rpt, _ = generate_batch(generators_rpt, rng_rpt, 16, 64)
                hidden_states_rpt = {}
                for n in trained_with_state_rpt:
                    hs_n = res[n].get("hidden_size", _def_hidden)
                    m_n = FULL_REGISTRY[n](input_size=1, hidden_size=hs_n, dropout=0.0)
                    m_n.load_state_dict(res[n]["model_state"])
                    m_n.eval()
                    with torch.no_grad():
                        o_n = _normalize_output(m_n, eval_batch_rpt)
                        h = o_n["hidden"].detach().cpu().numpy()
                        hidden_states_rpt[n] = h.reshape(-1, h.shape[-1])
                if len(hidden_states_rpt) >= 2:
                    _, cka_M_rpt = _compute_cka_matrix(hidden_states_rpt)
                    off_diag_rpt = cka_M_rpt[np.triu_indices(len(hidden_states_rpt), k=1)]
                    mean_cka_rpt = float(off_diag_rpt.mean())
                    verdict = "convergent" if mean_cka_rpt > 0.6 else "divergent"
                    lines.append(f"Mean off-diagonal CKA: **{mean_cka_rpt:.3f}** ({verdict})")
                else:
                    lines.append("Not enough valid hidden states for CKA.")
            except Exception as e:
                lines.append(f"CKA computation failed: {e}")
        else:
            lines.append("Not enough trained brains with saved weights for CKA.")
        lines.append("")

        # Statistical significance
        multi_seed_rpt = [n for n in names if res[n].get("n_seeds", 1) > 1 and len(res[n].get("per_seed_loss", [])) > 1]
        if len(multi_seed_rpt) >= 2:
            lines.append("## Statistical Significance")
            sig_count_rpt = 0
            total_pairs_rpt = 0
            for i in range(len(multi_seed_rpt)):
                for j in range(i + 1, len(multi_seed_rpt)):
                    a = np.array(res[multi_seed_rpt[i]]["per_seed_loss"])
                    b = np.array(res[multi_seed_rpt[j]]["per_seed_loss"])
                    _, p = _welch_t_test(a, b)
                    total_pairs_rpt += 1
                    if p < 0.05:
                        sig_count_rpt += 1
            lines.append(f"**{sig_count_rpt} of {total_pairs_rpt}** pairs statistically significant (p < 0.05)")
            lines.append("")

        # Ensemble
        if st.session_state.ensemble_result:
            er = st.session_state.ensemble_result
            lines.append("## Ensemble")
            lines.append(f"Ensemble eval loss: **{er['eval_loss']:.5f}**")
            best_ind = min(res.values(), key=lambda x: x.get("eval_loss", 999))
            best_ind_loss = best_ind["eval_loss"]
            if er["eval_loss"] < best_ind_loss:
                imp = (best_ind_loss - er["eval_loss"]) / max(best_ind_loss, 1e-9) * 100
                lines.append(f"Beats best individual by **{imp:.1f}%**")
            else:
                lines.append("Did not beat best individual brain.")
            lines.append("")

        # Task affinity
        ta = st.session_state.get("task_affinity")
        if ta:
            lines.append("## Task Affinity")
            ta_brains = ta["brains"]
            ta_gens = ta["generators"]
            ta_mse = np.array(ta["mse_matrix"])
            for gi, gname in enumerate(ta_gens):
                col_vals = ta_mse[:, gi]
                best_idx = int(np.nanargmin(col_vals))
                lines.append(f"- **{gname}**: best = {ta_brains[best_idx]} (MSE {col_vals[best_idx]:.5f})")
            lines.append("")

        # Rankings
        lines.append("## Rankings")
        lines.append("| Rank | Brain | Eval Loss | Params | Time |")
        lines.append("|------|-------|-----------|--------|------|")
        for rank, n in enumerate(sorted_names, 1):
            r = res[n]
            loss_str = f"{r.get('eval_loss',0):.5f}"
            if r.get("n_seeds", 1) > 1:
                loss_str += f" ± {r.get('eval_loss_std', 0):.5f}"
            lines.append(f"| {rank} | {_i(n)} {n} | {loss_str} | {r.get('params',0):,} | {r.get('train_time',0)}s |")
        lines.append("")

        report_text = "\n".join(lines)

        st.code(report_text, language="markdown")
        st.caption("Use the copy button above to copy the full report.")

    else:
        st.info("Train some brains first to generate a report.")


# ════════════════════════════════════════
# PAGE: Auto-Loop
# ════════════════════════════════════════
elif page == "🔄 Auto-Loop":
    st.markdown("""
    <p class="sec-header">Autonomous Research Loop</p>
    <p class="sec-sub">Train → Evaluate → Self-improve the worst → Repeat. Runs continuously until you stop it.<br>
    Each cycle trains all brains, identifies the weakest, evolves it, then starts again with better brains.</p>
    """, unsafe_allow_html=True)

    with st.expander("💡 How the auto-loop works", expanded=False):
        st.markdown("""
**Each cycle does four things:**
1. **Train** all 10 brains on fresh random data with fresh seeds
2. **Quality check** — compare losses, identify the worst-performing brain
3. **Self-improve** — run evolution on the weakest brain to try to rescue it
4. **Log** — record what happened and start the next cycle

**Why this matters:** A single training run is a snapshot. The loop reveals *trends* — does the ranking stabilize? Does evolution actually help the weakest brain catch up? Do the brains converge over time or stay different?

**When to stop:** Watch the cycle log. If losses stop improving and the rankings are stable across 3+ cycles, the experiment has converged. If the worst brain keeps getting replaced by a different brain each cycle, the architectures are genuinely competitive.
""")

    with st.expander("⚙️ Loop Settings", expanded=True):
        lc1, lc2 = st.columns(2)
        with lc1:
            loop_steps = st.slider("Train steps per cycle", 100, 1000, 300, 50, key="loop_steps")
            loop_evo_steps = st.slider("Evolution steps", 50, 300, 150, 50, key="loop_evo")
        with lc2:
            loop_n_mut = st.slider("Evolution candidates", 1, 4, 2, key="loop_nmut")
            loop_seeds = st.slider("Seeds per cycle", 1, 3, 1, key="loop_seeds")
    max_cycles = st.slider("Max cycles (0 = unlimited until you navigate away)", 0, 50, 10, key="loop_max")

    st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)

    if "loop_log" not in st.session_state:
        st.session_state.loop_log = []

    col1, col2 = st.columns([1, 1])
    start_loop = col1.button("🔄 Start Research Loop", type="primary", key="loop_start")
    col2.caption(f"{len(st.session_state.loop_log)} cycles completed so far")

    if start_loop:
        generators = get_all_generators()
        loss_fn = nn.MSELoss()
        hidden_size = _def_hidden

        cycle_num = len(st.session_state.loop_log)
        max_c = int(max_cycles) if int(max_cycles) > 0 else 999

        log_container = st.empty()
        progress_bar = st.progress(0)
        phase_status = st.empty()
        detail_container = st.container()

        for cycle in range(max_c):
            cycle_num += 1
            cycle_seed = 1000 + cycle_num * 7  # different seed each cycle

            # ── Phase 1: Train all brains ──
            phase_status.markdown(f"""
            <div style="padding:10px 16px;background:#0d1220;border:1px solid #1a2744;border-radius:10px;margin:4px 0;">
                <span style="color:#60a5fa;font-weight:800;">CYCLE {cycle_num}</span>
                <span style="color:#64748b;"> · Phase 1/3 ·</span>
                <span style="color:#fbbf24;font-weight:600;">Training all brains...</span>
            </div>""", unsafe_allow_html=True)

            cycle_results = {}
            for brain_name, Cls in FULL_REGISTRY.items():
                n_s = int(loop_seeds)
                per_seed_eval = []
                best_state = None
                best_loss = float("inf")

                for si in range(n_s):
                    run_seed = cycle_seed + si
                    model = Cls(input_size=1, hidden_size=hidden_size, dropout=0.1)
                    # Warm start from previous cycle if available
                    if brain_name in st.session_state.results and "model_state" in st.session_state.results[brain_name]:
                        try:
                            model.load_state_dict(st.session_state.results[brain_name]["model_state"], strict=False)
                        except Exception:
                            pass
                    optimizer = torch.optim.AdamW(model.parameters(), lr=_def_lr, weight_decay=0.01)
                    torch.manual_seed(run_seed)
                    rng = np.random.default_rng(run_seed)
                    model.train()
                    for step in range(int(loop_steps)):
                        batch, _ = generate_batch(generators, rng, _def_batch, _def_seq)
                        out = _normalize_output(model, batch)
                        loss = loss_fn(out["predictions"], batch[:, 1:, :])
                        optimizer.zero_grad()
                        loss.backward()
                        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                        optimizer.step()
                    model.eval()
                    with torch.no_grad():
                        eb, _ = generate_batch(generators, rng, _def_batch * 4, _def_seq)
                        eo = _normalize_output(model, eb)
                        el = float(loss_fn(eo["predictions"], eb[:, 1:, :]).item())
                    per_seed_eval.append(el)
                    if el < best_loss:
                        best_loss = el
                        best_state = model.state_dict()

                mean_loss = float(np.mean(per_seed_eval))
                std_loss = float(np.std(per_seed_eval)) if len(per_seed_eval) > 1 else 0.0
                params = sum(p.numel() for p in model.parameters())
                cycle_results[brain_name] = mean_loss

                st.session_state.results[brain_name] = {
                    "eval_loss": mean_loss,
                    "eval_loss_std": std_loss,
                    "n_seeds": n_s,
                    "per_seed_loss": per_seed_eval,
                    "pca_top3": 0.0,
                    "train_time": 0,
                    "loss_history": [],
                    "params": params,
                    "regions": 0,
                    "model_state": best_state,
                    "hidden_size": hidden_size,
                }

            progress_bar.progress((cycle * 3 + 1) / (max_c * 3))

            # ── Phase 2: Quality check — find worst brain ──
            phase_status.markdown(f"""
            <div style="padding:10px 16px;background:#0d1220;border:1px solid #1a2744;border-radius:10px;margin:4px 0;">
                <span style="color:#60a5fa;font-weight:800;">CYCLE {cycle_num}</span>
                <span style="color:#64748b;"> · Phase 2/3 ·</span>
                <span style="color:#a78bfa;font-weight:600;">Quality check...</span>
            </div>""", unsafe_allow_html=True)

            sorted_brains = sorted(cycle_results.items(), key=lambda x: x[1])
            best_name, best_val = sorted_brains[0]
            worst_name, worst_val = sorted_brains[-1]

            progress_bar.progress((cycle * 3 + 2) / (max_c * 3))

            # ── Phase 3: Evolve the worst brain ──
            phase_status.markdown(f"""
            <div style="padding:10px 16px;background:#0d1220;border:1px solid #1a2744;border-radius:10px;margin:4px 0;">
                <span style="color:#60a5fa;font-weight:800;">CYCLE {cycle_num}</span>
                <span style="color:#64748b;"> · Phase 3/3 ·</span>
                <span style="color:#34d399;font-weight:600;">Evolving {_i(worst_name)} {worst_name}...</span>
            </div>""", unsafe_allow_html=True)

            evo_result = None
            if worst_name in FULL_REGISTRY and "model_state" in st.session_state.results.get(worst_name, {}):
                try:
                    Cls_w = FULL_REGISTRY[worst_name]
                    model_w = Cls_w(input_size=1, hidden_size=hidden_size, dropout=0.1)
                    model_w.load_state_dict(st.session_state.results[worst_name]["model_state"])
                    cfg = EvolutionConfig(
                        train_steps=int(loop_evo_steps), batch_size=_def_batch, seq_len=_def_seq,
                        lr=_def_lr, mutation_rate=0.15, mutation_strength=0.2, n_candidates=int(loop_n_mut))
                    evo_result = self_improve_cycle(model_w, worst_name, cfg)
                    st.session_state.results[worst_name]["model_state"] = model_w.state_dict()
                    st.session_state.results[worst_name]["eval_loss"] = evo_result["after_loss"]
                    if worst_name not in st.session_state.evo_logs:
                        st.session_state.evo_logs[worst_name] = []
                    st.session_state.evo_logs[worst_name].append(evo_result)
                except Exception as e:
                    evo_result = {"error": str(e)}

            progress_bar.progress((cycle * 3 + 3) / (max_c * 3))

            # ── Log this cycle ──
            evo_imp = evo_result.get("improvement_pct", 0) if evo_result and "improvement_pct" in evo_result else 0
            cycle_entry = {
                "cycle": cycle_num,
                "best": best_name, "best_loss": round(best_val, 5),
                "worst": worst_name, "worst_loss": round(worst_val, 5),
                "evolved": worst_name, "evo_improvement": round(evo_imp, 1),
                "spread": round(worst_val - best_val, 5),
            }
            st.session_state.loop_log.append(cycle_entry)

            # Show running log
            log_lines = []
            for entry in st.session_state.loop_log[-10:]:
                evo_str = f"evolved → {entry['evo_improvement']:+.1f}%" if entry['evo_improvement'] else "no improvement"
                log_lines.append(
                    f"**Cycle {entry['cycle']}** · "
                    f"Best: {_i(entry['best'])} {entry['best']} ({entry['best_loss']:.5f}) · "
                    f"Worst: {_i(entry['worst'])} {entry['worst']} ({entry['worst_loss']:.5f}) · "
                    f"{evo_str} · spread: {entry['spread']:.5f}"
                )
            log_container.markdown("\n\n".join(log_lines))

        _save_results()
        progress_bar.progress(1.0)
        phase_status.success(f"✅ Completed {min(max_c, cycle_num)} research cycles!")

    # Show history
    if st.session_state.loop_log:
        st.markdown('<div class="sec-line"></div>', unsafe_allow_html=True)
        st.markdown('<p class="sec-header" style="font-size:1.05em;">Loop History</p>', unsafe_allow_html=True)

        # Spread over time
        fig = go.Figure()
        cycles = [e["cycle"] for e in st.session_state.loop_log]
        fig.add_trace(go.Scatter(
            x=cycles, y=[e["best_loss"] for e in st.session_state.loop_log],
            mode="lines+markers", name="Best brain",
            line=dict(color="#34d399", width=2.5),
            marker=dict(size=8)))
        fig.add_trace(go.Scatter(
            x=cycles, y=[e["worst_loss"] for e in st.session_state.loop_log],
            mode="lines+markers", name="Worst brain",
            line=dict(color="#ef4444", width=2.5),
            marker=dict(size=8)))
        fig.add_trace(go.Scatter(
            x=cycles, y=[e["spread"] for e in st.session_state.loop_log],
            mode="lines", name="Spread",
            line=dict(color="#fbbf24", width=1.5, dash="dot")))
        _plot_defaults(fig, 350, title="Research Loop Progress",
                       xaxis_title="Cycle", yaxis_title="Loss")
        st.plotly_chart(fig, use_container_width=True)

        # Who was worst most often?
        from collections import Counter
        worst_counts = Counter(e["worst"] for e in st.session_state.loop_log)
        if worst_counts:
            st.markdown("**Most frequently weakest:**")
            for name, count in worst_counts.most_common(5):
                st.markdown(f"- {_i(name)} **{name}** — weakest in {count}/{len(st.session_state.loop_log)} cycles")
