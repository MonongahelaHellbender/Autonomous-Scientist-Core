# Next AI Scientist Actions

## Purpose

This file ranks the next AI-scientist jobs in `Autonomous-Scientist-Core`
according to current source support, cleanup value, and likely scientific yield.

## Ranked Next Actions

### Completed - Carbon Capture - Abundance-Safe Subset v1

What it is:

- isolate and save a maintained abundance-safe subset from the hardened retained
  carbon lane

Why it matters:

- this moved the carbon lane from a note-level abundance concern to a
  maintained artifact

Current sources:

- `carbon_capture/abundance_safe_subset_v1.json`
- `carbon_capture/stress_artifacts/abundance_safe_subset_v1_property_conditioned_stress_bundle_top_25_seed_20260429.json`
- `internal/patent_prep/CALCIUM_CAGE_BASELINE_INTEGRITY.md`

Current result:

- completed as a maintained heuristic abundance screen
- still not a full planetary resource model

### Completed - Carbon Capture - Composition-Sensitive Stress Model

What it is:

- replace the current generic or property-conditioned thermal proxy with a
  stronger composition-sensitive model based on parsed formula chemistry

Why it matters:

- this upgrades the stress lane from element-count conditioning to parsed
  stoichiometry, chemistry-family fractions, and composition-derived
  descriptors

Current sources:

- `carbon_capture/composition_sensitive_stress_proxy.py`
- `carbon_capture/generate_composition_sensitive_stress_artifact.py`
- `carbon_capture/generate_composition_sensitive_stress_bundle.py`
- `carbon_capture/audit_composition_sensitive_stress_model.py`
- `carbon_capture/stress_artifacts/ca3si_clo2_2_composition_sensitive_stress_artifact_seed_20260429.json`
- `carbon_capture/stress_artifacts/ca3si_clo2_2_composition_sensitive_stress_audit_2000_seeds_0_to_1999.json`
- `carbon_capture/stress_artifacts/abundance_safe_subset_v1_composition_sensitive_stress_bundle_top_25_seed_20260429.json`

Current result:

- completed as a replayable composition-sensitive proxy model
- `Ca3Si(ClO2)2` now has both a saved deterministic artifact and a `2000`-seed
  audit under the upgraded proxy
- the top abundance-safe bundle no longer tracks pore ranking alone:
  oxide-rich silicates rise while chloride- and alkali-bearing candidates are
  penalized
- still remains proxy work rather than first-principles thermal physics

### Completed - Carbon Capture - CO2 Uptake / Adsorption Proxy

What it is:

- add a semi-physical CO2 uptake proxy so the claim lane can move beyond
  pure screening language

Why it matters:

- the repo now needs something more grounded than pore space alone if it is
  going to talk about sequestration relevance at all

Current sources:

- `carbon_capture/chemical_formula_features.py`
- `carbon_capture/co2_uptake_proxy.py`
- `carbon_capture/generate_co2_uptake_proxy_artifact.py`
- `carbon_capture/audit_co2_uptake_proxy_sensitivity.py`
- `carbon_capture/co2_uptake_proxy_v1.json`
- `carbon_capture/stress_artifacts/co2_uptake_proxy_sensitivity_audit_v1.json`

Current result:

- completed as a semi-physical uptake screen
- the uptake lane now deduplicates the abundance-safe subset from `368` rows to
  `307` formula-level candidates
- the top readiness lane is no longer just the highest-pore set:
  calcium-rich silicates such as `Ca3SiO5`, `Ca11AlSi3ClO18`, `Ca11Si4SO18`,
  and `Ca2SiO4` rise because stoichiometric carbonate ceiling is now included
- a useful internal split appeared:
  `balanced structural capture` versus `capacity-driven mineralization`
- the `1000`-trial sensitivity audit kept the current top `10` formulas in the
  top `10` on every run
- still remains proxy work rather than measured adsorption or industrial
  throughput evidence

### 1. Carbon Capture - Thermochemical / Carbonation Corroboration

What it is:

- test whether the new uptake split is thermochemically plausible enough to
  distinguish pore-assisted capture from direct mineralization-heavy pathways

Why it matters:

- the current uptake lane is stronger than pore ranking alone, but it still
  stops at stoichiometric ceiling plus accessibility heuristics

Current sources:

- `carbon_capture/co2_uptake_proxy_v1.json`
- `carbon_capture/composition_sensitive_stress_proxy.py`
- `internal/patent_prep/PLANETARY_SEQUESTRATION_SUPPORT_CHART.md`

Pass/fail:

- pass: add a stronger carbonation-likelihood or thermochemical corroboration
  layer to the top formula families
- fail: if the added layer is still too detached from chemistry, keep the
  current uptake proxy as the ceiling of the filing lane

### 2. Biology - Cross-Dataset Topology Hardening

What it is:

- extend the current graph-topology lane from one breast-cancer dataset to a
  cross-dataset cancer/diabetes comparison with threshold sweeps

Why it matters:

- the repo already has multi-dataset biological audit scripts, but the current
  topology script still uses only one dataset

Current sources:

- `Biology_UIL/intelligence/graph_topology.py`
- `Biology_UIL/intelligence/cross_dataset_audit.py`
- `Biology_UIL/intelligence/robust_audit.py`

Pass/fail:

- pass: topology measures show which parts are state-dependent versus stable
  across disease domains
- fail: if the network picture changes too much with threshold choice, treat it
  as exploratory support only

### 3. Battery Lane - Reproducible Discovery Packet

What it is:

- package the sulfosilicate discovery lane into a current reproducible packet

Why it matters:

- the README and replication docs still point at the battery discovery path as
  the repo’s flagship story

Current sources:

- `README.md`
- `HOW_TO_REPLICATE.md`
- `final_validated_candidates.json`
- `discovery_report_v1.1.json`

Pass/fail:

- pass: the battery lane can be rerun and summarized cleanly as a maintained
  proof packet
- fail: if the current repo has drifted too far, keep it as historical context
  instead of flagship messaging
