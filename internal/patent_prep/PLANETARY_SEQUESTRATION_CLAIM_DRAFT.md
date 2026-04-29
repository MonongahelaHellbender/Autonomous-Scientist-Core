# Planetary Sequestration Claim Draft

## Purpose

This is an internal claim-drafting note built only from the current
source-controlled calcium-based materials evidence in
`Autonomous-Scientist-Core`.

It is not a filing-ready patent application and should not be treated as legal
advice. Its job is to define the narrowest claim lane the repository can
currently support without importing falsified cross-domain artifacts.

## Plain-Language Framing

What this is:

- a draft claim lane for identifying and validating calcium-based structure
  materials using the current screening workflow and, where separately
  supported, a stochastic thermal hardening probe

Why it matters:

- the current repository supports a materials-screening and hardening workflow
  better than it supports a broad claim that any one named composition already
  delivers finished real-world sequestration performance

What would count as a pass:

- every claim element can be mapped to a current file, script, or saved result

What would count as a fail:

- the claim depends on `CaC2` specifically, on the historical ~43k bridge
  constant, on candidate-specific stress-test support that is not saved, or on
  unmeasured CO2-capture performance

## Current Claim Posture

The strongest current lane is:

- a computational method for screening calcium-based structure candidates
- using pore-space, stability, and environmental-risk filters

The partial current lane is:

- an optional composition-sensitive stochastic thermal stress probe with a saved
  deterministic formula-linked artifact and a `2000`-seed audit for
  `Ca3Si(ClO2)2`, but no first-principles thermal model and no generalized
  admission rule across the retained set

The weaker current lane is:

- a composition-family claim over the currently retained calcium-based
  structures in `carbon_capture/vetted_carbon_results.json`, without claiming
  that each named composition has already passed a saved stress artifact

The unsupported current lane is:

- a claim specific to `CaC2`
- a claim of demonstrated end-to-end industrial carbon sequestration capacity
- a claim that named compositions have already cleared a reproducible `<1%`
  stress threshold
- a claim that the current retained set is already abundance-clean enough for
  planetary-scale deployment
- a claim derived from cosmology / biology bridge artifacts

## Draft Independent Claims

### Claim 1 - Screening And Validation Method

A computer-implemented method for screening calcium-based material candidates
for further carbon-sequestration evaluation, the method
comprising:

1. retrieving or receiving material candidates that include calcium;
2. computing a pore-space metric for each candidate from structure-derived
   volume per atom;
3. computing or retrieving a stability metric for each candidate;
4. ranking the candidates according to pore space; and
5. rejecting at least some candidates according to an environmental-reactivity
   screening rule.

### Claim 2 - Optional Stress Hardening Probe

The method of Claim 1, further comprising an optional stochastic thermal stress
probe applied to a selected calcium-based candidate family, the probe having:

1. a baseline temperature of about `582°C`;
2. a perturbation model comprising approximately `5%` Gaussian noise;
3. an exposure window of `1000` simulated intervals; and
4. a structural-failure threshold of about `650°C`.

## Draft Dependent Claims

### Claim 3

The method of Claim 1, wherein the candidate-retrieval stage is restricted to a
calcium-silicon-oxygen element set and an energy-above-hull window.

### Claim 4

The method of Claim 1, wherein the environmental-risk screen rejects a
suboxide-like calcium composition predicted to undergo atmospheric collapse.

### Claim 5

The method of Claim 1, wherein a retained candidate includes a formula drawn
from the current retained calcium-based structure lane in
`carbon_capture/vetted_carbon_results.json`.

### Claim 6

The method of Claim 5, wherein the retained candidate set includes
`Ca3Si(ClO2)2` or `Ca2SiCl2O3`.

### Claim 7

The method of Claim 2, wherein the stress probe is recorded as a hardening
artifact rather than as candidate-admission proof unless the run is tied to a
saved, reproducible result.

## Support Map

