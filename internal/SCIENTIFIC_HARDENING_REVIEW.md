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

### What is still missing

- No real reaction-condition window.
  The packet still lacks candidate-specific temperature / pressure / humidity
  target ranges.
- No synthesis-feasibility model.
  A real lab would want expected synthesis route, precursor burden, and likely
  impurity risks.
- No kinetic model.
  The repo still says more about plausible product families than about how fast
  they should form.
- No quantitative phase-fraction model.
  The current lane can say what kinds of products should appear, but not how
  much of each one to expect.

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

### What would need improvement for a stronger biology lane

- Clearer confounder and cohort notes.
- A mapping from the stable latent or graph objects back to interpretable
  biological features or modules.
- Independent cohorts beyond the two sklearn benchmark datasets.
- A preprocessing-sensitivity note that makes it explicit how strongly the
  numeric intrinsic-dimension values depend on geometry choices such as
  feature scaling.

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

## What Now Looks Close To Minimal

- The carbon lane now has:
  screening, hardening, uptake proxy, corroboration, reaction hypotheses, exact
  subset, thermodynamic calibration, packet, observation template, and
  regression checks.
- The biology lane now has:
  a sign-safe cross-dataset structural audit, topology threshold sweeps,
  resample-based robustness checks, and a local regression guardrail.
- That is enough internal structure that the next improvements should mostly be
  about real observations, synthesis realism, kinetics, and phase-fraction
  expectations, not more abstract ranking layers.

## Highest-Value Remaining Additions

1. Add a candidate-specific reaction-condition suggestion layer for the
   reinforced anchors.
2. Add a synthesis-feasibility or precursor-burden screen for the anchor lane.
3. Add candidate-specific reaction-condition suggestions for the reinforced
   exact anchors.
4. For biology, add independent cohorts plus interpretable mapping from stable
   latent structure back to features or modules.
5. For cosmology, keep the falsified lane archived unless a new fully audited
   evidence path is intentionally opened.
