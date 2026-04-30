import math
from collections import Counter
from pathlib import Path
from typing import Iterable

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer, load_diabetes, load_iris, load_wine
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

DEFAULT_K_VALUES = (5, 10, 15, 20)
DEFAULT_BOOTSTRAP_TRIALS = 100
DEFAULT_GRAPH_THRESHOLDS = tuple(np.round(np.arange(0.45, 0.91, 0.05), 2))
DEFAULT_SEED = 20260429
DEFAULT_RESAMPLE_FRACTION = 0.8
DEFAULT_NULL_TRIALS = 50
DEFAULT_OMICS_FEATURE_CAP = 150
REPO_ROOT = Path(__file__).resolve().parents[2]
OMICS_CACHE_DIR = REPO_ROOT / "Biology_UIL" / "data" / "external_omics_cache"

COHORT_METADATA = {
    "cancer": {
        "display_name": "Breast Cancer Wisconsin (Diagnostic)",
        "modality": "oncology biomarker panel",
        "target_type": "classification",
        "dataset_kind": "biomedical benchmark",
        "domain_note": (
            "Morphometric / texture-style tumor descriptors rather than direct "
            "transcriptomic counts."
        ),
        "confounder_notes": [
            "No explicit batch covariates are provided in the sklearn bundle.",
            "Feature families include mean, error, and worst summaries, which can inflate local correlation structure.",
            "Class balance should be checked before over-reading global topology as biology rather than case mix.",
        ],
    },
    "diabetes": {
        "display_name": "Diabetes Disease Progression",
        "modality": "metabolic clinical chemistry",
        "target_type": "regression",
        "dataset_kind": "biomedical benchmark",
        "domain_note": (
            "Standardized clinical covariates plus serum measurements; good for "
            "structure checks, but not a genomics cohort."
        ),
        "confounder_notes": [
            "The sklearn benchmark is centered and standardized, so mean-based ratio metrics are invalid.",
            "No explicit medication, fasting-state, or batch covariates are bundled.",
            "The target is continuous progression, not discrete disease subtype.",
        ],
    },
    "wine": {
        "display_name": "Wine Recognition",
        "modality": "biochemical assay panel",
        "target_type": "classification",
        "dataset_kind": "biological benchmark",
        "domain_note": (
            "A chemistry-rich cohort that broadens the structural lane beyond disease-only datasets."
        ),
        "confounder_notes": [
            "Class structure partly reflects cultivar identity rather than pathology.",
            "Measured chemistry may exaggerate coherent modules because assays are compositionally linked.",
        ],
    },
    "iris": {
        "display_name": "Iris Morphology",
        "modality": "organismal morphology",
        "target_type": "classification",
        "dataset_kind": "biological benchmark",
        "domain_note": (
            "A small morphology cohort that stress-tests whether low-dimensional structure is robust outside clinical datasets."
        ),
        "confounder_notes": [
            "Small feature count makes graph topology especially threshold-sensitive.",
            "Species labels can dominate latent structure in a way that would not transfer to genomics directly.",
        ],
    },
    "nci60": {
        "display_name": "NCI60 Gene Expression",
        "modality": "gene expression",
        "target_type": "classification",
        "dataset_kind": "true omics cohort",
        "domain_note": (
            "A high-dimensional cancer cell-line expression panel. The upstream bundle uses "
            "anonymous probe-style feature names, so structural testing is stronger here than "
            "gene-level interpretability."
        ),
        "confounder_notes": [
            "Small-n / large-p geometry means any topology claim must be interpreted as a screened feature-space result, not a full-transcriptome graph proof.",
            "The public ISLR bundle does not ship explicit batch covariates or probe annotation in the fetched frame.",
            "Cell-line lineage labels can dominate latent structure, so this cohort is best used as a structure stress test rather than as a clean patient-population model.",
        ],
    },
    "tissue_gene_expression": {
        "display_name": "DSLabs Tissue Gene Expression",
        "modality": "gene expression",
        "target_type": "classification",
        "dataset_kind": "true omics cohort",
        "domain_note": (
            "A tissue-level expression cohort with named genes, useful for widening the registry "
            "into real omics while retaining a workable interpretability surface."
        ),
        "confounder_notes": [
            "Tissue identity is expected to dominate the first latent axes, so this tests structured biology more than subtle within-tissue state shifts.",
            "No explicit batch variable is bundled in the cached frame, so any batch-effect claim remains out of scope.",
            "The analysis frame is variance-filtered for tractable graph work; results should be read as a high-variance gene subset audit.",
        ],
    },
}


