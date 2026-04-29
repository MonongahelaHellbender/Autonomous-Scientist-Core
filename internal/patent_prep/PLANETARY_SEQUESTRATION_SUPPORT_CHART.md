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
- Generic-model audit result: a `2000`-seed deterministic audit still showed
  only `49.85%` of runs below the `<1%` threshold
- Composition-sensitive audit result: `Ca3Si(ClO2)2` now also has a saved
  `2000`-seed audit under the upgraded proxy with `100.00%` of runs below the
  `<1%` threshold
- Pass/fail meaning:
  - pass would mean a saved or seeded rerun reproduces the claimed threshold
  - fail means the threshold is a proposed gate, not current general proof

### Finding 2 - Named retained formulas are not linked to saved stress results

- Current status: partially corrected
- Why: `Ca3Si(ClO2)2` is now linked to both a saved deterministic
  composition-sensitive artifact and a `2000`-seed audit, and the top abundance-safe
  subset now has a replayable composition-sensitive bundle; other retained
  formulas still remain un-audited individually

### Finding 3 - Biology summary must stay state-dependent

- Current status: corrected
- Why: `RESEARCH_LOG.md` rejects a universal biological ID and records
  state-dependent values instead

### Finding 4 - The retained carbon lane is safer but not yet abundance-clean

- Current status: partially corrected
- Why: abundance-safe subset v1 now removes the `70` scarcity-heavy formulas
  from the hardened retained lane, but the subset is still heuristic rather
  than a full resource model
- Practical meaning:
  - pass means a dedicated maintained abundance-safe subset now exists
  - remaining boundary means we still avoid claiming full planetary resource
    proof

### Finding 5 - A semi-physical uptake proxy now exists, but it is still not measured performance

- Current status: partially corrected
- Why: `carbon_capture/co2_uptake_proxy_v1.json` now stores a formula-level
  uptake lane that combines stoichiometric carbonate ceiling with chemistry and
  accessibility modifiers
- Sensitivity result:
  `carbon_capture/stress_artifacts/co2_uptake_proxy_sensitivity_audit_v1.json`
  kept the current top `10` formulas in the top `10` across `1000` weight
  perturbations
- Remaining boundary:
  - pass means a direct uptake-style metric now exists in source control
  - fail means it still is not measured adsorption, throughput, or industrial
    sequestration proof

### Finding 6 - Thermochemical corroboration refines the uptake split into a hybrid lane

- Current status: partially corrected
- Why:
  `carbon_capture/thermochemical_carbonation_corroboration_v1.json` now tests
  whether the uptake ranking survives a thermal-margin and pathway-style
  corroboration pass
- Main result:
  the old binary split was too coarse; the dominant new class in the top `25`
  is `hybrid framework mineralization`
- Audit result:
  `carbon_capture/corroboration_artifacts/thermochemical_corroboration_sensitivity_v1.json`
  kept the top formulas very stable in rank, even though some exact class
  labels remained only moderately stable
- Remaining boundary:
- pass means we now have pathway-style corroboration rather than just another
  screening score
- fail means we still do not have direct carbonation thermodynamics or
  measured reaction products

### Finding 7 - Reaction-level pathways isolate a cleaner exact-oxide chemistry lane

- Current status: partially corrected
- Why:
  `carbon_capture/reaction_level_carbonation_pathways_v1.json` now stores
  explicit reaction-family hypotheses, including exact mass-balanced
  oxide-to-carbonate conversion ceilings where the formula chemistry permits it
- Main result:
  `13` of the current top `25` formulas admit exact mass-balanced conversion
  ceilings, and the maintained exact subset now contains `38` formulas
- New maintained subset:
  `carbon_capture/exact_oxide_conversion_subset_v1.json`
- Remaining boundary:
  - pass means the cleanest internal chemistry lane is now isolated
  - fail means exact stoichiometric ceilings still do not equal measured
    thermodynamic favorability or product confirmation

### Finding 8 - Exact-subset thermodynamic calibration identifies a reinforced lane

- Current status: partially corrected
- Why:
  `carbon_capture/exact_subset_thermodynamic_calibration_v1.json` now applies a
  stronger surrogate thermodynamic calibration only to the `38` exact
  oxide-conversion candidates
- Main result:
  the reinforced exact lane is now led by `Ca3SiO5`, `Ca2SiO4`, `CaMgSiO4`,
  and `Ca3Mg(SiO4)2`
- Audit result:
  `carbon_capture/corroboration_artifacts/exact_subset_thermodynamic_calibration_sensitivity_v1.json`
  kept the current top `10` exact candidates in the top `10` across `1000`
  perturbation trials
