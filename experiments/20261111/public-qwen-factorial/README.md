# Qwen30B real-tool matched factorial and repeated-run evidence

`REVERSOME_public_qwen_factorial_v254_20261111.zip`: 691,952 bytes; SHA256 `be7db270a31c875d453873c0ea16af549e52dd5ec19950c965302cec3e20f5bc`.

96 primary claims, one per source/evidence-connected component; prespecified32claim subset at two extra seeds =160 actual stochastic case-runs.3 acquisition policies x3 verification tracks. Official Qwen3-30B-A3B Q4_K_M and real frozen NLI tools; full params, prompts, source bindings and all results retained. Existing exposed public benchmark, not a new untouched cohort. ReAct-style adapted comparator, not native GeneAgent/DeepEvidence reproduction.

Run `python reproduce.py --bundle-dir EXTRACTED_BUNDLE --output-dir NEW_OUTPUT` with NumPy2.0.2. Independent numerical replay581/581 checks, zero metric difference. This does not execute models: the704MB fine-tuned NLI checkpoint is not included. Archived methods retain upstream IBEX dependencies. Public output vectors are not advertised as full neural-inference reproduction.

With common NLI, ECAPF1 fixed3=.15789, source-active=.17647,Qwen-tool=.15718; active differences not significant. With freshQwen evidence judgment, Qwen-tool=.31963 vsfixed3=.19394 (difference .12570,95%source-componentbootstrapCI[.03959,.20711]). Report all9cells and coverage/cost tradeoffs, not universal superiority of the deterministic active policy.

Source/claim/request-binding checks and3seed stability independently verified. All160case-runs completed without inference failures. A mutable-message logging alias affected saved request histories:972 were reconstructed from append-only turn prefixes; all1452recorded prompt-token counts match the pinned template/tokenizer engine (3876/3876checks). Original traces retained. Derived requests are labelled reconstructed, not wire captures; future logger uses immutable snapshots. No scientific output changed.

No source abstracts or private hospital/expert records are distributed. Raw scientific tool traces stay on IBEX; public release includes source IDs, model probabilities, official label mappings, token/response metadata and hashes.
