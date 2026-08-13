# Data dictionary

## Paired analysis

- `reversome_v5b_lung_paired_multiome_folds.csv`: one row per held-out lung
  specimen; effect, comparator and retrieval metrics.
- `reversome_v5b_lung_paired_multiome_pairs.csv`: one row per evaluated exact
  barcode pair with observed control outcomes.
- `reversome_v5b_lung_paired_multiome_sampled_cells.csv`: frozen sampling
  manifest.
- `reversome_v5b_lung_paired_multiome_train_only_features.csv`: fold-specific
  RNA genes and 100-kb ATAC bins selected from training specimens only.
- `paired_specimen_inference.tsv/json`: specimen bootstrap confidence
  intervals, exact sign-flip tests and leakage gates.

## Foundation benchmark

- `census_real_pseudobulk.npz`: CSR expression matrix (`data`, `indices`,
  `indptr`, `shape`).
- `census_real_pseudobulk_meta.parquet`: row-aligned public metadata.
- `foundation_*_embeddings.npz`: row-aligned frozen embeddings under key
  `embeddings`; these are model outputs, not redistributed weights.
- `foundation_fold_metrics_hardened.tsv`: every model/baseline/fold result,
  including ineligible sensitivity folds.
- `foundation_oof_predictions.parquet`: row-level truth and out-of-fold
  prediction for audit and cluster bootstrap.
- `foundation_sensitivity_summary.tsv`: eligible-fold and pooled summaries.

Missing macro-F1 values indicate a single-class test fold and are intentionally
not imputed.