def load_biology_datasets():
    cancer = load_breast_cancer()
    diabetes = load_diabetes()
    return {
        "cancer": pd.DataFrame(cancer.data, columns=cancer.feature_names),
        "diabetes": pd.DataFrame(diabetes.data, columns=diabetes.feature_names),
    }


def load_cached_rdataset(dataset_name: str, package_name: str, cache_stem: str) -> pd.DataFrame:
    OMICS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = OMICS_CACHE_DIR / f"{cache_stem}.csv.gz"
    if cache_path.exists():
        return pd.read_csv(cache_path, index_col=0)

    from statsmodels.datasets import get_rdataset

    frame = get_rdataset(dataset_name, package_name).data.copy()
    frame.to_csv(cache_path, compression="gzip")
    return frame


def variance_screen_frame(
    frame: pd.DataFrame,
    feature_cap: int = DEFAULT_OMICS_FEATURE_CAP,
) -> tuple[pd.DataFrame, dict]:
    if frame.shape[1] <= feature_cap:
        return frame.copy(), {
            "raw_feature_count": int(frame.shape[1]),
            "analysis_feature_count": int(frame.shape[1]),
            "feature_selection_strategy": "all_features_retained",
        }

    variances = frame.var(ddof=0).sort_values(ascending=False)
    selected_features = list(variances.head(feature_cap).index)
    screened = frame.loc[:, selected_features].copy()
    return screened, {
        "raw_feature_count": int(frame.shape[1]),
        "analysis_feature_count": int(screened.shape[1]),
        "feature_selection_strategy": f"top_{feature_cap}_variance_features",
    }


def load_cached_omics_registry_entry(
    cohort_name: str,
    dataset_name: str,
    package_name: str,
    *,
    target_column: str,
) -> dict:
    raw = load_cached_rdataset(dataset_name, package_name, cache_stem=cohort_name)
    target = raw[target_column].astype("string").to_numpy()
    frame = raw.drop(columns=[target_column]).copy()
    frame.columns = [
        column[2:] if isinstance(column, str) and column.startswith("x.") else column
        for column in frame.columns
    ]
    analysis_frame, feature_space = variance_screen_frame(frame)
    return {
        "name": cohort_name,
        "frame": analysis_frame,
        "target": target,
        "target_names": sorted(pd.Series(target).dropna().astype(str).unique().tolist()),
        "source_package": package_name,
        "source_dataset": dataset_name,
        "batch_annotation_status": "not_provided_in_cached_source",
        "feature_space": feature_space,
        **COHORT_METADATA[cohort_name],
    }


def load_biology_cohort_registry():
    loaders = {
        "cancer": load_breast_cancer,
        "diabetes": load_diabetes,
        "wine": load_wine,
        "iris": load_iris,
    }

    registry = {}
    for name, loader in loaders.items():
        bundle = loader()
        frame = pd.DataFrame(bundle.data, columns=bundle.feature_names)
        target = getattr(bundle, "target", None)
        target_names = getattr(bundle, "target_names", None)
        registry[name] = {
            "name": name,
            "frame": frame,
            "target": target,
            "target_names": list(target_names) if target_names is not None else None,
            **COHORT_METADATA[name],
        }

    registry["nci60"] = load_cached_omics_registry_entry(
        "nci60",
        "NCI60",
        "ISLR",
        target_column="labs",
    )
    registry["tissue_gene_expression"] = load_cached_omics_registry_entry(
        "tissue_gene_expression",
        "tissue_gene_expression",
        "dslabs",
        target_column="y",
    )
    return registry


def shuffled_feature_null_frame(frame, rng):
    shuffled = {
        column: rng.permutation(frame[column].to_numpy())
        for column in frame.columns
    }
    return pd.DataFrame(shuffled, columns=frame.columns)


def standardize_frame(frame):
    scaler = StandardScaler()
    return scaler.fit_transform(frame.to_numpy())


