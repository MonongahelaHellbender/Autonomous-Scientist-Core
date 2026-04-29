# Calcium-Based Cage Baseline Integrity

## Purpose

This file is the isolated patent-prep note for the surviving material-science
lane inside `Autonomous-Scientist-Core`.

It exists to keep the calcium-based materials evidence separate from falsified
cosmology and biology bridge artifacts.

## Defensible Evidence In Current Source Control

1. Stress-test mechanism

- Source: `carbon_capture/cage_stress_test.py`
- Baseline temperature: `582.0°C`
- Noise model: `5%` Gaussian ambient perturbation
- Exposure window: `1000` simulated planetary hours
- Failure threshold: `650.0°C`

2. Historical logged survivor metrics

- Source: `RESEARCH_LOG.md`
- Logged result: `0.80%` structural failure rate
- Logged peak spike: `662°C`
- Important boundary: these are historical logged values, not a deterministic
  saved result file tied to a seeded replay.

3. Current source-controlled calcium-based structure lane

- Source: `carbon_capture/vetted_carbon_results.json`
- Current retained leading entries include:
  - `Ca3Si(ClO2)2` with pore space `17.82` and stability `-3.281`
  - `Ca2SiCl2O3` with pore space `17.29` and stability `-3.19`

4. Hardened safety screen

- Source: `carbon_capture/reactivity_scrutiny.py`
- Current hardening behavior:
  - rejects atmospheric-collapse candidates
  - rejects toxic, radioactive, and selected supply-chain-risk elements
- Current retained count after hardening: `438`
- Forbidden-element count after hardening: `0`

5. Maintained abundance-safe subset v1

- Source: `carbon_capture/abundance_safe_subset_v1.json`
- Input count: `438` hardened retained candidates
- Output count: `368` abundance-safe v1 candidates
- Policy: explicit exclusion of scarcity-heavy elements such as `Hf`, `Ta`,
  `Nb`, `Y`, `La`, `Ce`, and related rare-earth / constrained-supply elements
- Boundary: this is a maintained heuristic abundance screen, not a full
  global-resource or extraction-cost model

6. Semi-physical CO2 uptake proxy

- Source: `carbon_capture/co2_uptake_proxy_v1.json`
- Formula-level candidates after deduplication: `307` from `368` abundance-safe
  rows
- Proxy basis:
  - stoichiometric carbonate-capacity ceiling from carbonatable cation count
    and formula mass
  - accessibility and chemistry modulation from pore space, oxygen support,
    halide / sulfur / alkali penalties, and stability
- Top readiness examples:
  - `Ca3SiO5`
  - `Ca11AlSi3ClO18`
  - `Ca11Si4SO18`
  - `CaMgSiO4`
  - `Ca2SiO4`
- Sensitivity support:
  `carbon_capture/stress_artifacts/co2_uptake_proxy_sensitivity_audit_v1.json`
  kept the current top `10` formulas in the top `10` across `1000` weight
  perturbations

## Scrutiny Audit - April 29, 2026

What was checked:

- a deterministic formula-linked stress artifact for `Ca3Si(ClO2)2` using seed
  `20260429`
- a deterministic `2000`-trial audit of the same stochastic model using seeds
  `0..1999`
- an earlier unseeded scrutiny rerun in the pinned `scientist-env`, kept only as
  evidence that the old script was not replay-stable

Why it matters:

- plain language: we need to know whether the logged `0.80%` pass is robust or
  whether it only happened on one favorable random draw
- technical language: the script is unseeded, so the pass/fail boundary is a
  random variable unless a saved artifact or deterministic seed is added; that
  replayability fix is now in place for the current proxy model

Observed results:

- saved formula-linked artifact:
  `carbon_capture/stress_artifacts/ca3si_clo2_2_stress_artifact_seed_20260429.json`
  with `0.80%` failure rate and `703.74°C` peak spike
- saved audit artifact:
  `carbon_capture/stress_artifacts/stress_model_audit_2000_seeds_0_to_1999.json`
  with mean failure rate `0.9663%`
