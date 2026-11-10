# Requirement origins and controlled threshold/input perturbations

Download and extract `REVERSOME_public_requirement_stress_v253_20261111.zip` (670,888 bytes; SHA256 `faa746d4786de37c889efafc06c5a554945da583fbc6f7279c26dfe775f05023`). Install NumPy2.0.2 and run:

```sh
python reproduce.py --bundle-dir EXTRACTED_BUNDLE --output-dir NEW_OUTPUT
```

The independent NumPy implementation reconstructs 331/331 metrics/checks exactly. The original primary-policy replay matches all 278 cases for each of 3 policies (837/837 checks including origin checks). No new model inference is claimed: this is sensitivity on archived actual inference outputs, not fresh independent confirmation or human requirement adjudication.

Eleven prespecified post-hoc configurations cover relation threshold, class margins, source cutoff, omitted extra-source eligibility and score-to-source binding destruction. Primary values remain frozen. Under active acquisition, ECAPF1 is0.1836066 at primary,0.1728045 without the additional-source gate and0.1162791 after source-score binding destruction. A stricter source cutoff0.95 reduces F1 to0.1433692; this does not select a replacement cutoff.

The origin ledger distinguishes the0.85 source cutoff fitted on204 source-disjoint calibration claims from0.7/0.2/0.1 declared guard design constants. With normalized3class probabilities, relation>=0.7 implies margins>=0.4; the tested smaller margin variants are algebraically redundant, not extra effective safeguards.

Includes public source IDs, model probabilities, source scores and official evidence labels, but no abstracts, hospital or expert case records. Official pooled source labels are incomplete, so an unannotated source prediction is not automatically a scientifically false conclusion.
