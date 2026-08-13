#!/usr/bin/env python3
"""Audit REVERSOME's frozen primary result and foundation benchmark.

This script does not tune or replace the frozen models.  It adds the formal
inference, sensitivity analyses and transparent baseline comparisons required
for manuscript V11.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler, normalize


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name == "analysis" else SCRIPT_DIR
SEED = 20260812
BOOTSTRAP_DRAWS = 20_000
MIN_SENSITIVITY_TEST_N = 50
MIN_SENSITIVITY_CLASSES = 2


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def lineage(cell_type: object) -> str | None:
    name = str(cell_type).lower()
    if any(term in name for term in ["t cell", "t-regulatory", "gamma-delta"]):
        return "T_lymphoid"
    if any(term in name for term in ["b cell", "plasma cell"]):
        return "B_plasma"
    if any(term in name for term in ["macrophage", "monocyte", "myeloid", "dendritic", "neutrophil"]):
        return "myeloid"
    if "mast" in name:
        return "mast"
    if "endothelial" in name:
        return "endothelial"
    if any(term in name for term in ["fibroblast", "stromal", "smooth muscle", "pericyte", "mesenchymal"]):
        return "stromal"
    if any(term in name for term in ["epithelial", "enterocyte", "goblet", "mucous", "foveolar", "secretory", "keratinocyte"]):
        return "epithelial"
    return None


def bootstrap_mean_ci(values: np.ndarray, seed: int = SEED) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(BOOTSTRAP_DRAWS, len(values)), replace=True).mean(axis=1)
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def exact_sign_flip_p(values: np.ndarray) -> float:
    """Exact two-sided randomisation p value for a specimen-level mean."""
    values = np.asarray(values, dtype=float)
    observed = abs(float(values.mean()))
    null = np.fromiter(
        (abs(float(np.mean(values * np.asarray(signs)))) for signs in product((-1.0, 1.0), repeat=len(values))),
        dtype=float,
        count=2 ** len(values),
    )
    return float(np.sum(null >= observed - 1e-15) / len(null))


def paired_audit() -> dict[str, object]:
    data_dir = ROOT / "source_data"
    if not data_dir.exists():
        data_dir = ROOT / "reports"
    folds_path = data_dir / "reversome_v5b_lung_paired_multiome_folds.csv"
    pairs_path = data_dir / "reversome_v5b_lung_paired_multiome_pairs.csv"
    features_path = data_dir / "reversome_v5b_lung_paired_multiome_train_only_features.csv"
    sampled_path = data_dir / "reversome_v5b_lung_paired_multiome_sampled_cells.csv"
    folds = pd.read_csv(folds_path)
    pairs = pd.read_csv(pairs_path)
    features = pd.read_csv(features_path)
    sampled = pd.read_csv(sampled_path)

    folds["retrieval_top1_excess_over_random"] = folds["retrieval_top1"] - folds["random_retrieval_expected"]
    metrics = [
        "paired_minus_permuted_cosine",
        "paired_minus_mean_atac_cosine",
        "relative_mae_gain_vs_mean_atac",
        "retrieval_top1_excess_over_random",
    ]
    inference_rows = []
    for i, metric in enumerate(metrics):
        values = folds[metric].to_numpy(dtype=float)
        low, high = bootstrap_mean_ci(values, SEED + i)
        inference_rows.append({
            "metric": metric,
            "n_independent_specimens": int(len(values)),
            "effect_estimator": "unweighted mean across held-out specimens",
            "effect": float(values.mean()),
            "median": float(np.median(values)),
            "fold_percentile_2_5": float(np.quantile(values, 0.025)),
            "fold_percentile_97_5": float(np.quantile(values, 0.975)),
            "specimen_bootstrap_ci95_low": low,
            "specimen_bootstrap_ci95_high": high,
            "exact_two_sided_sign_flip_p": exact_sign_flip_p(values),
            "positive_specimen_fraction": float(np.mean(values > 0)),
            "bootstrap_draws": BOOTSTRAP_DRAWS,
            "random_seed": SEED + i,
        })

    train_exclusion = folds.apply(
        lambda row: str(row["heldout_specimen"]) not in str(row["train_specimens"]).split(";"), axis=1
    )
    feature_counts = features.groupby(["heldout_specimen", "modality"]).size().unstack(fill_value=0)
    audit = {
        "heldout_specimen_never_in_training_list": bool(train_exclusion.all()),
        "unique_heldout_specimens": bool(folds["heldout_specimen"].is_unique),
        "pair_rows_unique": bool(pairs["paired_cell_id"].is_unique),
        "sampled_rows_unique": bool(sampled["paired_cell_id"].is_unique),
        "pair_and_sampled_manifests_identical": bool(
            set(pairs["paired_cell_id"].astype(str)) == set(sampled["paired_cell_id"].astype(str))
        ),
        "all_pairs_exact_same_barcode": bool(
            set(pairs["pair_evidence"].astype(str)) == {"same_released_10x_multiome_barcode"}
        ),
        "each_pair_appears_in_its_specimen_holdout_only": bool(
            (pairs["specimen"].astype(str) == pairs["heldout_specimen"].astype(str)).all()
        ),
        "train_only_feature_manifest_complete": bool(
            set(feature_counts.index.astype(str)) == set(folds["heldout_specimen"].astype(str))
            and set(feature_counts.columns.astype(str)) == {"ATAC_100kb_bin", "RNA"}
            and (feature_counts == 64).all().all()
        ),
        "preprocessing_fit_scope": "feature selection, StandardScaler and PCA fitted on training specimens only",
        "outer_split": "leave-one-released-specimen-out; no cell-level random split",
        "hyperparameter_search": "none after registration; Ridge alpha=1.0 and 16 PCs frozen",
    }
    if not all(value for value in audit.values() if isinstance(value, bool)):
        raise RuntimeError(f"paired leakage audit failed: {audit}")

    inference = pd.DataFrame(inference_rows)
    out_dir = ROOT / "reports/v11"
    out_dir.mkdir(parents=True, exist_ok=True)
    inference.to_csv(out_dir / "paired_specimen_inference.tsv", sep="\t", index=False)
    report = {
        "status": "frozen_paired_result_formally_audited",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "primary_endpoint": "mean specimen-level paired-minus-permuted cosine similarity",
        "inference": inference_rows,
        "leakage_audit": audit,
        "input_sha256": {p.name: sha256(p) for p in [folds_path, pairs_path, features_path, sampled_path]},
        "interpretation": "Bootstrap confidence intervals quantify uncertainty in the mean effect across specimens; fold percentiles describe heterogeneity and are not confidence intervals.",
    }
    (out_dir / "paired_specimen_inference.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def load_csr(path: Path) -> sparse.csr_matrix:
    data = np.load(path, allow_pickle=False)
    return sparse.csr_matrix(
        (data["data"], data["indices"], data["indptr"]),
        shape=tuple(int(value) for value in data["shape"]),
    )


def prepare_foundation_frame() -> tuple[pd.DataFrame, np.ndarray]:
    source_dir = ROOT / "source_data"
    if not source_dir.exists():
        source_dir = ROOT / "data/gold"
    meta = pd.read_parquet(source_dir / "census_real_pseudobulk_meta.parquet").reset_index(drop=True)
    meta["lineage"] = meta["cell_type"].map(lineage)
    counts = meta.dropna(subset=["lineage"]).groupby("lineage")["dataset_id"].nunique()
    allowed = counts[counts >= 3].index
    keep = meta["lineage"].isin(allowed).to_numpy()
    return meta.loc[keep].reset_index().rename(columns={"index": "source_index"}), keep


def fixed_splits(frame: pd.DataFrame, axis: str) -> list[tuple[np.ndarray, np.ndarray]]:
    groups = frame[axis].astype(str).to_numpy()
    labels = frame["lineage"].astype(str).to_numpy()
    return list(GroupKFold(n_splits=min(5, len(np.unique(groups)))).split(frame, labels, groups))


def study_only_predict(frame: pd.DataFrame, train: np.ndarray, test: np.ndarray) -> np.ndarray:
    labels = frame["lineage"].astype(str)
    global_majority = labels.iloc[train].value_counts().idxmax()
    lookup = (
        frame.iloc[train].assign(_label=labels.iloc[train].to_numpy())
        .groupby("dataset_id")["_label"].agg(lambda values: values.value_counts().idxmax())
    )
    return frame.iloc[test]["dataset_id"].map(lookup).fillna(global_majority).to_numpy(dtype=str)


def raw_baseline_features(raw: sparse.csr_matrix, train: np.ndarray, test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    # Library-size normalisation and log1p are fixed. Feature ranking is fitted
    # only on training rows; no test labels or test expression summaries enter.
    train_x = normalize(raw[train], norm="l1", axis=1) * 10_000.0
    test_x = normalize(raw[test], norm="l1", axis=1) * 10_000.0
    train_x.data = np.log1p(train_x.data)
    test_x.data = np.log1p(test_x.data)
    mean = np.asarray(train_x.mean(axis=0)).ravel()
    mean_sq = np.asarray(train_x.power(2).mean(axis=0)).ravel()
    variance = mean_sq - mean ** 2
    top = np.argsort(variance)[-min(2_000, raw.shape[1]):]
    return train_x[:, top], test_x[:, top]


def score_foundation() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    frame, keep_mask = prepare_foundation_frame()
    labels = frame["lineage"].astype(str).to_numpy()
    source_indices = frame["source_index"].to_numpy(dtype=int)
    source_dir = ROOT / "source_data"
    artifact_dir = source_dir if source_dir.exists() else ROOT / "artifacts"
    model_paths = {
        "Geneformer-V1-10M": artifact_dir / "foundation_geneformer_v1_10m_embeddings.npz",
        "scGPT-original-public": artifact_dir / "foundation_scgpt_embeddings.npz",
        "UCE-4-layer-public-mirror": artifact_dir / "foundation_uce_v3_embeddings.npz",
        "scFoundation-public-mirror": artifact_dir / "foundation_scfoundation_v3_embeddings.npz",
    }
    embeddings = {name: np.load(path, allow_pickle=False)["embeddings"][source_indices] for name, path in model_paths.items()}
    raw_all = load_csr((source_dir if source_dir.exists() else ROOT / "data/gold") / "census_real_pseudobulk.npz")
    raw = raw_all[source_indices]
    rows: list[dict[str, object]] = []
    predictions: list[dict[str, object]] = []

    for axis in ["donor_id", "dataset_id"]:
        for fold, (train, test) in enumerate(fixed_splits(frame, axis)):
            classes_test = int(len(np.unique(labels[test])))
            valid = bool(len(test) >= MIN_SENSITIVITY_TEST_N and classes_test >= MIN_SENSITIVITY_CLASSES)
            global_majority = pd.Series(labels[train]).value_counts().idxmax()
            fold_predictions: dict[str, np.ndarray] = {
                "Majority": np.repeat(global_majority, len(test)),
                "Study-only": study_only_predict(frame, train, test),
            }

            train_raw, test_raw = raw_baseline_features(raw, train, test)
            svd = TruncatedSVD(n_components=min(50, train_raw.shape[0] - 1, train_raw.shape[1] - 1), random_state=SEED)
            train_pca = svd.fit_transform(train_raw)
            test_pca = svd.transform(test_raw)
            pca_scaler = StandardScaler().fit(train_pca)
            pca_model = LogisticRegression(C=1.0, max_iter=4_000, class_weight="balanced", random_state=SEED)
            pca_model.fit(pca_scaler.transform(train_pca), labels[train])
            fold_predictions["Expression-PCA50+logistic"] = pca_model.predict(pca_scaler.transform(test_pca))
            ridge = RidgeClassifier(alpha=1.0, class_weight="balanced")
            ridge.fit(train_raw, labels[train])
            fold_predictions["Expression-Ridge"] = ridge.predict(test_raw)

            for model_name, emb in embeddings.items():
                scaler = StandardScaler().fit(emb[train])
                classifier = LogisticRegression(C=1.0, max_iter=4_000, class_weight="balanced", random_state=SEED)
                classifier.fit(scaler.transform(emb[train]), labels[train])
                fold_predictions[model_name] = classifier.predict(scaler.transform(emb[test]))

            for model_name, pred in fold_predictions.items():
                row = {
                    "model": model_name,
                    "axis": axis,
                    "fold": fold,
                    "heldout_groups": ";".join(sorted(frame.iloc[test][axis].astype(str).unique())),
                    "n_train": int(len(train)),
                    "n_test": int(len(test)),
                    "classes_train": int(len(np.unique(labels[train]))),
                    "classes_test": classes_test,
                    "sensitivity_eligible": valid,
                    "exclusion_reason": "" if valid else ("single_test_class" if classes_test < 2 else "n_test_below_50"),
                    "balanced_accuracy": float(balanced_accuracy_score(labels[test], pred)) if classes_test >= 2 else np.nan,
                    "macro_f1": float(f1_score(labels[test], pred, average="macro", zero_division=0)) if classes_test >= 2 else np.nan,
                }
                rows.append(row)
                for idx, truth, predicted in zip(test, labels[test], pred):
                    predictions.append({
                        "model": model_name,
                        "axis": axis,
                        "fold": fold,
                        "row_id": str(frame.iloc[idx]["group_id"]),
                        "heldout_group": str(frame.iloc[idx][axis]),
                        "truth": str(truth),
                        "prediction": str(predicted),
                        "sensitivity_eligible": valid,
                    })

    metrics = pd.DataFrame(rows)
    pred_frame = pd.DataFrame(predictions)
    summary_rows = []
    rng = np.random.default_rng(SEED)
    for (model, axis), group in pred_frame.groupby(["model", "axis"]):
        eligible = group[group["sensitivity_eligible"]].copy()
        valid_folds = metrics[(metrics["model"] == model) & (metrics["axis"] == axis) & metrics["sensitivity_eligible"]]
        item = {
            "model": model,
            "axis": axis,
            "analysis_role": "primary" if axis == "donor_id" else "dataset-holdout sensitivity stress test",
            "primary_endpoint": axis == "donor_id",
            "total_folds": int(group["fold"].nunique()),
            "eligible_folds": int(valid_folds["fold"].nunique()),
            "excluded_folds": int(group["fold"].nunique() - valid_folds["fold"].nunique()),
            "eligible_test_rows": int(len(eligible)),
            "median_fold_balanced_accuracy": float(valid_folds["balanced_accuracy"].median()) if len(valid_folds) else np.nan,
            "median_fold_macro_f1": float(valid_folds["macro_f1"].median()) if len(valid_folds) else np.nan,
        }
        if len(eligible) and eligible["truth"].nunique() >= 2:
            groups = eligible["heldout_group"].unique()
            class_names = np.unique(np.concatenate([eligible["truth"].to_numpy(), eligible["prediction"].to_numpy()]))
            group_cms = np.stack([
                confusion_matrix(
                    eligible.loc[eligible["heldout_group"] == value, "truth"],
                    eligible.loc[eligible["heldout_group"] == value, "prediction"],
                    labels=class_names,
                )
                for value in groups
            ])
            sampled_indices = rng.integers(0, len(groups), size=(BOOTSTRAP_DRAWS, len(groups)))
            sampled_cms = group_cms[sampled_indices].sum(axis=1)
            true_totals = sampled_cms.sum(axis=2)
            predicted_totals = sampled_cms.sum(axis=1)
            true_positive = np.diagonal(sampled_cms, axis1=1, axis2=2)
            recall = np.divide(true_positive, true_totals, out=np.full_like(true_positive, np.nan, dtype=float), where=true_totals > 0)
            ba_draws = np.nanmean(recall, axis=1)
            f1_denominator = 2 * true_positive + (predicted_totals - true_positive) + (true_totals - true_positive)
            class_f1 = np.divide(2 * true_positive, f1_denominator, out=np.zeros_like(true_positive, dtype=float), where=f1_denominator > 0)
            f1_draws = class_f1.mean(axis=1)
            item.update({
                "pooled_balanced_accuracy": float(balanced_accuracy_score(eligible["truth"], eligible["prediction"])),
                "cluster_bootstrap_balanced_accuracy_ci95_low": float(np.quantile(ba_draws, 0.025)),
                "cluster_bootstrap_balanced_accuracy_ci95_high": float(np.quantile(ba_draws, 0.975)),
                "pooled_macro_f1": float(f1_score(eligible["truth"], eligible["prediction"], average="macro", zero_division=0)),
                "cluster_bootstrap_macro_f1_ci95_low": float(np.quantile(f1_draws, 0.025)),
                "cluster_bootstrap_macro_f1_ci95_high": float(np.quantile(f1_draws, 0.975)),
            })
        summary_rows.append(item)

    summary = pd.DataFrame(summary_rows)
    out_dir = ROOT / "reports/v11"
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(out_dir / "foundation_fold_metrics_hardened.tsv", sep="\t", index=False)
    summary.to_csv(out_dir / "foundation_sensitivity_summary.tsv", sep="\t", index=False)
    pred_frame.to_parquet(out_dir / "foundation_oof_predictions.parquet", index=False)
    report = {
        "status": "foundation_benchmark_hardened_with_baselines_and_degenerate_fold_policy",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "primary_endpoint": "donor-grouped pooled out-of-fold balanced accuracy",
        "secondary_endpoint": "donor-grouped pooled macro-F1",
        "dataset_axis_role": "sensitivity stress test; not pooled with the primary endpoint",
        "degenerate_fold_policy": {
            "minimum_test_rows": MIN_SENSITIVITY_TEST_N,
            "minimum_test_classes": MIN_SENSITIVITY_CLASSES,
            "single-class_macro_f1": "missing by design; never imputed and never included in medians",
            "excluded_folds_remain_in_fold_table": True,
        },
        "confidence_intervals": f"cluster bootstrap over held-out {BOOTSTRAP_DRAWS} times with seed {SEED}",
        "baselines": ["Majority", "Study-only", "Expression-PCA50+logistic", "Expression-Ridge"],
        "summary": summary.replace({np.nan: None}).to_dict(orient="records"),
        "embedding_receipts": {
            name: {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)} for name, path in model_paths.items()
        },
    }
    (out_dir / "foundation_benchmark_hardened.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return metrics, summary, report


def main() -> None:
    paired = paired_audit()
    _, summary, foundation = score_foundation()
    combined = {
        "status": "reversome_v11_statistical_hardening_complete",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "paired_primary": paired["inference"][0],
        "foundation_primary_endpoint": foundation["primary_endpoint"],
        "foundation_summary_rows": int(len(summary)),
    }
    (ROOT / "reports/v11/statistical_hardening_manifest.json").write_text(
        json.dumps(combined, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(combined, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