- saved cross-candidate comparison artifact:
  `carbon_capture/stress_artifacts/property_conditioned_stress_bundle_top_25_seed_20260429.json`
  showing replayable heuristic stress comparisons across the top `25` retained
  candidates by pore space
- saved composition-sensitive single-candidate artifact:
  `carbon_capture/stress_artifacts/ca3si_clo2_2_composition_sensitive_stress_artifact_seed_20260429.json`
  with `0.10%` failure rate under the upgraded proxy
- saved composition-sensitive cross-seed audit:
  `carbon_capture/stress_artifacts/ca3si_clo2_2_composition_sensitive_stress_audit_2000_seeds_0_to_1999.json`
  with `100.00%` of audited seeds below the `<1%` proxy threshold
- saved composition-sensitive bundle artifact:
  `carbon_capture/stress_artifacts/abundance_safe_subset_v1_composition_sensitive_stress_bundle_top_25_seed_20260429.json`
  showing oxide-rich silicates outranking chloride- and alkali-bearing
  variants under parsed-formula chemistry penalties
- audit median failure rate: `1.00%`
- fraction of audit runs below `1%` failure: `49.85%`
- earlier unseeded scrutiny rerun: `1.20%` failure rate and `676.73°C` peak
  spike

Pass/fail interpretation:

- pass would mean the historical `<1%` threshold reproduces reliably
- fail means the current stress script is too borderline to serve as strong
  patent-admission evidence without a seeded rerun or saved result artifact

Current conclusion:

- the stress-test lane is useful as a hardening probe
- `Ca3Si(ClO2)2` is now linked to a saved deterministic proxy-stress artifact
- the generic legacy audit remains borderline, so the historical unqualified
  `<1%` claim still should not be reused as current ground truth
- `Ca3Si(ClO2)2` is now also linked to a composition-sensitive deterministic
  artifact and a `2000`-seed composition-sensitive audit
- the upgraded model is materially stronger because it uses parsed formula
  chemistry, but it still remains proxy evidence rather than first-principles
  thermal proof
- the current carbon lane now supports one named composition under a stronger
  audited proxy, but it does not yet support generalized admission claims
  across all retained formulas

## CO2 Uptake Proxy - April 29, 2026

What was checked:

- a formula-level semi-physical uptake proxy across the abundance-safe subset
- a `1000`-trial sensitivity audit that perturbed only the heuristic
  accessibility weights

Why it matters:

- plain language: this is the first time the repo stores an uptake-relevant
  metric that is not just pore size or a materials-screening label
- technical language: the proxy combines a stoichiometric carbonate-capacity
  upper bound with accessibility and chemistry penalties, so it carries more
  physical meaning than the earlier screening-only lane

Observed results:

- saved uptake artifact:
  `carbon_capture/co2_uptake_proxy_v1.json`
- saved sensitivity audit:
  `carbon_capture/stress_artifacts/co2_uptake_proxy_sensitivity_audit_v1.json`
- formula-level candidate count after deduplication: `307`
- top readiness formula: `Ca3SiO5`
- top `25` mode split:
  - `20` balanced structural capture candidates
  - `5` capacity-driven mineralization candidates
- top `10` formulas remained top `10` across all `1000` sensitivity trials

Current conclusion:

- the repo now supports a semi-physical uptake proxy lane
- this is stronger than pore ranking alone and strong enough to inform internal
  claim-scoping language
- it still should not be described as measured adsorption, direct industrial
  capture rate, or proven sequestration throughput

## Thermochemical / Carbonation Corroboration - April 29, 2026

What was checked:

- a corroboration layer that combined the uptake proxy with deterministic
  composition-sensitive thermal margin signals
- a `1000`-trial weight-perturbation audit on the corroboration layer

Why it matters:

- plain language: this tests whether the uptake ranking looks chemically and
  thermally self-consistent, not just convenient
- technical language: the new layer compares uptake mode with
  structural-capture propensity, mineralization propensity, and thermal-margin
  support

Observed results:

- saved corroboration artifact:
  `carbon_capture/thermochemical_carbonation_corroboration_v1.json`
