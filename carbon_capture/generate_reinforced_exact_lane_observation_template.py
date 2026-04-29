import argparse
import json
from pathlib import Path

DEFAULT_PACKET_JSON = "carbon_capture/reinforced_exact_lane_experimental_packet_v1.json"
DEFAULT_OVERLAY_JSON = "carbon_capture/reinforced_exact_lane_stability_overlay_v1.json"
DEFAULT_OUTPUT_JSON = "carbon_capture/reinforced_exact_lane_observation_template_v1.json"


def load_json(path):
    return json.loads(Path(path).read_text())


def overlay_map(overlay):
    return {
        row["formula"]: row for row in overlay["candidate_stability_profiles"]
    }


def build_observation_records(packet, overlay):
    stability_by_formula = overlay_map(overlay)
    records = []

    for dossier in packet["candidate_dossiers"]:
        stability = stability_by_formula[dossier["formula"]]
        replicate_count = stability["recommended_replicates"]
        for condition_label in dossier["condition_family"]:
            for replicate_id in range(1, replicate_count + 1):
                records.append(
                    {
                        "formula": dossier["formula"],
                        "selected_role": dossier["selected_role"],
                        "stability_tier": stability["stability_tier"],
                        "campaign_batch": dossier["campaign_batch"],
                        "condition_label": condition_label,
                        "replicate_id": replicate_id,
                        "required_techniques": dossier["required_techniques"],
                        "completed": False,
                        "technique_results": {
                            technique: "PENDING" for technique in dossier["required_techniques"]
                        },
                        "overall_condition_outcome": "PENDING",
                        "notes": "",
                    }
                )
    return records


def build_artifact(packet_json, overlay_json):
    packet = load_json(packet_json)
    overlay = load_json(overlay_json)
    records = build_observation_records(packet, overlay)
    return {
        "artifact_type": "reinforced_exact_lane_observation_template_v1",
        "sources": {
            "packet": packet_json,
            "stability_overlay": overlay_json,
        },
        "record_count": len(records),
        "candidate_count": len(packet["candidate_dossiers"]),
        "observation_records": records,
        "boundary_note": (
            "This template is a scaffold for future observations. Leaving fields "
            "empty or pending is expected until real outcomes exist."
        ),
    }


def write_json_output(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-json", default=DEFAULT_PACKET_JSON)
    parser.add_argument("--overlay-json", default=DEFAULT_OVERLAY_JSON)
    parser.add_argument("--json-output", default=DEFAULT_OUTPUT_JSON)
    return parser.parse_args()


def main():
    args = parse_args()
    artifact = build_artifact(args.packet_json, args.overlay_json)
    print("--- Reinforced Exact Lane Observation Template v1 ---")
    print(f"Packet Source:                  {args.packet_json}")
    print(f"Overlay Source:                 {args.overlay_json}")
    print(f"Candidate Count:                {artifact['candidate_count']}")
    print(f"Observation Record Count:       {artifact['record_count']}")
    write_json_output(args.json_output, artifact)
    print(f"Saved Artifact:                 {args.json_output}")


if __name__ == "__main__":
    main()
