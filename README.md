# REVERSOME evidence-bounded benchmark

This repository is the public, manuscript-linked release for REVERSOME. It
contains the frozen statistical audit, derived source data and compact model
artefacts needed to reproduce the two central computational results:

1. specimen-held-out RNA-to-ATAC state transfer in GSE241468; and
2. a four-model foundation-embedding benchmark with explicit degenerate-fold
   handling and simple expression baselines.

The release does **not** claim experimental, causal or clinical validation.
The hPCLS, spatial, external-cohort and agent layers are contextual or
release-control evidence.

## Central results

- Lung paired-state primary effect: mean paired-minus-permuted cosine 0.2164,
  95% specimen bootstrap CI 0.1947–0.2385, exact two-sided sign-flip
  p=3.0518e-5, n=16 specimens.
- Foundation primary endpoint: donor-grouped pooled out-of-fold balanced
  accuracy. Dataset-held-out analysis is a sensitivity stress test; folds with
  fewer than 50 test rows or fewer than two test classes remain visible but
  are excluded from sensitivity summaries.
- Expression PCA50+logistic is a mandatory baseline and is competitive with
  the strongest frozen foundation embeddings on this endpoint.

## Repository map

- `analysis/`: deterministic statistical hardening script.
- `source_data/`: paired fold/pair manifests, compact expression input and
  frozen foundation embeddings. These are derived computational artefacts,
  not model weights.
- `reports/`: machine-readable primary inference, benchmark fold table,
  out-of-fold predictions and sensitivity summaries.
- `registrations/`: time-stamped internal pre-specified analysis plan and
  scope boundaries.
- `environment/`: exact Python package freeze used on KAUST IBEX.
- `docs/`: data/code availability, data dictionary and model provenance.
- `third_party_licenses/`: upstream licence notices. Model weights are not
  redistributed.

## Reproduction

Create a Python 3.9 environment, then install the frozen dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r environment/requirements.freeze.txt
python analysis/reversome_v11_statistical_hardening.py
```

The script expects the repository layout provided here. It writes results to
`reports/v11/`; compare regenerated files with `checksums.sha256`. Numerical
reproduction was verified on Linux x86_64. The statistical script uses CPU;
the included embeddings were previously extracted on KAUST IBEX GPU nodes.

## Public source data

- GSE241468: barcode-shared human lung RNA+ATAC multiome. The source repository
  replaced an erroneous processed object; this project used the corrected
  `GSE241468_share_seur.rds` object.
- GSE291190: public hPCLS context.
- GSE178361: normal distal-lung spatial transcriptomics.
- GSE47460 and GSE188464: external/perturbational lung context.

Large raw public files are not duplicated here. Their accessions and source
study licences remain authoritative.

## Citation and archive

Use `CITATION.cff` for software citation. The GitHub manuscript release is
`v1.0.0-manuscript`. A Zenodo DOI will be added after author-controlled
deposition of this exact tagged release.

The exact Git commit, tag and release URL are recorded in
`release_manifest.json`. The archive is DOI-ready, but a DOI cannot be minted
without the submitting authors' verified identity and archive authorization.

## Licence

Project code is released under the MIT License. Derived tabular outputs are
released under CC BY 4.0 as stated in `docs/DATA_LICENSE.md`. Third-party data,
models and weights retain their original terms.
