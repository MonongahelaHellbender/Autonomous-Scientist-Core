import argparse
import json
from collections import Counter
from pathlib import Path

from reinforced_exact_lane_experimental_packet import (
    DEFAULT_INPUT_JSON,
    build_packet,
    load_calibrated_exact_rows,
)

DEFAULT_OUTPUT_JSON = "carbon_capture/reinforced_exact_lane_experimental_packet_v1.json"


def write_json_output(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))


def build_artifact(input_json):
    rows = load_calibrated_exact_rows(input_json)
    return build_packet(rows)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", default=DEFAULT_INPUT_JSON)
    parser.add_argument("--json-output", default=DEFAULT_OUTPUT_JSON)
    return parser.parse_args()


def main():
    args = parse_args()
    artifact = build_artifact(args.input_json)
    batch_counts = {
        batch["batch_id"]: len(batch["candidates"]) for batch in artifact["campaign_batches"]
    }
    technique_counts = Counter(
        row["technique"] for row in artifact["measurement_technique_matrix"]
    )

    print("--- Reinforced Exact Lane Experimental Packet v1 ---")
    print(f"Source:                         {args.input_json}")
    print(f"Reinforced Anchors:            {artifact['reinforced_anchor_formulas']}")
    print(f"Campaign Batch Sizes:          {batch_counts}")
    print(f"Technique Counts:              {dict(technique_counts)}")
    print("")
    print(f"{'Rank':<5} {'Formula':<24} {'Batch':<34} {'Band'}")
    print("-" * 120)
    for row in artifact["candidate_dossiers"][:10]:
        print(
            f"{row['priority_rank']:<5} {row['formula']:<24} "
            f"{row['campaign_batch']:<34} {row['calibration_band']}"
        )

    write_json_output(args.json_output, artifact)
    print("")
    print(f"Saved Artifact:                 {args.json_output}")


if __name__ == "__main__":
    main()
