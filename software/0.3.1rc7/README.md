# REVERSOME 0.3.1rc7 software snapshot

This folder provides the portable, data-free source and installed-wheel reproduction bundle for the evidence-control runtime. It is distinct from the historical v1.0.0-manuscript statistical-artifact release at repository root.

## Reproduce

Download REVERSOME_0.3.1rc7_software_repro_bundle_v2.zip from this folder and verify its SHA-256 against the sidecar. Extract it, then run bash reproduce.sh using Python 3.9.18. The archive includes the source distribution, wheel, complete pinned test dependency closure (including the optional SciPy MILP solver), and source/wheel test logs.

A fresh Linux clean-room replay on 2026-11-10 passed 408 source tests and the same 408 tests against a separately installed wheel. The recipe checks that imports originate from the installed wheel. These are two executions of one software suite, not 816 independent scientific cases.

SHA-256: 16225364d0c4bd79011bdcf9eb1242ec0a8de5f16006c433cdda6e8cc31b01f7

## Scope

The package contains code, schemas, software fixtures and reproduction logs. It does not contain cohort data, expert-level records, clinical records, manuscript documents, model weights or peer-review correspondence. It does not reproduce every biological analysis or establish scientific/clinical accuracy. Experimental policy-development candidates are not part of this tested snapshot. No DOI is asserted for this software snapshot.

The existing project and third-party licence notices apply. Keep the historical manuscript release and this runtime version distinct when citing results.
