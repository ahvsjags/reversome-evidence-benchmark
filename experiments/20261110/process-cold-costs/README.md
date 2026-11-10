# Actual fresh-process versus warm-service costs

Six physically executed fresh Python processes (3 repeats x fixed3/source_active), including interpreter/model/index startup, source-worker initialization where needed, actual neural verification of all278 frozen public claims, and shutdown.

Same audited V4 action-execution body, unchanged frozen models/thresholds. Same host as the warm-service experiment. All278 per-claim source identities, final decisions, and neural posteriors were checked against the warm reference; maximum posterior difference0. Independent check35/35PASS.

Median complete fresh-process costs: fixed3=147.238602s wall and379.964838 CPU-s; source_active=152.700191s wall and337.154063 CPU-s. Active saves11.27% CPU but takes3.71% longer wall time at startup. Warm-service savings were9.82% wall and21.03% CPU. Neither is universal latency improvement.

All three runs, including the slower first fixed baseline run, remain in the receipt. Process-cold is not OS/filesystem-cold: shared caches were not flushed. These are real frozen-policy computation/reproduction measurements, not six independent accuracy confirmations or new scientific claim collections.

The public-open-runtime bundle in the same revision provides the same frozen scientific vectors and official-annotation numerical verifier. This addition reports actual process-level resource use rather than deriving it by summing setup estimates.
