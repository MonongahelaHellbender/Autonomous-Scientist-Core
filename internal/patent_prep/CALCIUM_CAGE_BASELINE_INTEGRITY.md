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
- the next AI-scientist task for carbon now shifts from subset isolation to
  stronger composition-sensitive and uptake-aware modeling

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
