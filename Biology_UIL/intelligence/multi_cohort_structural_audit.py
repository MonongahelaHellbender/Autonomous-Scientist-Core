import argparse
import json
from pathlib import Path

from biology_structural_utils import (
    correlation_graph_sweep,
    covariance_structure_summary,
    load_biology_cohort_registry,
    summarize_intrinsic_dimension,
    target_summary,
)

DEFAULT_OUTPUT_JSON = "Biology_UIL/validated/multi_cohort_structural_audit_v1.json"


def build_artifact():
    registry = load_biology_cohort_registry()
    cohort_reports = {}
    for cohort_name, cohort in registry.items():
        frame = cohort["frame"]
        id_summary = summarize_intrinsic_dimension(frame)
        covariance_summary = covariance_structure_summary(frame)
        graph_summary = correlation_graph_sweep(frame)
        cohort_reports[cohort_name] = {
            "display_name": cohort["display_name"],
            "dataset_kind": cohort["dataset_kind"],
            "modality": cohort["modality"],
            "sample_count": frame.shape[0],
            "feature_count": frame.shape[1],
            "raw_feature_count": cohort.get("feature_space", {}).get("raw_feature_count", frame.shape[1]),
            "analysis_feature_count": cohort.get("feature_space", {}).get(
                "analysis_feature_count",
                frame.shape[1],
            ),
            "feature_selection_strategy": cohort.get("feature_space", {}).get(
                "feature_selection_strategy",
                "all_features_retained",
            ),
            "batch_annotation_status": cohort.get("batch_annotation_status", "not_reported"),
            "target_type": cohort["target_type"],
            "target_summary": target_summary(
                cohort["target"],
                cohort["target_type"],
                cohort["target_names"],
            ),
            "domain_note": cohort["domain_note"],
            "confounder_notes": cohort["confounder_notes"],
            "dimension_mean": id_summary["dimension_mean"],
            "dimension_ci95": id_summary["resample_ci95"],
            "dimension_k_cv": id_summary["k_cv"],
            "dimension_resample_cv": id_summary["resample_cv"],
            "normalized_effective_rank": covariance_summary["normalized_effective_rank"],
            "top3_variance_fraction": covariance_summary["top3_variance_fraction"],
            "median_absolute_correlation": covariance_summary["median_absolute_correlation"],
            "best_topology_threshold": graph_summary["best_threshold"],
            "topology_support_thresholds": graph_summary["support_thresholds"],
            "topology_weak_support_thresholds": graph_summary["weak_support_thresholds"],
            "largest_component_fraction": graph_summary["best_record"]["largest_component_fraction"],
        }

    cohort_names = sorted(cohort_reports)
    dimension_values = [cohort_reports[name]["dimension_mean"] for name in cohort_names]
    rank_values = [cohort_reports[name]["normalized_effective_rank"] for name in cohort_names]
    return {
        "artifact_type": "multi_cohort_structural_audit_v1",
        "cohort_count": len(cohort_reports),
        "cohorts": cohort_reports,
        "cross_cohort_summary": {
            "cohorts": cohort_names,
            "dimension_range": [min(dimension_values), max(dimension_values)],
            "normalized_effective_rank_range": [min(rank_values), max(rank_values)],
            "low_dimensional_cohorts": [
                name
                for name in cohort_names
                if cohort_reports[name]["dimension_mean"] <= min(10.0, 0.75 * cohort_reports[name]["feature_count"])
            ],
        },
        "boundary_note": (
            "This is a broad biology benchmark audit rather than a pure genetics panel. "
            "It is meant to widen cohort coverage without pretending that all cohort "
            "modalities share the same biological semantics."
        ),
    }


def write_json_output(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Generate a multi-cohort structural biology audit.")
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    args = parser.parse_args()

    artifact = build_artifact()
    write_json_output(args.output_json, artifact)

    print("--- UIL Multi-Cohort Structural Audit v1 ---")
    print(f"Cohort Count:                 {artifact['cohort_count']}")
    print(
        "Dimension Range:              "
        f"{artifact['cross_cohort_summary']['dimension_range'][0]:.3f} - "
        f"{artifact['cross_cohort_summary']['dimension_range'][1]:.3f}"
    )
    print(
        "Effective-Rank Range:         "
        f"{artifact['cross_cohort_summary']['normalized_effective_rank_range'][0]:.3f} - "
        f"{artifact['cross_cohort_summary']['normalized_effective_rank_range'][1]:.3f}"
    )
    print("\nCohort                    Dim Mean  Rank    Topology")
    print("-" * 72)
    for cohort_name, report in artifact["cohorts"].items():
        topology_note = (
            "strong"
            if report["topology_support_thresholds"]
            else "weak"
            if report["topology_weak_support_thresholds"]
            else "none"
        )
        print(
            f"{cohort_name:<24}{report['dimension_mean']:<10.3f}"
            f"{report['normalized_effective_rank']:<8.3f}{topology_note}"
        )
    print(f"\nSaved Artifact:              {args.output_json}")


if __name__ == "__main__":
    main()
