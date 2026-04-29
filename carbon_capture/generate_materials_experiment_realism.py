import argparse

from materials_experiment_realism import (
    DEFAULT_CALIBRATION_JSON,
    DEFAULT_OUTPUT_JSON,
    DEFAULT_OVERLAY_JSON,
    DEFAULT_PACKET_JSON,
    build_artifact,
    write_json_output,
)


def main():
    parser = argparse.ArgumentParser(
        description="Generate candidate-specific materials experiment realism artifact."
    )
    parser.add_argument("--calibration-json", default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--packet-json", default=DEFAULT_PACKET_JSON)
    parser.add_argument("--overlay-json", default=DEFAULT_OVERLAY_JSON)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    args = parser.parse_args()

    artifact = build_artifact(
        calibration_json=args.calibration_json,
        packet_json=args.packet_json,
        overlay_json=args.overlay_json,
    )
    write_json_output(args.output_json, artifact)

    print("--- Materials Experiment Realism v1 ---")
    print(f"Calibration Source:            {args.calibration_json}")
    print(f"Experimental Packet Source:    {args.packet_json}")
    print(f"Stability Overlay Source:      {args.overlay_json}")
    print(f"Candidate Count:               {artifact['candidate_count']}")
    print(f"Synthesis Feasibility Counts:  {artifact['synthesis_feasibility_counts']}")
    print(f"Kinetics Rate Counts:          {artifact['kinetics_rate_counts']}")

    print("\nFormula                  Tier                         Feasibility  Kinetics")
    print("-" * 92)
    for profile in artifact["candidate_profiles"][:12]:
        print(
            f"{profile['formula']:<24}"
            f"{profile['stability_tier']:<29}"
            f"{profile['synthesis_feasibility']['synthesis_feasibility_tier']:<13}"
            f"{profile['kinetics_expectation']['kinetics_rate_class']}"
        )

    print(f"\nSaved Artifact:                {args.output_json}")


if __name__ == "__main__":
    main()