| Claim element | Status | Current support | Why it is supportable |
| :--- | :--- | :--- |
| calcium-based screening workflow | Supported | `carbon_capture/abundance_pivot.py`, `carbon_capture/reactivity_scrutiny.py`, `carbon_capture/vetted_carbon_results.json` | current code and saved results screen calcium-containing structures by pore space, stability, and environmental risk |
| pore-space ranking | Supported | `carbon_capture/abundance_pivot.py`, `carbon_capture/final_leaderboard.py` | code explicitly ranks by pore space / volume per atom |
| stability metric | Supported | `carbon_capture/pore_ceiling_results.json`, `carbon_capture/vetted_carbon_results.json` | saved candidates include stability values |
| environmental-risk rejection | Supported | `carbon_capture/reactivity_scrutiny.py`, `carbon_capture/vetted_carbon_results.json` | current workflow marks some candidates as atmospheric-collapse rejections |
| toxic / radioactive exclusion | Supported | `carbon_capture/reactivity_scrutiny.py`, `carbon_capture/vetted_carbon_results.json` | the current hardening step now excludes forbidden-element formulas from the retained set |
| stochastic stress probe structure | Supported | `carbon_capture/cage_stress_test.py`, `carbon_capture/stress_artifacts/stress_model_audit_2000_seeds_0_to_1999.json` | the replayable probe parameters are encoded in source and exercised in a saved audit artifact |
| formula-linked deterministic composition-sensitive stress artifact | Supported | `carbon_capture/stress_artifacts/ca3si_clo2_2_composition_sensitive_stress_artifact_seed_20260429.json`, `carbon_capture/generate_composition_sensitive_stress_artifact.py` | one retained formula is now linked to a replayable parsed-formula proxy artifact |
| formula-linked composition-sensitive cross-seed audit | Partial | `carbon_capture/stress_artifacts/ca3si_clo2_2_composition_sensitive_stress_audit_2000_seeds_0_to_1999.json`, `carbon_capture/audit_composition_sensitive_stress_model.py` | strong support for one named formula under the upgraded proxy, but not yet a generalized retained-set claim |
| cross-candidate composition-sensitive comparison | Partial | `carbon_capture/stress_artifacts/abundance_safe_subset_v1_composition_sensitive_stress_bundle_top_25_seed_20260429.json`, `carbon_capture/composition_sensitive_stress_proxy.py` | the retained candidates can now be compared under a parsed-formula chemistry proxy, but it remains heuristic rather than first-principles |
| `<1%` admission rule for named candidates | Unsupported | `RESEARCH_LOG.md`, `carbon_capture/stress_artifacts/stress_model_audit_2000_seeds_0_to_1999.json` | one saved pass exists, but the cross-seed audit is borderline and does not justify a general admission claim |
| retained calcium-based structures | Supported | `carbon_capture/vetted_carbon_results.json` | current retained list contains named calcium-based candidates |
| abundance-safe subset v1 | Partial | `carbon_capture/abundance_safe_subset_v1.json` | a maintained scarcity-screened subset now exists, but it remains heuristic rather than a full resource model |

## Boundary Notes

### What we can say now

- the repository supports a narrow computational screening-and-validation lane
  for calcium-based structure candidates
- the repository supports a stochastic hardening probe, but not yet a stable
  candidate-admission threshold
- the repository supports one formula-linked deterministic
  composition-sensitive proxy artifact and cross-seed audit for
  `Ca3Si(ClO2)2`
- the repository supports naming current retained calcium-based candidates such
  as `Ca3Si(ClO2)2` and `Ca2SiCl2O3`
- the repository supports a maintained abundance-safe subset v1, but not yet a
  full abundance-proof planetary subset

### What we should not say yet

- that `CaC2` is the maintained patent survivor
- that the repository proves finished industrial sequestration throughput
- that abundance-safe subset v1 alone proves a full planetary resource posture
- that the calcium lane is validated by cosmology or biology bridges
- that a universal invariant proves the material claim

## Best Next Upgrade

If the goal is a stronger future filing lane, the highest-value next step is:

1. add a direct CO2-uptake or sequestration proxy so the claim can move from
   "candidate screening" toward "validated sequestration performance."
2. if needed later, upgrade the composition-sensitive stress proxy toward a
   stronger thermochemical model rather than stopping at heuristic screening.
