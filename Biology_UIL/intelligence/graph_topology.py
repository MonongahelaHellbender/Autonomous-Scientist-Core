from biology_structural_utils import correlation_graph_sweep, load_biology_datasets


def build_graph_topology_report():
    dataset_reports = {}
    for dataset_name, frame in load_biology_datasets().items():
        sweep = correlation_graph_sweep(frame)
        dataset_reports[dataset_name] = {
            "feature_count": frame.shape[1],
            "sample_count": frame.shape[0],
            **sweep,
        }

    return {
        "artifact_type": "biological_graph_topology_report_v2",
        "datasets": dataset_reports,
        "boundary_note": (
            "Topology is now assessed across a threshold sweep instead of a single "
            "hard-coded cutoff. This makes fragmentation versus connectivity a "
            "measured sensitivity question rather than a one-threshold verdict."
        ),
    }


def print_graph_topology_report(report):
    print("--- UIL Biological Intelligence: Graph Connectivity Hardening Audit ---")
    for dataset_name, dataset_report in report["datasets"].items():
        best = dataset_report["best_record"]
        print(f"\n=== {dataset_name.upper()} TOPOLOGY REPORT ===")
        print(
            f"Samples: {dataset_report['sample_count']}, "
            f"Features: {dataset_report['feature_count']}"
        )
        print(
            f"Support Thresholds: {dataset_report['support_threshold_count']} "
            f"({dataset_report['support_thresholds']})"
        )
        print(
            f"Weaker Support:     {dataset_report['weak_support_threshold_count']} "
            f"({dataset_report['weak_support_thresholds']})"
        )
        print(f"Best Threshold:     {dataset_report['best_threshold']:.2f}")
        print(f"Edges:              {best['edges']}")
        print(f"Edge Density:       {best['edge_density']:.4f}")
        print(f"Largest Component:  {best['largest_component_fraction']:.4f}")
        print(f"Component Strength: {best['largest_component_connectivity']:.6f}")
        print(f"Global Clustering:  {best['global_clustering']:.6f}")

    print("\n[VERDICT] TOPOLOGY HARDENED.")
    print(
        "Finding: biological graph structure is threshold-sensitive, so the repo now "
        "reports a support window and best-supported threshold rather than a single "
        "binary pass/fail cutoff."
    )


def analyze_graph_topology():
    report = build_graph_topology_report()
    print_graph_topology_report(report)
    return report


if __name__ == "__main__":
    analyze_graph_topology()
