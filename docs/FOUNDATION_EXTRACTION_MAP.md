# Foundation Extraction Map

Created: 2026-05-06
Purpose: Improve the one Foundation / Build Your Own Scientist repo now, while keeping future extraction clean.

## Current Decision

Do not create new repos yet.

Use this repo as the one working repo while Foundation is being stabilized. Extract later only after the source, app, outputs, and public claims are clean.

## Core That Should Stay In The Main Repo

Keep these as the active Foundation / Build Your Own Scientist spine:

- `foundation_lab.py`
- `app.py`
- `science_chat.py`
- `autonomous_core_regression_suite.py`
- `tools/foundation_doctor.py`
- `tools/foundation_qc.py`
- `tools/foundation_health_summary.py`
- `tools/foundation_major_suite.py`
- `tools/foundation_one_button_ops.py`
- `tools/foundation_project_status.py`
- `tools/foundation_handoff.py`
- `tools/foundation_handoff_snapshot.py`
- `tools/foundation_export_bundle.py`
- `docs/PROJECT_PORTFOLIO_DECISIONS.md`
- `docs/NEXT_5_ACTIONS.md`
- `docs/FOUNDATION_APP_BOUNDARY_AUDIT.md`

## App / UI Source Candidates

Track as source candidates when intentionally adding the app folder to the main repo:

- `Tasuke/README.md`
- `Tasuke/requirements.txt`
- `Tasuke/launch_ui.command`
- `Tasuke/run_foundation.command`
- `Tasuke/tasuke_menu.py`
- `Tasuke/health_check.py`
- `Tasuke/regression_check.py`
- `Tasuke/src/`
- `Tasuke/data/`
- `Tasuke/experiments/`
- `Tasuke/tools/`
- `Tasuke/ui/`
- `Tasuke/docs/`

Do not track as active source:

- `Tasuke/.git/`
- `Tasuke/.venv/`
- `Tasuke/venv/`
- `Tasuke/output/`
- `Tasuke/checkpoints/`
- `Tasuke/snapshots/`
- `Tasuke/releases/`
- `Tasuke/**/__pycache__/`
- `*.backup_*`
- `*.bak`

## Future Extraction: Aegis / CurrentTruth / Safety Gate

Extract later, not now.

Candidate source areas:

- `tools/foundation_safety_gate.py`
- `tools/foundation_predictive_coding.py`
- `tools/foundation_autoloop_truth.py`
- `tools/foundation_constraints.py`
- `tools/foundation_action_queue.py`
- `tools/foundation_action_queue_triage.py`
- `tools/foundation_snapshot.py`
- `tools/foundation_consolidation_pack.py`
- `tools/foundation_verifier.py`
- `tools/foundation_decision_pipeline.py`
- `tools/foundation_run_ledger.py`

Target shape later:

- action intake
- stale-state check
- evidence requirement check
- contradiction/current-truth check
- proceed / hold / needs-review gate
- audit log
- report package

## Future Extraction: Scientific Claim Stress Tester

Extract later from:

- `tools/foundation_experiment_designer.py`
- `tools/foundation_eval_runner.py`
- `tools/foundation_eval_scoring.py`
- `tools/foundation_eval_quality.py`
- `tools/foundation_eval_report.py`
- Geometry-Likelihood null-result workflow

Target shape later:

- claim intake
- falsifiability check
- evidence ladder
- contradiction scan
- reproducibility packet

## CCS Boundary

Do not extract CCS into Foundation.

CCS remains separate at:

`/Users/melissaellison/Documents/Projects/CCS Patent Project`

Status:

`tracked_separately_on_trustee_hold`

Use only a high-level pointer in Foundation docs. Do not copy CCS claims, legal materials, buyer materials, or detailed technical proof into this repo.

## Next Repo Hygiene Step

When ready to make the app part of the one repo, add only source-candidate paths and verify:

- active app source compiles
- root launcher opens the unified app
- generated folders remain ignored
- backup files are excluded or archived
- old identity/name language is legacy-labeled
