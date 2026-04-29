# Planetary Sequestration Claim Draft

## Purpose

This is an internal claim-drafting note built only from the current
source-controlled calcium-cage evidence in `Autonomous-Scientist-Core`.

It is not a filing-ready patent application and should not be treated as legal
advice. Its job is to define the narrowest claim lane the repository can
currently support without importing falsified cross-domain artifacts.

## Plain-Language Framing

What this is:

- a draft claim lane for identifying and validating calcium-based cage
  materials that remain structurally viable under a defined stochastic thermal
  stress test for planetary-scale carbon-capture use

Why it matters:

- the current repository supports a materials-screening and hardening workflow
  better than it supports a broad claim that any one named composition already
  delivers finished real-world sequestration performance

What would count as a pass:

- every claim element can be mapped to a current file, script, or saved result

What would count as a fail:

- the claim depends on `CaC2` specifically, on the historical ~43k bridge
  constant, or on unmeasured CO2-capture performance

## Current Claim Posture

The strongest current lane is:

- a computational method for screening calcium-based cage candidates
- plus a validation rule that admits only candidates surviving a stochastic
  thermal stress test with failure rate below `1%`

The weaker current lane is:

- a composition-family claim over the currently approved calcium-based
  structures in `carbon_capture/vetted_carbon_results.json`

The unsupported current lane is:

- a claim specific to `CaC2`
- a claim of demonstrated end-to-end industrial carbon sequestration capacity
- a claim derived from cosmology / biology bridge artifacts

## Draft Independent Claims

### Claim 1 - Screening And Validation Method

A computer-implemented method for identifying a calcium-based cage material
candidate for high-temperature carbon-sequestration deployment, the method
comprising:

1. receiving a candidate material description for a calcium-containing cage
   structure;
2. computing a pore-space metric for the candidate structure;
3. computing or retrieving a stability metric for the candidate structure;
4. rejecting candidates classified as environmentally reactive under a
   stoichiometric screening rule;
5. subjecting each non-rejected candidate to a stochastic thermal stress test
   having:
   - a baseline temperature of about `582°C`,
   - a perturbation model comprising approximately `5%` Gaussian noise,
   - an exposure window of `1000` simulated intervals, and
   - a structural-failure threshold of about `650°C`; and
6. admitting the candidate to a carbon-sequestration candidate set only when
   the simulated structural-failure rate remains below `1%`.

### Claim 2 - Candidate Family Defined By Screening Outcome

A calcium-based cage material candidate set identified by the method of Claim
1, wherein the set comprises candidates that:

1. are calcium-containing structures with positive cage-space ranking under the
   repository screening workflow;
2. are not rejected as atmosphere-collapse candidates by the environmental-risk
   screen; and
3. satisfy the stochastic thermal stress criterion of structural-failure rate
   below `1%`.

## Draft Dependent Claims

### Claim 3

The method of Claim 1, wherein the pore-space metric is evaluated as volume per
atom and ranked to prioritize higher-porosity calcium-based structures.

### Claim 4

The method of Claim 1, wherein the environmental-risk screen rejects a
suboxide-like calcium composition predicted to undergo atmospheric collapse.

### Claim 5

The method of Claim 1, wherein an approved candidate includes a formula drawn
from the current approved calcium-based structure lane in
`carbon_capture/vetted_carbon_results.json`.

### Claim 6

The method of Claim 5, wherein the approved candidate set includes
`Ca3Si(ClO2)2` or `Ca2SiCl2O3`.

### Claim 7

The method of Claim 1, wherein a candidate is excluded from patent-prep
promotion unless the candidate remains below the `1%` structural-failure
threshold under the defined stochastic thermal stress test.

## Support Map

| Claim element | Current support | Why it is supportable |
| :--- | :--- | :--- |
| calcium-based cage screening workflow | `carbon_capture/abundance_pivot.py`, `carbon_capture/reactivity_scrutiny.py`, `carbon_capture/vetted_carbon_results.json` | current code and saved results already screen calcium-containing structures by pore space, stability, and environmental risk |
| pore-space ranking | `carbon_capture/abundance_pivot.py`, `carbon_capture/final_leaderboard.py` | code explicitly ranks by pore space / volume per atom |
| stability metric | `carbon_capture/pore_ceiling_results.json`, `carbon_capture/vetted_carbon_results.json` | saved candidates include stability values |
| environmental-risk rejection | `carbon_capture/reactivity_scrutiny.py`, `carbon_capture/vetted_carbon_results.json` | current workflow marks some candidates as atmospheric-collapse rejections |
| stochastic stress test | `carbon_capture/cage_stress_test.py` | exact baseline, perturbation, interval count, and failure threshold are encoded in source |
| `<1%` admission rule | `carbon_capture/cage_stress_test.py`, `RESEARCH_LOG.md`, `HANDOFF_CODEX.md` | current survivor narrative and patent-prep boundary use this threshold explicitly |
| approved calcium-based structures | `carbon_capture/vetted_carbon_results.json` | current approved list contains named calcium-based candidates |

## Boundary Notes

### What we can say now

- the repository supports a narrow computational screening-and-validation lane
  for calcium-based cage candidates
- the repository supports a hardening rule based on stochastic thermal stress
- the repository supports naming current approved calcium-based candidates such
  as `Ca3Si(ClO2)2` and `Ca2SiCl2O3`

### What we should not say yet

- that `CaC2` is the maintained patent survivor
- that the repository proves finished industrial sequestration throughput
- that the calcium lane is validated by cosmology or biology bridges
- that a universal invariant proves the material claim

## Best Next Upgrade

If the goal is a stronger future filing lane, the highest-value next step is:

1. promote one specific calcium-based structure into a maintained, reproducible
   survivor record under `carbon_capture/`;
2. add a saved result file for the stochastic stress run rather than relying on
   log text alone; and
3. add a direct CO2-uptake or sequestration proxy so the claim can move from
   "candidate screening" toward "validated sequestration performance."
