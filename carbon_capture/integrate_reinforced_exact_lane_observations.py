import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT_INPUT_JSON = "carbon_capture/reinforced_exact_lane_observation_template_v1.json"
DEFAULT_OUTPUT_JSON = "carbon_capture/reinforced_exact_lane_observation_status_v1.json"


def load_json(path):
    return json.loads(Path(path).read_text())


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


def build_artifact(input_json):
    template = load_json(input_json)
    grouped = defaultdict(list)
    for record in template["observation_records"]:
        grouped[record["formula"]].append(record)

    candidate_status = []
    for formula, records in grouped.items():
        completed_count = sum(record["completed"] for record in records)
        candidate_status.append(
            {
                "formula": formula,
                "selected_role": records[0]["selected_role"],
                "stability_tier": records[0]["stability_tier"],
                "campaign_batch": records[0]["campaign_batch"],
                "planned_record_count": len(records),
                "completed_record_count": completed_count,
                "completion_fraction": completed_count / len(records),
                "candidate_status": status_for_candidate(records),
            }
        )

    status_counts = Counter(row["candidate_status"] for row in candidate_status)
    candidate_status.sort(key=lambda row: (row["campaign_batch"], row["formula"]))
    return {
        "artifact_type": "reinforced_exact_lane_observation_status_v1",
        "source": input_json,
        "candidate_status_counts": dict(status_counts),
        "candidate_status": candidate_status,
        "boundary_note": (
            "This integration artifact summarizes the state of observed outcomes. "
            "With an untouched template, every candidate should remain unobserved."
        ),
    }


def write_json_output(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", default=DEFAULT_INPUT_JSON)
    parser.add_argument("--json-output", default=DEFAULT_OUTPUT_JSON)
    return parser.parse_args()


def main():
    args = parse_args()
    artifact = build_artifact(args.input_json)
    print("--- Reinforced Exact Lane Observation Status v1 ---")
    print(f"Source:                         {args.input_json}")
    print(f"Candidate Status Counts:       {artifact['candidate_status_counts']}")
    write_json_output(args.json_output, artifact)
    print(f"Saved Artifact:                 {args.json_output}")


if __name__ == "__main__":
    main()