- saved corroboration audit:
  `carbon_capture/corroboration_artifacts/thermochemical_corroboration_sensitivity_v1.json`
- top `25` corroboration classes:
  - `11` hybrid framework mineralization
  - `5` mineralization corroborated
  - `9` mixed / ambiguous
- strict mode alignment in the top `25`: `4%`
- mode compatibility in the top `25`: `48%`
- top `10` ranking remained highly stable across the audit

Current conclusion:

- the strongest new pattern is not a clean two-way split
- many of the best calcium-rich formulas behave more like hybrid
  framework-mineralization candidates than pure pore-capture candidates
- this is useful internal pathway evidence, but it is still not direct
  reaction energetics or measured capture chemistry

## Reaction-Level Carbonation Pathways - April 29, 2026

What was checked:

- an explicit pathway-family layer built on top of the thermochemical
  corroboration artifact
- a maintained exact-oxide subset for formulas whose simplified carbonation
  ceiling admits an exact mass-balanced oxide-to-carbonate conversion

Why it matters:

- plain language: this is the first layer that turns the carbon ranking into
  named, testable reaction-family hypotheses instead of only abstract scores
- technical language: the new scripts derive simplified pathway families and
  stoichiometric carbonate-conversion ceilings directly from formula counts,
  then isolate the exact oxide-supported subset

Observed results:

- saved pathway artifact:
  `carbon_capture/reaction_level_carbonation_pathways_v1.json`
- saved exact-oxide subset artifact:
  `carbon_capture/exact_oxide_conversion_subset_v1.json`
- top `25` pathway-family counts:
  - `1` oxide-framework bulk mineralization
  - `8` oxide-framework hybrid mineralization
  - `4` oxide-framework mixed restructuring
  - `3` mixed-anion restructuring carbonation
  - `2` pre-carbonated completion pathways
  - `7` mixed-network restructuring cases
- exact mass-balanced oxide-conversion paths in the top `25`: `13`
- total exact-subset candidate count: `38`
- leading exact-subset examples:
  - `Ca3SiO5`
  - `CaMgSiO4`
  - `Ca2SiO4`
  - `Ca3Mg(SiO4)2`
  - `Ca8Si5O18`

Current conclusion:

- the cleanest current chemistry lane is no longer the whole abundance-safe
  carbon set
- it is the exact oxide-conversion subset isolated in
  `carbon_capture/exact_oxide_conversion_subset_v1.json`
- this is stronger than the earlier proxy-only labeling because it supplies
  explicit reaction-family hypotheses and exact mass-balanced conversion
  ceilings for a focused subset
- it still should not be described as direct thermodynamics, measured reaction
  products, or industrial sequestration proof

## Exact-Subset Thermodynamic Calibration - April 29, 2026

What was checked:

- a surrogate thermodynamic calibration layer applied only to the maintained
  exact oxide-conversion subset
- a `1000`-trial sensitivity audit that perturbed both the calibration weights
  and the surrogate product-family support coefficients

Why it matters:

- plain language: this asks which exact stoichiometric conversion routes still
  look strongest after we account for product-family simplicity and reactant
  resistance, rather than only counting how much CO2 a formula could hold
- technical language: the new layer scores each exact conversion using
  stoichiometric carbonate yield, product-phase support, product simplicity,
  reactant resistance, and the existing corroboration signals

Observed results:

- saved calibration artifact:
  `carbon_capture/exact_subset_thermodynamic_calibration_v1.json`
- saved calibration audit:
  `carbon_capture/corroboration_artifacts/exact_subset_thermodynamic_calibration_sensitivity_v1.json`
- top `25` calibration-band counts:
  - `4` thermodynamically reinforced exact conversions
  - `6` thermodynamically plausible exact restructurings
  - `2` surface-limited exact conversions
  - `13` lower-confidence exact conversions
- reinforced exact lane:
  - `Ca3SiO5`
  - `Ca2SiO4`
  - `CaMgSiO4`
  - `Ca3Mg(SiO4)2`
- audit result:
  the current top `10` exact candidates remained in the top `10` across all
  `1000` perturbation trials

Current conclusion:

