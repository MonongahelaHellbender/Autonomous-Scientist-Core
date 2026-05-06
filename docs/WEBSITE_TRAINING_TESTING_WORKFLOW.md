# Website Training And Testing Workflow

Created: 2026-05-06
Purpose: Make the local Foundation website/app useful during training, testing, and next-step decisions.

## Canonical Website Entry

Open the local Foundation website/app:

```bash
open '/Users/melissaellison/Autonomous-Scientist-Core/launch_foundation.command'
```

Canonical Streamlit app:

`Tasuke/ui/foundation_unified_app.py`

Use this as the first screen. Treat older direct pages as debugging routes, not the default website.

## The Seamless Loop

Use this order when training or testing:

1. Open the website.
2. Read the dashboard status.
3. Use **Run Center** or **Full Cycle** for the next run.
4. Use **Evidence** to convert outputs into evidence.
5. Use **Synthesis** to summarize what changed.
6. Run full QC.
7. Decide the next action from the QC and synthesis outputs.

The website should answer:

- What did we just run?
- What evidence changed?
- What is now true?
- What is risky or stale?
- What should happen next?

## Full QC Command

Run:

```bash
cd /Users/melissaellison/Autonomous-Scientist-Core
python3 tools/foundation_full_qc.py
```

Outputs:

- `outputs/foundation_full_qc/latest_full_qc.json`
- `outputs/foundation_full_qc/latest_full_qc.md`

This wraps:

- Foundation doctor
- Foundation QC
- Foundation major suite
- Autonomous core regression suite
- Foundation app compile check

## When A Run Fails

Use this order:

1. Fix compile/import failure first.
2. Fix broken app launcher or routing second.
3. Fix stale or contradictory truth third.
4. Fix visual/UI debt fourth.
5. Only then add or improve capabilities.

## Website Renovation Priorities

Do next:

- keep one canonical launch path
- keep generated app artifacts ignored
- reduce unsafe HTML/CSS only where it causes visible artifacts
- make Run Center, Evidence, Synthesis, and QC feel like one workflow
- show latest QC result on the dashboard

Do not do yet:

- rename the `Tasuke/` folder
- merge CCS content
- add new product tracks
- publish Aegis details
- over-polish visuals before run/QC flow is reliable

## Black-Box Rule For CCS And Aegis

CCS and Aegis can inform the philosophy, but should not become visible app content by default.

Treat them as black-box or sealed-room lanes:

- CCS: private patent-sensitive project, tracked separately
- Aegis: black-box future concept until boundaries are clear
- Foundation: may track that they exist, but should not expose sensitive details

Public or semi-public website language should focus on Foundation's general safety/control architecture, not protected CCS specifics.
