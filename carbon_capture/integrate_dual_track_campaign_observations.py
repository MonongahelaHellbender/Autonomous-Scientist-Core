#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_INPUT_JSON = "carbon_capture/co2_mineralization_dual_track_observation_template_v1.json"
DEFAULT_OUTPUT_JSON = "carbon_capture/co2_mineralization_dual_track_observation_status_v1.json"


def load_json(path):
    return json.loads(resolve_path(path).read_text())


def resolve_path(path):
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return ROOT / candidate


def normalize_environment_label(text: str) -> str:
    label = (text or "").strip().lower()
    if not label:
        return "missing"
    if "ambient" in label:
        return "ambient"
    if "humid" in label:
        return "humidified_high_co2"
    if "dry" in label and "co2" in label:
        return "dry_high_co2"
    if "high-co2" in label or "high co2" in label or "near-pure co2" in label or "pure co2" in label:
        return "high_co2"
    if "co2" in label:
        return "co2_present"
    return "other"


def numeric_window_alignment(record: dict) -> str:
    if not record["completed"]:
        return "PENDING"

    suggested = record.get("suggested_window")
    if not suggested:
        return "NO_WINDOW_GUIDANCE"

    actual = record.get("actual_run_metadata") or {}
    fields = [
        ("temperature_c", "temperature_c_window"),
        ("relative_humidity_percent", "relative_humidity_percent_window"),
        ("dwell_hours", "dwell_hours_window"),
    ]
    observed_values = 0
    for actual_key, window_key in fields:
        actual_value = actual.get(actual_key)
        window = suggested.get(window_key)
        if actual_value is None or not window:
            continue
        observed_values += 1
        if actual_value < window[0] or actual_value > window[1]:
            return "OUT_OF_WINDOW"

    if observed_values == 0:
        return "MISSING_RUNTIME_METADATA"
    if observed_values < len(fields):
        return "PARTIAL_METADATA_WITHIN_WINDOW"
    return "WITHIN_WINDOW"


def environment_alignment(record: dict) -> str:
    if not record["completed"]:
        return "PENDING"

    suggested = record.get("suggested_window")
    if not suggested:
        return "NO_WINDOW_GUIDANCE"

    expected = normalize_environment_label(suggested.get("co2_environment", ""))
    actual = normalize_environment_label((record.get("actual_run_metadata") or {}).get("co2_environment", ""))
    if actual == "missing":
        return "MISSING_RUNTIME_METADATA"
    if expected == actual:
        return "MATCH"
    if expected == "high_co2" and actual == "dry_high_co2":
        return "MATCH"
    return "MISMATCH"


def runtime_metadata_completion_fraction(records: list[dict]) -> float:
    completed = [record for record in records if record["completed"]]
    if not completed:
        return 0.0

    full = 0
    for record in completed:
        actual = record.get("actual_run_metadata") or {}
        if all(
            actual.get(field) is not None
            for field in ("temperature_c", "relative_humidity_percent", "dwell_hours")
        ) and actual.get("co2_environment", "").strip():
            full += 1
    return full / len(completed)


def evidence_quality_tier(records: list[dict]) -> str:
    completed = [record for record in records if record["completed"]]
    if not completed:
        return "NO_DATA"

    numeric_alignments = Counter(numeric_window_alignment(record) for record in completed)
    env_alignments = Counter(environment_alignment(record) for record in completed)
    pending_technique_total = sum(
        value == "PENDING"
        for record in completed
        for value in record["technique_results"].values()
    )
    metadata_fraction = runtime_metadata_completion_fraction(records)

    if (
        numeric_alignments["WITHIN_WINDOW"] == len(completed)
        and env_alignments["MATCH"] == len(completed)
        and pending_technique_total == 0
        and metadata_fraction >= 1.0
    ):
        return "HIGH"
    if (
        numeric_alignments["OUT_OF_WINDOW"] == 0
        and env_alignments["MISMATCH"] == 0
        and metadata_fraction >= 0.5
    ):
        return "MODERATE"
    return "LOW"


def support_window_flag(records: list[dict]) -> str:
    support_records = [
        record
        for record in records
        if record["completed"] and record["overall_condition_outcome"] == "SUPPORTS"
    ]
    if not support_records:
        return "no_support_records"

    numeric_alignments = [numeric_window_alignment(record) for record in support_records]
    env_alignments = [environment_alignment(record) for record in support_records]
    if "WITHIN_WINDOW" in numeric_alignments and "MATCH" in env_alignments:
        return "within_window_support_present"
    if (
        any(
            alignment in {"WITHIN_WINDOW", "PARTIAL_METADATA_WITHIN_WINDOW"}
            for alignment in numeric_alignments
        )
        and "MISMATCH" not in env_alignments
    ):
        return "partial_window_support_present"
    if any(alignment == "OUT_OF_WINDOW" for alignment in numeric_alignments) or "MISMATCH" in env_alignments:
        return "support_only_out_of_window"
    return "support_missing_window_metadata"


