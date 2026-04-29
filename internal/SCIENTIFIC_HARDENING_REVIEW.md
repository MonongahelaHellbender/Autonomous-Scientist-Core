# Scientific Hardening Review

## Purpose

This note records a devil's-advocate review of the current
`Autonomous-Scientist-Core` state after the reinforced exact carbon lane was
turned into a maintained experimental packet.

The goal is not to celebrate the lane. The goal is to say what a skeptical,
field-trained scientist would still look for, what the current repo now does
better, and what remains missing.

## Materials / Carbonation View

### What a real materials scientist would ask first

- Are the top formulas experimentally distinguishable from one another as
  phases, or are some of them likely to collapse into the same synthesis /
  product family?
- Under what actual temperature, pressure, humidity, and exposure-time windows
  are these hypotheses meant to operate?
- What negative controls would tell us the apparent carbonate signal is not
  just generic degradation?
- Are the predicted products phase-pure enough to be recognizable, or are the
  signals likely to be mixed and ambiguous?
- What synthesis burden, polymorph ambiguity, or metastability risk do these
  candidates carry?
- Is the workflow honest about kinetics versus thermodynamics?

### What the repo now does better

- The reinforced exact lane is no longer just a ranking.
  `carbon_capture/reinforced_exact_lane_experimental_packet_v1.json` now stores
  anchors, controls, campaign batches, pass/fail gates, and the next ten
  logical execution steps.
- The packet no longer treats all top formulas as equally stable.
  `carbon_capture/reinforced_exact_lane_stability_overlay_v1.json` is intended
  to separate core anchors from provisional or threshold-sensitive roles.
- Future outcomes no longer require ad hoc interpretation paths.
  The observation template and integration harness define how real results can
  enter the lane without rewriting the entire workflow by hand.
- Future code drift is less likely to go unnoticed.
  `carbon_capture/carbon_lane_regression_check.py` now enforces several core
  internal invariants.
- The lane now has candidate-specific lab-start realism.
  `carbon_capture/materials_experiment_realism_v1.json` now adds starting
  reaction windows, synthesis-burden screens, kinetics expectations, and
  phase-fraction proxies for the reinforced exact candidates.

### What is still missing

- The new reaction windows are still heuristic.
  They are good enough for starting-screen design, but they are not measured
  optimums or equilibrium boundaries.
- The synthesis-feasibility layer is still a burden screen, not a measured
  synthesis-success model.
- The kinetics and phase-fraction layers are still proxies.
  They provide plausible onset and product-share windows, not fitted kinetic
  constants or quantitative diffraction refinements.
- The lane still lacks direct condition-varying observations.
  A real materials paper would still want actual carbonation outcomes under the
  suggested windows.

## Cosmology View

### What a cosmology PhD would look for

- Explicit null models and model-comparison baselines.
- Posterior predictive checks and sensitivity to priors or measurement
  assumptions.
- Clear treatment of observational systematics and calibration errors.
- Separation between an archived or falsified lane and any active framework
  claims.
- No rhetorical reuse of historical exploratory constants after falsification.

### Current repo posture

- The strongest cosmology-relevant boundary is already the right one:
  `RESEARCH_LOG.md` and `archive/failed_hypotheses/adversarial_cosmo.py`
  keep the Hubble-drift / bridge-constant lane in the falsified or provenance
  bucket.
- That boundary is now explicit at the process level too:
  `archive/failed_hypotheses/COSMOLOGY_REOPEN_PROTOCOL.md`
  defines the null-model, predictive-check, and systematics gates required
  before cosmology can re-enter the active framework.
- That boundary should stay hard.
  A cosmology reviewer would treat any new cross-domain rhetorical reuse as a
  red flag unless it came with new statistical evidence, null comparisons, and
  systematics work.

### What would need improvement if cosmology became active again

- A maintained posterior-check artifact rather than console-only summaries.
- A direct null-model comparison table with information criteria or equivalent
  scoring.
- A systematics checklist that says what measurement or calibration issues were
  considered and how they could falsify the interpretation.
- Blind or out-of-sample validation wherever possible.

## Genetics / Biology View

### What a genetics PhD would look for

- Explicit cohort provenance and sample-size transparency.
- Batch-effect or confounder handling.
- Out-of-sample validation across independent cohorts.
- Threshold sensitivity for topology or clustering claims.
- Multiple-testing or selection-bias awareness.
- Biological interpretability: what the latent or topological objects mean in
  molecular terms, not just that they are stable numerically.

### Current repo posture