def estimate_intrinsic_dimension(array, k=5):
    if k < 2 or k >= len(array):
        raise ValueError(f"k must be between 2 and {len(array) - 1}, got {k}")

    neigh = NearestNeighbors(n_neighbors=k + 1).fit(array)
    distances, _ = neigh.kneighbors(array)
    dist_k = np.maximum(distances[:, k], 1e-12)
    dist_others = np.maximum(distances[:, 1:k], 1e-12)
    inv_id = np.mean(np.log(dist_k[:, None] / dist_others))
    if not np.isfinite(inv_id) or inv_id <= 0:
        raise ValueError("Intrinsic-dimension estimate became non-finite")
    return float(1.0 / inv_id)


def intrinsic_dimension_estimates(frame, k_values=DEFAULT_K_VALUES):
    array = standardize_frame(frame)
    estimates = {}
    for k in k_values:
        effective_k = min(k, len(array) - 1)
        estimates[effective_k] = estimate_intrinsic_dimension(array, k=effective_k)
    return estimates


def summarize_intrinsic_dimension(
    frame,
    k_values=DEFAULT_K_VALUES,
    num_bootstrap=DEFAULT_BOOTSTRAP_TRIALS,
    seed=DEFAULT_SEED,
    resample_fraction=DEFAULT_RESAMPLE_FRACTION,
):
    full_estimates = intrinsic_dimension_estimates(frame, k_values=k_values)
    full_mean = float(np.mean(list(full_estimates.values())))
    full_cv = float(np.std(list(full_estimates.values())) / full_mean)

    rng = np.random.default_rng(seed)
    resample_means = []
    resample_by_k = {k: [] for k in full_estimates}
    sample_size = max(max(full_estimates) + 5, int(len(frame) * resample_fraction))
    sample_size = min(sample_size, len(frame))
    for _ in range(num_bootstrap):
        chosen = rng.choice(len(frame), size=sample_size, replace=False)
        sample = frame.iloc[chosen]
        sample_estimates = intrinsic_dimension_estimates(sample, k_values=tuple(full_estimates))
        resample_means.append(float(np.mean(list(sample_estimates.values()))))
        for k, value in sample_estimates.items():
            resample_by_k[k].append(value)

    resample_ci = np.percentile(resample_means, [2.5, 97.5]).tolist()
    return {
        "k_estimates": {str(k): value for k, value in full_estimates.items()},
        "k_cv": full_cv,
        "dimension_mean": full_mean,
        "resample_mean": float(np.mean(resample_means)),
        "resample_cv": float(np.std(resample_means) / np.mean(resample_means)),
        "resample_ci95": [float(value) for value in resample_ci],
        "per_k_resample_mean": {
            str(k): float(np.mean(samples)) for k, samples in resample_by_k.items()
        },
        "resample_fraction": resample_fraction,
    }


def covariance_structure_summary(frame):
    array = standardize_frame(frame)
    corr = np.corrcoef(array, rowvar=False)
    eigvals = np.clip(np.linalg.eigvalsh(corr), 0.0, None)
    eigvals = eigvals[eigvals > 1e-12]
    weights = eigvals / eigvals.sum()
    spectral_entropy = -float(np.sum(weights * np.log(weights)))
    effective_rank = float(math.exp(spectral_entropy))
    off_diagonal = np.abs(corr[np.triu_indices_from(corr, k=1)])
    top3_fraction = float(np.sort(eigvals)[-3:].sum() / eigvals.sum())
    return {
        "effective_rank": effective_rank,
        "normalized_effective_rank": effective_rank / frame.shape[1],
        "top3_variance_fraction": top3_fraction,
        "median_absolute_correlation": float(np.median(off_diagonal)),
    }


