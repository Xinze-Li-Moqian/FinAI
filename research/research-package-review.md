# Prompt companion package: reading and verification opportunities

Inspected on 2026-09-18. The package was downloaded and extracted, and 640 files were checked by SHA-256. Three main Python scripts passed static syntax parsing. Instructor scripts were not imported or executed, package credentials were not used, paid APIs were not called, and sample results were not reproduced.

## Reading order

1. `prompt_reorganized.md`: the fuller natural-language task and constraints.
2. `prompt_prolog_version.md`: a Prolog-style representation; determine which statements are executable and which are explanatory.
3. `compendium_StructuralDescription_relationshiptypes.md`: entity and relationship structure.
4. `StructuralAndIntegrityRules_reference.md` and `PipelineAndIntermediateOutputs_reference.md`: rules and intermediate outputs. The latter describes itself as reference material, not another actual pipeline input.
5. Main program, evaluator, and verification program; then existing results in `output/`. The correspondence between sample outputs and the current code version remains unverified.

See the [catalog](../readings/library/COURSE_CATALOG.md) for file links and the [source map](python-source-map.json) for function locations. Original files are in `materials/07_Prompt_Pipeline/DeepSeek_revised2_by_chatgpt/`.

## Package contents

The 640 files include 410 JSON, 107 TXT, 100 Markdown, 3 Python, 7 PDF, 2 DOCX, and 1 PPTX files, plus environment configuration, logs, web diagrams, EPUB, and other files. `output/` accounts for 511 files and `transcripts/` for 100. The received package included `.env`; original credentials remain local. The public package substitutes `.env.example` without keys.

| Program | Lines | Purpose |
|---|---:|---|
| deepseek_speech_processing_program1_notree_revised2.py | 4780 | Five phases: transcript extraction, aggregation, classification, deterministic remapping, and compendium synthesis |
| standalone_evaluation_script_notree_revised2.py | 4673 | Structural, provenance, version, and semantic evaluation |
| deepseek_program2_verify_claims_revised.py | 1379 | Model judgments and optional search, followed by status-marker replacement for matching entries |

Word and PowerPoint carry lectures and research discussion; execution materials already include MD/TXT, Python, JSON, and YAML. File formats alone do not establish that a method is outdated. Opportunities include clearer separation of materials, entry points, reproducible environments, automated checks, and version correspondence. No `test_` files were found, but an independent evaluator exists; it would be inaccurate to claim there is no validation.

## Observed implementation and limits

- Main-program Phase 4 adds mapping information to `copy.deepcopy(source_record)` around line 3048, providing a concrete entry point for studying preservation. Fields and branches still need individual checking.
- Around lines 4590–4638, the main program writes compendium files before running and saving integrity checks. Failures are logged and the manifest is marked incomplete; `main` returns exit code 3 around line 4765. Files may therefore exist after failure. Publication must inspect acceptance status or occur only after a separate acceptance step.
- Phase 5 records and skips buckets whose synthesis fails, then builds a pair table from successful buckets. Compare the expected input set with the failures; consistency of the surviving subset does not establish complete coverage.
- The evaluator defaults at line 125 to `speech_processing_program_notree_revised.py`, which differs from the received main-program filename. Pass the correct path explicitly when reproducing results.
- The second program defines status replacement and preservation checks at lines 954–1019 and checks before writing at lines 1030–1040. This is a smaller, more precise formalization target.
- Verification judgments from model memory or search are not formal proofs. Preserving source IDs and text also does not establish the truth of financial claims or the faithfulness of synthesized prose.

## A first Lean experiment

Start by formalizing status replacement: define documents, permitted edit positions, and valid statuses. Prove that replacement affects only status fields at specified positions and preserves all other fields and text. Then consider Phase 4 field preservation, reference integrity, and budget constraints.

A proof of a Lean model does not automatically cover the existing Python implementation. Either prove correspondence or have Python call a verified checker and ensure that accepted data are exactly what downstream steps use. Specify the boundaries for regular-expression parsing, serialization, file writes, and error handling.

This package concerns constrained LLM information processing. The inspection did not identify an RL training or multi-agent RL verification implementation. It can support a small experiment in model proposals, deterministic checks, and accepted state, while extension to control of RL populations remains a research question.