- the exact subset now has an internally ranked thermodynamic-calibration lane
- the best current carbon candidates are no longer just "exactly balanced" or
  "high capacity"; they now also survive a stronger product-family calibration
- this is the strongest internal carbon lane in the repo so far
- it still remains surrogate thermodynamic work rather than first-principles
  free-energy calculations or measured carbonation chemistry

## Reinforced Exact Experimental / Falsification Packet - April 29, 2026

What was checked:

- a maintained experimental packet built directly on the reinforced exact lane
- a `1000`-trial packet audit that perturbed the upstream calibration knobs
- a reusable carbon-lane regression check for future self-auditing

Why it matters:

- plain language: this converts the strongest internal carbon lane into a
  concrete do-this-next workflow instead of leaving it as a ranking
- technical language: the packet stores candidate tiers, measurement matrix,
  campaign batches, decision gates, consensus hypotheses, and the next ten
  execution steps for the reinforced exact candidates

Observed results:

- saved packet artifact:
  `carbon_capture/reinforced_exact_lane_experimental_packet_v1.json`
- saved packet audit:
  `carbon_capture/corroboration_artifacts/reinforced_exact_lane_experimental_packet_sensitivity_v1.json`
- self-check script:
  `carbon_capture/carbon_lane_regression_check.py`
- reinforced anchors:
  - `Ca3SiO5`
  - `Ca2SiO4`
  - `CaMgSiO4`
  - `Ca3Mg(SiO4)2`
- packet audit:
  mean reinforced-anchor overlap `93.38%` across `1000` perturbation trials
- regression check:
  current pass status confirmed after packet generation

Current conclusion:

- the repo now contains a concrete confirm/falsify packet for the strongest
  current exact-conversion lane
- the packet is useful because it turns internal rankings into explicit
  measurement tasks and failure triggers
- the regression check is useful because it lets the AI scientist re-test its
  own assumptions after code changes
- neither the packet nor the regression harness should be described as
  experimental evidence by themselves

## Planetary-Scale Abundance Boundary

What was checked:

- an explicit abundance-safe v1 screen across the hardened retained set

Observed result:

- `70` hardened retained formulas were excluded into the scarcity lane
- `368` candidates remain in `carbon_capture/abundance_safe_subset_v1.json`

Why it matters:

- plain language: the lane is cleaner, but not yet clean enough to claim a
  true planetary-scale abundance posture
- technical language: safety hardening and abundance hardening are separate
  filters; abundance-safe v1 is now maintained as a separate screened subset

Current conclusion:

- the present abundance-safe v1 subset is usable as the maintained planetary
  screening lane
- it should still not be described as a full abundance-proof deployment set
- the next AI-scientist task for carbon now shifts from packet generation to an
  observation-integration or experimental-results update path

## Formula Boundary

The current committed carbon-capture source set does not isolate a reproducible
`CaC2` patent-survivor record under `carbon_capture/`.

`CaC2` does appear in the solar-data ingestion / adversarial source lane, but
that is not the same as a maintained carbon-capture survivor artifact.

Until a direct `CaC2` structure is promoted into the maintained
`carbon_capture/` source set, patent-prep wording should stay at the
"calcium-based structure family" level or cite the current retained formulas
above.

## Exclusions

Do not carry any of the following into patent-prep claims or evidence packets:

- Hubble Drift
- historical ~43k bridge-ratio claims
- universal biological-ID claims
- cross-domain scaling tables from `PROVENANCE_HISTORY.md`

## Validation Standard

Proposed admission rule:

- any new candidate should pass a stochastic-noise stress test with failure rate
  below `1%`

Current boundary:

- this rule is now stronger for `Ca3Si(ClO2)2` under the composition-sensitive
  proxy because saved deterministic and audited artifacts exist
- it is still not strong enough to serve as a generalized proof of admission
  for the whole retained lane

## Current Boundary Decision

No standalone calcium patent repository was present on disk during this pass.

To avoid contaminating the unrelated CCS patent repository, this evidence is
quarantined here as an internal patent-prep lane until a dedicated materials
patent workspace exists.