def correlation_graph_sweep(frame, thresholds=DEFAULT_GRAPH_THRESHOLDS):
    corr_matrix = frame.corr().abs().to_numpy(copy=True)
    np.fill_diagonal(corr_matrix, 0.0)
    corr_frame = pd.DataFrame(corr_matrix, index=frame.columns, columns=frame.columns)
    records = []

    for threshold in thresholds:
        adj_matrix = (corr_frame >= threshold).astype(int)
        G = nx.from_pandas_adjacency(adj_matrix)
        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()
        edge_density = float(nx.density(G)) if num_nodes > 1 else 0.0
        clustering = float(nx.average_clustering(G)) if num_edges else 0.0

        if num_edges:
            components = list(nx.connected_components(G))
            largest_nodes = max(components, key=len)
            largest_component = G.subgraph(largest_nodes).copy()
            largest_fraction = len(largest_nodes) / num_nodes
            if largest_component.number_of_nodes() > 1:
                largest_connectivity = float(nx.algebraic_connectivity(largest_component))
            else:
                largest_connectivity = 0.0
        else:
            largest_fraction = 1.0 / num_nodes
            largest_connectivity = 0.0

        records.append(
            {
                "threshold": float(threshold),
                "edges": num_edges,
                "edge_density": edge_density,
                "largest_component_fraction": float(largest_fraction),
                "largest_component_connectivity": largest_connectivity,
                "global_clustering": clustering,
            }
        )

    supported = [
        record
        for record in records
        if 0.05 <= record["edge_density"] <= 0.35
        and record["largest_component_fraction"] >= 0.8
    ]
    weakly_supported = [
        record
        for record in records
        if 0.05 <= record["edge_density"] <= 0.35
        and record["largest_component_fraction"] >= 0.6
    ]
    selected_pool = supported or weakly_supported or records
    best_record = max(
        selected_pool,
        key=lambda row: (
            row["largest_component_fraction"],
            row["largest_component_connectivity"],
            -abs(row["edge_density"] - 0.15),
        ),
    )

    return {
        "support_threshold_count": len(supported),
        "support_thresholds": [row["threshold"] for row in supported],
        "weak_support_threshold_count": len(weakly_supported),
        "weak_support_thresholds": [row["threshold"] for row in weakly_supported],
        "best_threshold": best_record["threshold"],
        "best_record": best_record,
        "threshold_records": records,
    }


def empirical_one_sided_pvalue(observed, null_values, direction):
    if direction not in {"low", "high"}:
        raise ValueError(f"Unknown direction: {direction}")
    if direction == "low":
        extreme = sum(value <= observed for value in null_values)
    else:
        extreme = sum(value >= observed for value in null_values)
    return float((extreme + 1) / (len(null_values) + 1))


def significant_quantile_win(observed, threshold, pvalue, direction, alpha=0.05):
    if direction not in {"low", "high"}:
        raise ValueError(f"Unknown direction: {direction}")
    if direction == "low":
        return observed < threshold and pvalue <= alpha
    return observed > threshold and pvalue <= alpha


