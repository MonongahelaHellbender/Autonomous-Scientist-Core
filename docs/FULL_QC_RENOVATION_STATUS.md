# Full QC Renovation Status

Created: 2026-05-06

## Result

Status: `pass`

The full local QC wrapper completed successfully.

Command:

```bash
python3 tools/foundation_full_qc.py
```

Generated local artifacts:

- `outputs/foundation_full_qc/latest_full_qc.json`
- `outputs/foundation_full_qc/latest_full_qc.md`

These artifacts are generated local state and are not intended to be committed by default.

## Checks Included

| Check | Status |
| --- | --- |
| Foundation doctor | `pass` |
| Foundation QC | `pass` |
| Foundation major suite | `pass` |
| Autonomous core regression suite | `pass` |
| Foundation app compile | `pass` |

## Cross-Lane Regression Results

The autonomous core regression suite passed these lanes:

- battery
- formal verification
- carbon
- biology
- text intake
- architecture

## Current Known Warnings

The system still reports UI/HTML review debt:

- many intentional `unsafe_allow_html=True` calls
- remaining diagnostic text that counts deprecated `use_container_width` patterns
- potential markdown HTML-without-unsafe-flag warnings in `foundation_lab.py`

These are renovation backlog items, not current blockers.

## Next Renovation Target

Next minor repair should make the website/app more useful during runs:

1. show latest full-QC status on the unified dashboard
2. link Run Center -> Evidence -> Synthesis -> QC more clearly
3. keep CCS and Aegis black-box/private by default
4. avoid new feature work until the run/test loop is smoother
