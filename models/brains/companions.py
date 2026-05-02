"""
Brain Companions — each brain has a distinct visual entity.
============================================================

Each companion's shape, animation, and behavior reflects the real
biology of its species. They react to the brain's training state.

  Human     → Hexagonal cortex (structured, layered)
  Octopus   → Amorphous blob (shapeshifting, 8 tendrils)
  Corvid    → Angular crystal (dense, sharp, efficient)
  Dolphin   → Wave form (flowing, oscillating between halves)
  Insect    → Dual orbs (learned track + innate track)
  Alien     → Tesseract (geometric, impossible, rotating)
  Ultimate  → Morphing ring (absorbs all shapes)

Each companion is pure CSS/HTML — no images needed.
"""
from __future__ import annotations


def _companion_css():
    """Return all companion CSS animations."""
    return """
<style>
/* ── Shared companion base ── */
.companion {
  width: 64px; height: 64px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.companion * { pointer-events: none; }

/* ══ HUMAN — Hexagonal cortex ══ */
.comp-human .hex-core {
  width: 40px; height: 40px;
  clip-path: polygon(50% 0%, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%);
  background: linear-gradient(135deg, #1d4ed8, #60a5fa, #93c5fd);
  animation: humanPulse 3s ease-in-out infinite;
}
.comp-human .hex-ring {
  position: absolute; inset: 4px;
  clip-path: polygon(50% 0%, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%);
  border: 1.5px solid #60a5fa80;
  animation: humanSpin 12s linear infinite;
}
.comp-human .hex-ring2 {
  position: absolute; inset: -2px;
  clip-path: polygon(50% 0%, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%);
  border: 1px solid #60a5fa40;
  animation: humanSpin 18s linear infinite reverse;
}
@keyframes humanPulse { 0%,100% { filter: brightness(1); } 50% { filter: brightness(1.3); } }
@keyframes humanSpin { to { transform: rotate(360deg); } }

/* ══ OCTOPUS — Amorphous blob with tendrils ══ */
.comp-octopus .blob-core {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #f9a8d4, #ec4899, #be185d);
  animation: octMorph 4s ease-in-out infinite;
}
.comp-octopus .tendril {
  position: absolute;
  width: 3px; height: 18px;
  background: linear-gradient(to bottom, #f472b6, transparent);
  border-radius: 2px;
  transform-origin: top center;
  top: 50%; left: 50%;
  margin-left: -1.5px;
}
.comp-octopus .tendril:nth-child(2) { transform: rotate(0deg) translateY(14px); animation: tentWave 2s ease-in-out infinite; }
.comp-octopus .tendril:nth-child(3) { transform: rotate(45deg) translateY(14px); animation: tentWave 2s ease-in-out 0.25s infinite; }
.comp-octopus .tendril:nth-child(4) { transform: rotate(90deg) translateY(14px); animation: tentWave 2s ease-in-out 0.5s infinite; }
.comp-octopus .tendril:nth-child(5) { transform: rotate(135deg) translateY(14px); animation: tentWave 2s ease-in-out 0.75s infinite; }
.comp-octopus .tendril:nth-child(6) { transform: rotate(180deg) translateY(14px); animation: tentWave 2s ease-in-out 1s infinite; }
.comp-octopus .tendril:nth-child(7) { transform: rotate(225deg) translateY(14px); animation: tentWave 2s ease-in-out 1.25s infinite; }
.comp-octopus .tendril:nth-child(8) { transform: rotate(270deg) translateY(14px); animation: tentWave 2s ease-in-out 1.5s infinite; }
.comp-octopus .tendril:nth-child(9) { transform: rotate(315deg) translateY(14px); animation: tentWave 2s ease-in-out 1.75s infinite; }
@keyframes octMorph {
  0%,100% { border-radius: 50% 50% 50% 50%; transform: scale(1); }
  25% { border-radius: 60% 40% 55% 45%; transform: scale(1.05); }
  50% { border-radius: 45% 55% 40% 60%; transform: scale(0.95); }
  75% { border-radius: 55% 45% 60% 40%; transform: scale(1.03); }
}
@keyframes tentWave { 0%,100% { transform: rotate(var(--base-rot, 0deg)) translateY(14px) scaleY(1); } 50% { transform: rotate(var(--base-rot, 0deg)) translateY(14px) scaleY(1.3); } }

/* ══ CORVID — Angular crystal ══ */
.comp-corvid .crystal-core {
  width: 32px; height: 32px;
  background: linear-gradient(135deg, #7c3aed, #a78bfa, #c4b5fd);
  clip-path: polygon(50% 0%, 100% 38%, 82% 100%, 18% 100%, 0% 38%);
  animation: crystalShimmer 3s ease-in-out infinite;
}
.comp-corvid .crystal-shard {
  position: absolute;
  width: 8px; height: 20px;
  background: linear-gradient(to bottom, #a78bfa60, transparent);
  clip-path: polygon(50% 0%, 100% 100%, 0% 100%);
}
.comp-corvid .crystal-shard:nth-child(2) { top: 0; left: 50%; transform: translateX(-50%) rotate(0deg); animation: shardFloat 4s ease-in-out infinite; }
.comp-corvid .crystal-shard:nth-child(3) { top: 50%; right: 0; transform: rotate(72deg); animation: shardFloat 4s ease-in-out 0.8s infinite; }
.comp-corvid .crystal-shard:nth-child(4) { bottom: 0; left: 30%; transform: rotate(144deg); animation: shardFloat 4s ease-in-out 1.6s infinite; }
@keyframes crystalShimmer { 0%,100% { filter: brightness(1) hue-rotate(0deg); } 50% { filter: brightness(1.4) hue-rotate(15deg); } }
@keyframes shardFloat { 0%,100% { opacity: 0.3; transform: translateY(0); } 50% { opacity: 0.7; transform: translateY(-3px); } }

/* ══ DOLPHIN — Wave form ══ */
.comp-dolphin .wave-left, .comp-dolphin .wave-right {
  position: absolute;
  width: 24px; height: 24px;
  border-radius: 50%;
  top: 50%; transform: translateY(-50%);
}
.comp-dolphin .wave-left {
  left: 6px;
  background: radial-gradient(circle, #22d3ee, #0891b2);
  animation: dolphLeft 3s ease-in-out infinite;
}
.comp-dolphin .wave-right {
  right: 6px;
  background: radial-gradient(circle, #0891b2, #164e63);
  animation: dolphRight 3s ease-in-out infinite;
}
.comp-dolphin .wave-bridge {
  position: absolute;
  width: 20px; height: 3px;
  background: linear-gradient(90deg, #22d3ee, #0891b2);
  top: 50%; left: 50%; transform: translate(-50%, -50%);
  border-radius: 2px;
  animation: bridgePulse 3s ease-in-out infinite;
}
@keyframes dolphLeft { 0%,100% { transform: translateY(-50%) scale(1); opacity: 1; } 50% { transform: translateY(-50%) scale(0.7); opacity: 0.5; } }
@keyframes dolphRight { 0%,100% { transform: translateY(-50%) scale(0.7); opacity: 0.5; } 50% { transform: translateY(-50%) scale(1); opacity: 1; } }
@keyframes bridgePulse { 0%,100% { opacity: 0.3; } 50% { opacity: 0.8; } }

/* ══ INSECT — Dual orbs ══ */
.comp-insect .orb-learned {
  position: absolute;
  width: 22px; height: 22px;
  border-radius: 50%;
  background: radial-gradient(circle, #fbbf24, #92400e);
  top: 12px; left: 10px;
  animation: insectPulse 2s ease-in-out infinite;
}
.comp-insect .orb-innate {
  position: absolute;
  width: 18px; height: 18px;
  border-radius: 50%;
  background: radial-gradient(circle, #f59e0b, #78350f);
  bottom: 12px; right: 10px;
  animation: insectPulse 2s ease-in-out 1s infinite;
}
.comp-insect .conn {
  position: absolute;
  width: 2px; height: 16px;
  background: linear-gradient(to bottom, #fbbf2480, #f59e0b40);
  top: 50%; left: 50%;
  transform: translate(-50%, -50%) rotate(45deg);
  animation: insectConn 2s ease-in-out infinite;
}
@keyframes insectPulse { 0%,100% { box-shadow: 0 0 8px #fbbf2440; } 50% { box-shadow: 0 0 20px #fbbf2480; } }
@keyframes insectConn { 0%,100% { opacity: 0.3; } 50% { opacity: 0.8; } }

/* ══ ALIEN — Tesseract ══ */
.comp-alien .tess-outer {
  width: 40px; height: 40px;
  border: 2px solid #34d39960;
  animation: tessRotate 6s linear infinite;
}
.comp-alien .tess-inner {
  position: absolute;
  width: 24px; height: 24px;
  border: 2px solid #34d399;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  animation: tessRotate 6s linear infinite reverse;
}
.comp-alien .tess-dot {
  position: absolute;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #34d399;
  top: 50%; left: 50%;
  margin: -3px 0 0 -3px;
  box-shadow: 0 0 12px #34d399;
  animation: tessPulse 2s ease-in-out infinite;
}
@keyframes tessRotate { to { transform: rotate(360deg); } }
@keyframes tessPulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.5); } }

/* ══ ULTIMATE — Morphing ring ══ */
.comp-ultimate .morph-ring {
  width: 44px; height: 44px;
  border: 3px solid #f97316;
  border-radius: 50%;
  animation: morphShape 6s ease-in-out infinite, morphColor 8s linear infinite;
}
.comp-ultimate .morph-core {
  position: absolute;
  width: 20px; height: 20px;
  background: radial-gradient(circle, #fb923c, #c2410c);
  border-radius: 50%;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  animation: tessPulse 3s ease-in-out infinite;
}
@keyframes morphShape {
  0%,100% { border-radius: 50%; }
  16% { border-radius: 30% 70% 70% 30%; }
  33% { clip-path: polygon(50% 0%, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%); border-radius: 0; }
  50% { clip-path: polygon(50% 0%, 100% 38%, 82% 100%, 18% 100%, 0% 38%); }
  66% { clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%); }
  83% { clip-path: none; border-radius: 20%; }
}
@keyframes morphColor {
  0% { border-color: #f97316; }
  14% { border-color: #60a5fa; }
  28% { border-color: #f472b6; }
  42% { border-color: #a78bfa; }
  57% { border-color: #22d3ee; }
  71% { border-color: #fbbf24; }
  85% { border-color: #34d399; }
  100% { border-color: #f97316; }
}

/* ══ Foundation Core — Stacked layers ══ */
.comp-foundation_core .layer {
  position: absolute;
  left: 50%; transform: translateX(-50%);
  height: 10px;
  border-radius: 5px;
  background: linear-gradient(90deg, #818cf840, #818cf8, #818cf840);
}
.comp-foundation_core .layer:nth-child(1) { width: 40px; top: 14px; animation: layerPulse 3s ease-in-out infinite; }
.comp-foundation_core .layer:nth-child(2) { width: 32px; top: 28px; animation: layerPulse 3s ease-in-out 0.5s infinite; }
.comp-foundation_core .layer:nth-child(3) { width: 24px; top: 42px; animation: layerPulse 3s ease-in-out 1s infinite; }
@keyframes layerPulse { 0%,100% { opacity: 0.6; } 50% { opacity: 1; } }

/* ══ Neuromorphic — 4 connected dots ══ */
.comp-neuromorphic .n-dot {
  position: absolute;
  width: 10px; height: 10px;
  border-radius: 50%;
  background: #fb923c;
}
.comp-neuromorphic .n-dot:nth-child(1) { top: 10px; left: 50%; transform: translateX(-50%); animation: nPulse 2s ease-in-out infinite; }
.comp-neuromorphic .n-dot:nth-child(2) { bottom: 10px; left: 12px; animation: nPulse 2s ease-in-out 0.5s infinite; }
.comp-neuromorphic .n-dot:nth-child(3) { bottom: 10px; right: 12px; animation: nPulse 2s ease-in-out 1s infinite; }
.comp-neuromorphic .n-dot:nth-child(4) { top: 30px; left: 50%; transform: translateX(-50%); animation: nPulse 2s ease-in-out 1.5s infinite; }
.comp-neuromorphic .n-line {
  position: absolute;
  height: 1px; background: #fb923c60;
  top: 50%; left: 50%;
  width: 30px;
  transform-origin: left center;
}
.comp-neuromorphic .n-line:nth-child(5) { transform: translate(-50%, 0) rotate(-30deg); }
.comp-neuromorphic .n-line:nth-child(6) { transform: translate(-50%, 0) rotate(30deg); }
@keyframes nPulse { 0%,100% { box-shadow: 0 0 4px #fb923c40; } 50% { box-shadow: 0 0 12px #fb923c; } }

/* ══ FUNGAL — Mycelium web ══ */
.comp-fungal .myc-core {
  width: 20px; height: 20px;
  border-radius: 50%;
  background: radial-gradient(circle, #a3e635, #65a30d);
  animation: fungalPulse 4s ease-in-out infinite;
}
.comp-fungal .myc-thread {
  position: absolute;
  width: 2px; background: linear-gradient(to bottom, #a3e63560, transparent);
  border-radius: 1px; top: 50%; left: 50%; margin-left: -1px;
  transform-origin: top center;
}
.comp-fungal .myc-thread:nth-child(2) { height: 20px; transform: rotate(0deg) translateY(8px); animation: mycGrow 5s ease-in-out infinite; }
.comp-fungal .myc-thread:nth-child(3) { height: 18px; transform: rotate(60deg) translateY(8px); animation: mycGrow 5s ease-in-out 0.8s infinite; }
.comp-fungal .myc-thread:nth-child(4) { height: 22px; transform: rotate(120deg) translateY(8px); animation: mycGrow 5s ease-in-out 1.6s infinite; }
.comp-fungal .myc-thread:nth-child(5) { height: 16px; transform: rotate(180deg) translateY(8px); animation: mycGrow 5s ease-in-out 2.4s infinite; }
.comp-fungal .myc-thread:nth-child(6) { height: 20px; transform: rotate(240deg) translateY(8px); animation: mycGrow 5s ease-in-out 3.2s infinite; }
.comp-fungal .myc-thread:nth-child(7) { height: 19px; transform: rotate(300deg) translateY(8px); animation: mycGrow 5s ease-in-out 4s infinite; }
.comp-fungal .myc-node { position: absolute; width: 5px; height: 5px; border-radius: 50%; background: #a3e635; }
.comp-fungal .myc-node:nth-child(8) { top: 8px; left: 50%; animation: fungalPulse 3s ease-in-out 0.5s infinite; }
.comp-fungal .myc-node:nth-child(9) { bottom: 8px; right: 12px; animation: fungalPulse 3s ease-in-out 1.5s infinite; }
@keyframes fungalPulse { 0%,100% { box-shadow: 0 0 4px #a3e63530; } 50% { box-shadow: 0 0 12px #a3e63580; } }
@keyframes mycGrow { 0%,100% { opacity: 0.3; height: 16px; } 50% { opacity: 0.8; height: 24px; } }

/* ══ REPTILE — Scaly diamond ══ */
.comp-reptile .scale-core {
  width: 32px; height: 32px;
  background: linear-gradient(135deg, #84cc16, #4d7c0f);
  clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
  animation: reptilePulse 4s ease-in-out infinite;
}
.comp-reptile .scale-eye {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  width: 8px; height: 4px;
  background: #fbbf24;
  border-radius: 50%;
  animation: reptileEye 5s ease-in-out infinite;
}
@keyframes reptilePulse { 0%,100% { filter: brightness(1); } 50% { filter: brightness(1.3); } }
@keyframes reptileEye { 0%,90%,100% { height: 4px; } 92%,98% { height: 1px; } }

/* ══ JELLYFISH — Pulsing bell ══ */
.comp-jellyfish .bell {
  width: 34px; height: 22px;
  background: radial-gradient(ellipse at top, #c084fc80, #7c3aed40);
  border-radius: 50% 50% 10% 10%;
  border: 1.5px solid #c084fc60;
  animation: jellyPulse 2.5s ease-in-out infinite;
}
.comp-jellyfish .jelly-trail {
  position: absolute; width: 2px; background: linear-gradient(to bottom, #c084fc40, transparent);
  border-radius: 1px; top: 70%; transform-origin: top center;
}
.comp-jellyfish .jelly-trail:nth-child(2) { left: 35%; height: 16px; animation: jellyTrail 2.5s ease-in-out infinite; }
.comp-jellyfish .jelly-trail:nth-child(3) { left: 50%; height: 20px; animation: jellyTrail 2.5s ease-in-out 0.4s infinite; }
.comp-jellyfish .jelly-trail:nth-child(4) { left: 65%; height: 14px; animation: jellyTrail 2.5s ease-in-out 0.8s infinite; }
@keyframes jellyPulse { 0%,100% { transform: scaleX(1); } 40% { transform: scaleX(0.85) scaleY(1.1); } }
@keyframes jellyTrail { 0%,100% { opacity: 0.3; } 50% { opacity: 0.7; } }

/* ══ CAT — Slit-pupil eye ══ */
.comp-cat .cat-eye {
  width: 36px; height: 28px;
  background: radial-gradient(ellipse, #fbcfe8, #f9a8d4, #ec4899);
  border-radius: 50%;
  position: relative;
  animation: catWatch 4s ease-in-out infinite;
}
.comp-cat .cat-pupil {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  width: 4px; height: 18px;
  background: #1f2937;
  border-radius: 2px;
  animation: catPupil 4s ease-in-out infinite;
}
.comp-cat .cat-ear { position: absolute; top: -6px; width: 0; height: 0; border-left: 6px solid transparent; border-right: 6px solid transparent; border-bottom: 10px solid #f9a8d4; }
.comp-cat .cat-ear:nth-child(3) { left: 4px; }
.comp-cat .cat-ear:nth-child(4) { right: 4px; }
@keyframes catWatch { 0%,80%,100% { transform: scale(1); } 85%,95% { transform: scale(1.05); } }
@keyframes catPupil { 0%,100% { width: 4px; } 50% { width: 8px; } }

/* ══ DOG — Friendly nose/face ══ */
.comp-dog .dog-nose {
  width: 20px; height: 14px;
  background: #1f2937;
  border-radius: 50% 50% 40% 40%;
  animation: dogSniff 1.5s ease-in-out infinite;
}
.comp-dog .dog-eye { position: absolute; width: 8px; height: 8px; border-radius: 50%; background: #fdba74; top: 14px; }
.comp-dog .dog-eye:nth-child(2) { left: 14px; animation: dogBlink 4s ease-in-out infinite; }
.comp-dog .dog-eye:nth-child(3) { right: 14px; animation: dogBlink 4s ease-in-out 0.2s infinite; }
.comp-dog .dog-ear { position: absolute; width: 12px; height: 18px; background: #fdba7460; border-radius: 0 0 50% 50%; top: 4px; }
.comp-dog .dog-ear:nth-child(4) { left: 2px; transform: rotate(-10deg); }
.comp-dog .dog-ear:nth-child(5) { right: 2px; transform: rotate(10deg); }
.comp-dog .dog-tongue { position: absolute; bottom: 8px; left: 50%; transform: translateX(-50%); width: 6px; height: 8px; background: #f472b6; border-radius: 0 0 50% 50%; animation: dogPant 1s ease-in-out infinite; }
@keyframes dogSniff { 0%,100% { transform: scale(1); } 50% { transform: scale(1.1); } }
@keyframes dogBlink { 0%,90%,100% { height: 8px; } 92%,98% { height: 2px; } }
@keyframes dogPant { 0%,100% { height: 8px; } 50% { height: 12px; } }

@media (prefers-reduced-motion: reduce) {
  .companion *, .brain-node, .glow-orb, .grid-bg, .scan-overlay { animation: none !important; }
}
</style>
"""