def structural_null_audit(
    frame,
    *,
    seed=DEFAULT_SEED,
    num_trials=DEFAULT_NULL_TRIALS,
):
    observed_dimension = summarize_intrinsic_dimension(frame)
    observed_covariance = covariance_structure_summary(frame)
    observed_graph = correlation_graph_sweep(frame)

    rng = np.random.default_rng(seed)
    null_dimension_means = []
    null_effective_ranks = []
    null_median_correlations = []
    null_support_counts = []
    null_largest_components = []

    for _ in range(num_trials):
        null_frame = shuffled_feature_null_frame(frame, rng)
        null_dimension = intrinsic_dimension_estimates(null_frame)
        null_covariance = covariance_structure_summary(null_frame)
        null_graph = correlation_graph_sweep(null_frame)

        null_dimension_means.append(float(np.mean(list(null_dimension.values()))))
        null_effective_ranks.append(float(null_covariance["normalized_effective_rank"]))
        null_median_correlations.append(float(null_covariance["median_absolute_correlation"]))
        null_support_counts.append(int(null_graph["support_threshold_count"]))
        null_largest_components.append(float(null_graph["best_record"]["largest_component_fraction"]))

    summary = {
        "observed": {
            "dimension_mean": float(observed_dimension["dimension_mean"]),
            "normalized_effective_rank": float(observed_covariance["normalized_effective_rank"]),
            "median_absolute_correlation": float(observed_covariance["median_absolute_correlation"]),
            "support_threshold_count": int(observed_graph["support_threshold_count"]),
            "largest_component_fraction": float(observed_graph["best_record"]["largest_component_fraction"]),
        },
        "null_distribution": {
            "dimension_mean": {
                "mean": float(np.mean(null_dimension_means)),
                "q05": float(np.quantile(null_dimension_means, 0.05)),
                "q95": float(np.quantile(null_dimension_means, 0.95)),
            },
            "normalized_effective_rank": {
                "mean": float(np.mean(null_effective_ranks)),
                "q05": float(np.quantile(null_effective_ranks, 0.05)),
                "q95": float(np.quantile(null_effective_ranks, 0.95)),
            },
            "median_absolute_correlation": {
                "mean": float(np.mean(null_median_correlations)),
                "q05": float(np.quantile(null_median_correlations, 0.05)),
                "q95": float(np.quantile(null_median_correlations, 0.95)),
            },
            "support_threshold_count": {
                "mean": float(np.mean(null_support_counts)),
                "q05": float(np.quantile(null_support_counts, 0.05)),
                "q95": float(np.quantile(null_support_counts, 0.95)),
            },
            "largest_component_fraction": {
                "mean": float(np.mean(null_largest_components)),
                "q05": float(np.quantile(null_largest_components, 0.05)),
                "q95": float(np.quantile(null_largest_components, 0.95)),
            },
        },
        "empirical_pvalues": {
            "dimension_mean_low": empirical_one_sided_pvalue(
                observed_dimension["dimension_mean"],
                null_dimension_means,
                "low",
            ),
            "normalized_effective_rank_low": empirical_one_sided_pvalue(
                observed_covariance["normalized_effective_rank"],
                null_effective_ranks,
                "low",
            ),
            "median_absolute_correlation_high": empirical_one_sided_pvalue(
                observed_covariance["median_absolute_correlation"],
                null_median_correlations,
                "high",
            ),
            "support_threshold_count_high": empirical_one_sided_pvalue(
                observed_graph["support_threshold_count"],
                null_support_counts,
                "high",
            ),
            "largest_component_fraction_high": empirical_one_sided_pvalue(
                observed_graph["best_record"]["largest_component_fraction"],
                null_largest_components,
                "high",
            ),
        },
        "null_model": (
            "Feature-wise permutation preserves each feature's marginal distribution "
            "while breaking cross-feature dependence."
        ),
        "num_trials": num_trials,
        "seed": seed,
    }

    summary["null_wins"] = {
        "lower_dimension_than_null_q05": significant_quantile_win(
            summary["observed"]["dimension_mean"],
            summary["null_distribution"]["dimension_mean"]["q05"],
            summary["empirical_pvalues"]["dimension_mean_low"],
            "low",
        ),
        "lower_effective_rank_than_null_q05": significant_quantile_win(
            summary["observed"]["normalized_effective_rank"],
            summary["null_distribution"]["normalized_effective_rank"]["q05"],
            summary["empirical_pvalues"]["normalized_effective_rank_low"],
            "low",
        ),
        "higher_median_correlation_than_null_q95": significant_quantile_win(
            summary["observed"]["median_absolute_correlation"],
            summary["null_distribution"]["median_absolute_correlation"]["q95"],
            summary["empirical_pvalues"]["median_absolute_correlation_high"],
            "high",
        ),
        "higher_support_count_than_null_q95": significant_quantile_win(
            summary["observed"]["support_threshold_count"],
            summary["null_distribution"]["support_threshold_count"]["q95"],
            summary["empirical_pvalues"]["support_threshold_count_high"],
            "high",
        ),
        "higher_largest_component_than_null_q95": significant_quantile_win(
            summary["observed"]["largest_component_fraction"],
            summary["null_distribution"]["largest_component_fraction"]["q95"],
            summary["empirical_pvalues"]["largest_component_fraction_high"],
            "high",
        ),
    }

    return summary


