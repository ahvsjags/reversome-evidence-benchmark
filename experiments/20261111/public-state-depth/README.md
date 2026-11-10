# RNA-state and sequencing-depth matched target controls

This public bundle adds four controls on the same 70,357 eligible cells from all 10 GSE286182 libraries (8 donors). It includes public RNA-only graph states, RNA H5 library totals, ATAC fragment totals, the frozen protocol, 4,000 derangement results, independent verification and a NumPy-only replay entry point. No model is refit.

Download and extract `REVERSOME_public_state_depth_controls_v252_20261111.zip`; SHA256 `b563eca6ef944e493c5cab920bc4704561c8ae15f390bcb7342f2e74f5feff35` (907,738 bytes).

Obtain the prior external frozen-model bundle using `experiments/20261111/public-external/fetch_and_reproduce.py` at immutable commit `cfd2d73f937435f8b7ad60528373e79b79e2f95b`. Then run:

```sh
python reproduce_state_depth_controls.py --bundle-dir MATCHED_BUNDLE --external-bundle-dir PREVIOUS_EXTERNAL_BUNDLE --output-dir NEW_OUTPUT
```

Independent raw-source reconstruction: 102/102 checks. Separate isolated NumPy-only replay: 82/82 checks, maximum permutation-mean discrepancy 2.22e-16. These are numerical checks, not accuracy cases.

On common eligible cells, the global contrast is 0.01969909. Matching RNA-only state and joint RNA/ATAC depth gives 0.00247518 (donor-bootstrap 95% CI 0.00118067–0.00387791; exact two-sided sign-flip P=0.015625; Holm-adjusted P=0.03125). The result is substantially attenuated, with a residual positive association. This is post-hoc sensitivity on a previously inspected cohort, not causal adjustment, an untouched confirmation cohort or a training-side pairing benefit.

Only public data and code are included. No private hospital or expert case records are included; manuscript and figure assets are not modified.
