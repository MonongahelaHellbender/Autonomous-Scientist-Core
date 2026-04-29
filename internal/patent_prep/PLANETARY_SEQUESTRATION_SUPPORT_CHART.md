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
- Why: the current stress script is unseeded and the historical `0.80%` pass is
  preserved only in `RESEARCH_LOG.md`
- Audit result: a scrutiny rerun in `scientist-env` produced `1.20%` failure,
  and a `2000`-trial audit showed only `47.9%` of runs below the `<1%`
  threshold
- Pass/fail meaning:
  - pass would mean a saved or seeded rerun reproduces the claimed threshold
  - fail means the threshold is a proposed gate, not current proof

### Finding 2 - Named retained formulas are not linked to saved stress results

- Current status: unsupported
- Why: `carbon_capture/vetted_carbon_results.json` records screening and
  environmental-risk outcomes, but not candidate-specific stress-test outcomes

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
| Claim 2 optional stress probe exists | Partial | `carbon_capture/cage_stress_test.py` | the probe exists, but it is generic and unseeded |
| Claim 2 baseline `582°C` | Partial | `carbon_capture/cage_stress_test.py` | encoded in source, but not saved as a deterministic candidate-specific result |
| Claim 2 `5%` Gaussian noise | Partial | `carbon_capture/cage_stress_test.py` | encoded in source, but outcome varies materially by run |
| Claim 2 `1000` intervals | Partial | `carbon_capture/cage_stress_test.py` | encoded in source |
| Claim 2 `650°C` failure threshold | Partial | `carbon_capture/cage_stress_test.py` | encoded in source |
| Claim 5 retained formulas come from current lane | Supported | `carbon_capture/vetted_carbon_results.json` | named retained formulas are present in the maintained results file |
| Claim 6 retained set includes `Ca3Si(ClO2)2` or `Ca2SiCl2O3` | Supported | `carbon_capture/vetted_carbon_results.json` | both formulas are present |
| Any claim that named formulas already pass `<1%` stress threshold | Unsupported | none | current repo does not store that linkage |
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

1. save a deterministic stress-test artifact with seed, summary, and candidate
   identity
2. link that artifact to one retained calcium-based formula
3. add a direct sequestration or adsorption metric so the claim can move beyond
   screening language
