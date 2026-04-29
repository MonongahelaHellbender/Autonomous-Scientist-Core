# Planetary Sequestration Support Chart

## Purpose

This is the attorney-style clause support chart for the current internal claim
draft in `PLANETARY_SEQUESTRATION_CLAIM_DRAFT.md`.

Plain language:

- this file says which claim parts are truly supported, only partly supported,
  or not currently supportable from the repository

Technical language:

- each clause is mapped to primary source files and graded for evidentiary
  strength so unsupported language can be cut before any filing draft

## Scrutiny Findings

### Finding 1 - Historical stress pass is not reproducibly supported

- Current status: unsupported as a named-candidate admission claim
- Why: the historical `0.80%` pass came from an unseeded legacy run and was
  preserved only in `RESEARCH_LOG.md`
- New artifact result: `Ca3Si(ClO2)2` now has a saved deterministic proxy
  artifact at seed `20260429` with `0.80%` failure
- Audit result: a `2000`-seed deterministic audit still showed only `49.85%` of
  runs below the `<1%` threshold
- Pass/fail meaning:
  - pass would mean a saved or seeded rerun reproduces the claimed threshold
  - fail means the threshold is a proposed gate, not current general proof

### Finding 2 - Named retained formulas are not linked to saved stress results

- Current status: partially corrected
- Why: `Ca3Si(ClO2)2` is now linked to a saved deterministic proxy artifact, but
  the current model is still not composition-sensitive and the other retained
  formulas remain unlinked

### Finding 3 - Biology summary must stay state-dependent

- Current status: corrected
- Why: `RESEARCH_LOG.md` rejects a universal biological ID and records
  state-dependent values instead

## Clause Map

| Clause | Status | Primary support | Plain-language note |
| :--- | :--- | :--- | :--- |
| Claim 1.1 retrieve or receive calcium candidates | Supported | `carbon_capture/abundance_pivot.py` | the repo does query calcium-containing materials |
| Claim 1.2 compute pore-space metric | Supported | `carbon_capture/abundance_pivot.py` | pore space is computed as volume per atom |
| Claim 1.3 compute or retrieve stability metric | Supported | `carbon_capture/abundance_pivot.py`, `carbon_capture/pore_ceiling_results.json` | stability values are saved with candidates |
| Claim 1.4 rank candidates by pore space | Supported | `carbon_capture/abundance_pivot.py`, `carbon_capture/final_leaderboard.py` | the workflow sorts by pore space |
| Claim 1.5 reject environmentally reactive candidates | Supported | `carbon_capture/reactivity_scrutiny.py`, `carbon_capture/vetted_carbon_results.json` | the workflow labels some candidates rejected for atmospheric collapse |
| Claim 2 optional stress probe exists | Supported | `carbon_capture/cage_stress_test.py`, `carbon_capture/stress_artifacts/stress_model_audit_2000_seeds_0_to_1999.json` | the probe now exists in replayable form and has a saved audit artifact |
| Claim 2 baseline `582°C` | Supported | `carbon_capture/cage_stress_test.py`, `carbon_capture/stress_artifacts/ca3si_clo2_2_stress_artifact_seed_20260429.json` | encoded in source and recorded in a saved artifact |
| Claim 2 `5%` Gaussian noise | Supported | `carbon_capture/cage_stress_test.py`, `carbon_capture/stress_artifacts/ca3si_clo2_2_stress_artifact_seed_20260429.json` | encoded in source and recorded in a saved artifact |
| Claim 2 `1000` intervals | Supported | `carbon_capture/cage_stress_test.py`, `carbon_capture/stress_artifacts/ca3si_clo2_2_stress_artifact_seed_20260429.json` | encoded in source and recorded in a saved artifact |
| Claim 2 `650°C` failure threshold | Supported | `carbon_capture/cage_stress_test.py`, `carbon_capture/stress_artifacts/ca3si_clo2_2_stress_artifact_seed_20260429.json` | encoded in source and recorded in a saved artifact |
| One retained formula linked to a saved proxy-stress artifact | Partial | `carbon_capture/stress_artifacts/ca3si_clo2_2_stress_artifact_seed_20260429.json` | useful as a replayable example, but still generic rather than composition-sensitive |
| Claim 5 retained formulas come from current lane | Supported | `carbon_capture/vetted_carbon_results.json` | named retained formulas are present in the maintained results file |
| Claim 6 retained set includes `Ca3Si(ClO2)2` or `Ca2SiCl2O3` | Supported | `carbon_capture/vetted_carbon_results.json` | both formulas are present |
| Any claim that named formulas already pass a robust generalized `<1%` stress threshold | Unsupported | audit artifact does not support it | one deterministic pass is not enough because the audit remains borderline |
| Any claim specific to `CaC2` as maintained survivor | Unsupported | none in `carbon_capture/` | `CaC2` appears in a solar lane, not the maintained carbon-capture lane |
| Any claim of proven industrial sequestration performance | Unsupported | none | repo does not contain direct CO2 uptake or throughput evidence |

## Recommended Filing Posture

### Safest current posture

- a computational screening method for calcium-based structures
- an environmental-risk rejection heuristic
- an optional stochastic hardening probe described as a further evaluation step

### Language to avoid for now

- "validated planetary sequestration material"
- "named compositions have passed the stress gate"
- "`CaC2` is the survivor"
- "industrial carbon capture is proven"

## Best Next Evidence Upgrade

1. replace the current generic proxy with a composition-sensitive stress model
2. extend saved artifacts to additional retained formulas
3. add a direct sequestration or adsorption metric so the claim can move beyond
   screening language
