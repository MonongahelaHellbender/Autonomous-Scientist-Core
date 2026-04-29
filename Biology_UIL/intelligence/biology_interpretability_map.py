import argparse
import json
from pathlib import Path

from biology_structural_utils import (
    graph_module_summary,
    load_biology_cohort_registry,
    pca_interpretability_summary,
    robust_feature_variability,
    semantic_feature_theme,
)

DEFAULT_OUTPUT_JSON = "Biology_UIL/validated/biology_interpretability_map_v1.json"


def build_artifact():
    registry = load_biology_cohort_registry()
    cohort_maps = {}
    for cohort_name, cohort in registry.items():
        frame = cohort["frame"]
        feature_stability = robust_feature_variability(frame)
        cohort_maps[cohort_name] = {
            "display_name": cohort["display_name"],
            "modality": cohort["modality"],
            "feature_semantic_groups": {
                feature: semantic_feature_theme(cohort_name, feature) for feature in frame.columns
            },
            "latent_axes": pca_interpretability_summary(frame, cohort_name),
            "graph_modules": graph_module_summary(frame, cohort_name),
            "stable_features": feature_stability[:8],
            "unstable_features": feature_stability[-8:],
            "interpretation_note": (
                "These mappings tie low-dimensional and topological structure back to "
                "named feature families so the biology lane is less of a black box."
            ),
        }
    return {
        "artifact_type": "biology_interpretability_map_v1",
        "cohort_count": len(cohort_maps),
        "cohorts": cohort_maps,
        "boundary_note": (
            "Interpretability here means feature-family and graph-module mapping. "
            "It does not yet imply mechanistic molecular causality."
        ),
    }


def write_json_output(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Generate biology interpretability mapping artifact.")
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    args = parser.parse_args()

    artifact = build_artifact()
    write_json_output(args.output_json, artifact)

    print("--- Biology Interpretability Map v1 ---")
    print(f"Cohort Count:                 {artifact['cohort_count']}")
    for cohort_name, report in artifact["cohorts"].items():
        first_axis = report["latent_axes"][0]
        top_features = ", ".join(feature["feature"] for feature in first_axis["top_features"][:3])
        print(
            f"{cohort_name:<12} modules={report['graph_modules']['module_count']:<2} "
            f"pc1={first_axis['explained_variance_ratio']:.3f} top={top_features}"
        )
    print(f"\nSaved Artifact:              {args.output_json}")


if __name__ == "__main__":
    main()