- The right survivor boundary is already recorded:
  `Biology_UIL/validated/intrinsic_bottleneck.py` and `RESEARCH_LOG.md`
  keep the biological ID result state-dependent instead of universal.
- The most obvious mathematical bug has now been removed:
  the old cross-dataset stability audit used coefficient-of-variation style
  ratios on the sklearn diabetes benchmark even though those features are
  centered near zero, which made the audit numerically invalid.
- The biology lane now has a harder structural baseline:
  `Biology_UIL/intelligence/cross_dataset_audit.py`,
  `Biology_UIL/intelligence/graph_topology.py`,
  `Biology_UIL/intelligence/robust_audit.py`, and
  `Biology_UIL/intelligence/biology_lane_regression_check.py`
  now report sign-safe structural summaries, threshold sweeps, and resample
  stability checks instead of single-threshold or mean-ratio heuristics.
- The lane is now broader and more interpretable:
  `Biology_UIL/validated/multi_cohort_structural_audit_v1.json` and
  `Biology_UIL/validated/biology_interpretability_map_v1.json`
  widen the benchmark set to four cohorts and map latent or graph structure
  back to named feature families and modules.

### What would need improvement for a stronger biology lane

- Independent cohorts beyond the current bundled benchmark set, ideally with
  true omics-scale or batch-annotated data.
- A preprocessing-sensitivity note that makes it explicit how strongly the
  numeric intrinsic-dimension values depend on geometry choices such as
  feature scaling.
- Stronger target-aware biology.
  The current interpretability layer maps structure back to features, but it is
  not yet a causal or pathway-enrichment analysis.

## Devil's-Advocate Findings

### Finding 1 - The anchor lane is real, but not perfectly flat

- Root cause:
  hard score thresholds and near-tied top formulas create role sensitivity near
  the anchor boundary.
- Current fix:
  add a stability-aware overlay so the lane distinguishes core anchors from
  provisional ones rather than pretending the top group is uniform.

### Finding 2 - A workflow without observation ingestion is still fragile

- Root cause:
  planning artifacts tend to drift when real outcomes arrive unless the repo
  already knows how to store and summarize them.
- Current fix:
  add a maintained observation template and integration harness for the
  reinforced exact lane.

### Finding 3 - Self-improvement needs explicit invariants

- Root cause:
  a coding agent can only "improve itself" safely if it has local checks that
  expose regressions after edits.
- Current fix:
  keep `carbon_capture/carbon_lane_regression_check.py` as a first-class part
  of the lane, and extend the same pattern to
  `Biology_UIL/intelligence/biology_lane_regression_check.py`.

### Finding 4 - The old biology cross-dataset metric was invalid

- Root cause:
  coefficient-of-variation style ratios fail on centered features because the
  denominator can approach zero or change sign, which is exactly what the
  sklearn diabetes benchmark does.
- Current fix:
  replace those ratios with sign-safe structural metrics:
  intrinsic-dimension summaries, effective-rank compression, median absolute
  correlation, topology threshold sweeps, and resample-based stability checks.

### Finding 5 - Materials needed a lab-start layer, not just a ranking

- Root cause:
  a ranking or pathway hypothesis is not enough for a real materials scientist
  to know what to synthesize, how to challenge it, or what product split to
  look for.
- Current fix:
  add `carbon_capture/materials_experiment_realism_v1.json` so the lane now has
  starting windows, synthesis burden, kinetics expectations, and phase-fraction
  proxies tied to specific candidates.

## What Now Looks Close To Minimal

- The carbon lane now has:
  screening, hardening, uptake proxy, corroboration, reaction hypotheses, exact
  subset, thermodynamic calibration, packet, observation template,
  candidate-specific materials realism, and regression checks.
- The biology lane now has:
  a sign-safe cross-dataset structural audit, a four-cohort benchmark layer,
  topology threshold sweeps, interpretability mapping, resample-based
  robustness checks, and a local regression guardrail.
- That is enough internal structure that the next improvements should mostly be
  about real observations, measured chemistry, richer cohorts, and better
  external validation, not more abstract ranking layers.

## Highest-Value Remaining Additions

1. Add real observation records to the reinforced exact lane under the new
   materials realism windows.
2. Add measured or literature-grounded kinetics / equilibrium calibration if
   that data becomes available.
3. For biology, add true omics or batch-annotated cohorts beyond the bundled
   benchmark set.
4. For biology, add target-aware pathway or enrichment interpretation on top of
   the current feature-family mapping.
5. For cosmology, keep the falsified lane archived unless a new fully audited
   evidence path is intentionally opened.