COMPANION_HTML = {
    "human": """<div class="companion comp-human"><div class="hex-ring2"></div><div class="hex-ring"></div><div class="hex-core"></div></div>""",
    "octopus": """<div class="companion comp-octopus"><div class="blob-core"></div><div class="tendril"></div><div class="tendril"></div><div class="tendril"></div><div class="tendril"></div><div class="tendril"></div><div class="tendril"></div><div class="tendril"></div><div class="tendril"></div></div>""",
    "corvid": """<div class="companion comp-corvid"><div class="crystal-shard"></div><div class="crystal-shard"></div><div class="crystal-shard"></div><div class="crystal-core"></div></div>""",
    "dolphin": """<div class="companion comp-dolphin"><div class="wave-left"></div><div class="wave-bridge"></div><div class="wave-right"></div></div>""",
    "insect": """<div class="companion comp-insect"><div class="orb-learned"></div><div class="conn"></div><div class="orb-innate"></div></div>""",
    "alien": """<div class="companion comp-alien"><div class="tess-outer"></div><div class="tess-inner"></div><div class="tess-dot"></div></div>""",
    "ultimate": """<div class="companion comp-ultimate"><div class="morph-ring"></div><div class="morph-core"></div></div>""",
    "foundation_core": """<div class="companion comp-foundation_core"><div class="layer"></div><div class="layer"></div><div class="layer"></div></div>""",
    "neuromorphic": """<div class="companion comp-neuromorphic"><div class="n-dot"></div><div class="n-dot"></div><div class="n-dot"></div><div class="n-dot"></div><div class="n-line"></div><div class="n-line"></div></div>""",
    "fungal": """<div class="companion comp-fungal"><div class="myc-core"></div><div class="myc-thread"></div><div class="myc-thread"></div><div class="myc-thread"></div><div class="myc-thread"></div><div class="myc-thread"></div><div class="myc-thread"></div><div class="myc-node"></div><div class="myc-node"></div></div>""",
    "reptile": """<div class="companion comp-reptile"><div class="scale-core"></div><div class="scale-eye"></div></div>""",
    "jellyfish": """<div class="companion comp-jellyfish"><div class="bell"></div><div class="jelly-trail"></div><div class="jelly-trail"></div><div class="jelly-trail"></div></div>""",
    "cat": """<div class="companion comp-cat"><div class="cat-eye"><div class="cat-pupil"></div></div><div class="cat-ear"></div><div class="cat-ear"></div></div>""",
    "dog": """<div class="companion comp-dog"><div class="dog-nose"></div><div class="dog-eye"></div><div class="dog-eye"></div><div class="dog-ear"></div><div class="dog-ear"></div><div class="dog-tongue"></div></div>""",
}


