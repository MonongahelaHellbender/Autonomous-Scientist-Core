import math
from collections import Counter
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
}


def load_biology_datasets():
    cancer = load_breast_cancer()
    diabetes = load_diabetes()
    return {
        "cancer": pd.DataFrame(cancer.data, columns=cancer.feature_names),
        "diabetes": pd.DataFrame(diabetes.data, columns=diabetes.feature_names),
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
    return registry


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
        counts = np.bincount(target.astype(int))
        class_labels = (
            target_names if target_names is not None else [f"class_{i}" for i in range(len(counts))]
        )
        class_counts = {label: int(count) for label, count in zip(class_labels, counts)}
        majority_fraction = float(counts.max() / counts.sum())
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
