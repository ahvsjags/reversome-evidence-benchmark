# Public external-cohort frozen-model reproduction

GEO GSE286182,10 libraries,8 donor units,70,400 jointly measured cells.
Every FASTQ library was reprocessed with CellRangerARC2.0.0 on IBEX; all H5/MEX
counts and feature/barcode ordering were independently compared. The frozen
model used64RNA features,64ATAC bins and293fixed training-peak intervals.
Independent numeric audit passed100/100. Portable pre-publication replay passed
117/117 with exactly equal per-cell model predictions.

Use Python3.10+ in a venv with NumPy2.0.2. Download fetch_and_reproduce.py and run:

    python -m pip install numpy==2.0.2
    OPENBLAS_NUM_THREADS=1 python fetch_and_reproduce.py --base-url RAW_IMMUTABLE_FOLDER_URL --work-dir /path/new_empty_work

The folder URL is this directory's raw.githubusercontent.com URL at the
immutable commit, not an HTML GitHub page. The loader fetches release_index.json,
SHA-verifies all2MBparts and the combined archive, then really re-executes every
cell prediction,100target permutations per library, donor aggregation,
20,000bootstrap draws, and all256sign-flip assignments. All per-cell reference
vectors and frozen coefficients are included. No model fit or target-driven
feature selection is performed.

The mean same-cell correspondence contrast is0.0195930; donor bootstrap95%CI
[0.0141689,0.0252862], exact two-sided sign-flip p0.0078125. This is a previously
inspected public cohort reanalysis, not an untouched new cohort. The portable
loader starts from released derived arrays; it does not realign FASTQs. It does
not establish training-pairing benefit, universal transport, or researcher
decision improvement. All data derive from public GEO, with no private patient
or individual expert records.

Original public accession: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE286182