def get_companion_html(brain_name: str) -> str:
    """Get the animated companion HTML for a brain."""
    return COMPANION_HTML.get(brain_name, "")


def get_companion_css() -> str:
    """Get all companion CSS (call once per page)."""
    return _companion_css()


# ════════════════════════════════════════════════════════════════
# LARGE ENTITY DISPLAY — state-reactive visual identity per brain
# ════════════════════════════════════════════════════════════════
#
# Each brain has a 200px entity whose animation speed, glow, and
# complexity react to training state. The entity is how the brain
# "chooses" to present itself — untrained brains are dim and slow,
# high-performing brains are vivid and complex.

_ENTITY_CSS = """
<style>
.entity-wrap {
  width: 200px; height: 200px;
  position: relative;
  margin: 0 auto;
}
.entity-wrap * { pointer-events: none; }

/* ── Human — layered cortical hex with orbiting rings ── */
.ent-human .e-hex-core {
  position: absolute; top: 50%; left: 50%;
  width: 80px; height: 80px;
  transform: translate(-50%, -50%);
  clip-path: polygon(50% 0%, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%);
  background: linear-gradient(135deg, #1d4ed8, #60a5fa, #93c5fd);
  animation: eHumanPulse var(--e-speed, 3s) ease-in-out infinite;
}
.ent-human .e-hex-ring {
  position: absolute; top: 50%; left: 50%;
  border: 2px solid #60a5fa50;
  clip-path: polygon(50% 0%, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%);
}
.ent-human .e-hex-ring.r1 { width: 110px; height: 110px; transform: translate(-50%, -50%); animation: eHumanSpin 12s linear infinite; }
.ent-human .e-hex-ring.r2 { width: 140px; height: 140px; transform: translate(-50%, -50%); animation: eHumanSpin 18s linear infinite reverse; border-color: #60a5fa30; }
.ent-human .e-hex-ring.r3 { width: 170px; height: 170px; transform: translate(-50%, -50%); animation: eHumanSpin 25s linear infinite; border-color: #60a5fa18; }
.ent-human .e-glow { position: absolute; inset: 0; border-radius: 50%; background: radial-gradient(circle, #60a5fa15 0%, transparent 70%); animation: eGlowPulse var(--e-speed, 3s) ease-in-out infinite; }
.ent-human .e-particle { position: absolute; width: 4px; height: 4px; border-radius: 50%; background: #60a5fa; }
.ent-human .e-particle:nth-child(5) { top: 20%; left: 30%; animation: eFloat 4s ease-in-out infinite; }
.ent-human .e-particle:nth-child(6) { top: 70%; left: 65%; animation: eFloat 5s ease-in-out 1s infinite; }
.ent-human .e-particle:nth-child(7) { top: 35%; left: 80%; animation: eFloat 3.5s ease-in-out 0.5s infinite; }
@keyframes eHumanPulse { 0%,100% { filter: brightness(var(--e-bright, 1)); } 50% { filter: brightness(calc(var(--e-bright, 1) * 1.4)); } }
@keyframes eHumanSpin { to { transform: translate(-50%, -50%) rotate(360deg); } }

/* ── Octopus — large blob with long waving tendrils ── */
.ent-octopus .e-blob {
  position: absolute; top: 50%; left: 50%;
  width: 70px; height: 70px;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #f9a8d4, #ec4899, #be185d);
  animation: eOctMorph var(--e-speed, 4s) ease-in-out infinite;
  box-shadow: 0 0 var(--e-glow-size, 20px) #ec489940;
}
.ent-octopus .e-tendril {
  position: absolute; top: 50%; left: 50%;
  width: 4px; height: 50px;
  background: linear-gradient(to bottom, #f472b6, transparent);
  border-radius: 2px;
  transform-origin: top center;
}
.ent-octopus .e-tendril:nth-child(2) { transform: rotate(0deg) translateY(28px); animation: eTentWave var(--e-speed, 3s) ease-in-out infinite; }
.ent-octopus .e-tendril:nth-child(3) { transform: rotate(45deg) translateY(28px); animation: eTentWave var(--e-speed, 3s) ease-in-out 0.375s infinite; }
.ent-octopus .e-tendril:nth-child(4) { transform: rotate(90deg) translateY(28px); animation: eTentWave var(--e-speed, 3s) ease-in-out 0.75s infinite; }
.ent-octopus .e-tendril:nth-child(5) { transform: rotate(135deg) translateY(28px); animation: eTentWave var(--e-speed, 3s) ease-in-out 1.125s infinite; }
.ent-octopus .e-tendril:nth-child(6) { transform: rotate(180deg) translateY(28px); animation: eTentWave var(--e-speed, 3s) ease-in-out 1.5s infinite; }
.ent-octopus .e-tendril:nth-child(7) { transform: rotate(225deg) translateY(28px); animation: eTentWave var(--e-speed, 3s) ease-in-out 1.875s infinite; }
.ent-octopus .e-tendril:nth-child(8) { transform: rotate(270deg) translateY(28px); animation: eTentWave var(--e-speed, 3s) ease-in-out 2.25s infinite; }
.ent-octopus .e-tendril:nth-child(9) { transform: rotate(315deg) translateY(28px); animation: eTentWave var(--e-speed, 3s) ease-in-out 2.625s infinite; }
.ent-octopus .e-glow { position: absolute; inset: 0; border-radius: 50%; background: radial-gradient(circle, #f472b615 0%, transparent 70%); animation: eGlowPulse var(--e-speed, 3s) ease-in-out infinite; }
@keyframes eOctMorph {
  0%,100% { border-radius: 50%; transform: translate(-50%, -50%) scale(1); }
  25% { border-radius: 60% 40% 55% 45%; transform: translate(-50%, -50%) scale(1.08); }
  50% { border-radius: 45% 55% 40% 60%; transform: translate(-50%, -50%) scale(0.92); }
  75% { border-radius: 55% 45% 60% 40%; transform: translate(-50%, -50%) scale(1.05); }
}
@keyframes eTentWave { 0%,100% { height: 50px; } 50% { height: 70px; } }

/* ── Corvid — large crystal with floating shards ── */
.ent-corvid .e-crystal {
  position: absolute; top: 50%; left: 50%;
  width: 70px; height: 70px;
  transform: translate(-50%, -50%);
  background: linear-gradient(135deg, #7c3aed, #a78bfa, #c4b5fd);
  clip-path: polygon(50% 0%, 100% 38%, 82% 100%, 18% 100%, 0% 38%);
  animation: eCrystalShimmer var(--e-speed, 3s) ease-in-out infinite;
  box-shadow: 0 0 var(--e-glow-size, 20px) #a78bfa30;
}
.ent-corvid .e-shard {
  position: absolute;
  width: 14px; height: 35px;
  background: linear-gradient(to bottom, #a78bfa50, transparent);
  clip-path: polygon(50% 0%, 100% 100%, 0% 100%);
}
.ent-corvid .e-shard:nth-child(2) { top: 5%; left: 50%; transform: translateX(-50%); animation: eShardOrbit 5s ease-in-out infinite; }
.ent-corvid .e-shard:nth-child(3) { top: 40%; right: 5%; transform: rotate(72deg); animation: eShardOrbit 5s ease-in-out 1s infinite; }
.ent-corvid .e-shard:nth-child(4) { bottom: 5%; right: 25%; transform: rotate(144deg); animation: eShardOrbit 5s ease-in-out 2s infinite; }
.ent-corvid .e-shard:nth-child(5) { bottom: 5%; left: 25%; transform: rotate(216deg); animation: eShardOrbit 5s ease-in-out 3s infinite; }
.ent-corvid .e-shard:nth-child(6) { top: 40%; left: 5%; transform: rotate(288deg); animation: eShardOrbit 5s ease-in-out 4s infinite; }
.ent-corvid .e-glow { position: absolute; inset: 0; border-radius: 50%; background: radial-gradient(circle, #a78bfa12 0%, transparent 70%); animation: eGlowPulse var(--e-speed, 3s) ease-in-out infinite; }
@keyframes eCrystalShimmer { 0%,100% { filter: brightness(var(--e-bright, 1)) hue-rotate(0deg); } 50% { filter: brightness(calc(var(--e-bright, 1) * 1.5)) hue-rotate(20deg); } }
@keyframes eShardOrbit { 0%,100% { opacity: 0.3; transform: translateY(0); } 50% { opacity: 0.8; transform: translateY(-8px); } }

/* ── Dolphin — two large hemispheres with pulsing bridge ── */
.ent-dolphin .e-hemi-l, .ent-dolphin .e-hemi-r {
  position: absolute; top: 50%;
  width: 60px; height: 60px;
  border-radius: 50%;
  transform: translateY(-50%);
}
.ent-dolphin .e-hemi-l { left: 25px; background: radial-gradient(circle, #22d3ee, #0891b2); animation: eDolphL var(--e-speed, 3s) ease-in-out infinite; }
.ent-dolphin .e-hemi-r { right: 25px; background: radial-gradient(circle, #0891b2, #164e63); animation: eDolphR var(--e-speed, 3s) ease-in-out infinite; }
.ent-dolphin .e-bridge {
  position: absolute; top: 50%; left: 50%;
  width: 50px; height: 6px;
  transform: translate(-50%, -50%);
  background: linear-gradient(90deg, #22d3ee, #06b6d4, #0891b2);
  border-radius: 3px;
  animation: eBridgePulse var(--e-speed, 3s) ease-in-out infinite;
  box-shadow: 0 0 12px #22d3ee40;
}
.ent-dolphin .e-wave {
  position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
  width: 140px; height: 30px;
  border: 2px solid #22d3ee20;
  border-radius: 50%;
  animation: eWaveRipple 4s ease-out infinite;
}
.ent-dolphin .e-glow { position: absolute; inset: 0; border-radius: 50%; background: radial-gradient(circle, #22d3ee10 0%, transparent 70%); animation: eGlowPulse var(--e-speed, 3s) ease-in-out infinite; }
@keyframes eDolphL { 0%,100% { transform: translateY(-50%) scale(1); opacity: 1; } 50% { transform: translateY(-50%) scale(0.75); opacity: 0.5; } }
@keyframes eDolphR { 0%,100% { transform: translateY(-50%) scale(0.75); opacity: 0.5; } 50% { transform: translateY(-50%) scale(1); opacity: 1; } }
@keyframes eBridgePulse { 0%,100% { opacity: 0.3; width: 50px; } 50% { opacity: 1; width: 60px; } }
@keyframes eWaveRipple { 0% { transform: translateX(-50%) scale(0.5); opacity: 0.5; } 100% { transform: translateX(-50%) scale(1.5); opacity: 0; } }

/* ── Insect — two large orbs with energy connection ── */
.ent-insect .e-orb-learned {
  position: absolute; top: 40px; left: 40px;
  width: 55px; height: 55px;
  border-radius: 50%;
  background: radial-gradient(circle, #fbbf24, #b45309);
  box-shadow: 0 0 var(--e-glow-size, 20px) #fbbf2440;
  animation: eInsectPulse var(--e-speed, 2s) ease-in-out infinite;
}
.ent-insect .e-orb-innate {
  position: absolute; bottom: 40px; right: 40px;
  width: 45px; height: 45px;
  border-radius: 50%;
  background: radial-gradient(circle, #f59e0b, #78350f);
  box-shadow: 0 0 var(--e-glow-size, 15px) #f59e0b40;
  animation: eInsectPulse var(--e-speed, 2s) ease-in-out 1s infinite;
}
.ent-insect .e-conn {
  position: absolute; top: 50%; left: 50%;
  width: 4px; height: 50px;
  transform: translate(-50%, -50%) rotate(45deg);
  background: linear-gradient(to bottom, #fbbf2480, #f59e0b80);
  border-radius: 2px;
  animation: eInsectConn var(--e-speed, 2s) ease-in-out infinite;
}
.ent-insect .e-spark { position: absolute; width: 3px; height: 3px; border-radius: 50%; background: #fbbf24; }
.ent-insect .e-spark:nth-child(4) { top: 25%; left: 60%; animation: eFloat 3s ease-in-out infinite; }
.ent-insect .e-spark:nth-child(5) { top: 65%; left: 35%; animation: eFloat 4s ease-in-out 1s infinite; }
.ent-insect .e-glow { position: absolute; inset: 0; border-radius: 50%; background: radial-gradient(circle, #fbbf2410 0%, transparent 70%); animation: eGlowPulse var(--e-speed, 2s) ease-in-out infinite; }
@keyframes eInsectPulse { 0%,100% { box-shadow: 0 0 var(--e-glow-size, 15px) #fbbf2430; transform: scale(1); } 50% { box-shadow: 0 0 calc(var(--e-glow-size, 15px) * 1.5) #fbbf2460; transform: scale(1.06); } }
@keyframes eInsectConn { 0%,100% { opacity: 0.3; } 50% { opacity: 0.9; } }

/* ── Alien — rotating tesseract with glowing center ── */
.ent-alien .e-tess-outer {
  position: absolute; top: 50%; left: 50%;
  width: 100px; height: 100px;
  transform: translate(-50%, -50%);
  border: 2px solid #34d39950;
  animation: eTessRot 6s linear infinite;
}
.ent-alien .e-tess-mid {
  position: absolute; top: 50%; left: 50%;
  width: 70px; height: 70px;
  transform: translate(-50%, -50%);
  border: 2px solid #34d39970;
  animation: eTessRot 6s linear infinite reverse;
}
.ent-alien .e-tess-inner {
  position: absolute; top: 50%; left: 50%;
  width: 40px; height: 40px;
  transform: translate(-50%, -50%);
  border: 2px solid #34d399;
  animation: eTessRot 4s linear infinite;
}
.ent-alien .e-tess-dot {
  position: absolute; top: 50%; left: 50%;
  width: 14px; height: 14px;
  margin: -7px 0 0 -7px;
  border-radius: 50%;
  background: #34d399;
  box-shadow: 0 0 var(--e-glow-size, 25px) #34d399;
  animation: eTessPulse var(--e-speed, 2s) ease-in-out infinite;
}
.ent-alien .e-glow { position: absolute; inset: 0; border-radius: 50%; background: radial-gradient(circle, #34d39915 0%, transparent 70%); animation: eGlowPulse var(--e-speed, 3s) ease-in-out infinite; }
@keyframes eTessRot { to { transform: translate(-50%, -50%) rotate(360deg); } }
@keyframes eTessPulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.6); } }

/* ── Ultimate — morphing ring cycling all species colors ── */
.ent-ultimate .e-morph-ring {
  position: absolute; top: 50%; left: 50%;
  width: 110px; height: 110px;
  transform: translate(-50%, -50%);
  border: 4px solid #f97316;
  border-radius: 50%;
  animation: eMorphShape 6s ease-in-out infinite, eMorphColor 8s linear infinite;
  box-shadow: 0 0 var(--e-glow-size, 20px) #f9731630;
}
.ent-ultimate .e-morph-core {
  position: absolute; top: 50%; left: 50%;
  width: 45px; height: 45px;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, #fb923c, #c2410c);
  border-radius: 50%;
  animation: eTessPulse var(--e-speed, 3s) ease-in-out infinite;
}
.ent-ultimate .e-morph-orbit {
  position: absolute; top: 50%; left: 50%;
  width: 150px; height: 150px;
  transform: translate(-50%, -50%);
  border: 1px solid #f9731620;
  border-radius: 50%;
  animation: eHumanSpin 20s linear infinite;
}
.ent-ultimate .e-morph-dot {
  position: absolute; width: 6px; height: 6px; border-radius: 50%;
  top: -3px; left: 50%; margin-left: -3px;
  background: #fb923c;
  box-shadow: 0 0 8px #fb923c;
}
.ent-ultimate .e-glow { position: absolute; inset: 0; border-radius: 50%; background: radial-gradient(circle, #f9731610 0%, transparent 70%); animation: eGlowPulse var(--e-speed, 3s) ease-in-out infinite; }
@keyframes eMorphShape {
  0%,100% { border-radius: 50%; }
  16% { border-radius: 30% 70% 70% 30%; }
  33% { clip-path: polygon(50% 0%, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%); border-radius: 0; }
  50% { clip-path: polygon(50% 0%, 100% 38%, 82% 100%, 18% 100%, 0% 38%); }
  66% { clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%); }
  83% { clip-path: none; border-radius: 20%; }
}
@keyframes eMorphColor {
  0% { border-color: #f97316; box-shadow: 0 0 20px #f9731630; }
  14% { border-color: #60a5fa; box-shadow: 0 0 20px #60a5fa30; }
  28% { border-color: #f472b6; box-shadow: 0 0 20px #f472b630; }
  42% { border-color: #a78bfa; box-shadow: 0 0 20px #a78bfa30; }
  57% { border-color: #22d3ee; box-shadow: 0 0 20px #22d3ee30; }
  71% { border-color: #fbbf24; box-shadow: 0 0 20px #fbbf2430; }
  85% { border-color: #34d399; box-shadow: 0 0 20px #34d39930; }
  100% { border-color: #f97316; box-shadow: 0 0 20px #f9731630; }
}

/* ── Foundation Core — deep stacked liquid layers ── */
.ent-foundation_core .e-layer {
  position: absolute; left: 50%; transform: translateX(-50%);
  height: 20px; border-radius: 10px;
  background: linear-gradient(90deg, #818cf830, #818cf8, #818cf830);
}
.ent-foundation_core .e-layer:nth-child(1) { width: 100px; top: 40px; animation: eLayerPulse 3s ease-in-out infinite; }
.ent-foundation_core .e-layer:nth-child(2) { width: 80px; top: 70px; animation: eLayerPulse 3s ease-in-out 0.5s infinite; }
.ent-foundation_core .e-layer:nth-child(3) { width: 60px; top: 100px; animation: eLayerPulse 3s ease-in-out 1s infinite; }
.ent-foundation_core .e-layer:nth-child(4) { width: 40px; top: 130px; animation: eLayerPulse 3s ease-in-out 1.5s infinite; }
.ent-foundation_core .e-glow { position: absolute; inset: 0; border-radius: 50%; background: radial-gradient(circle, #818cf810 0%, transparent 70%); animation: eGlowPulse 3s ease-in-out infinite; }
@keyframes eLayerPulse { 0%,100% { opacity: 0.5; transform: translateX(-50%) scaleX(1); } 50% { opacity: 1; transform: translateX(-50%) scaleX(1.1); } }

/* ── Neuromorphic — 4 large pulsing nodes with connections ── */
.ent-neuromorphic .e-node {
  position: absolute; width: 24px; height: 24px;
  border-radius: 50%; background: #fb923c;
  box-shadow: 0 0 var(--e-glow-size, 12px) #fb923c60;
}
.ent-neuromorphic .e-node:nth-child(1) { top: 30px; left: 50%; transform: translateX(-50%); animation: eNPulse 2s ease-in-out infinite; }
.ent-neuromorphic .e-node:nth-child(2) { bottom: 30px; left: 30px; animation: eNPulse 2s ease-in-out 0.5s infinite; }
.ent-neuromorphic .e-node:nth-child(3) { bottom: 30px; right: 30px; animation: eNPulse 2s ease-in-out 1s infinite; }
.ent-neuromorphic .e-node:nth-child(4) { top: 90px; left: 50%; transform: translateX(-50%); animation: eNPulse 2s ease-in-out 1.5s infinite; }
.ent-neuromorphic .e-link {
  position: absolute; height: 2px; background: #fb923c40;
  top: 50%; left: 50%; width: 60px; transform-origin: left center;
}
.ent-neuromorphic .e-link:nth-child(5) { transform: translate(-50%, 0) rotate(-35deg); }
.ent-neuromorphic .e-link:nth-child(6) { transform: translate(-50%, 0) rotate(35deg); }
.ent-neuromorphic .e-link:nth-child(7) { transform: translate(-50%, 0) rotate(0deg); width: 40px; }
.ent-neuromorphic .e-glow { position: absolute; inset: 0; border-radius: 50%; background: radial-gradient(circle, #fb923c10 0%, transparent 70%); animation: eGlowPulse 3s ease-in-out infinite; }
@keyframes eNPulse { 0%,100% { box-shadow: 0 0 8px #fb923c40; transform: scale(1); } 50% { box-shadow: 0 0 20px #fb923c; transform: scale(1.1); } }

/* ── Fungal entity — spreading mycelium web ── */
.ent-fungal .e-myc-center { position: absolute; top: 50%; left: 50%; width: 30px; height: 30px; transform: translate(-50%,-50%); border-radius: 50%; background: radial-gradient(circle, #a3e635, #4d7c0f); animation: eGlowPulse var(--e-speed, 4s) ease-in-out infinite; box-shadow: 0 0 var(--e-glow-size, 15px) #a3e63540; }
.ent-fungal .e-hypha { position: absolute; top: 50%; left: 50%; width: 3px; background: linear-gradient(to bottom, #a3e63560, transparent); border-radius: 2px; transform-origin: top center; }
.ent-fungal .e-hypha:nth-child(2) { height: 60px; transform: rotate(0deg) translateY(12px); animation: eMycGrow var(--e-speed, 5s) ease-in-out infinite; }
.ent-fungal .e-hypha:nth-child(3) { height: 55px; transform: rotate(45deg) translateY(12px); animation: eMycGrow var(--e-speed, 5s) ease-in-out 0.6s infinite; }
.ent-fungal .e-hypha:nth-child(4) { height: 65px; transform: rotate(90deg) translateY(12px); animation: eMycGrow var(--e-speed, 5s) ease-in-out 1.2s infinite; }
.ent-fungal .e-hypha:nth-child(5) { height: 50px; transform: rotate(135deg) translateY(12px); animation: eMycGrow var(--e-speed, 5s) ease-in-out 1.8s infinite; }
.ent-fungal .e-hypha:nth-child(6) { height: 58px; transform: rotate(180deg) translateY(12px); animation: eMycGrow var(--e-speed, 5s) ease-in-out 2.4s infinite; }
.ent-fungal .e-hypha:nth-child(7) { height: 62px; transform: rotate(225deg) translateY(12px); animation: eMycGrow var(--e-speed, 5s) ease-in-out 3s infinite; }
.ent-fungal .e-hypha:nth-child(8) { height: 48px; transform: rotate(270deg) translateY(12px); animation: eMycGrow var(--e-speed, 5s) ease-in-out 3.6s infinite; }
.ent-fungal .e-hypha:nth-child(9) { height: 56px; transform: rotate(315deg) translateY(12px); animation: eMycGrow var(--e-speed, 5s) ease-in-out 4.2s infinite; }
.ent-fungal .e-spore { position: absolute; width: 8px; height: 8px; border-radius: 50%; background: #a3e635; box-shadow: 0 0 8px #a3e63560; }
.ent-fungal .e-spore:nth-child(10) { top: 15%; left: 50%; animation: eFloat 3s ease-in-out infinite; }
.ent-fungal .e-spore:nth-child(11) { top: 70%; left: 25%; animation: eFloat 4s ease-in-out 1s infinite; }
.ent-fungal .e-spore:nth-child(12) { top: 40%; left: 80%; animation: eFloat 3.5s ease-in-out 2s infinite; }
.ent-fungal .e-glow { position: absolute; inset: 0; border-radius: 50%; background: radial-gradient(circle, #a3e63512 0%, transparent 70%); animation: eGlowPulse var(--e-speed, 4s) ease-in-out infinite; }
@keyframes eMycGrow { 0%,100% { opacity: 0.3; } 50% { opacity: 0.8; } }

/* ── Reptile entity — diamond with slit eye ── */
.ent-reptile .e-diamond { position: absolute; top: 50%; left: 50%; width: 80px; height: 80px; transform: translate(-50%,-50%) rotate(45deg); background: linear-gradient(135deg, #84cc16, #4d7c0f, #365314); animation: eReptPulse var(--e-speed, 4s) ease-in-out infinite; box-shadow: 0 0 var(--e-glow-size, 15px) #84cc1630; }
.ent-reptile .e-eye { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); width: 30px; height: 20px; background: #fbbf24; border-radius: 50%; }
.ent-reptile .e-slit { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); width: 6px; height: 16px; background: #1f2937; border-radius: 3px; animation: eReptSlit var(--e-speed, 5s) ease-in-out infinite; }
.ent-reptile .e-scale { position: absolute; width: 20px; height: 20px; border: 1px solid #84cc1620; transform: rotate(45deg); }
.ent-reptile .e-scale:nth-child(4) { top: 20px; left: 40px; animation: eFloat 4s ease-in-out infinite; }
.ent-reptile .e-scale:nth-child(5) { top: 140px; left: 120px; animation: eFloat 5s ease-in-out 1s infinite; }
.ent-reptile .e-scale:nth-child(6) { top: 50px; left: 140px; animation: eFloat 3s ease-in-out 2s infinite; }
.ent-reptile .e-glow { position: absolute; inset: 0; border-radius: 50%; background: radial-gradient(circle, #84cc1610 0%, transparent 70%); animation: eGlowPulse var(--e-speed, 4s) ease-in-out infinite; }
@keyframes eReptPulse { 0%,100% { filter: brightness(var(--e-bright, 1)); } 50% { filter: brightness(calc(var(--e-bright, 1) * 1.3)); } }
@keyframes eReptSlit { 0%,100% { width: 6px; } 50% { width: 12px; } }

/* ── Jellyfish entity — translucent pulsing bell ── */
.ent-jellyfish .e-bell { position: absolute; top: 30px; left: 50%; transform: translateX(-50%); width: 100px; height: 65px; background: radial-gradient(ellipse at top, #c084fc50, #7c3aed30, transparent); border: 2px solid #c084fc40; border-radius: 50% 50% 15% 15%; animation: eJellyPulse var(--e-speed, 2.5s) ease-in-out infinite; box-shadow: 0 0 var(--e-glow-size, 15px) #c084fc20; }
.ent-jellyfish .e-tent { position: absolute; top: 88px; width: 2px; background: linear-gradient(to bottom, #c084fc40, transparent); border-radius: 1px; }
.ent-jellyfish .e-tent:nth-child(2) { left: 55px; height: 50px; animation: eJellyTrail var(--e-speed, 2.5s) ease-in-out infinite; }
.ent-jellyfish .e-tent:nth-child(3) { left: 75px; height: 60px; animation: eJellyTrail var(--e-speed, 2.5s) ease-in-out 0.3s infinite; }
.ent-jellyfish .e-tent:nth-child(4) { left: 95px; height: 45px; animation: eJellyTrail var(--e-speed, 2.5s) ease-in-out 0.6s infinite; }
.ent-jellyfish .e-tent:nth-child(5) { left: 115px; height: 55px; animation: eJellyTrail var(--e-speed, 2.5s) ease-in-out 0.9s infinite; }
.ent-jellyfish .e-tent:nth-child(6) { left: 135px; height: 40px; animation: eJellyTrail var(--e-speed, 2.5s) ease-in-out 1.2s infinite; }
.ent-jellyfish .e-rhop { position: absolute; top: 30px; width: 6px; height: 6px; border-radius: 50%; background: #e9d5ff; box-shadow: 0 0 6px #c084fc; }
.ent-jellyfish .e-rhop:nth-child(7) { left: 55px; animation: eGlowPulse 2s ease-in-out infinite; }
.ent-jellyfish .e-rhop:nth-child(8) { left: 95px; animation: eGlowPulse 2s ease-in-out 0.7s infinite; }
.ent-jellyfish .e-rhop:nth-child(9) { left: 135px; animation: eGlowPulse 2s ease-in-out 1.4s infinite; }
.ent-jellyfish .e-glow { position: absolute; inset: 0; border-radius: 50%; background: radial-gradient(circle, #c084fc10 0%, transparent 70%); animation: eGlowPulse var(--e-speed, 3s) ease-in-out infinite; }
@keyframes eJellyPulse { 0%,100% { transform: translateX(-50%) scaleX(1); } 40% { transform: translateX(-50%) scaleX(0.85) scaleY(1.1); } }
@keyframes eJellyTrail { 0%,100% { opacity: 0.3; } 50% { opacity: 0.7; } }

/* ── Cat entity — large predatory eye ── */
.ent-cat .e-cat-eye { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); width: 90px; height: 70px; background: radial-gradient(ellipse, #fbcfe8, #f9a8d4, #ec4899); border-radius: 50%; box-shadow: 0 0 var(--e-glow-size, 20px) #f9a8d430; animation: eCatWatch var(--e-speed, 4s) ease-in-out infinite; }
.ent-cat .e-cat-pupil { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); width: 8px; height: 45px; background: #1f2937; border-radius: 4px; animation: eCatPupil var(--e-speed, 4s) ease-in-out infinite; }
.ent-cat .e-cat-ear { position: absolute; width: 0; height: 0; border-left: 16px solid transparent; border-right: 16px solid transparent; border-bottom: 28px solid #f9a8d480; }
.ent-cat .e-cat-ear:nth-child(3) { top: 16px; left: 30px; }
.ent-cat .e-cat-ear:nth-child(4) { top: 16px; right: 30px; }
.ent-cat .e-whisker { position: absolute; height: 1px; background: #f9a8d460; }
.ent-cat .e-whisker:nth-child(5) { top: 48%; left: 10px; width: 30px; transform: rotate(-5deg); }
.ent-cat .e-whisker:nth-child(6) { top: 52%; left: 10px; width: 28px; transform: rotate(5deg); }
.ent-cat .e-whisker:nth-child(7) { top: 48%; right: 10px; width: 30px; transform: rotate(5deg); }
.ent-cat .e-whisker:nth-child(8) { top: 52%; right: 10px; width: 28px; transform: rotate(-5deg); }
.ent-cat .e-glow { position: absolute; inset: 0; border-radius: 50%; background: radial-gradient(circle, #f9a8d412 0%, transparent 70%); animation: eGlowPulse var(--e-speed, 3s) ease-in-out infinite; }
@keyframes eCatWatch { 0%,80%,100% { transform: translate(-50%,-50%) scale(1); } 85%,95% { transform: translate(-50%,-50%) scale(1.05); } }
@keyframes eCatPupil { 0%,100% { width: 8px; } 50% { width: 16px; } }

/* ── Dog entity — friendly face with big nose ── */
.ent-dog .e-dog-nose { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); width: 45px; height: 32px; background: #292524; border-radius: 50% 50% 40% 40%; animation: eDogSniff var(--e-speed, 1.5s) ease-in-out infinite; box-shadow: 0 0 var(--e-glow-size, 12px) #fdba7430; }
.ent-dog .e-dog-eye { position: absolute; width: 18px; height: 18px; border-radius: 50%; background: radial-gradient(circle, #fef3c7, #fdba74); top: 55px; }
.ent-dog .e-dog-eye:nth-child(2) { left: 45px; animation: eDogBlink 4s ease-in-out infinite; }
.ent-dog .e-dog-eye:nth-child(3) { right: 45px; animation: eDogBlink 4s ease-in-out 0.2s infinite; }
.ent-dog .e-dog-ear { position: absolute; width: 28px; height: 45px; background: #fdba7440; border-radius: 0 0 50% 50%; top: 30px; }
.ent-dog .e-dog-ear:nth-child(4) { left: 20px; transform: rotate(-10deg); animation: eDogEar 3s ease-in-out infinite; }
.ent-dog .e-dog-ear:nth-child(5) { right: 20px; transform: rotate(10deg); animation: eDogEar 3s ease-in-out 0.5s infinite; }
.ent-dog .e-dog-tongue { position: absolute; bottom: 40px; left: 50%; transform: translateX(-50%); width: 14px; height: 20px; background: #f472b6; border-radius: 0 0 50% 50%; animation: eDogPant var(--e-speed, 1s) ease-in-out infinite; }
.ent-dog .e-glow { position: absolute; inset: 0; border-radius: 50%; background: radial-gradient(circle, #fdba7410 0%, transparent 70%); animation: eGlowPulse var(--e-speed, 3s) ease-in-out infinite; }
@keyframes eDogSniff { 0%,100% { transform: translate(-50%,-50%) scale(1); } 50% { transform: translate(-50%,-50%) scale(1.1); } }
@keyframes eDogBlink { 0%,90%,100% { height: 18px; } 92%,98% { height: 4px; } }
@keyframes eDogEar { 0%,100% { transform: rotate(var(--ear-rot, -10deg)); } 50% { transform: rotate(calc(var(--ear-rot, -10deg) + 5deg)); } }
@keyframes eDogPant { 0%,100% { height: 20px; } 50% { height: 28px; } }

/* ── Shared ── */
@keyframes eGlowPulse { 0%,100% { opacity: 0.5; } 50% { opacity: 1; } }
@keyframes eFloat { 0%,100% { transform: translateY(0); opacity: 0.4; } 50% { transform: translateY(-6px); opacity: 0.9; } }

@media (prefers-reduced-motion: reduce) { .entity-wrap * { animation: none !important; } }
</style>
"""

