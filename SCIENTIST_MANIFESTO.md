# The Autonomous Research Framework (UIL-v1.0)
## A Modular Template for Universal Scientific Discovery

This repository is structured as a "Self-Driving Lab." It can be adapted to any scientific field by replacing the target elements and validation heuristics.

### 1. The Core Loop Architecture
To build your own scientist, you need four distinct modules:

1. **The Ingestion Layer (`discovery_module.py`):** - *Current:* Queries Materials Project API for crystal structures.
   - *Universal:* Connects to any ground-truth source (Genome databases, telescope feeds, economic tickers).

2. **The Intelligence Layer (`evolution_module.py`):**
   - *Current:* Uses UIL Geometric Likelihood to find high-volume manifolds.
   - *Universal:* The AI that identifies "Invariants" (patterns) in your data and suggests new configurations.

3. **The Simulation Layer (`physics_validator.py`):**
   - *Current:* Calculates Voronoi Bottlenecks and Thermal Phase Boundaries.
   - *Universal:* The "Reality Check." Can be a fluid dynamics sim, a protein folder, or a market crash simulator.

4. **The Viability Layer (`market_economics.py`):**
   - *Current:* Calculates Cost-per-Kilogram of the discovery.
   - *Universal:* Filters discoveries based on real-world constraints (Toxicity, Budget, Ethics, Time).

### 2. How to Start a New Project
1. **Define the Manifold:** Write your goals in `config.json`.
2. **Setup the Sieve:** Adjust your "Pass/Fail" thresholds in the validation scripts.
3. **Execute the Loop:** Let the AI query, hypothesize, and validate until it logs a "BREAKTHROUGH" in the results file.

---
*Created by the MonongahelaHellbender Lab*

## v1.2 Update: Adversarial Validation
Every discovery cycle now includes a 'Devil’s Advocate' script to penalize moisture sensitivity and kinetic bottlenecks. This ensures only 'Industrial-Grade' manifolds are prioritized.
