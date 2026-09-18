# Prompt pipeline and Lean verification review

Status: 2026-09-18. The archive is downloaded and indexed; three Python scripts were statically parsed and selected validation paths inspected. See [concrete findings](research-package-review.md). No API calls or pipeline execution were performed. The proposals below are not completed proofs.

## Repository layout

Published course attachments are in `materials/APS1053/`; reading copies and study notes are in `knowledge/APS1053/`. Credential files and personal correspondence are excluded.

## Files expected from the package

- `prompt_reorganized.md`
- `prompt_prolog_version.txt`
- `compendium_StructuralDescription_relationshiptypes.txt`
- `deepseek_speech_processing_program1_notree_revised2.py`

Record hashes and preserve originals before making modifications. Inspect code without importing it or making paid API requests.

## Questions for code inspection

1. What data structures represent speeches, claims, themes and contribution records?
2. Which conditions are checked, and which appear only in prompts?
3. Are failed checks rejected, repaired, warned about, or silently ignored?
4. Can caches, retries or intermediate files bypass validation?
5. Which phase can change accepted mappings or relationship labels?
6. Does final prose still agree with the validated records, and how is that checked?
7. What assumptions are made about identifiers, input ordering, uniqueness, parsing and external services?

## Candidate first guarantees

These are proposed properties, not verified facts about the existing code.

- Accepted references resolve to existing source records.
- Accepted relation labels belong to the specified vocabulary.
- Required cardinalities and uniqueness rules hold.
- Rejected candidates cannot enter the accepted state.
- Deterministic remapping preserves accepted identifiers and relation labels.

Source existence and label validity do not establish semantic correctness, source truth, or faithfulness of generated prose.

## Three implementation routes

### A. Model and specify

Represent the relevant data and state transitions in Lean. Prove that allowed transitions preserve selected invariants. This proves the Lean model, not equivalence to Python. Differential tests provide evidence about a correspondence but not a universal equivalence proof.

### B. Verified checker used by Python

Implement a small executable checker in Lean and prove, for a specified predicate P:

`check(x) = true -> P(x)`

Have Python send typed/serialized records to the checker and proceed only on acceptance. Include or account for parsing, versioning, data identity, fail-closed invocation, and downstream use. The production guarantee still depends on the actual integration and runtime/compiler boundary; Python must not substitute or modify unchecked data after acceptance.

### C. Verify the Python program itself

Model the relevant Python semantics and establish a correspondence between the actual program and its Lean representation, or use an appropriate verified translation/verification toolchain. Mutation, exceptions, I/O and library behavior must be covered or stated as assumptions. An automatic source translation by itself does not establish semantic preservation.

## First bounded experiment

After inspecting the real code, choose one pure validation/remapping function. Extract the exact contract, prepare passing and failing examples, then decide whether to model it, replace it with a verified checker, or prove a translation correspondence. Do not start by claiming verification of the entire five-phase LLM pipeline.

## References

- Lean compilation: https://lean-lang.org/doc/reference/latest/Elaboration-and-Compilation/
- Lean foreign function interface: https://lean-lang.org/doc/reference/latest/Run-Time-Code/Foreign-Function-Interface/
- Python specification translation benchmark: https://fvspec.galois.com/