def structural_stability_profile(
    frame,
    k_values=DEFAULT_K_VALUES,
    num_bootstrap=DEFAULT_BOOTSTRAP_TRIALS,
    seed=DEFAULT_SEED,
    resample_fraction=DEFAULT_RESAMPLE_FRACTION,
):
    baseline_id = intrinsic_dimension_estimates(frame, k_values=k_values)
    baseline_structure = covariance_structure_summary(frame)
    baseline_graph = correlation_graph_sweep(frame)

    rng = np.random.default_rng(seed)
    id_means = []
    effective_ranks = []
    median_correlations = []
    best_thresholds = []
    support_counts = []
    sample_size = max(max(baseline_id) + 5, int(len(frame) * resample_fraction))
    sample_size = min(sample_size, len(frame))
    for _ in range(num_bootstrap):
        chosen = rng.choice(len(frame), size=sample_size, replace=False)
        sample = frame.iloc[chosen]
        sample_id = intrinsic_dimension_estimates(sample, k_values=tuple(baseline_id))
        sample_structure = covariance_structure_summary(sample)
        sample_graph = correlation_graph_sweep(sample)

        id_means.append(float(np.mean(list(sample_id.values()))))
        effective_ranks.append(sample_structure["normalized_effective_rank"])
        median_correlations.append(sample_structure["median_absolute_correlation"])
        best_thresholds.append(sample_graph["best_threshold"])
        support_counts.append(sample_graph["support_threshold_count"])

    return {
        "baseline_dimension_mean": float(np.mean(list(baseline_id.values()))),
        "baseline_dimension_cv": float(
            np.std(list(baseline_id.values())) / np.mean(list(baseline_id.values()))
        ),
        "baseline_normalized_effective_rank": baseline_structure["normalized_effective_rank"],
        "baseline_median_absolute_correlation": baseline_structure[
            "median_absolute_correlation"
        ],
        "baseline_best_threshold": baseline_graph["best_threshold"],
        "dimension_mean_resample_cv": float(np.std(id_means) / np.mean(id_means)),
        "effective_rank_resample_cv": float(np.std(effective_ranks) / np.mean(effective_ranks)),
        "median_correlation_resample_cv": float(
            np.std(median_correlations) / np.mean(median_correlations)
        ),
        "best_threshold_resample_mean": float(np.mean(best_thresholds)),
        "best_threshold_resample_std": float(np.std(best_thresholds)),
        "support_threshold_resample_mean": float(np.mean(support_counts)),
        "resample_fraction": resample_fraction,
    }


def finite_metrics(metrics):
    return all(np.isfinite(value) for value in metrics if isinstance(value, (int, float)))


def rowwise_metric_values(report):
    values = []
    for value in report.values():
        if isinstance(value, dict):
            values.extend(rowwise_metric_values(value))
        elif isinstance(value, list):
            values.extend(
                item for item in value if isinstance(item, (int, float, np.floating, np.integer))
            )
        elif isinstance(value, (int, float, np.floating, np.integer)):
            values.append(float(value))
    return values


def target_summary(target, target_type, target_names=None):
    if target is None:
        return {"target_present": False}

    target = np.asarray(target)
    if target_type == "classification":
        series = pd.Series(target)
        if pd.api.types.is_numeric_dtype(series) and target_names is not None:
            counts = np.bincount(series.astype(int))
            class_labels = list(target_names)
            class_counts = {label: int(count) for label, count in zip(class_labels, counts)}
            majority_fraction = float(counts.max() / counts.sum())
        else:
            counts = series.astype("string").fillna("NA").value_counts()
            class_counts = {str(label): int(count) for label, count in counts.items()}
            majority_fraction = float(counts.iloc[0] / counts.sum())
        return {
            "target_present": True,
            "class_counts": class_counts,
            "majority_fraction": majority_fraction,
        }

    return {
        "target_present": True,
        "target_mean": float(np.mean(target)),
        "target_std": float(np.std(target)),
        "target_min": float(np.min(target)),
        "target_max": float(np.max(target)),
    }


