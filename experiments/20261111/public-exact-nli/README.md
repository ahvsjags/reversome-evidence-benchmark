# Exact public NLI checkpoint (v255)

Lossless reconstruction of the original 737,722,356-byte float32 checkpoint (SHA256 4ea38ec8530be55df421a53585dff01e571df49e5a543e2a74a1098c52c22709), not quantization or retraining. Download fetch_exact_nli.py from an immutable commit, install the bundled dependency versions and run:

```
python fetch_exact_nli.py --commit COMMIT_SHA --output-dir fresh_nli --run-neural-probe
```

144 parts and the archive, pinned public base, exact fitted checkpoint and public input text are hash-verified. Optional --base-checkpoint and --public-data-dir reuse only verified public dependencies. No credentials/private hospital records required. The loader uses only Python's standard library; restoration needs NumPy; neural replay needs PyTorch/Transformers, with versions in the bundle requirements. The 96 input groups and 525 neural sentence pairs reproduce fixed outputs, not new independent accuracy samples. This does not rerun Qwen or all 95 manuscript assets.

Base model: https://huggingface.co/MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli (MIT), revision 6f5cf0a2b59cabb106aca4c287eed12e357e90eb; retain attribution and license. Fitting used 603 public SciFact claims only. Training receipt/protocol and exact tokenizer/config are bundled. Archived training source retains historical IBEX paths; portable entry points are restore_checkpoint.py and reproduce_neural.py. The anonymous published-download/fresh-neural receipt will be added after verification.
