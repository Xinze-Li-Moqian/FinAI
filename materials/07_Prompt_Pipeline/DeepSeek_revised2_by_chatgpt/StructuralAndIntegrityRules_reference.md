StructuralAndIntegrityRules.txt
STRUCTURAL AND INTEGRITY RULES
Split out of compendium_StructuralDescription_relationshiptypes.md

[Editorial note: this document is a reference only. It is not being used as
an input to the pipeline-construction prompt. It holds the 17 rules
originally gathered under a single "Structural and Integrity Rules" heading
in compendium_StructuralDescription_relationshiptypes.md, split into two
groups: rules stating properties of the finished ER model (checkable by
inspecting the model itself), and rules constraining pipeline/LLM behavior
during processing (checkable only by watching the process, not the finished
artifact). One rule (9) is internally mixed and appears split across both
groups. Original rule numbers are preserved for cross-reference.

ALREADY INCORPORATED INTO prompt_reorganized.md — the following rules'
content already exists there and is not being restated as new content
elsewhere; this file is documentation of where the rule came from, not a
second independent source of it:

  – Rule 3  (best argumentative home)      → RULES, Structural Rules,
                                              "Best Argumentative Home Standard"
  – Rule 8  (lossless remapping)           → DIRECTIVES, Principle of Fidelity
                                              to Underlying Data, "Output
                                              Fidelity Rules"; also stated
                                              directly in QUERY, Query
                                              Elaboration, Five-Phase
                                              Pipeline, Phase 4
  – Rule 9, structural half                → RULES, Structural Rules,
                                              "Relationship-Type Integrity"
  – Rule 9, behavioral half                → DIRECTIVES, Principle of Least
                                              Agency, "Relationship-Type
                                              Preservation"
  – Rule 15 (canonical versioning)         → DIRECTIVES, Principle of Least
                                              Agency, "Many-to-Many
                                              Relationship Materialization"

The remaining rules below (1, 2, 4, 5, 6, 7, 10, 11, 12, 13, 14, 16, 17)
overlap in substance with material already present in
compendium_StructuralDescription_relationshiptypes.md (their content
motivated several of that document's Definitions, its Section 2 "Junction
Tables and Runtime Buckets," and its ER cardinality tables) and, to varying
degrees, with prompt_reorganized.md's own Structural Rules and Objective —
but no specific one-to-one section citation is asserted for them here beyond
what is noted rule-by-rule below, to avoid overstating a precise
correspondence that has not been individually verified the way the five
rules above have been.]


PART A — Rules stating properties of the finished ER model

1. Authoritative chapter orientation

Canonical Central Claims remain the authoritative argument chapters.
Canonical Themes remain the authoritative cross-cutting navigation concepts.

The publication hierarchy is:

Compendium
→ Canonical Central Claim chapter
→ Canonical Theme section
→ Canonical Argument Conclusion
→ premises, evidence, devices, evolution, provenance

[Already reflected in compendium_StructuralDescription_relationshiptypes.md,
Section 1.A and Section 3 (Nested Hierarchy Structure of Entities), and in
prompt_reorganized.md's Publication Architecture definition and Output
Fidelity Rules ("Canonical CC chapters are authoritative").]

2. Theme-oriented navigation

The architecture provides two Theme-oriented navigation products:

a. Theme Cross-Index inside compendium.md
   – shared Themes only
   – lists parent CCs
   – links to authoritative sections

b. theme_index.md
   – all Canonical Themes
   – all associated CC × T pairs
   – all canonical argument conclusions
   – links to authoritative sections

Neither index is allowed to become a second authoritative copy of the full
compendium text.

[Already reflected in compendium_StructuralDescription_relationshiptypes.md,
Section 1.A and 1.B, and in prompt_reorganized.md's Theme Index / Theme View
definition.]

4. Default speech placement

A confidently categorised speech has:

– exactly one primary Canonical Central Claim;
– exactly one controlled primary_cc_relationship_type;
– one non-empty primary_cc_relationship_explanation;
– one to three Canonical Themes;
– one default CC × T pair membership for each assigned Theme;
– all default pair memberships under the same primary CC.

A shared Theme does not automatically place the speech under every CC
associated with that Theme.

[Restates cardinalities C8–C11, C31–C32 in
compendium_StructuralDescription_relationshiptypes.md, Section 5.A; the
"all default pair memberships under the same primary CC" clause and the
shared-Theme clause are reflected in that document's Entity-Relationship
Cardinalities bullet list.]

5. Optional secondary contributions

A specific local argument, premise, evidence item, or rhetorical device may
contribute to a CC × T pair outside the speech's primary CC only when an
explicit secondary mapping is created.

Secondary contributions:
– are disabled by default;
– apply to specific source contributions, not automatically to the whole speech;
– require provenance and rationale;
– must not alter the speech's primary CC assignment.

[Restates cardinality C27 in
compendium_StructuralDescription_relationshiptypes.md, Section 5.A; the
detail clauses are reflected in that document's Entity-Relationship
Cardinalities bullet list.]

6. Persistent pair versus runtime bucket

The persistent Canonical CC × T pair:
– exists in cc_theme_pairs.json;
– has a stable pair ID;
– owns canonical argument conclusions;
– has one authoritative publication anchor.

The runtime CC × T bucket:
– is temporary;
– is instantiated during Phase 5;
– gathers source contributions mapped to the persistent pair;
– supplies material for synthesis;
– is not text;
– is not contained inside a speech.

[This is the authoritative source for
compendium_StructuralDescription_relationshiptypes.md, Section 2, "Junction
Tables and Runtime Buckets," which cross-references this rule rather than
restating it.]

7. Argument ownership

Each canonical argument conclusion is owned by exactly one Canonical CC × T
pair.

Near-identical conclusions appearing in different pair contexts may be linked
as related propositions, but they must not share one canonical argument ID
unless they belong to the same exact pair.

[Restates cardinalities C6–C7 in
compendium_StructuralDescription_relationshiptypes.md, Section 5.A; also
reflected in prompt_reorganized.md's Entity-Relationship Cardinalities
bullet list.]

10. Provenance

No canonical argument conclusion may exist without at least one source
contribution.

Every canonical premise synthesis, evidence item, rhetorical device, and
Evolution Over Time statement must be traceable to source speech records.
Relationship-role records must likewise be traceable to the exact source
contributions from which they were deterministically derived.

[Reflected in compendium_StructuralDescription_relationshiptypes.md's
Provenance role definition and in prompt_reorganized.md's Provenance
definition.]

11. Evidence status

Verified, Unverifiable, and Disputed are transcript-analysis labels.
They are not external web-verification results.

Each evidence item must include a verification_basis.
Where possible, it must also include a source excerpt and deterministic
location data.

[Reflected in prompt_reorganized.md's Structural Rules, Evidence Tagging.]

12. Uncategorised speeches

A speech that fails the classification-confidence threshold or for which no
supplied CC provides a meaningful argumentative home:
– has no primary Canonical Central Claim;
– has no accepted primary_cc_relationship_type;
– retains its diagnostic relationship explanation and rejection reasons;
– has no valid default CC × T pair memberships;
– is logged with a reason;
– remains preserved in source and inventory records;
– is not placed in an "Uncategorised Speeches" chapter.

[Restates cardinality C9 in
compendium_StructuralDescription_relationshiptypes.md, Section 5.A; also
reflected in prompt_reorganized.md's Output Fidelity Rules and Phase 4
description.]

13. Complete index coverage

Every Canonical Theme must appear in theme_index.md.
Every persistent Canonical CC × T pair must have:
– one authoritative compendium section;
– one stable anchor;
– one corresponding pair entry under its Theme in theme_index.md.

Every shared Theme must also appear in the Theme Cross-Index.

[Reflected in prompt_reorganized.md's Structural Rules consistency-checks
paragraph.]

17. No shallow collapse

The final compendium must preserve:
– distinct canonical propositions;
– recurring and minority arguments;
– evidence richness;
– analogies and rhetorical devices;
– disagreement and qualification;
– explicit opposition and other speech-to-chapter relationship roles;
– temporal development;
– source provenance.

The corpus must not be reduced to a shallow thematic summary.

[Reflected in prompt_reorganized.md's Output Fidelity Rules.]


PART B — Rules constraining pipeline/LLM process behavior

3. Speech-to-Canonical-CC chapter assignment: best argumentative home

The Phase 3 classifier asks which supplied Canonical Central Claim provides the
speech's best argumentative home. It must not require the local central claim
to paraphrase or be semantically equivalent to the complete canonical CC.

A speech may be assigned because it performs exactly one primary role:

– supports
– specific_instance
– mechanism
– consequence
– qualification
– opposition
– historical_example
– application
– evidence

The selected role must be accompanied by a non-empty relationship explanation
stating what intellectual contribution the speech makes inside that chapter.
Topical similarity alone is insufficient. The classifier returns
UNCLASSIFIED only when none of the supplied CCs provides a meaningful
argumentative home; it must not reject a speech merely because its claim is
narrower, concrete, oppositional, qualified, historical, applied, or differently
worded.

The classification-confidence threshold remains an independent acceptance
rule. Broadening the meaning of chapter membership does not authorise Python or
the LLM to ignore the configured threshold.

[ALREADY INCORPORATED — see prompt_reorganized.md, RULES, Structural Rules,
"Best Argumentative Home Standard."]

8. Lossless remapping

Phase 4 must not replace, paraphrase, or discard local cc, t, arguments,
premises, evidence, analogies, or unverifiable claims.

It must preserve the Phase 1 record and add canonical mappings.

[ALREADY INCORPORATED — see prompt_reorganized.md, DIRECTIVES, Principle of
Fidelity to Underlying Data, "Output Fidelity Rules," and QUERY, Query
Elaboration, Five-Phase Pipeline, Phase 4.]

14. Deterministic index generation

The Theme Cross-Index, complete Theme Index, stable anchors, and pair-to-anchor
links must be generated deterministically from the canonical machine-readable
records.

The final-reduction LLM must not create a competing second copy of either index.

[Reflected in prompt_reorganized.md's LLM Prompt Rules ("Do not ask an LLM to
generate deterministic indexes, anchors, CC × T memberships...") and Phase 5
description.]

15. Canonical versioning and checkpoint validity

Canonical IDs and pair IDs are meaningful only relative to a specific
canonical model/version.

If canonical CCs, canonical Themes, mappings, relationship types,
relationship explanations, pair definitions, classification prompt/schema
versions, or bucket prompt/schema versions change, dependent Phase 4 and Phase
5 outputs must be invalidated and regenerated.

Idempotency must not preserve stale outputs built from superseded canonical
structures.

[ALREADY INCORPORATED — see prompt_reorganized.md, DIRECTIVES, Principle of
Least Agency, "Many-to-Many Relationship Materialization" (the
canonical_model_version trigger list), and QUERY, Query Elaboration,
Idempotency & Checkpoints.]

16. Canonical count targets

Corpus-size-relative CC and Theme count ranges are quality targets, not grounds
for merging semantically distinct entities merely to satisfy a numeric quota.

Semantic coherence, separability, provenance, and stable reuse take precedence
over an exact target count.

[Reflected in prompt_reorganized.md's Structural Rules, Targets.]


PART C — Rule 9 (internally mixed; presented whole)

Rule 9's structural bullets are already incorporated in prompt_reorganized.md's
"Relationship-Type Integrity" (RULES, Structural Rules); its final paragraph is
already incorporated in "Relationship-Type Preservation" (DIRECTIVES, Principle
of Least Agency). It is kept whole here, rather than split across Parts A and
B, since a rule this short reads more clearly as one unit than as two
fragments in different parts of this file.

9. Relationship-type integrity

For every categorised speech:

– primary_cc_relationship_type must be exactly one controlled value;
– primary_cc_relationship_explanation must be non-empty;
– the local-CC mapping must preserve both fields exactly;
– every primary-default Phase 4 source contribution must inherit both fields
  unchanged;
– each pair's relationship_type_speech_ids and relationship_type_counts must
  equal the accepted classifications contributing to that pair;
– every canonical argument's relationship_roles must be derived only from its
  validated source-contribution IDs;
– qualification and opposition contributions must remain visible as such and
  must be represented in Disagreements and Qualifications when relevant;
– the rendered Speech-to-Chapter Relationship Roles subsection must agree with
  the validated canonical-argument relationship_roles.

The LLM may explain and synthesise the implications of a role, but it may not
change the controlled type, reassign a source to another role, or turn
qualification or opposition into affirmative support.
