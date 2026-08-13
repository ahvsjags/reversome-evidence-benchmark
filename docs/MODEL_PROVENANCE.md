# Model provenance and redistribution boundary

The repository includes frozen embedding outputs and SHA256 receipts, but does
not redistribute third-party model weights.

| Artefact | Output dimension | Upstream model | Redistribution |
|---|---:|---|---|
| Geneformer V1-10M | 256 | Geneformer | embeddings only |
| scGPT original public | 512 | scGPT | embeddings only |
| UCE four-layer public checkpoint | 1,280 | UCE | embeddings only |
| scFoundation public mirror | 768 | scFoundation | embeddings only |

The machine-readable hashes are in
`reports/foundation_benchmark_hardened.json`. Upstream licence notices are
provided under `third_party_licenses/` when present in the local source tree.
