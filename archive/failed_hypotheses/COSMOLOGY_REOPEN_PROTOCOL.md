# Cosmology Reopen Protocol

## Purpose

The cosmology lane remains archived in `archive/failed_hypotheses/` unless a
new analysis is intentionally opened with stronger scientific controls than the
historical exploratory pass.

This protocol exists to prevent rhetorical reuse of the falsified
Hubble-drift / bridge-constant lane while still allowing future discovery if
new data or stronger methods are introduced.

## Non-Negotiable Reopen Gates

Any future cosmology reopening must include all of the following before it can
be treated as an active framework input:

1. Null-model comparison
- At minimum compare against:
  - constant or near-constant baseline
  - low-complexity logarithmic model
  - low-order rational / polynomial baseline
  - physics-motivated baseline if one is explicitly being challenged
- Report a table of fit quality and complexity so any claimed improvement is not
  just overfitting.

2. Posterior predictive checks or equivalent predictive validation
- A future cosmology lane must show that the fitted model reproduces the data
  distribution under simulation or held-out prediction, not only that it fits
  the observed points.
- At minimum include:
  - residual-pattern check
  - leave-one-out or holdout sensitivity
  - high-leverage-point sensitivity, especially for extreme-redshift anchors

3. Systematics handling
- Explicitly document what calibration or measurement systematics were checked.
- At minimum consider:
  - anchor calibration choices
  - redshift binning sensitivity
  - extreme-point leverage
  - unit or transform sensitivity
  - whether a result depends on one special data point or preprocessing choice

4. Boundary note
- Every reopened cosmology artifact must say whether it is:
  - exploratory only
  - audit-ready internal evidence
  - eligible for cross-domain discussion
- Nothing becomes cross-domain eligible unless the null-model, predictive, and
  systematics gates all pass cleanly.

## Required Output Package

A valid reopened cosmology run should produce:

- a data manifest
- a model-comparison table
- a predictive-check artifact
- a systematics checklist
- a final boundary statement

Console-only output is not enough.

## Stop Conditions

The lane should be re-archived immediately if any of the following happens:

- the proposed signal disappears under a simpler null model
- predictive checks fail even when in-sample fit looks good
- the effect depends heavily on one anchor or preprocessing choice
- cross-domain language appears before the internal audit package is complete

## Current Status

As of April 29, 2026, the cosmology lane remains archived.
The historical Hubble-drift and bridge-constant results are provenance only and
must not be treated as active support for UIL claims.