- Remaining boundary:
  - pass means the exact subset now has a stronger internal thermodynamic lane
  - fail means the calibration is still surrogate chemistry rather than direct
    free-energy or product-measurement evidence

## Clause Map

| Clause | Status | Primary support | Plain-language note |
| :--- | :--- | :--- | :--- |
| Claim 1.1 retrieve or receive calcium candidates | Supported | `carbon_capture/abundance_pivot.py` | the repo does query calcium-containing materials |
| Claim 1.2 compute pore-space metric | Supported | `carbon_capture/abundance_pivot.py` | pore space is computed as volume per atom |
| Claim 1.3 compute or retrieve stability metric | Supported | `carbon_capture/abundance_pivot.py`, `carbon_capture/pore_ceiling_results.json` | stability values are saved with candidates |
| Claim 1.4 rank candidates by pore space | Supported | `carbon_capture/abundance_pivot.py`, `carbon_capture/final_leaderboard.py` | the workflow sorts by pore space |
| Claim 1.5 reject environmentally reactive candidates | Supported | `carbon_capture/reactivity_scrutiny.py`, `carbon_capture/vetted_carbon_results.json` | the workflow labels some candidates rejected for atmospheric collapse |
| Toxic / radioactive exclusion in retained set | Supported | `carbon_capture/reactivity_scrutiny.py`, `carbon_capture/vetted_carbon_results.json` | the hardened screen now removes forbidden-element formulas from the retained set |
| Claim 2 optional stress probe exists | Supported | `carbon_capture/cage_stress_test.py`, `carbon_capture/stress_artifacts/stress_model_audit_2000_seeds_0_to_1999.json` | the probe now exists in replayable form and has a saved audit artifact |
| Claim 2 baseline `582°C` | Supported | `carbon_capture/cage_stress_test.py`, `carbon_capture/stress_artifacts/ca3si_clo2_2_stress_artifact_seed_20260429.json` | encoded in source and recorded in a saved artifact |
| Claim 2 `5%` Gaussian noise | Supported | `carbon_capture/cage_stress_test.py`, `carbon_capture/stress_artifacts/ca3si_clo2_2_stress_artifact_seed_20260429.json` | encoded in source and recorded in a saved artifact |
| Claim 2 `1000` intervals | Supported | `carbon_capture/cage_stress_test.py`, `carbon_capture/stress_artifacts/ca3si_clo2_2_stress_artifact_seed_20260429.json` | encoded in source and recorded in a saved artifact |
| Claim 2 `650°C` failure threshold | Supported | `carbon_capture/cage_stress_test.py`, `carbon_capture/stress_artifacts/ca3si_clo2_2_stress_artifact_seed_20260429.json` | encoded in source and recorded in a saved artifact |
| One retained formula linked to a saved composition-sensitive stress artifact | Supported | `carbon_capture/stress_artifacts/ca3si_clo2_2_composition_sensitive_stress_artifact_seed_20260429.json`, `carbon_capture/generate_composition_sensitive_stress_artifact.py` | the repo now stores a deterministic named-candidate artifact under the upgraded parsed-formula proxy |
| One retained formula linked to a composition-sensitive cross-seed audit | Partial | `carbon_capture/stress_artifacts/ca3si_clo2_2_composition_sensitive_stress_audit_2000_seeds_0_to_1999.json`, `carbon_capture/audit_composition_sensitive_stress_model.py` | strong support for one named formula under the upgraded proxy, but not yet a general claim across retained formulas |
| Cross-candidate replayable composition-sensitive comparison exists | Partial | `carbon_capture/stress_artifacts/abundance_safe_subset_v1_composition_sensitive_stress_bundle_top_25_seed_20260429.json`, `carbon_capture/composition_sensitive_stress_proxy.py` | stronger than the earlier property-conditioned bundle because parsed stoichiometry and chemistry families now change the ranking, but the result remains proxy rather than first-principles |
| Formula-level CO2 uptake proxy exists | Partial | `carbon_capture/co2_uptake_proxy_v1.json`, `carbon_capture/co2_uptake_proxy.py` | the repo now stores a semi-physical uptake screen based on stoichiometric carbonate ceiling plus chemistry/accessibility modifiers |
| CO2 uptake proxy rank stability audit exists | Partial | `carbon_capture/stress_artifacts/co2_uptake_proxy_sensitivity_audit_v1.json`, `carbon_capture/audit_co2_uptake_proxy_sensitivity.py` | the current top uptake formulas are stable under weight perturbations, but the audit tests ranking robustness rather than physical correctness |
| Thermochemical / carbonation corroboration exists | Partial | `carbon_capture/thermochemical_carbonation_corroboration_v1.json`, `carbon_capture/thermochemical_carbonation_corroboration.py` | the uptake lane is now checked against thermal margin and pathway-style corroboration, which reveals a dominant hybrid framework-mineralization class |
| Thermochemical corroboration sensitivity audit exists | Partial | `carbon_capture/corroboration_artifacts/thermochemical_corroboration_sensitivity_v1.json`, `carbon_capture/audit_thermochemical_corroboration_sensitivity.py` | the top corroborated formulas are stable in rank, though some exact class labels remain moderately sensitive |
| Reaction-level carbonation pathway layer exists | Partial | `carbon_capture/reaction_level_carbonation_pathways_v1.json`, `carbon_capture/reaction_level_carbonation_pathways.py` | the repo now stores explicit pathway-family hypotheses and exact mass-balanced conversion ceilings for oxide-only formulas where the chemistry permits it |
| Exact oxide conversion subset exists | Partial | `carbon_capture/exact_oxide_conversion_subset_v1.json`, `carbon_capture/generate_exact_oxide_conversion_subset.py` | `38` formulas are now isolated in a cleaner stoichiometric subset, but exact conversion ceilings still do not prove real thermodynamic favorability |
| Exact-subset thermodynamic calibration exists | Partial | `carbon_capture/exact_subset_thermodynamic_calibration_v1.json`, `carbon_capture/exact_subset_thermodynamic_calibration.py` | the repo now stores a stronger surrogate thermodynamic ranking over the exact subset, and it isolates a reinforced exact-conversion lane |
| Exact-subset thermodynamic calibration audit exists | Partial | `carbon_capture/corroboration_artifacts/exact_subset_thermodynamic_calibration_sensitivity_v1.json`, `carbon_capture/audit_exact_subset_thermodynamic_calibration.py` | the exact-subset top ranks are stable under weight and support-map perturbations, but the calibration still is not direct thermodynamics |
| Claim 5 retained formulas come from current lane | Supported | `carbon_capture/vetted_carbon_results.json` | named retained formulas are present in the maintained results file |
| Claim 6 retained set includes `Ca3Si(ClO2)2` or `Ca2SiCl2O3` | Supported | `carbon_capture/vetted_carbon_results.json` | both formulas are present |
| Any claim that named formulas already pass a robust generalized `<1%` stress threshold | Unsupported | generalized retained-set audit does not support it | one named formula now clears the upgraded proxy audit, but that is not enough to support a generalized retained-set claim |
| Maintained abundance-safe subset exists | Partial | `carbon_capture/abundance_safe_subset_v1.json` | useful and maintained, but still heuristic rather than a full resource model |
| Any claim that abundance-safe subset v1 proves full planetary resource readiness | Unsupported | heuristic screen only | the subset is a practical filter, not a complete resource proof |
| Any claim specific to `CaC2` as maintained survivor | Unsupported | none in `carbon_capture/` | `CaC2` appears in a solar lane, not the maintained carbon-capture lane |
| Any claim of proven industrial sequestration performance | Unsupported | none | repo does not contain direct CO2 uptake or throughput evidence |

