# Public full-refit replay: GSE241468

Download `REVERSOME_public_full_refits_v246_20261110.zip` and verify SHA256 `aa72192a46552300bc6260f0f48571070862d46fa4066018075d50b0f12aaa6f`.

The archive contains a path-independent R runner, two public frozen model checkpoints, complete800-row reference outputs, and a standalone verifier. Obtain the public20GB revised RDS from [NCBI GEO](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE241nnn/GSE241468/suppl/GSE241468_share_seur.rds), then verify input SHA256 `98c542ab238a9df25b0e98f568bacb392276f8a5b5fa385541e5e53e2e680fac`.

Run `REV_REPEATS=20 Rscript --vanilla reproduce_refits.R PUBLIC_RDS NEW_OUTPUT golden`, then `python verify_public_refits.py NEW_OUTPUT .`. Record R4.3.0, Matrix, SeuratObject, jsonlite and single-thread BLAS. The numerical verifier requires NumPy and SciPy.

All20 splits independently refit feature selection, scaling, PCA and ridge, with5 training-side pairing controls each. They use16 released assay/specimen-pool units, not16 established independent individual donors. The [source article](https://doi.org/10.1038/s41467-024-52356-9) reports tissue pooling. Original source/data licenses remain in force. The package contains no hospital/expert/manuscript/reviewer records.
