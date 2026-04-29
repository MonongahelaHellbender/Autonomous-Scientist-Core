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

## Scrutiny Audit - April 29, 2026

What was checked:

- a direct rerun of `carbon_capture/cage_stress_test.py` in the pinned
  `scientist-env`
- a `2000`-trial audit of the same stochastic model

Why it matters:

- plain language: we need to know whether the logged `0.80%` pass is robust or
  whether it only happened on one favorable random draw
- technical language: the script is unseeded, so the pass/fail boundary is a
  random variable unless a saved artifact or deterministic seed is added

Observed results:

- direct scrutiny rerun: `1.20%` failure rate and `676.73°C` peak spike
- `2000`-trial audit mean failure rate: `0.9817%`
- `2000`-trial audit median failure rate: `1.00%`
- fraction of audit runs below `1%` failure: `47.9%`

Pass/fail interpretation:

- pass would mean the historical `<1%` threshold reproduces reliably
- fail means the current stress script is too borderline to serve as strong
  patent-admission evidence without a seeded rerun or saved result artifact

Current conclusion:

- the stress-test lane is useful as a hardening probe
- the historical `0.80%` pass should not currently be treated as a reproducible
  survivor metric
- no named composition in `carbon_capture/vetted_carbon_results.json` is
  currently linked to a saved candidate-specific stress-test pass

## Formula Boundary

The current committed carbon-capture source set does not isolate a reproducible
`CaC2` patent-survivor record under `carbon_capture/`.

`CaC2` does appear in the solar-data ingestion / adversarial source lane, but
that is not the same as a maintained carbon-capture survivor artifact.

Until a direct `CaC2` structure is promoted into the maintained
`carbon_capture/` source set, patent-prep wording should stay at the
"calcium-based structure family" level or cite the current approved formulas
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

- this rule is not yet strong enough to serve as current proof of admission for
  named candidates until the stress test is tied to saved, reproducible,
  candidate-specific artifacts

## Current Boundary Decision

No standalone calcium patent repository was present on disk during this pass.

To avoid contaminating the unrelated CCS patent repository, this evidence is
quarantined here as an internal patent-prep lane until a dedicated materials
patent workspace exists.
