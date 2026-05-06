# Next 5 Actions

Created: 2026-05-06
Purpose: Keep the next work session narrow.

## 1. Geometry-Likelihood Public Cleanup

Goal: make the public GitHub repo and Pages site match the local null-result truth.

Do:
- update public-facing README/site language
- center the falsification/null-result packet
- label older positive materials as historical

Do not:
- revive the old positive claim
- add new cosmology claims

## 2. Foundation App/UI Boundary Decision

Goal: treat the existing UI folder as part of the system, not a separate product identity, and decide what belongs in the main repo.

Status: mostly complete.

Do:
- keep `Tasuke/` as the internal implementation folder for now
- use `launch_foundation.command` as the root launcher
- use `Tasuke/ui/foundation_unified_app.py` as the canonical Streamlit entry point
- keep generated folders ignored unless intentionally archived

Do not:
- patch UI blindly
- commit `.venv`, checkpoints, or generated caches

Remaining:
- visual CSS pass on app shell/theme helpers
- decide later whether to rename the internal folder

## 3. Foundation Stability Pass

Goal: identify the smallest reliable Foundation / Build Your Own Scientist core.

Status: in progress.

Do:
- run existing doctor/QC tools
- map source files vs generated outputs
- identify files that belong in archive, docs, source, or ignore rules
- keep improving the one main repo rather than scattering into new folders
- use `python3 tools/foundation_full_qc.py` as the full-stack local QC wrapper

Do not:
- add new feature modules
- delete outputs without review

## 4. Extraction Map

Goal: map Foundation's best parts into future clean projects.

Extract later:
- Safety Gate
- CurrentTruth
- evidence-before-action rules
- action queue pressure checks
- audit/report packaging

Do not:
- create the new repo before Foundation is stable

Training growth note:
- use `docs/EVOLUTIONARY_LIQUID_TRAINING_ROADMAP.md` to guide bottom-up liquid training and plateau checks

## 5. CCS Hold Check

Goal: keep CCS protected while trustee/legal authority is unresolved.

Do:
- preserve the separate CCS project
- maintain private Codex review notes only inside CCS `codex_reviews/`
- prepare trustee/counsel questions

Do not:
- merge CCS into Foundation or Aegis
- start sale, licensing, buyer, investor, or public expansion work until cleared