def semantic_feature_theme(dataset_name, feature_name):
    name = feature_name.lower()
    if dataset_name == "cancer":
        if any(token in name for token in ("radius", "perimeter", "area")):
            return "size"
        if "texture" in name:
            return "texture"
        if any(token in name for token in ("smoothness", "compactness", "concavity", "concave")):
            return "surface_irregularity"
        if any(token in name for token in ("symmetry", "fractal")):
            return "symmetry_roughness"
        if "error" in name:
            return "uncertainty_scale"
        if "worst" in name:
            return "extreme_tail"
    if dataset_name == "diabetes":
        mapping = {
            "age": "demographic",
            "sex": "demographic",
            "bmi": "body_composition",
            "bp": "blood_pressure",
            "s1": "serum_lipid_total",
            "s2": "serum_ldl_like",
            "s3": "serum_hdl_like",
            "s4": "serum_ratio_like",
            "s5": "serum_triglyceride_like",
            "s6": "serum_glucose_like",
        }
        return mapping.get(name, "metabolic")
    if dataset_name == "wine":
        if "phenol" in name or "flav" in name or "proanthocyanins" in name:
            return "polyphenol_chemistry"
        if "acid" in name or "ash" in name:
            return "acidity_mineral_balance"
        if "color" in name or "hue" in name or "od280" in name:
            return "optical_profile"
        if "alcohol" in name or "proline" in name or "magnesium" in name:
            return "bulk_composition"
    if dataset_name == "iris":
        if "sepal" in name:
            return "sepal_morphology"
        if "petal" in name:
            return "petal_morphology"
    if dataset_name in {"nci60", "tissue_gene_expression"}:
        symbol = feature_name.upper().replace("X.", "")
        if symbol.startswith("DATA."):
            return "expression_probe_panel"
        if symbol.startswith(("HOX", "SOX", "MAML", "ZNF")):
            return "developmental_regulation"
        if symbol.startswith(("CYP", "BLVR", "HEMK", "LHPP")):
            return "metabolic_enzyme_activity"
        if symbol.startswith(("LILR", "FAP", "KREMEN")) or "C21ORF" in symbol:
            return "signaling_surface_identity"
        if symbol.startswith(("SEPT", "PER", "GSAP")):
            return "cytoskeletal_or_timing_program"
        return "gene_expression_signal"
    return "general_biological_measurement"


def pca_interpretability_summary(frame, dataset_name, n_components=3, top_k=5):
    array = standardize_frame(frame)
    max_components = min(n_components, frame.shape[1])
    pca = PCA(n_components=max_components)
    pca.fit(array)

    components = []
    feature_names = list(frame.columns)
    for index, (variance_ratio, loading_vector) in enumerate(
        zip(pca.explained_variance_ratio_, pca.components_),
        start=1,
    ):
        top_indices = np.argsort(np.abs(loading_vector))[::-1][:top_k]
        features = []
        for feature_index in top_indices:
            feature_name = feature_names[feature_index]
            loading = float(loading_vector[feature_index])
            features.append(
                {
                    "feature": feature_name,
                    "loading": loading,
                    "abs_loading": abs(loading),
                    "semantic_theme": semantic_feature_theme(dataset_name, feature_name),
                }
            )
        theme_counts = Counter(feature["semantic_theme"] for feature in features)
        components.append(
            {
                "component": f"PC{index}",
                "explained_variance_ratio": float(variance_ratio),
                "top_features": features,
                "dominant_themes": dict(theme_counts),
            }
        )
    return components


def graph_module_summary(frame, dataset_name):
    graph_report = correlation_graph_sweep(frame)
    threshold = graph_report["best_threshold"]
    corr_matrix = frame.corr().abs().to_numpy(copy=True)
    np.fill_diagonal(corr_matrix, 0.0)
    corr_frame = pd.DataFrame(corr_matrix, index=frame.columns, columns=frame.columns)
    graph = nx.from_pandas_adjacency((corr_frame >= threshold).astype(int))

    if graph.number_of_edges() == 0:
        return {
            "best_threshold": threshold,
            "module_count": 0,
            "modules": [],
        }

    communities = list(nx.algorithms.community.greedy_modularity_communities(graph))
    modules = []
    for index, community in enumerate(sorted(communities, key=len, reverse=True), start=1):
        ordered = sorted(community)
        theme_counts = Counter(semantic_feature_theme(dataset_name, feature) for feature in ordered)
        modules.append(
            {
                "module_id": index,
                "size": len(ordered),
                "features": ordered,
                "dominant_themes": dict(theme_counts),
            }
        )
    return {
        "best_threshold": threshold,
        "module_count": len(modules),
        "modules": modules,
    }


def robust_feature_variability(frame):
    median = frame.median()
    iqr = frame.quantile(0.75) - frame.quantile(0.25)
    scale = frame.std(ddof=0).replace(0, np.nan)
    proxy = (iqr / scale).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    ordered = proxy.sort_values()
    return [
        {
            "feature": feature,
            "stability_proxy": float(value),
        }
        for feature, value in ordered.items()
    ]