def status_for_candidate(records):
    completed = [record for record in records if record["completed"]]
    if not completed:
        return "unobserved"

    outcomes = Counter(record["overall_condition_outcome"] for record in completed)
    total = len(completed)
    if outcomes["CONTRADICTS"] >= max(1, total // 3):
        return "contradicted_signal_present"
    if outcomes["SUPPORTS"] >= max(2, total // 2) and not outcomes["CONTRADICTS"]:
        return "supported_ready_for_review"
    if outcomes["MIXED"] or outcomes["SUPPORTS"]:
        return "partial_signal_present"
    return "pending_manual_review"


def interpret_campaign(candidate_rows: list[dict]) -> str:
    if all(row["candidate_status"] == "unobserved" for row in candidate_rows):
        return "no_data_yet"

    def count(track_label=None, selected_role=None, statuses=None):
        statuses = set(statuses or [])
        total = 0
        for row in candidate_rows:
            if track_label and row["track_label"] != track_label:
                continue
            if selected_role and row["selected_role"] != selected_role:
                continue
            if statuses and row["candidate_status"] not in statuses:
                continue
            total += 1
        return total

    track_a_anchor_supported = count(
        track_label="track_a_core_pilot",
        selected_role="reinforced_anchors",
        statuses={"supported_ready_for_review"},
    )
    track_a_anchor_contradicted = count(
        track_label="track_a_core_pilot",
        selected_role="reinforced_anchors",
        statuses={"contradicted_signal_present"},
    )
    track_a_control_supported = count(
        track_label="track_a_core_pilot",
        statuses={"supported_ready_for_review"},
    ) - track_a_anchor_supported
    track_b_supported = count(
        track_label="track_b_shadow_challengers",
        statuses={"supported_ready_for_review"},
    )
    track_b_partial_or_supported = count(
        track_label="track_b_shadow_challengers",
        statuses={"supported_ready_for_review", "partial_signal_present"},
    )

    if track_a_anchor_contradicted >= 2:
        return "anchor_lane_weakened"
    if track_b_supported >= 2 and track_a_anchor_supported < 2:
        return "recalibrate_core_lane"
    if track_a_anchor_supported >= 2 and track_a_control_supported == 0 and track_b_supported >= 1:
        return "widen_exploratory_appendix"
    if track_a_anchor_supported >= 2 and track_a_control_supported == 0 and track_b_partial_or_supported >= 1:
        return "keep_core_lane_expand_shadow_exploration"
    if track_a_anchor_supported >= 2 and track_a_control_supported == 0:
        return "keep_lane_narrow"
    return "mixed_manual_review"


def build_artifact(input_json):
    template = load_json(input_json)
    grouped = defaultdict(list)
    for record in template["observation_records"]:
        grouped[record["formula"]].append(record)

    candidate_status = []
    all_numeric_alignments = Counter()
    all_environment_alignments = Counter()
    evidence_quality_counts = Counter()
    for formula, records in grouped.items():
        completed_count = sum(record["completed"] for record in records)
        completed_records = [record for record in records if record["completed"]]
        numeric_alignments = Counter(numeric_window_alignment(record) for record in completed_records)
        environment_alignments = Counter(environment_alignment(record) for record in completed_records)
        quality = evidence_quality_tier(records)
        all_numeric_alignments.update(numeric_alignments)
        all_environment_alignments.update(environment_alignments)
        evidence_quality_counts[quality] += 1
        candidate_status.append(
            {
                "formula": formula,
                "track_label": records[0]["track_label"],
                "track_role": records[0]["track_role"],
                "selected_role": records[0]["selected_role"],
                "stability_tier": records[0]["stability_tier"],
                "campaign_batch": records[0]["campaign_batch"],
                "pathway_family": records[0]["pathway_family"],
                "planned_record_count": len(records),
                "completed_record_count": completed_count,
                "completion_fraction": completed_count / len(records),
                "candidate_status": status_for_candidate(records),
                "runtime_metadata_completion_fraction": runtime_metadata_completion_fraction(records),
                "numeric_window_alignment_counts": dict(numeric_alignments),
                "environment_alignment_counts": dict(environment_alignments),
                "support_window_flag": support_window_flag(records),
                "evidence_quality_tier": quality,
            }
        )

    candidate_status.sort(key=lambda row: (row["track_label"], row["campaign_batch"], row["formula"]))
    status_counts = Counter(row["candidate_status"] for row in candidate_status)
    track_status_counts = defaultdict(Counter)
    for row in candidate_status:
        track_status_counts[row["track_label"]][row["candidate_status"]] += 1

    return {
        "artifact_type": "co2_mineralization_dual_track_observation_status_v1",
        "source": input_json,
        "completed_record_count": sum(row["completed_record_count"] for row in candidate_status),
        "candidate_status_counts": dict(status_counts),
        "track_status_counts": {track: dict(counts) for track, counts in track_status_counts.items()},
        "record_numeric_window_alignment_counts": dict(all_numeric_alignments),
        "record_environment_alignment_counts": dict(all_environment_alignments),
        "candidate_evidence_quality_counts": dict(evidence_quality_counts),
        "campaign_interpretation": interpret_campaign(candidate_status),
        "candidate_status": candidate_status,
        "boundary_note": (
            "This integration artifact summarizes the state of the dual-track campaign. "
            "It does not create evidence; it only organizes observed outcomes into a decision branch "
            "and flags whether completed runs stayed inside the planned screening windows."
        ),
    }


def write_json_output(path, payload):
    output_path = resolve_path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", default=DEFAULT_INPUT_JSON)
    parser.add_argument("--json-output", default=DEFAULT_OUTPUT_JSON)
    return parser.parse_args()


def main():
    args = parse_args()
    artifact = build_artifact(args.input_json)
    print("--- CO2 Mineralization Dual-Track Observation Status v1 ---")
    print(f"Source:                         {args.input_json}")
    print(f"Candidate Status Counts:       {artifact['candidate_status_counts']}")
    print(f"Campaign Interpretation:       {artifact['campaign_interpretation']}")
    write_json_output(args.json_output, artifact)
    print(f"Saved Artifact:                 {args.json_output}")


if __name__ == "__main__":
    main()
