# 🔷 Foundation Lab

**A research workbench for comparing 12 biologically-inspired liquid neural network architectures.**

Foundation Lab lets you train, compare, ensemble, evolve, and query brains based on different evolutionary solutions to intelligence — from jellyfish nerve nets to hand-designed chimeras combining the best features of every species.

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/MonongahelaHellbender/Autonomous-Scientist-Core.git
cd Autonomous-Scientist-Core

# 2. Install
python3 -m venv scientist-env
source scientist-env/bin/activate
pip install streamlit torch numpy plotly

# 3. Launch
streamlit run foundation_lab.py --server.port 8570
```

Open `http://localhost:8570`.

On macOS, the included `Foundation Lab.app` (in `~/Desktop/`) is a one-click launcher.

---

## The 12 brains

Each brain is a different bet on what makes intelligence work. They all share the same liquid time-constant cell as a substrate but wire it up completely differently.

| Brain | Inspiration | Unique trick |
|---|---|---|
| 🪼 **Jellyfish** | 600 MYA, no brain | Diffuse nerve net, ring topology, no central decision-maker |
| 🍄 **Fungal** | 1.5 BYA, no neurons | Mycelium network, learned chemical diffusion matrix, distributed pooling |
| 🐝 **Insect** | 400 MYA, 960K neurons | Dual-track: learned mushroom body + innate lateral horn (innate inhibits learned) |
| 🦎 **Reptile** | 320 MYA, 10M neurons | Brainstem-dominant, learned metabolic rate modulates all dt, spinal reflex bypass |
| 🐙 **Octopus** | 300 MYA, 500M neurons | 8 semi-autonomous arm ganglia, distributed processing |
| 🐦‍⬛ **Corvid** | 150 MYA, 1.2B neurons | Dense flat nuclear clusters, no cortex, lateral connections |
| 🐬 **Dolphin** | 50 MYA, 12B neurons | Hemispheric switching (one half sleeps), paralimbic lobe |
| 🐱 **Cat** | 10 MYA, 760M neurons | Visual-cortex-dominant, huge whisker barrel cortex, predatory amygdala→visual gate |
| 🐕 **Dog** | 15K YA, 530M neurons | Olfactory-bulb-dominant, social cortex, social→reward link |
| 🧠 **Human** | 2 MYA, 86B neurons | Full cortical hierarchy, hemispheres, prefrontal planning |
| 👽 **Alien** | — | No biological constraints: 8 fully-connected adaptive regions, learned routing, learned dt |
| ⚡ **Ultimate** | Now | Hand-designed chimera combining the best feature from every species |

Plus two reference architectures: **Foundation Core** (deep liquid baseline) and **Neuromorphic** (4-region prototype).

---

## What you can do

### 🏠 Overview
Visual gallery — see each brain's animated identity. Each entity reacts to its training state (untrained = dim/slow, optimal = bright/fast).

### ⚡ Train
Pick **All Brains** or specific ones. Settings expander for hyperparameters. During training:
- **Left**: live network topology diagram showing every region as a node, lighting up by activity
- **Right**: the brain's animated entity reacting to current loss

### 📊 Compare
After training 2+ brains, see convergence analysis. Do different architectures discover the same structure? If they converge, the structure is necessary. If they diverge, wiring matters.

### 🔗 Ensemble
Train a meta-router that learns which brain to trust on which input. "Group think" — sometimes the ensemble beats every individual brain.

### 🧬 Evolve
View brains arranged by evolutionary timeline. Each card shows performance + animated entity.

### 💬 Query
- **Ask All Trained Brains**: feed text/numbers/generated signal, see how each predicts and where it's surprised
- **Ask Specific Brain**: drill into one brain's response

Get region activity heatmaps showing which parts of each brain activate.

### 🪞 Presence
The lab itself decides how to visually present its current state based on internal model metrics.

### 🔧 Self-Improve
Pick a brain. It diagnoses its weaknesses, mutates its time constants, retrains on hard patterns, keeps the fittest version. Evolution at the neuron level.

---

## Architecture interface

Every brain follows the same contract so they're interchangeable:

```python
class MyBrain(nn.Module):
    def __init__(self, input_size=1, hidden_size=128, n_properties=2, dropout=0.1, dt=1.0): ...

    def forward(self, x, **kwargs) -> dict:
        # x: [B, T, input_size]
        return {
            "predictions":   ...,  # [B, T-1, input_size]
            "hidden":        ...,  # [B, T, hidden_size]
            "anomaly_score": ...,  # [B, T]
            "surprise":      ...,  # [B, T-1]
            "properties":    ...,  # [B, n_properties]
            "region_traces": {region_name: [B, T, region_size]},
        }

    def param_count(self) -> dict: ...
```

This means you can swap any brain into the ensemble or self-improver without changing other code.

---

## Adding your own brain

1. Create `models/brains/your_brain.py` — copy `insect_brain.py` as a template
2. Implement the interface above
3. Register in `models/brains/__init__.py`:
   ```python
   from models.brains.your_brain import YourBrain
   ALL_BRAINS["your_name"] = YourBrain
   ```
4. Add visuals in `models/brains/companions.py` (small companion + large entity CSS/HTML)
5. Add metadata in `foundation_lab.py`:
   - `BRAIN_META["your_name"] = {"icon": ..., "color": ..., "era": ..., "neurons": ..., "tag": ...}`
   - `BRAIN_TOPOLOGY["your_name"] = [(region_a, region_b), ...]`
   - Position in 3D `positions` dict on the Overview page
6. Restart — your brain shows up everywhere automatically

---

## File map

```
foundation_lab.py              # Main Streamlit app
models/
  liquid_core.py               # The LiquidCell — shared substrate
  brains/
    __init__.py                # ALL_BRAINS registry
    companions.py              # All visual entities (CSS-only)
    ensemble.py                # BrainEnsemble meta-controller
    self_improve.py            # Evolutionary mutation + focused training
    {human,octopus,corvid,dolphin,insect,alien,ultimate,
     fungal,reptile,jellyfish,cat,dog}_brain.py
training/
  train_brain.py               # Signal generators + batch generator
outputs/brain_zoo/             # Saved checkpoints + results.json (gitignored)
```

---

## Contributing

If you build a new brain or improve an existing one:
1. Fork
2. Add your brain
3. Run training and include before/after loss numbers in your PR
4. Open a PR

If you discover a topology that dramatically outperforms others, document the finding before publishing — but the code itself stays open.

---

## License

MIT. Use freely. Attribution appreciated.
