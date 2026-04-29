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

### Completed - Carbon Capture - Thermochemical / Carbonation Corroboration

What it is:

- test whether the uptake split is thermochemically plausible enough to
  distinguish porous structural capture from mineralization-heavy pathways

Why it matters:

- the uptake lane is stronger than pore ranking alone, but it still needs a
  pathway-style cross-check before the labels can be trusted

Current sources:

- `carbon_capture/co2_uptake_proxy_v1.json`
- `carbon_capture/composition_conditioning.py`
- `carbon_capture/thermochemical_carbonation_corroboration.py`
- `carbon_capture/generate_thermochemical_corroboration_artifact.py`
- `carbon_capture/audit_thermochemical_corroboration_sensitivity.py`
- `carbon_capture/thermochemical_carbonation_corroboration_v1.json`
- `carbon_capture/corroboration_artifacts/thermochemical_corroboration_sensitivity_v1.json`

Current result:

- completed as a thermochemical corroboration layer on top of the uptake proxy
- the old binary uptake split did not survive cleanly; the strongest new
  pattern is a `hybrid framework mineralization` class
- top `25` corroboration classes:
  `11` hybrid framework mineralization, `5` mineralization corroborated, `9`
  mixed / ambiguous
- strict mode alignment is only `4%` in the current top `25`, but mode
  compatibility rises to `48%`, which means the earlier uptake labels were
  often too binary rather than simply wrong
- the top `10` formulas remain highly stable in rank under `1000`
  corroboration-weight perturbations

### Completed - Carbon Capture - Reaction-Level Carbonation Pathways

What it is:

- build explicit simplified carbonation pathway families for the top formulas,
  such as framework-retaining capture versus carbonate-plus-silica conversion

Why it matters:

- the carbon lane now has stable rankings and pathway hints, but not yet
  explicit reaction-family hypotheses

Current sources:

- `carbon_capture/thermochemical_carbonation_corroboration_v1.json`
- `carbon_capture/reaction_level_carbonation_pathways.py`
- `carbon_capture/generate_reaction_level_carbonation_pathways.py`
- `carbon_capture/reaction_level_carbonation_pathways_v1.json`

Current result:

- completed as an explicit reaction-family layer
- the strongest new chemistry result is that `13` of the current top `25`
  candidates admit exact mass-balanced oxide-to-carbonate conversion ceilings
- top `25` pathway-family counts:
  `1` oxide-framework bulk mineralization, `8` oxide-framework hybrid
  mineralization, `4` oxide-framework mixed restructuring, `3` mixed-anion
  restructuring carbonation, `2` pre-carbonated completion pathways, and `7`
  mixed-network restructuring cases
- this is a stronger mechanistic layer than the earlier corroboration labels,
  but it still remains pathway hypothesis work rather than measured
  thermodynamics

### Completed - Carbon Capture - Exact Oxide Conversion Subset

What it is:

- isolate the formulas whose simplified carbonation ceiling admits an exact
  mass-balanced oxide-to-carbonate conversion

Why it matters:

- this is now the cleanest internal chemistry lane in the current carbon set
- it separates the strongest stoichiometric candidates from mixed-anion and
  already-carbon-bearing edge cases

Current sources:

- `carbon_capture/reaction_level_carbonation_pathways_v1.json`
- `carbon_capture/generate_exact_oxide_conversion_subset.py`
- `carbon_capture/exact_oxide_conversion_subset_v1.json`

Current result:

- completed as a maintained exact-chemistry subset
- current exact candidate count: `38`
- top `25` exact-subset family counts:
  `1` oxide-framework bulk mineralization, `8` oxide-framework hybrid
  mineralization, `12` oxide-framework mixed restructuring, and `4`
  oxide-framework surface-carbonation cases
- the leading exact subset is headed by `Ca3SiO5`, `CaMgSiO4`, `Ca2SiO4`,
  `Ca3Mg(SiO4)2`, and `Ca8Si5O18`
- this is the best-supported carbon lane for future mechanistic hardening, but
  it is still not measured carbonation thermodynamics

### Completed - Carbon Capture - Thermodynamic Calibration For Exact Oxide Subset

What it is:

- add a stronger surrogate thermodynamic calibration pass specifically for the
  `38` exact oxide-conversion candidates

Why it matters:

- the exact subset is now the cleanest carbon lane, so the highest-value next
  carbon step is to strengthen that lane rather than invent another broad
  heuristic screen

Current sources:

- `carbon_capture/exact_oxide_conversion_subset_v1.json`
- `carbon_capture/exact_subset_thermodynamic_calibration.py`
- `carbon_capture/generate_exact_subset_thermodynamic_calibration.py`
- `carbon_capture/audit_exact_subset_thermodynamic_calibration.py`
- `carbon_capture/exact_subset_thermodynamic_calibration_v1.json`
- `carbon_capture/corroboration_artifacts/exact_subset_thermodynamic_calibration_sensitivity_v1.json`

Current result:

- completed as a surrogate thermodynamic calibration layer on the exact subset
- top `25` calibration-band counts:
  `4` thermodynamically reinforced exact conversions, `6`
  thermodynamically plausible exact restructurings, `2` surface-limited exact
  conversions, and `13` lower-confidence exact conversions
- the reinforced exact lane is now led by `Ca3SiO5`, `Ca2SiO4`, `CaMgSiO4`,
  and `Ca3Mg(SiO4)2`
- the `1000`-trial calibration audit kept the current top `10` exact
  candidates in the top `10` on every trial, although some threshold-edge band
  labels remained moderately sensitive
- this is a stronger product-family thermodynamic layer than the earlier exact
  subset alone, but it still remains surrogate calibration rather than
  first-principles or measured thermodynamics

### 1. Biology - Cross-Dataset Topology Hardening

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

### 2. Carbon Capture - Experimental Falsification Packet For Reinforced Exact Lane

What it is:

- build a concrete measurement and falsification packet for the reinforced
  exact-conversion candidates, starting with `Ca3SiO5`, `Ca2SiO4`, `CaMgSiO4`,
  and `Ca3Mg(SiO4)2`

Why it matters:

- the carbon lane now has a much cleaner exact subset and a stronger internal
  thermodynamic calibration, so the next honest upgrade is to define what
  experimental or external evidence would confirm or reject the strongest lane

Current sources:

- `carbon_capture/exact_subset_thermodynamic_calibration_v1.json`
- `carbon_capture/reaction_level_carbonation_pathways_v1.json`
- `internal/patent_prep/CALCIUM_CAGE_BASELINE_INTEGRITY.md`

Pass/fail:

- pass: the repo stores a concrete confirm/falsify packet for the reinforced
  exact lane without overstating what is already known
- fail: if the packet still depends on unknown thermodynamic data, keep it as
  an internal planning note rather than evidence

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