ENTITY_HTML = {
    "human": """<div class="entity-wrap ent-human" style="{style}">
        <div class="e-glow"></div>
        <div class="e-hex-ring r3"></div>
        <div class="e-hex-ring r2"></div>
        <div class="e-hex-ring r1"></div>
        <div class="e-hex-core"></div>
        <div class="e-particle"></div><div class="e-particle"></div><div class="e-particle"></div>
    </div>""",
    "octopus": """<div class="entity-wrap ent-octopus" style="{style}">
        <div class="e-glow"></div>
        <div class="e-blob"></div>
        <div class="e-tendril"></div><div class="e-tendril"></div><div class="e-tendril"></div><div class="e-tendril"></div>
        <div class="e-tendril"></div><div class="e-tendril"></div><div class="e-tendril"></div><div class="e-tendril"></div>
    </div>""",
    "corvid": """<div class="entity-wrap ent-corvid" style="{style}">
        <div class="e-glow"></div>
        <div class="e-crystal"></div>
        <div class="e-shard"></div><div class="e-shard"></div><div class="e-shard"></div><div class="e-shard"></div><div class="e-shard"></div>
    </div>""",
    "dolphin": """<div class="entity-wrap ent-dolphin" style="{style}">
        <div class="e-glow"></div>
        <div class="e-hemi-l"></div>
        <div class="e-bridge"></div>
        <div class="e-hemi-r"></div>
        <div class="e-wave"></div>
    </div>""",
    "insect": """<div class="entity-wrap ent-insect" style="{style}">
        <div class="e-glow"></div>
        <div class="e-orb-learned"></div>
        <div class="e-conn"></div>
        <div class="e-orb-innate"></div>
        <div class="e-spark"></div><div class="e-spark"></div>
    </div>""",
    "alien": """<div class="entity-wrap ent-alien" style="{style}">
        <div class="e-glow"></div>
        <div class="e-tess-outer"></div>
        <div class="e-tess-mid"></div>
        <div class="e-tess-inner"></div>
        <div class="e-tess-dot"></div>
    </div>""",
    "ultimate": """<div class="entity-wrap ent-ultimate" style="{style}">
        <div class="e-glow"></div>
        <div class="e-morph-orbit"><div class="e-morph-dot"></div></div>
        <div class="e-morph-ring"></div>
        <div class="e-morph-core"></div>
    </div>""",
    "foundation_core": """<div class="entity-wrap ent-foundation_core" style="{style}">
        <div class="e-glow"></div>
        <div class="e-layer"></div><div class="e-layer"></div><div class="e-layer"></div><div class="e-layer"></div>
    </div>""",
    "neuromorphic": """<div class="entity-wrap ent-neuromorphic" style="{style}">
        <div class="e-glow"></div>
        <div class="e-node"></div><div class="e-node"></div><div class="e-node"></div><div class="e-node"></div>
        <div class="e-link"></div><div class="e-link"></div><div class="e-link"></div>
    </div>""",
    "fungal": """<div class="entity-wrap ent-fungal" style="{style}">
        <div class="e-glow"></div>
        <div class="e-myc-center"></div>
        <div class="e-hypha"></div><div class="e-hypha"></div><div class="e-hypha"></div><div class="e-hypha"></div>
        <div class="e-hypha"></div><div class="e-hypha"></div><div class="e-hypha"></div><div class="e-hypha"></div>
        <div class="e-spore"></div><div class="e-spore"></div><div class="e-spore"></div>
    </div>""",
    "reptile": """<div class="entity-wrap ent-reptile" style="{style}">
        <div class="e-glow"></div>
        <div class="e-diamond"></div>
        <div class="e-eye"><div class="e-slit"></div></div>
        <div class="e-scale"></div><div class="e-scale"></div><div class="e-scale"></div>
    </div>""",
    "jellyfish": """<div class="entity-wrap ent-jellyfish" style="{style}">
        <div class="e-glow"></div>
        <div class="e-bell"></div>
        <div class="e-tent"></div><div class="e-tent"></div><div class="e-tent"></div><div class="e-tent"></div><div class="e-tent"></div>
        <div class="e-rhop"></div><div class="e-rhop"></div><div class="e-rhop"></div>
    </div>""",
    "cat": """<div class="entity-wrap ent-cat" style="{style}">
        <div class="e-glow"></div>
        <div class="e-cat-eye"><div class="e-cat-pupil"></div></div>
        <div class="e-cat-ear"></div><div class="e-cat-ear"></div>
        <div class="e-whisker"></div><div class="e-whisker"></div><div class="e-whisker"></div><div class="e-whisker"></div>
    </div>""",
    "dog": """<div class="entity-wrap ent-dog" style="{style}">
        <div class="e-glow"></div>
        <div class="e-dog-nose"></div>
        <div class="e-dog-eye"></div><div class="e-dog-eye"></div>
        <div class="e-dog-ear"></div><div class="e-dog-ear"></div>
        <div class="e-dog-tongue"></div>
    </div>""",
}


def get_entity_css() -> str:
    """Return all large entity CSS (call once per page)."""
    return _ENTITY_CSS


def get_entity_html(brain_name: str, loss: float | None = None) -> str:
    """
    Get large entity HTML for a brain, styled by training state.

    The entity 'decides' how to present itself based on performance:
      - Untrained: dim, slow animations, small glow
      - Learning:  moderate brightness, medium speed
      - Strong:    bright, fast, large glow
      - Optimal:   vivid, rapid, intense glow
    """
    template = ENTITY_HTML.get(brain_name, "")
    if not template:
        return ""

    # Derive visual properties from loss
    if loss is None or loss > 0.5:
        speed, bright, glow = "5s", "0.6", "10px"
    elif loss > 0.15:
        speed, bright, glow = "3.5s", "0.8", "18px"
    elif loss > 0.05:
        speed, bright, glow = "2.5s", "1.0", "28px"
    else:
        speed, bright, glow = "1.5s", "1.3", "40px"

    style = f"--e-speed:{speed}; --e-bright:{bright}; --e-glow-size:{glow};"
    return template.format(style=style)
