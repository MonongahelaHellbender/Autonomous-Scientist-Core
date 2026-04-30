#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CARBON = ROOT / "carbon_capture"
ARTIFACTS = CARBON / "corroboration_artifacts"
CAMPAIGN_JSON = ARTIFACTS / "co2_mineralization_dual_track_campaign_v1.json"
TEMPLATE_JSON = CARBON / "co2_mineralization_dual_track_observation_template_v1.json"
OUTPUT_JSON = ARTIFACTS / "co2_mineralization_run_packet_v1.json"
OUTPUT_MD = ARTIFACTS / "co2_mineralization_run_packet_v1.md"


def load_json(path: Path):
    return json.loads(path.read_text())


def summarize_track(records: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for record in records:
        grouped[record["formula"]].append(record)

    rows = []
    for formula, formula_records in sorted(grouped.items()):
        condition_labels = sorted({row["condition_label"] for row in formula_records})
        required_techniques = sorted(
            {tech for row in formula_records for tech in row["required_techniques"]}
        )
        replicate_count = max(row["replicate_id"] for row in formula_records)
        rows.append(
            {
                "formula": formula,
                "track_label": formula_records[0]["track_label"],
                "track_role": formula_records[0]["track_role"],
                "selected_role": formula_records[0]["selected_role"],
                "pathway_family": formula_records[0]["pathway_family"],
                "replicate_count": replicate_count,
                "condition_count": len(condition_labels),
                "conditions": condition_labels,
                "required_techniques": required_techniques,
                "planned_record_count": len(formula_records),
            }
        )
    return rows


def build_artifact() -> dict:
    campaign = load_json(CAMPAIGN_JSON)
    template = load_json(TEMPLATE_JSON)
    records = template["observation_records"]

    by_track = defaultdict(list)
    for record in records:
        by_track[record["track_label"]].append(record)

    track_a_summary = summarize_track(by_track["track_a_core_pilot"])
    track_b_summary = summarize_track(by_track["track_b_shadow_challengers"])

    return {
        "artifact_type": "co2_mineralization_run_packet_v1",
        "decision_question": campaign["decision_question"],
        "run_modes": {
            "minimum_interpretable_run": {
                "description": "Track A only. Best when the priority is clear interpretation with the fewest materials.",
                "materials": track_a_summary,
                "planned_record_count": len(by_track["track_a_core_pilot"]),
            },
            "expanded_two_track_run": {
                "description": "Track A plus Track B. Best when the priority is testing whether the exact-core lane is too narrow.",
                "materials": track_a_summary + track_b_summary,
                "planned_record_count": len(records),
            },
        },
        "decision_branches": campaign["decision_branches"],
        "boundary_note": (
            "This run packet is an execution aid derived from the dual-track campaign and "
            "its observation template. It does not add experimental evidence."
        ),
        "sources": {
            "dual_track_campaign": str(CAMPAIGN_JSON),
            "dual_track_template": str(TEMPLATE_JSON),
        },
    }


def write_markdown(artifact: dict) -> str:
    lines = [
        "# CO2 Mineralization Run Packet",
        "",
        artifact["decision_question"],
        "",
        "## Minimum Interpretable Run",
        "",
        artifact["run_modes"]["minimum_interpretable_run"]["description"],
        "",
        "| Formula | Role | Replicates | Conditions | Planned Records |",
        "| --- | --- | --- | --- | --- |",
    ]

    for row in artifact["run_modes"]["minimum_interpretable_run"]["materials"]:
        lines.append(
            f"| {row['formula']} | {row['track_role']} | {row['replicate_count']} | "
            f"{row['condition_count']} | {row['planned_record_count']} |"
        )

    lines.extend(
        [
            "",
            f"Total planned records: `{artifact['run_modes']['minimum_interpretable_run']['planned_record_count']}`",
            "",
            "## Expanded Two-Track Run",
            "",
            artifact["run_modes"]["expanded_two_track_run"]["description"],
            "",
            "| Formula | Track | Role | Pathway | Replicates | Conditions | Planned Records |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for row in artifact["run_modes"]["expanded_two_track_run"]["materials"]:
        lines.append(
            f"| {row['formula']} | {row['track_label']} | {row['track_role']} | "
            f"{row['pathway_family']} | {row['replicate_count']} | {row['condition_count']} | "
            f"{row['planned_record_count']} |"
        )

    lines.extend(
        [
            "",
            f"Total planned records: `{artifact['run_modes']['expanded_two_track_run']['planned_record_count']}`",
            "",
            "## Decision Branches",
            "",
        ]
    )

    for row in artifact["decision_branches"]:
        lines.append(f"- {row}")

    lines.extend(
        [
            "",
            artifact["boundary_note"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    artifact = build_artifact()
    OUTPUT_JSON.write_text(json.dumps(artifact, indent=2) + "\n")
    OUTPUT_MD.write_text(write_markdown(artifact) + "\n")
    print(f"wrote {OUTPUT_JSON}")
    print(f"wrote {OUTPUT_MD}")


if __name__ == "__main__":
    main()
