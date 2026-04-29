import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BIOLOGY_ROOT = REPO_ROOT / "Biology_UIL"

PYTHON_FILES = [
    "Biology_UIL/intelligence/biology_structural_utils.py",
    "Biology_UIL/intelligence/graph_topology.py",
    "Biology_UIL/intelligence/cross_dataset_audit.py",
    "Biology_UIL/intelligence/robust_audit.py",
    "Biology_UIL/intelligence/multi_cohort_structural_audit.py",
    "Biology_UIL/intelligence/biology_interpretability_map.py",
    "Biology_UIL/intelligence/genomic_stability.py",
    "Biology_UIL/validated/intrinsic_bottleneck.py",
    "Biology_UIL/validated/real_genetics.py",
]

JSON_FILES = [
    "Biology_UIL/validated/multi_cohort_structural_audit_v1.json",
    "Biology_UIL/validated/biology_interpretability_map_v1.json",
]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def load_json(path):
    return json.loads((REPO_ROOT / path).read_text())


def run_py_compile():
    cmd = [sys.executable, "-m", "py_compile", *[str(REPO_ROOT / path) for path in PYTHON_FILES]]
    subprocess.run(cmd, check=True)


def main():
    run_py_compile()

    graph_topology = load_module(
        "graph_topology",
        BIOLOGY_ROOT / "intelligence" / "graph_topology.py",
    )
    cross_dataset_audit = load_module(
        "cross_dataset_audit",
        BIOLOGY_ROOT / "intelligence" / "cross_dataset_audit.py",
    )
    robust_audit = load_module(
        "robust_audit",
        BIOLOGY_ROOT / "intelligence" / "robust_audit.py",
    )
    multi_cohort_structural_audit = load_module(
        "multi_cohort_structural_audit",
        BIOLOGY_ROOT / "intelligence" / "multi_cohort_structural_audit.py",
    )
    biology_interpretability_map = load_module(
        "biology_interpretability_map",
        BIOLOGY_ROOT / "intelligence" / "biology_interpretability_map.py",
    )
    intrinsic_bottleneck = load_module(
        "intrinsic_bottleneck",
        BIOLOGY_ROOT / "validated" / "intrinsic_bottleneck.py",
    )

    for path in JSON_FILES:
        load_json(path)

    graph_report = graph_topology.build_graph_topology_report()
    cross_report = cross_dataset_audit.build_cross_dataset_report()
    robust_report = robust_audit.build_robust_audit()
    multi_cohort_report = multi_cohort_structural_audit.build_artifact()
    interpretability_report = biology_interpretability_map.build_artifact()
    id_report = intrinsic_bottleneck.build_id_audit()

    assert_true(set(graph_report["datasets"]) == {"cancer", "diabetes"}, "Graph report lost a dataset")
    assert_true(set(cross_report["datasets"]) == {"cancer", "diabetes"}, "Cross-dataset report lost a dataset")
    assert_true(set(id_report["datasets"]) == {"cancer", "diabetes"}, "ID report lost a dataset")
    assert_true(multi_cohort_report["cohort_count"] >= 4, "Multi-cohort audit lost cohort coverage")
    assert_true(interpretability_report["cohort_count"] >= 4, "Interpretability map lost cohort coverage")

    for dataset_name, dataset_report in cross_report["datasets"].items():
        assert_true(
            0.0 < dataset_report["normalized_effective_rank"] <= 1.0,
            f"{dataset_name} effective rank out of range",
        )
        assert_true(
            0.0 < dataset_report["median_absolute_correlation"] < 1.0,
            f"{dataset_name} median correlation invalid",
        )
        assert_true(
            1.0 < dataset_report["dimension_mean"] < 10.0,
            f"{dataset_name} dimension estimate out of expected range",
        )

    for dataset_name, dataset_report in graph_report["datasets"].items():
        assert_true(
            dataset_report["weak_support_threshold_count"] >= 1,
            f"{dataset_name} lost all workable topology thresholds",
        )
        assert_true(
            dataset_report["best_record"]["largest_component_fraction"] >= 0.6,
            f"{dataset_name} topology became too fragmented",
        )

    for dataset_name, dataset_report in robust_report["datasets"].items():
        assert_true(
            dataset_report["dimension_mean_resample_cv"] < 0.20,
            f"{dataset_name} dimension resample became unstable",
        )
        assert_true(
            dataset_report["effective_rank_resample_cv"] < 0.20,
            f"{dataset_name} effective-rank resample became unstable",
        )

    for cohort_name, cohort_report in multi_cohort_report["cohorts"].items():
        assert_true(
            cohort_report["dimension_resample_cv"] < 0.25,
            f"{cohort_name} multi-cohort dimension became unstable",
        )
        assert_true(
            len(cohort_report["confounder_notes"]) >= 1,
            f"{cohort_name} lost confounder notes",
        )

    for cohort_name, cohort_report in interpretability_report["cohorts"].items():
        assert_true(
            len(cohort_report["latent_axes"]) >= 1,
            f"{cohort_name} lost latent-axis interpretation",
        )
        assert_true(
            cohort_report["graph_modules"]["module_count"] >= 1,
            f"{cohort_name} lost graph modules",
        )

    print("biology lane regression check: PASS")
    print(f"cross-dataset dimension gap: {cross_report['dimension_gap']:.4f}")
    print(f"max biology dimension resample cv: {robust_report['max_dimension_resample_cv']:.4f}")


if __name__ == "__main__":
    main()
