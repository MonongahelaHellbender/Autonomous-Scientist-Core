# Open Science and Defensive IP Policy

## Purpose

This repository is operated under the following default principle:

**Open by default, attributed by design, patent only if needed to prevent enclosure.**

The goal is broad human benefit, clear credit, and a clean boundary between open research and legal protection workflows.

## Scope

This policy applies to the research and engineering workflow in this repository unless a file, folder, or related project is explicitly marked as patent-sensitive or legal-restricted.

This repository is not the primary legal workspace for the CCS provisional filings.

## Project Boundary

- `Autonomous-Scientist-Core` is the active open-research and validation workspace.
- `CCS Patent Project` is a separate repository and separate legal workspace.
- Patent-bound materials, filing drafts, prosecution notes, and other legal-sensitive CCS content should remain in the CCS repository unless intentionally copied with a clear reason.
- Cross-project transfers should be documented so provenance stays visible.

## Default Release Rule

When a result appears useful to the public:

1. Prefer public release.
2. Make attribution easy.
3. Preserve reproducibility.
4. Use patent filing only when there is a credible risk that someone else could lock the work away from public benefit.

## Defensive IP Trigger

Patent protection may be appropriate when one or more of the following are true:

- A third party could realistically patent the same invention and restrict use.
- The work has immediate commercialization value and enclosure risk is high.
- A narrow filing would preserve the ability to release the work openly after filing.
- The filing is being used as a shield against exclusionary control rather than as a tollbooth.

If these conditions are not met, public release is the default.

## Release Sequence

For work that is safe to publish immediately:

- release code under the repository's chosen software license
- release writing, figures, and datasets under an attribution-friendly public license
- add clear authorship and citation metadata
- archive a versioned public release

For work with real enclosure risk:

1. isolate the patent-sensitive material
2. decide whether a narrow filing is needed first
3. file only if the protective value is real
4. publish as broadly as possible afterward

## Credit Standard

Attribution should be designed into the release package rather than left to chance.

Use the following when appropriate:

- `LICENSE`
- `NOTICE`
- `CITATION.cff`
- `AUTHORS.md` or `CREDITS.md`
- DOI-backed releases
- provenance notes for major theory changes, falsifications, and transfer decisions

## Scientific Integrity Rule

- Do not move speculative or falsified artifacts into legal or public claim packages as if they were validated evidence.
- Keep pre-hardening and post-hardening outputs clearly labeled.
- Keep patent support packages tied only to reproducible artifacts.

## Current License Note

This repository now uses Apache 2.0 for the repository-level software license
and includes a `NOTICE` file for attribution context.

This policy document explains operating intent, but it does not by itself
separately license every non-code artifact under a different scheme. If
writing, figures, or datasets should later move to `CC BY 4.0`, that should be
done explicitly rather than assumed.

## Operating Intent

The intended norm is:

- publish what can safely be shared
- preserve credit visibly
- protect only when protection prevents a worse enclosure outcome
- avoid using IP to block public benefit
