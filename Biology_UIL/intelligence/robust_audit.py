from biology_structural_utils import load_biology_datasets, structural_stability_profile


def build_robust_audit():
    dataset_reports = {}
    for dataset_name, frame in load_biology_datasets().items():
        dataset_reports[dataset_name] = structural_stability_profile(frame)

    max_dimension_cv = max(
        report["dimension_mean_resample_cv"] for report in dataset_reports.values()
    )
    max_rank_cv = max(
        report["effective_rank_resample_cv"] for report in dataset_reports.values()
    )
    max_threshold_std = max(
        report["best_threshold_resample_std"] for report in dataset_reports.values()
    )
    return {
        "artifact_type": "robust_biological_audit_v2",
        "datasets": dataset_reports,
        "max_dimension_resample_cv": max_dimension_cv,
        "max_effective_rank_resample_cv": max_rank_cv,
        "max_best_threshold_resample_std": max_threshold_std,
        "boundary_note": (
            "Robustness is now checked with resample stability of structural metrics, "
            "not with mean-based ratios that can explode on centered features."
        ),
    }


def print_robust_audit(report):
    print("--- UIL Quality Control: Robust Biological Audit ---")
    for dataset_name, dataset_report in report["datasets"].items():
        print(f"\n=== {dataset_name.upper()} ROBUSTNESS SUMMARY ===")
        print(
            "Resample CV (dimension mean):    "
            f"{dataset_report['dimension_mean_resample_cv']:.4f}"
        )
        print(
            "Resample CV (effective rank):    "
            f"{dataset_report['effective_rank_resample_cv']:.4f}"
        )
        print(
            "Resample CV (median |corr|):     "
            f"{dataset_report['median_correlation_resample_cv']:.4f}"
        )
        print(
            "Best-threshold mean +/- std:     "
            f"{dataset_report['best_threshold_resample_mean']:.3f} +/- "
            f"{dataset_report['best_threshold_resample_std']:.3f}"
        )
        print(
            "Support-threshold mean count:    "
            f"{dataset_report['support_threshold_resample_mean']:.2f}"
        )

    print(f"\nMax Dimension Resample CV:        {report['max_dimension_resample_cv']:.4f}")
    print(f"Max Effective-Rank Resample CV:   {report['max_effective_rank_resample_cv']:.4f}")
    print(f"Max Best-Threshold Std:           {report['max_best_threshold_resample_std']:.4f}")

    if (
        report["max_dimension_resample_cv"] < 0.15
        and report["max_effective_rank_resample_cv"] < 0.15
        and report["max_best_threshold_resample_std"] < 0.10
    ):
        print("\n[VERDICT] ROBUST STRUCTURAL SIGNAL DETECTED.")
    else:
        print("\n[VERDICT] STRUCTURAL SIGNAL REMAINS THRESHOLD-SENSITIVE.")


def run_robust_audit():
    report = build_robust_audit()
    print_robust_audit(report)
    return report


if __name__ == "__main__":
    run_robust_audit()