## Recommended Filing Posture

### Safest current posture

- a computational screening method for calcium-based structures
- an environmental-risk rejection heuristic
- an optional stochastic hardening probe described as a further evaluation step
- one named-candidate composition-sensitive proxy artifact and audit as support
  for a narrower follow-on evaluation lane
- a semi-physical uptake estimator based on stoichiometric capacity ceiling and
  chemistry/accessibility modifiers
- an internal thermochemical corroboration layer that can distinguish
  mineralization-heavy and hybrid-framework candidates
- an internal reaction-level pathway layer and exact-oxide subset that define
  the cleanest stoichiometric chemistry lane
- an exact-subset thermodynamic calibration that further narrows the strongest
  current internal carbon lane
- abundance-safe subset v1 language rather than full planetary resource language

### Language to avoid for now

- "validated planetary sequestration material"
- "fully proven planetary-scale abundant deployment set"
- "named compositions have passed the stress gate"
- "`CaC2` is the survivor"
- "industrial carbon capture is proven"

## Best Next Evidence Upgrade

1. turn the reinforced exact lane into an experimental or falsification packet
   if the filing posture needs a path beyond internal surrogate calibration
2. convert the composition-sensitive stress lane from proxy chemistry toward a
   stronger thermochemical basis if the filing posture needs more than a proxy
3. convert abundance-safe v1 from a heuristic screen into a stronger resource
   model if the project still needs planetary-scale claims
