# Foundation App Boundary Audit

Created: 2026-05-06

## Decision

The folder currently named `Tasuke/` is treated as the Foundation app/liquid-workbench implementation area, not as a separate product identity.

Keep the folder name for now to avoid breaking imports and launch scripts. Rename only after the app is stable and import paths are mapped.

Canonical app entry point:

- root launcher: `launch_foundation.command`
- internal launcher: `Tasuke/launch_ui.command`
- Streamlit app: `Tasuke/ui/foundation_unified_app.py`

Legacy/direct pages remain available for debugging, but should not be treated as the default app.

## Current Local Footprint

Approximate size highlights from the local scan:

- `Tasuke/.venv/`: 1.2G
- `Tasuke/venv/`: 959M
- `Tasuke/output/`: 227M
- `Tasuke/checkpoints/`: 69M
- `Tasuke/.git/`: 4.2M
- `Tasuke/ui/`: 2.1M
- `Tasuke/tools/`: 560K
- `Tasuke/experiments/`: 288K
- `Tasuke/docs/`: 240K

## Repo Boundary

Treat as source / review candidates:

- `Tasuke/ui/`
- `Tasuke/tools/`
- `Tasuke/src/`
- `Tasuke/data/`
- `Tasuke/experiments/`
- `Tasuke/docs/`
- top-level launch/status scripts
- top-level README/status docs

Treat as local/generated and do not track in the main repo:

- `Tasuke/.git/`
- `Tasuke/.venv/`
- `Tasuke/venv/`
- `Tasuke/__pycache__/`
- `Tasuke/output/`
- `Tasuke/checkpoints/`
- `Tasuke/snapshots/`
- `Tasuke/releases/`

## Cleanup Rule

Do not delete generated folders until a separate archive decision is made.

For now, `.gitignore` prevents accidental tracking while preserving local work.

## Next Checks

1. Run syntax checks on the app/UI Python files. Done: active source compiles.
2. Identify import errors, especially missing training modules. Current active `Tasuke/ui/app.py` already adds `Tasuke/experiments` to `sys.path`; no active-source compile failure found.
3. Decide which launch path is canonical. Done: `Tasuke/ui/foundation_unified_app.py`.
4. Fix UI rendering only after syntax/import failures are mapped.
5. After stabilization, decide whether to rename `Tasuke/` to a neutral internal folder.

## Check Results

Commands run:

- `python3 -m py_compile Tasuke/ui/*.py Tasuke/tools/*.py`
- `find Tasuke/ui Tasuke/tools Tasuke/src Tasuke/experiments -name '*.py' -type f -print0 | xargs -0 python3 -m py_compile`
- `python3 tools/foundation_doctor.py`
- `python3 tools/foundation_qc.py`
- `zsh -n launch_foundation.command && zsh -n Tasuke/launch_ui.command && zsh -n Tasuke/run_foundation.command`
- `python3 -m py_compile Tasuke/ui/foundation_unified_app.py Tasuke/tools/tool_registry.py Tasuke/tasuke_menu.py`

Results:

- Active app/UI/tool/source/experiment Python files compile.
- Canonical app entry point compiles.
- Launch scripts parse.
- Tool registry has 37 entries and no missing target files.
- Live smoke test served the canonical app successfully on `http://localhost:8571`.
- Foundation doctor reports compile pass.
- Foundation QC reports compile pass.
- Foundation QC still warns about Streamlit HTML/CSS surfaces:
  - 27 potential markdown HTML-without-unsafe-flag matches
  - deprecated button-width calls removed from active app/UI surfaces; remaining `use_container_width` mentions are diagnostic/helper text
  - many intentional `unsafe_allow_html=True` calls in the UI layer
- A recursive compile of all `Tasuke/` files fails inside ignored snapshot path `Tasuke/snapshots/foundation_snapshot_20260501_141250/ui/tasuke_home.py`; this is archive/local state, not active source.

## Current UI Risk

The earlier visible-artifact complaints are more likely caused by CSS/HTML rendering debt than by syntax failure in active source.

Immediate hardening already applied:

- canonical app no longer injects the fixed top-right presence overlay by default
- main shell cards use smaller 8px radius instead of large pill-like cards
- active Streamlit button calls use `width="stretch"` / `width="content"` instead of deprecated `use_container_width`

Next UI work should start with:

- the canonical app entry point
- `Tasuke/tools/foundation_shell.py`
- `Tasuke/tools/tasuke_theme.py`
- `Tasuke/tools/foundation_presence.py`
- `Tasuke/ui/foundation_unified_app.py`

Avoid broad visual rewrites until the canonical launch path is chosen.
