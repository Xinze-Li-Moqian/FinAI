**PROMPT**

*Financial Speech Compendium Pipeline*

Specification for a Python Map-Reduce-Summarisation Program using DeepSeek LLM

*Revision note: this version reorganizes a prompt into four main sections — Directives, Facts, Rules, and Query — based on what kind of instruction each piece of content is (a constraint on process/behavior, a domain fact, a checkable property of correct output, or the task itself). Query includes a Query Elaboration subsection holding the procedural detail — the phase-by-phase pipeline, its idempotency behavior, an intermediate-artifact map, and the evaluation script — through which the Objective and Final Outputs get fulfilled and checked.*

---

# DIRECTIVES

Directives state how the system — Python and the LLM together — is permitted to behave while producing its output: what it may and may not do, as opposed to what a correct finished output looks like (Rules) or what the domain's vocabulary is (Facts). This section states two governing principles first, followed by the specific behavioral constraints, persona instructions, tooling permissions, and API/runtime rules that implement them throughout the pipeline.

## Principle of Fidelity to Underlying Data

Every stage of canonicalisation and assembly must preserve source data as fully as possible. A stage may augment a record with derived structure — labels, mappings, IDs, confidence scores — but must never rewrite, paraphrase, or discard original content. Wherever the pipeline has a checkpoint (a phase boundary at which one representation of a speech is converted into another), convert this general principle into a mechanically checkable operation specific to that boundary, rather than relying on the general instruction alone. The following techniques accomplish this:

1. **Schema-constrained extraction** — require the LLM's output to conform to a schema in which original fields are copied into named slots, so preservation is a structural property of the output shape rather than a behavioral request.
2. **Verbatim-span extraction with citation/offset requirements** — require the LLM to point at source material (a location, an excerpt to be matched against the source) rather than retype it, so a downstream deterministic step performs the actual copy.
3. **Diff-based / round-trip validation as a pipeline gate** — after generation, mechanically compare output against source and reject or flag any divergence, rather than trusting the instruction to have been followed.
4. **Structured "immutable fields" contracts** — mark certain fields as read-only/pass-through in the output contract itself, so the model is never given an affordance to alter them.

The existing specification already embodies this principle and its techniques at specific phase boundaries; rather than restating that content here, see: the Objective bullet on provenance (QUERY), the Phase 1 no-canonicalisation rule and its evidence source-matching requirement (QUERY — Query Elaboration, Five-Phase Pipeline), and the Phase 4 remapping and losslessness-check requirements (QUERY — Query Elaboration, Five-Phase Pipeline).

The following complete sub-section of the original specification is relocated here in full, since it consists entirely of behavioral fidelity constraints:

### Output Fidelity Rules

- Do not collapse the corpus into a shallow or overly generic summary.
- Preserve the intellectual structure, evidence, analogies, rhetorical devices, recurring claims, and temporal evolution of the corpus.
- The final compendium must contain no "Uncategorised Speeches" section.
- The Evolution Over Time sub-section must be populated when the speech-date span exceeds one year.
- Do not fabricate evidence items, statistics, or quoted statements. If the LLM cannot extract a specific item from the transcript, it must omit that item rather than invent it.
- CC taglines must be concise (≤ 15 words) and must be distinct from the CC full proposition. The tagline is a memorable shorthand, not a repetition.
- Canonical CC chapters are authoritative. theme_index.md and the Shared Theme Cross-Index are navigation layers and must link to, not recreate, the authoritative synthesis.
- Preserve all distinct source-supported arguments even when they are minority, contradictory, or temporally superseded. Record disagreement and evolution rather than forcing a single harmonized conclusion.
- A canonical argument conclusion must not be created unless at least one mapped local argument supports it and the supporting speech filename is retained.

## Principle of Least Agency

The program must be designed to minimise unnecessary LLM discretion and maximise deterministic execution. Specifically:

1. Every LLM classification or labeling output must be validated against a fixed enumerated set; free text may justify a choice but must not define the category itself.
2. Each LLM call must decide one thing — never combine classification/structuring with content synthesis in a single call.
3. Each LLM call receives only the content within its assigned scope; it must never be shown material outside what it is authorized to act on.
4. All LLM output is a proposal, not a result: Python validates it against explicit constraints before acceptance, and rejects or flags output that fails.
5. All counting, grouping, ID assignment, ordering, and cross-referencing is performed by Python; it is never delegated to the LLM regardless of apparent simplicity.
6. Any step claimed to be deterministic must be verifiable as such — identical inputs must be checked to produce identical output.
7. Bucket construction for a CC × T pair is always complete — grouped, validated, and finalized — before any LLM synthesis call is made against that pair; the LLM is never called mid-construction or asked to help finish sequencing its own input.

### Many-to-Many Relationship Materialization

For every Many-to-Many relationship in the Entity-Relation model described in compendium_StructuralDescription_relationshiptypes.md, determine whether its membership depends on a judgment call — canonical-entity discovery (deduplicating local claims/themes into canonical CCs and Themes) or speech-to-CC classification (selecting a speech's best argumentative home) — rather than on deterministic computation. Whenever a judgment call is involved, materialize that relationship's membership as a persistent artifact tagged with a canonical_model_version (a content-derived version, not a manually incremented one — it must change automatically if any canonical entity, classification, relationship type, relationship explanation, pair definition, classification prompt/schema version, or bucket prompt/schema version changes). Downstream phases must consume this artifact and must not: (a) re-derive membership from raw speech text, or (b) reinterpret, upgrade, or reassign a stored relationship type once accepted. Any phase consuming an artifact must first confirm its canonical_model_version matches the current one; on mismatch, regenerate rather than reuse.

This directive's concrete embodiment in the present pipeline is the CC × Theme junction table (cc_theme_pairs.json) and the Speech × Canonical CC classification artifact (speech_classifications.json) from which it is deterministically derived; see the Objective bullet on the CC × T junction table (QUERY), Phase 3 and Phase 5 (QUERY — Query Elaboration, Five-Phase Pipeline), and Entity-Relationship Cardinalities (RULES — Structural Rules).

### Relationship-Type Preservation

Once a categorised speech's controlled relationship type and explanation are accepted in Phase 3, the LLM may explain and synthesise the implications of that role in later phases, but it may not change the controlled type, reassign a source contribution to a different role, invent a consensus, add source records, move content to a different CC × T pair, or convert a qualification or opposition contribution into affirmative support. This applies throughout Phase 4 propagation and Phase 5 synthesis; the checkable consequence of this directive — that every downstream record's relationship type and explanation match what was accepted in Phase 3 — is stated in RULES — Structural Rules, Relationship-Type Integrity.

## Roles and Persona

The LLM must be prompted to operate as:

- Expert AI Python programmer
- Expert analyst of financial and economic speeches
- Expert in investment theory

## Tools
<!-- Analogy: like declaring Prolog external predicates — Permitted = declared foreign predicates, Prohibited = predicates that don't exist / always fail -->

### Permitted

- LLM semantic reasoning: DeepSeek V4 Flash
- Cosine similarity
- String matching
- Sentence-transformer embeddings using one configured financial-domain embedding model consistently for CC deduplication, Theme deduplication, classification diagnostics, and evaluation.
- Deterministic Python grouping, indexing, anchor generation, referential-integrity checks, hashing, and checkpoint dependency validation.

### Prohibited

- Web search (no external verification at runtime)

## Model & API Configuration

The values of MODEL, BASE_URL, API_KEY_ENV_VAR, and MIN_MAX_TOKENS are declared once, as constants, under FACTS — Configuration Block. They are cross-referenced here because each also carries a behavioral constraint on how the system is permitted to run, distinct from the fact of what value it holds:

- **MODEL** and **BASE_URL** bound which engine and endpoint the pipeline is permitted to call — no other model or base URL may be substituted, regardless of apparent equivalence.
- **API_KEY_ENV_VAR** names the environment variable the key must be read from. The key itself must be loaded at runtime from a `.env` file via `python-dotenv`; it must never be hardcoded, logged, or embedded in checkpoint or output files.
- **MIN_MAX_TOKENS** sets a floor enforced on every LLM call (see LLM Prompt Rules: "Always specify max_tokens ≥ 8 000 on every API call") — a truncated response is a process failure, not a property of a finished compendium, which is why the floor lives here rather than in Rules.

API compatibility: The DeepSeek V4 Flash endpoint is OpenAI-compatible. Use the openai Python SDK (already in conda_list.md) with base_url and api_key overrides — do not use a custom HTTP client.

Temperature: Set temperature=0 (see TEMPERATURE in FACTS — Configuration Block) on all LLM calls to maximise reproducibility and determinism. Do not expose temperature as a user-configurable parameter.

Thinking mode: Disable the model's extended-thinking/reasoning mode on every API call (pass the provider's disable parameter, e.g. `extra_body={"thinking": {"type": "disabled"}}` for a DeepSeek-compatible endpoint). This pipeline's prompts already decompose every LLM call into one narrow, scoped decision (see Principle of Least Agency) and require a single JSON-only response with no preamble; a visible reasoning phase is neither required by that contract nor accounted for in MIN_MAX_TOKENS, and a reasoning-capable model left in its default thinking mode can consume its entire token budget on hidden reasoning and return no usable content at all. If the configured MODEL is later changed to one with no thinking-mode toggle, this constraint does not apply, but MIN_MAX_TOKENS must then be re-validated empirically against that model's actual reasoning-plus-content token usage before relying on it.

## LLM Prompt Rules

- Always instruct the LLM to return only JSON (no preamble, no Markdown fences) when structured data is required.
- Always instruct the LLM to reason as a financial speech analyst with expertise in investment theory.
- Always specify max_tokens ≥ 8 000 on every API call.
- Set temperature = 0 on all API calls.
- Disable extended-thinking/reasoning mode on all API calls (see Model & API Configuration: Thinking mode).
- Strip any \`\`\`json ... \`\`\` fences from LLM responses before calling json.loads(). Wrap all json.loads() calls in try/except and apply the recursive batch-splitting retry (see Phase 3).
- JSON extraction must be shape-validated, not just syntax-validated. Every prompt requiring structured output must state explicitly whether the top-level response is a JSON object ({}) or a JSON array ([]), and the extraction function must accept that expected shape as a parameter and enforce it as a hard constraint — returning only a match of the declared shape, and raising an error (to be caught by the existing retry/halving logic) if no valid match of that shape exists, even when a valid match of the *other* shape is present in the same text. A response that parses successfully but is the wrong shape must be treated as an extraction failure, not a success. Do not use a single bracket-matching heuristic (e.g. "try {} first, then []" or "prefer whichever candidate is structurally larger") as the sole decision rule for which shape to return: a well-formed JSON array of objects always contains a valid, parseable object as its first element, and a well-formed JSON object often contains a long nested array, so naive shape inference fails in both directions and will silently return a fragment of the correct answer instead of the correct answer itself.
- Validate semantic constraints after JSON parsing: CC text contains a predicate, Theme text is a noun phrase without a finite verb where practicable, IDs are unique, referenced IDs exist, confidence values are within [0,1], and required arrays are non-empty where mandated.
- Do not ask an LLM to generate deterministic indexes, anchors, CC × T memberships, or file-integrity checks. Build these in Python from validated structured records.
- Do not use an LLM in Phase 4 to rewrite source content. If formatting with an LLM is unavoidable, compare the output against the source JSON and reject any loss, addition, or semantic alteration.
- Include prompt_version and schema_version in every checkpoint-producing prompt and checkpoint record so stale outputs can be detected.

## Compatibility Rules

- Compatible with Python Spyder IDE (no top-level asyncio.run(); use synchronous calls or a \_\_main\_\_ guard).
- Use only libraries present in conda_list.md.
- Do not import any library not listed in conda_list.md.
- Use os.path and pathlib for all file paths to ensure Windows/POSIX compatibility. Never hard-code path separators.
- Avoid f-strings with backslashes inside the braces (Python < 3.12 incompatibility). Use a variable to hold the value before embedding it in the f-string.

## Logging & Error Handling

- Log the start and end of every phase, the number of speeches processed, and the number of LLM API calls made.
- Log every retry attempt (with batch size and reason) at WARNING level.
- Log every skipped speech (idempotency skip) at DEBUG level.
- Use Python's built-in logging module. Configure a file handler writing to logs/pipeline.log and a stream handler to stdout. Log level: INFO by default; DEBUG when a --debug flag is passed.
- Never silently swallow exceptions. If a phase fails fatally, log the full traceback and exit with a non-zero return code.
- Log canonical-model version changes, entity merges/splits, ID reuse, checkpoint invalidations, classification confidence distributions, uncategorised speeches, orphan mappings, broken anchors, and provenance failures.

---

# FACTS

Facts state the domain's vocabulary and the static, given data of the pipeline — content that does not change based on how the program executes, as opposed to constraints on process (Directives) or checkable properties of output (Rules).

## Attached Files

- **Requirements:** conda_list.md
- **Example input:** 20211111_The Cost of Money.md
- **Example outputs:** compendium_model.md, unverifiable_claims_model.md, theme_index.md, integrity_report.json
- **Output structure description:** compendium_StructuralDescription_relationshiptypes.md — defines the nested hierarchy of levels/entities, their roles, their relationsips and entity-relationship cardinalities.
- Current implementation for comparison (when supplied): speech_processing_program_notree.py. If the implementation conflicts with this specification, this specification governs.

## Definitions

**Canonical** — Normalised and deduplicated across the corpus.

**Abbreviations:** CC = canonical central claim | T = canonical theme | cc = central claim (per-speech) | t = theme (per-speech)

### Central Claim (CC / cc)

A full proposition with a verb, asserting the speaker's overarching thesis for a speech or for a canonical cluster of speeches. A good Central Claim is specific enough that some speeches in the corpus clearly do not belong to it. Wherever semantically natural, a canonical CC should be decomposable as [canonical Theme noun phrase] + predicate/verb + [canonical Theme noun phrase]. This is a modelling preference, not a compulsory two-Theme template: do not invent or force artificial Themes merely to satisfy the grammatical pattern.

### Theme (T / t)

A noun phrase, with no verb, naming a specific topical sub-domain. Themes are canonical concepts shared across Central Claims and function as corpus-wide navigation keys. A Theme may appear as the subject, object, mechanism, outcome, institution, asset, policy, or other concept in a Central Claim. Themes must be narrow enough to remain analytically meaningful; where possible, a Theme should naturally participate in several CCs, but a valid Theme must not be merged or broadened solely to meet a numerical sharing target.

### Argument

A structured logical unit interpreted within one specific Canonical Central Claim × Canonical Theme context. At the speech level, an argument contains one or more premise clauses and one conclusion clause. At the corpus level, argument conclusions are canonical and deduplicated across speeches within their CC × T context. The authoritative ownership rule is: Canonical CC × Canonical T → one or more canonical argument conclusions. The same wording under a different CC × T context must not be merged automatically if its meaning or inferential role differs.

### Evidence

Empirical or illustrative grounding for the premises: facts, statistics, anecdotes, quoted claims, examples, historical precedents, or cited data.

### Notable Analogies & Rhetorical Devices

Significant analogies, metaphors, thought experiments, extended illustrative narratives, slogans, or rhetorical frames used to support or communicate an argument.

### CC × T Bucket

A runtime aggregation or junction container representing one canonical Central Claim paired with one canonical Theme. A bucket is not text and is not an entity contained inside a speech. Speeches or speech-level argument contributions are assigned to the bucket; the bucket supplies the source material for one Theme section inside the corresponding CC chapter.

### Primary and Secondary CC Assignment

Every confidently categorised speech has exactly one primary canonical CC. By default, its runtime bucket memberships are (primary CC, each assigned canonical Theme). A speech must not be placed under additional CCs merely because one of its Themes is shared globally. Cross-CC contribution is permitted only if the program explicitly creates a separate secondary_cc_contributions mapping with confidence, rationale, and source-level argument references; this feature is disabled by default.

### Publication Architecture

Canonical Central Claims are the authoritative argument chapters. Canonical Themes are sections inside those chapters. Theme-oriented navigation is secondary: it must gather and link the relevant CCs and argument conclusions without replacing, rewriting, or duplicating the authoritative chapter synthesis.

### Theme Index / Theme View

A complete secondary view listing every canonical Theme, every CC × T pairing in which it occurs, and the canonical argument conclusions belonging to each pairing. It must contain stable hyperlinks to the corresponding sections in compendium.md. It may summarize navigation metadata, but it must not duplicate the full premises, evidence, analogies, or Evolution Over Time text.

### Provenance

The traceable link from every canonical argument, premise synthesis, evidence item, analogy, and unverifiable claim back to one or more source speech filenames and, where feasible, an exact transcript excerpt or deterministic character/line location. Every canonical argument conclusion and every evidence item must additionally carry its own list of source_contribution_ids — the specific source contributions it was built from — as a field distinct from, and in addition to, the source speech filenames it cites; a filename alone is not sufficient provenance. Relationship-role records are likewise traceable to the exact source contributions from which they were deterministically derived.

### Speech-to-Canonical-CC Relationship Type

The explicit argumentative role that a categorised speech plays relative to its one primary Canonical Central Claim chapter. The controlled vocabulary is:

- **supports** — the speech directly argues that the Canonical Central Claim is true.
- **specific_instance** — the speech presents a narrower, concrete, or more specific instance of the broader Canonical Central Claim.
- **mechanism** — the speech explains a process through which the Canonical Central Claim operates or could become true.
- **consequence** — the speech explains a result, implication, or downstream effect of the Canonical Central Claim.
- **qualification** — the speech limits, conditions, refines, or adds an exception to the Canonical Central Claim.
- **opposition** — the speech challenges, disputes, or presents contrary evidence against the Canonical Central Claim.
- **historical_example** — the speech supplies a historical illustration, analogy, or precedent that bears on the Canonical Central Claim.
- **application** — the speech applies the Canonical Central Claim to a specific policy, market, institution, country, period, or event.
- **evidence** — the speech mainly supplies empirical or illustrative evidence relevant to the Canonical Central Claim rather than independently restating its full thesis.

## Inputs

**Type:** Markdown (.md)

**Location:** transcripts/ folder

**Filename structure:** YYYYMMDD_Title.md

- **YYYYMMDD** = date of the speech (used to populate Evolution Over Time)
- **Title** = speech title (a strong hint of the central claim, not a literal statement of it)

**Approximate size range:** 1 KB – 112 KB (average ≈ 20 KB)

**Content format:** Unstructured raw transcript text

**Corpus size:** ≈ 900 transcripts (relevant to token-cost planning)

Note on title semantics: The filename Title is a strong hint of — but not a literal statement of — the central claim of the speech. The LLM must infer the actual CC from the transcript body; it must not copy the filename title verbatim as the CC.

## Configuration Block

All tuneable parameters must be centralised in a single configuration section at the top of the script:

MODEL = "deepseek-v4-flash"

BASE_URL = "https://api.deepseek.com/v1"

TRANSCRIPTS_DIR = "transcripts"

OUTPUT_DIR = "output"

CHECKPOINTS_DIR = "checkpoints"

BATCH = 50

EMBEDDING_MODEL_NAME = "mukaj/fin-mpnet-base"

CC_DEDUP_THRESHOLD = 0.85

THEME_DEDUP_THRESHOLD = 0.85

CLASSIFICATION_CONFIDENCE_MIN = 0.70

MAX_THEMES_PER_SPEECH = 3

ALLOW_SECONDARY_CC_CONTRIBUTIONS = False

WRITE_THEME_INDEX = True

RECONSOLIDATE = False

CC_RATIO_MIN = 0.06

CC_RATIO_MAX = 0.08

THEME_RATIO_MIN = 0.12

THEME_RATIO_MAX = 0.16

TARGET_COUNTS_ARE_HARD = False

BUCKET_SUBGROUP_SIZE = 10

PROMPT_VERSION = "2.0"

SCHEMA_VERSION = "2.0"

TEMPERATURE = 0

MIN_MAX_TOKENS = 8000

API_KEY_ENV_VAR = "DEEPSEEK_API_KEY"

CC_PER_BATCH_MIN = 3

CC_PER_BATCH_MAX = 6

T_PER_BATCH_MIN = 8

T_PER_BATCH_MAX = 11

ASSEMBLY_BUCKET_LIMIT = 20 # max speeches per CC×T before two-pass assembly

All tunable parameters, including the green additions above, must be centralized in this configuration block and must not be redefined inline inside functions. The program must include the configuration values in dependency manifests so checkpoint validity is reproducible.

---

# RULES

Rules state properties a correct finished output must have — content checkable by inspecting the output itself, as opposed to constraints on how the system is allowed to behave while producing it (Directives). These take precedence over any LLM-generated content.

## Structural Rules

### Targets

- Canonical CC count has a diagnostic target of 6%–8% of total corpus size; semantic coherence takes precedence over the target.
- Canonical Theme count has a diagnostic target of 12%–16% of total corpus size; semantic coherence takes precedence over the target.
- Total target: calculate the 6%–8% CC range and 12%–16% Theme range from the actual runtime corpus size and report deviations. Do not repeatedly force the LLM to merge or split valid entities solely to land inside the range. If the result remains outside range after semantic deduplication, log the deviation for review.
- *Worked examples (not fixed values — recompute per actual corpus size): for a 950-speech corpus, 6–8% → 57–76 CCs, and 12–16% → 114–152 themes. For a 271-speech corpus, the SAME percentages give 16–22 CCs and 33–43 themes — a different absolute number from a different corpus size, using the same rule.*
- The two corpus-wide ratios imply approximately two distinct canonical Themes per canonical CC on average, before accounting for Theme sharing. Do not impose a separate 3–5-Themes-per-CC quota unless explicitly configured; observed CC × T mappings determine the actual count.

### Entity-Relationship Cardinalities

Defined authoritatively in compendium_StructuralDescription_relationshiptypes.md (Section 5, Tables A and B). Key constraints:

- Canonical CC and canonical Theme have a many-to-many relationship implemented through cc_theme_pairs.json: one CC may have many Themes, and one Theme may occur under many CCs.
- One canonical CC × T pair → one authoritative rendered Theme section and one or more canonical argument conclusions. The pair/bucket is a junction and aggregation object, not a paragraph and not a child entity stored inside a speech.
- One confidently categorised speech → exactly one primary canonical CC and 1–3 canonical Themes; one uncategorised speech → zero CCs and zero valid buckets. Default runtime bucket memberships are (primary CC, each assigned Theme). Global Theme sharing does not by itself create multi-CC speech assignment. All default CC × T pair memberships for a categorised speech are under that same primary CC.
- One CC × T pair → many speech contributions; one speech → one or more bucket memberships under its primary CC. Use a separate secondary_cc_contributions relation only when explicitly enabled and supported at the argument level. A secondary contribution applies to a specific local argument, premise, evidence item, or rhetorical device — not automatically to the whole speech — and requires its own provenance and rationale; it must never alter the speech's primary CC assignment. The persistent record schema for this relation is defined in compendium_StructuralDescription_relationshiptypes.md, Section 1.D (secondary_cc_contributions.json) and Section 5.A (cardinalities C27, C37).
- Every canonical argument conclusion belongs to exactly one CC × T pair in the canonical model, though source-level arguments may contribute to more than one canonical conclusion only when the mappings explicitly record that fact. Near-identical canonical argument conclusions arising in different CC × T pair contexts may be linked as related propositions, but must not share one canonical argument ID unless they belong to the same exact pair.
- Every canonical argument conclusion must retain at least one Evidence & Support item (C18: 1 → 1..many). Phase 5 must reject a canonical argument conclusion — not render it with a placeholder such as "no evidence item was retained" — if bucket assembly and synthesis leave it with zero validated evidence items.
- One speech → 0..many unverifiable claims (C16).

### Speech-to-Canonical-CC Relationship Type Assignment

Every categorised speech must have exactly one controlled primary relationship type, drawn from the vocabulary defined in FACTS — Speech-to-Canonical-CC Relationship Type, and a non-empty relationship explanation.

### Best Argumentative Home Standard

The Phase 3 classifier asks which supplied Canonical Central Claim provides the speech's best argumentative home; it must not require the local central claim to paraphrase or be semantically equivalent to the complete canonical CC. Exact semantic equivalence is not required. Topical similarity alone is insufficient. The classifier returns UNCLASSIFIED only when none of the supplied CCs provides a meaningful argumentative home; it must not reject a speech merely because its claim is narrower, concrete, oppositional, qualified, historical, applied, or differently worded. The classification-confidence threshold remains an independent acceptance rule: broadening the meaning of chapter membership does not authorise Python or the LLM to ignore the configured threshold.

### Relationship-Type Integrity

For every categorised speech: the local-CC mapping must preserve the accepted relationship type and explanation exactly; every primary-default Phase 4 source contribution must inherit both fields unchanged; each pair's relationship_type_speech_ids and relationship_type_counts must equal the accepted classifications contributing to that pair; every canonical argument's relationship_roles must be derived only from its validated source-contribution IDs, and every one of the argument's own source_contribution_ids must appear in exactly one role — no contribution may be silently omitted from every role; qualification and opposition contributions must remain visible as such and must be represented in the argument's Disagreements and Qualifications content where relevant; and the rendered Speech-to-Chapter Relationship Roles subsection (see QUERY — Final Outputs and Verification) must agree with the validated canonical-argument relationship_roles. The corresponding behavioral constraint on the LLM is stated in DIRECTIVES — Relationship-Type Preservation.

### Evidence Tagging

- Every evidence item must carry exactly one status: ✅ Verified, ⚠️ Unverifiable, or ❌ Disputed, plus a verification_basis. Because the pipeline performs no web search, ✅ Verified means that the transcript supplies an explicit identifiable source, quotation, datum, or internally checkable support; it does not mean the program independently verified the claim against external evidence.
- Tags are provisionally assigned during Phase 1 from transcript content and the model's internal reasoning only. They must be presented as workflow labels, not external fact-check verdicts. MEMORY must remain a separate advisory field and must not change the evidence status or determine inclusion.
- Every ⚠️ Unverifiable factual evidence item and every explicit Phase 1 unverifiable claim must appear in unverifiable_claims.md. No item may be omitted because MEMORY=Corroborated.

Consistency checks at Phase 5: assert that every Phase 1 unverifiable record appears in unverifiable_claims.md; every canonical argument and evidence item has provenance; every classification references valid IDs; every bucket references one valid CC and one valid Theme; every compendium section has one unique anchor; every theme_index.md entry resolves to that anchor; every persistent CC × T pair has exactly one corresponding pair entry under its Theme in theme_index.md; and no canonical pair is orphaned or duplicated.

---

# QUERY

The Query is the actual task being requested — everything above states the vocabulary (Facts), what a correct result looks like (Rules), and how the system may behave while getting there (Directives). Objective and Final Outputs and Verification state the request itself; Query Elaboration, below, is the procedural detail through which that request is carried out and checked — it does not add a new ask.

## Objective

Write a Python program using the libraries available in conda_list.md that:

- Processes a folder of single-speaker finance, economics, and investment transcripts into a structured compendium and a structured list of unverifiable claims.
- Uses a Large Language Model as a financial speech-analysis assistant in a five-phase "map-reduce-summarisation" pipeline with phases: Summarize → Inventory → Consolidate → Remap → Assemble.
- Produces output rich enough to preserve the intellectual structure, evidence, analogies, rhetorical devices, recurring claims, and temporal evolution of a large transcript corpus.
- Does NOT collapse the corpus into a shallow or overly generic summary.
- Performs no web search. Any Verified, Unverifiable, or Disputed labels are produced as part of the transcript-analysis workflow and are not the result of external web verification by the program.
- Preserves Canonical Central Claims as the authoritative chapter structure while producing a complete Theme index or Theme-oriented view that gathers and links all CCs and argument conclusions involving each Theme.
- Creates an explicit machine-readable CC × T junction table so that the many-to-many CC–Theme relationship, bucket membership, and rendered section ownership are deterministic rather than inferred from prose.
- Preserves source provenance and local speech-level wording throughout canonicalisation and assembly; canonical remapping must add labels and mappings rather than silently rewrite or discard local intellectual content.

## Final Outputs and Verification

Files: compendium.md, theme_index.md, unverifiable_claims.md, and integrity_report.json

**Type:** Markdown (.md) for the first three; JSON for integrity_report.json

**Location:** output/ folder

### compendium.md

Must follow the structure of compendium_model.md and the authoritative hierarchy in compendium_StructuralDescription_relationshiptypes.md. The rendered hierarchy is Compendium → Canonical CC chapter → Canonical Theme section → canonical argument conclusion. Every CC chapter and every CC × T section must have a stable, deterministic Markdown/HTML anchor that can be linked from theme_index.md.

Each canonical argument conclusion additionally renders a **Speech-to-Chapter Relationship Roles** subsection: a deterministically generated list of every controlled relationship type (see FACTS — Speech-to-Canonical-CC Relationship Type) represented among the argument's validated source contributions, with the source speech filenames, source-contribution IDs, and stored relationship explanations for each role. Every one of the argument's own source contributions must appear under exactly one role — none may be silently left out of the subsection, and none may appear under a role other than its validated type. Where the represented roles include qualification or opposition contributions, the argument also presents them in a **Disagreements and Qualifications** subsection so that limiting, conditioning, or contrary contributions remain visible as such rather than being absorbed into the affirmative synthesis. The checkable requirements for both subsections are stated in RULES — Structural Rules, Relationship-Type Integrity; the behavioral constraint on the LLM while producing them is stated in DIRECTIVES — Relationship-Type Preservation.

### theme_index.md

Must list every canonical Theme, including Themes associated with only one CC. Under each Theme, list every related Canonical Central Claim and every canonical argument conclusion in the corresponding CC × T bucket, with links to the authoritative section in compendium.md. Shared Themes may additionally display the number of parent CCs. Do not reproduce full synthesis or evidence text.

### unverifiable_claims.md

Must follow the structure of unverifiable_claims_model.md. Each entry must include: SPEECH_REF: {filename} | CLAIM: {claim} | REASON: {reason} | MEMORY: {memory_check: Corroborated/Contradicted/NoInternalBasis}. The MEMORY field is advisory metadata only. No unverifiable claim may be removed because the model labels it Corroborated; every Phase 1 unverifiable claim must remain auditable in this file.

### integrity_report.json

A machine-readable, mandatory verification artifact generated automatically at the end of Phase 5, for every run — unlike the Evaluation Script below, it is not optional and not a separate standalone invocation. Its status gates whether the run is considered complete.

Fields:
- schema_version, prompt_version — version stamps matching the run's configuration.
- generated_at — ISO 8601 UTC timestamp.
- status — "PASS" if errors is empty, otherwise "FAIL". A FAIL must not be silently treated as a complete run.
- errors — list of specific, human-readable violation strings; any non-empty list forces status to "FAIL".
- warnings — list of human-readable advisory strings (for example, a count of uncategorised speeches). Warnings never affect status; being uncategorised is a legitimate outcome, not a defect.
- checks — an object with exactly these seven boolean keys, each true only if no error of the corresponding kind was found:
  - classification_referential_integrity — every categorised speech's primary_cc_id, theme_ids, and bucket-membership pair_ids reference real canonical entities.
  - pair_referential_integrity — no duplicate pair IDs or duplicate CC×Theme pairs; every pair's cc_id and theme_id are valid; every pair has both a synthesis and a rendered authoritative section (no orphaned or duplicated pair).
  - anchor_integrity — every pair's authoritative anchor exists in compendium.md, and all anchors are unique.
  - theme_index_completeness — theme_index.md's set of anchors and set of pair IDs each exactly equal the persistent pairs' own sets, in both directions: no persistent pair is missing from theme_index.md, and no entry in theme_index.md references an anchor or pair ID that doesn't exist.
  - provenance_coverage — every synthesized argument has at least one source_contribution_id and at least one source_speech_filename, every referenced filename corresponds to a real speech, and every evidence item carries its own provenance.
  - relationship_type_integrity — every source contribution's relationship type matches what its speech was actually classified with; every argument's relationship-role entries reference only contributions that actually carry the stated type; and the set of contribution IDs covered by an argument's relationship roles exactly equals that argument's own set of source_contribution_ids — no contribution may be silently omitted from every role, and no role may reference a contribution outside the argument's own set.
  - unverifiable_completeness — every explicit Phase 1 unverifiable claim survives into the published unverifiable_claims.md.
- referential_integrity_rate — the fraction of the seven checks above that passed (passes ÷ 7).
- counts — an object of raw tallies: canonical_ccs, canonical_themes, pairs, synthesized_pairs, compendium_anchors, theme_index_pairs, unverifiable_records, uncategorised_speeches.

**Verification:** compendium.md, theme_index.md, and unverifiable_claims.md are verified by the Phase 5 Consistency checks (RULES — Structural Rules, Evidence Tagging) and by integrity_report.json above, which is the mandatory, automatic implementation of those same checks; the Evaluation Script below is a separate, optional, standalone script computing a broader set of quality metrics and is not a substitute for integrity_report.json. Those sections state the specific checks; this section is only a pointer to them, not a restatement.

## Query Elaboration

This subsection holds the procedural detail through which the Objective and Final Outputs above actually get fulfilled and checked: the phase-by-phase pipeline mechanism, its idempotent re-run behavior, a reader's map of the intermediate artifacts it produces, and the standalone script that verifies the result. None of it introduces a new ask — it elaborates the one ask already stated in Objective — which is why it sits here as part of Query rather than as a separate main section.

*Note on redundancy: the Five-Phase Pipeline description below restates, in narrative form, a number of constraints already stated under DIRECTIVES and RULES above — for example, ordering constraints, cardinality constraints, and fidelity constraints. This overlap is intentional, not an error to reconcile: the phase-by-phase narrative exists to make the construction sequence and per-step behavior easier to follow and synthesize correctly, not to introduce a second, independent source of requirements. Treat the narrative as authoritative guidance for sequencing and process; where its wording differs from a Directive or Rule stated above, DIRECTIVES and RULES govern.*

### Five-Phase Pipeline

*Kept intact and un-fragmented below, including its embedded fidelity and least-agency content, per instruction not to pull intermediate-output verification logic out of its per-phase context. See Directives above for the general principles this content embodies, and Intermediate Outputs and Verification below for a summary map of the artifacts produced here.*

#### Phase 1 — Summarize

For each transcript, call the LLM once to produce a per-speech structured JSON summary. Preserve the transcript filename, parsed date, a stable speech_id, and a source-file hash in addition to the intellectual fields below:

- Per-speech central claim (cc)
- Per-speech themes (t) — noun phrases only
- Per-speech argument conclusions with their premises, each explicitly attached to one local theme
- Evidence items, each with status (✅ Verified / ⚠️ Unverifiable / ❌ Disputed), verification_basis, source speech filename, and an exact source_excerpt when available. The program must verify by string matching that quoted excerpts occur in the transcript; otherwise mark source_match=false.
- Notable analogies and rhetorical devices
- Unverifiable claims (SPEECH_REF, CLAIM, REASON, MEMORY), retained in full regardless of the MEMORY value

Output format: Each Phase 1 result must be saved as a JSON file (one file per speech) in checkpoints/phase1/. The JSON schema must mirror the per-speech fields in compendium_StructuralDescription_relationshiptypes.md (Section 5.B, S1–S11) and must also include speech_id, date, source_hash, source_excerpt/source_match fields, and a schema_version. Validate required keys and value types before writing the checkpoint.

Phase 1 must not canonicalise, rename, merge, or discard local cc, t, argument, premise, or evidence wording. It is a source-analysis phase, not a corpus-normalisation phase.

#### Phase 2 — Inventory

Aggregate all valid Phase 1 JSON files into a single master_inventory.json. Each record corresponds to one speech and stores the complete Phase 1 structure, not only flattened labels: filename, date, speech_id, source_hash, cc text, local t records, argument conclusions, premises, evidence, analogies, and unverifiable claims.

Near-duplicate diagnostics: encode both local cc texts and local t texts with EMBEDDING_MODEL_NAME and compute cosine similarity using separate CC_DEDUP_THRESHOLD and THEME_DEDUP_THRESHOLD values. Record candidate duplicate pairs for Phase 3 review, but do not merge or delete entities in Phase 2. Do not use TF-IDF for semantic deduplication when the configured sentence-embedding model is available.

Write an inventory manifest containing the transcript count, sorted source hashes, schema version, prompt version, model name, and relevant configuration values. Downstream checkpoint validity must depend on this manifest.

#### Phase 3 — Consolidate

Discover canonical Central Claims (CC) and canonical Themes (T) separately from master_inventory.json, then classify speeches and construct the authoritative CC × T relationship model.

- CC discovery: cluster only the per-speech cc texts and produce canonical full propositions with verbs. The 3–6-per-batch range and corpus-wide percentage range are diagnostic granularity targets, not permission to merge semantically distinct claims or split coherent claims solely to hit a count.
- T discovery: cluster the actual per-speech t texts independently of CC discovery and produce canonical noun-phrase Themes. Do not ask the LLM to invent the Theme inventory from CC wording alone. The 8–11-per-batch and corpus-wide percentage ranges are diagnostic targets; semantic validity takes precedence over count compliance.
- Cross-indexing: model CC and Theme as a many-to-many relationship through an explicit junction record for each observed CC × T pair. Each pair must have a stable pair_id, cc_id, theme_id, source_speech_ids, and later its canonical argument_conclusion_ids.
- Canonical mappings: save local_cc → canonical_cc and local_t → canonical_t mapping records, including similarity/confidence, rationale, aliases, and source speech IDs. Canonical IDs must be unique and referentially valid.
- Speech classification: for every speech, return exactly one primary cc_id when confidence is at or above CLASSIFICATION_CONFIDENCE_MIN, plus 1–3 canonical theme_ids. Also return confidence scores and a concise rationale. If no CC clears the threshold, classify the speech as uncategorised rather than forcing a poor match.
- Bucket membership: by default, create one membership for each (speech.primary_cc_id, assigned_theme_id) pair. Do not infer that a speech belongs to multiple CCs merely because a Theme is globally shared. Optional secondary cross-CC contributions require a separate, explicitly enabled mapping at the argument level, per the secondary_cc_contributions.json schema in compendium_StructuralDescription_relationshiptypes.md, Section 1.D.
- Optional grammatical decomposition: where semantically reliable, store each canonical CC as subject_theme_ids + predicate + object_theme_ids in addition to its full proposition. This decomposition supports analysis but does not replace the full CC text and must not be forced when the claim has a different logical form.
- Canonical stability: compute a semantic fingerprint for every canonical CC and Theme. When reconsolidating, preserve an old ID where the entity remains materially the same; otherwise record superseded_by / merged_from relationships so links and prior checkpoints can be audited.

LLM prompts for consolidation: provide CC-discovery calls with the relevant per-speech cc texts and provide Theme-discovery calls with the relevant per-speech t texts, including speech IDs for provenance. Do not send raw transcripts. Require the declared top-level JSON shape and validate every returned object against the expected schema.

Retry logic: If the LLM returns malformed JSON, re-split the batch in half and retry each half independently. Continue halving recursively until the call succeeds or the batch size reaches 1, at which point log the failure and skip that record.

Checkpoint: save checkpoints/phase3/canonical_ccs.json, canonical_themes.json, local_to_canonical_mappings.json, speech_classifications.json, and cc_theme_pairs.json before proceeding. The cc_theme_pairs.json file is the authoritative junction table used by Phase 4, Phase 5, the Theme Cross-Index, and theme_index.md.

#### Phase 4 — Remap

For each speech, create a remapped representation by preserving every local Phase 1 field and appending its canonical CC ID, canonical Theme IDs, mapping confidence, pair IDs, and bucket memberships. Do not replace or paraphrase the local cc, t, argument, premise, evidence, or analogy text.

Perform remapping deterministically in Python from the validated JSON mappings whenever possible. An LLM may format Markdown only if required, but it must not be asked to reinterpret content, and the resulting record must pass a field-by-field losslessness check against Phase 1.

Map each local argument to the canonical Theme that owns it. If an argument cannot be mapped confidently, retain it with an UNMAPPED_ARGUMENT flag rather than dropping it.

Storage: save a lossless remapped JSON record and, optionally, a rendered Markdown view for each speech in checkpoints/phase4/. Each record maps 1-to-1 with the source transcript and contains explicit bucket_memberships. A speech has memberships, but it does not contain bucket entities.

Uncategorised speeches: if a speech cannot be confidently assigned to a canonical CC, log it to checkpoints/phase4/uncategorised.jsonl with the best candidates, confidence scores, and reason. It receives zero valid CC × T bucket memberships and is excluded from the final hierarchy. The final compendium must not contain an "Uncategorised" chapter.

#### Phase 5 — Assemble

Construct compendium.md, theme_index.md, unverifiable_claims.md, and integrity_report.json from the validated Phase 4 records and the authoritative cc_theme_pairs.json junction table.

- Construct CC × T buckets deterministically before any LLM synthesis. Group only the speech-level arguments, premises, evidence, analogies, and dates mapped to each explicit pair_id; do not ask the LLM to discover bucket boundaries from a mixed global chunk. Within each bucket, Python additionally groups the validated source contributions by controlled relationship type before any synthesis call, and the bucket input handed to the LLM includes the resulting relationship_type_counts and source_contributions_by_relationship_type alongside the validated source IDs, filenames, excerpts, and local argument content.
- For each CC × T bucket, synthesise canonical argument conclusions, premises, evidence, analogies, rhetorical devices, and temporal development across that bucket's mapped source contributions, including the Speech-to-Chapter Relationship Roles and, where applicable, Disagreements and Qualifications content described in QUERY — Final Outputs and Verification. One pair_id must render as exactly one Theme section under its CC chapter, although that section may contain many canonical argument subsections.
- Populate Evolution Over Time from source dates. If multiple speeches span more than one year, provide a longitudinal synthesis. If multiple speeches span one year or less, state whether the reasoning is stable or changes within the period. If only one speech supports the argument, state the date and explicitly note that no cross-speech evolution can be inferred.
- After the last CC chapter, append one deterministically generated Shared Theme Cross-Index listing Themes that occur under more than one CC. Generate this index in Python from cc_theme_pairs.json; do not also ask the final-reduction LLM to generate it.
- Write unverifiable_claims.md by aggregating every unverifiable claim record from Phase 1, deduplicating only exact duplicate records with the same speech reference and claim text. MEMORY is advisory and must never be used to discard a claim.
- Authoritative chapters: render one chapter per canonical CC. Within each chapter, order its Theme sections deterministically and include a stable anchor such as cc-<id>-theme-<id> before each section.
- Complete Theme view: generate theme_index.md from cc_theme_pairs.json after compendium.md is finalized. List every Theme, every associated CC, and every canonical argument conclusion under the pair, linking each entry to the authoritative compendium anchor. Do not duplicate full evidence or synthesis text.
- Cross-index consistency: every link in theme_index.md and the Shared Theme Cross-Index must resolve to exactly one existing compendium anchor. Every compendium CC × T section must appear in theme_index.md.
- Canonical argument provenance: every synthesized argument conclusion and evidence bullet must cite one or more source speech filenames and must carry its own non-empty list of source_contribution_ids identifying the specific source contributions it was built from. Filenames alone do not satisfy this requirement. No source-free canonical argument may be emitted, and no argument or evidence item may omit its source_contribution_ids even when its filenames are present.
- Integrity verification: after compendium.md, theme_index.md, and unverifiable_claims.md are finalized, run the checks in QUERY — Final Outputs and Verification, integrity_report.json against them and write the results to integrity_report.json. This runs automatically on every invocation, not only when explicitly requested. If status is "FAIL", the run must not be reported as complete; surface the errors list rather than proceeding as though generation succeeded.

Assembly prompt budget: chunk within each CC × T bucket, never across unrelated buckets. When a bucket exceeds ASSEMBLY_BUCKET_LIMIT, synthesize source contributions in sub-groups of BUCKET_SUBGROUP_SIZE and then reduce only those sub-group outputs into the final section. Preserve source references through every reduce pass.

### Idempotency & Checkpoints

Each phase must be idempotent: re-running the program must skip already-completed work and resume from the last successful checkpoint.

- Phase 1: skip speeches whose JSON already exists in checkpoints/phase1/.
- Phase 2: regenerate master_inventory.json only if new Phase 1 files exist.
- Phase 3: reuse checkpoints only when the inventory manifest, prompt version, schema version, embedding model, thresholds, and canonicalisation configuration match. If any dependency changes or new/changed speeches exist, reconsolidate or incrementally update the canonical model according to RECONSOLIDATE.
- Phase 4: skip a speech only when its source hash, Phase 1 record hash, canonical-model version, and mapping configuration match the stored Phase 4 dependency record. Canonical ID changes must invalidate affected remapped records.
- Phase 5: always rebuild compendium.md, theme_index.md, unverifiable_claims.md, anchors, and indexes from the current validated Phase 4 records and current cc_theme_pairs.json.

Checkpoint directories must be created automatically. Maintain a dependency manifest for each phase containing input hashes, output hashes, schema/prompt/model/configuration versions, and completion status. The program must never treat a stale checkpoint as complete merely because the file exists.

### Intermediate Outputs and Verification (Directives Implementation)

*This section is a map for readers, listing the intermediate artifacts the pipeline produces between input and final output, and pointing to where each one is defined and verified above. It does not restate that logic — see the referenced sub-sections of Five-Phase Pipeline and Idempotency & Checkpoints for the actual definitions and checks.*

- **Phase 1 — checkpoints/phase1/\*.json** (one per speech): per-speech structured summary. Defined and schema-validated under Five-Phase Pipeline, Phase 1; source-excerpt verification (source_match) also defined there; idempotency/skip condition defined under Idempotency & Checkpoints, Phase 1.
- **Phase 2 — checkpoints/phase2/master_inventory.json** and its inventory manifest: aggregated corpus inventory plus near-duplicate diagnostics. Defined under Five-Phase Pipeline, Phase 2; regeneration condition defined under Idempotency & Checkpoints, Phase 2.
- **Phase 3 — checkpoints/phase3/canonical_ccs.json, canonical_themes.json, local_to_canonical_mappings.json, speech_classifications.json, cc_theme_pairs.json**: canonical CC/Theme discovery, the local-to-canonical mappings, the Speech × CC classification artifact, and the CC × Theme junction table. Defined under Five-Phase Pipeline, Phase 3; reuse/reconsolidation conditions defined under Idempotency & Checkpoints, Phase 3; the CC × T pair's status as the authoritative, Directive-protected artifact is stated under Directives, Many-to-Many Relationship Materialization, and its cardinalities are stated under Rules, Entity-Relationship Cardinalities.
- **Phase 4 — checkpoints/phase4/\*.json** (one per speech) and checkpoints/phase4/uncategorised.jsonl: lossless remapped records carrying canonical IDs and bucket memberships, plus the log of speeches that could not be confidently classified. Defined under Five-Phase Pipeline, Phase 4, including the field-by-field losslessness check; skip/invalidation condition defined under Idempotency & Checkpoints, Phase 4.

### Evaluation Script (optional standalone)

A standalone evaluation script (eval_compendium.py) should be included alongside the main pipeline. It must compute the following metrics against the generated compendium and master_inventory.json:

- Theme near-duplicate rate — fraction of canonical Theme pairs above THEME_DEDUP_THRESHOLD using the same configured EMBEDDING_MODEL_NAME and preprocessing as the pipeline.
- Speech-to-CC silhouette score — compute from the same normalized sentence embeddings used for classification diagnostics, not TF-IDF, unless TF-IDF is explicitly selected as the pipeline-wide representation.
- Claim usage entropy — Shannon entropy of the distribution of speeches across CCs (should be > 2.0 for a balanced compendium).
- Claim usage Gini coefficient — should be < 0.5 to flag excessive concentration of speeches under a single CC.
- Phase completion health — verify non-empty required checkpoint directories, dependency-manifest validity, Phase 4/source count reconciliation, and successful generation of all three final outputs.
- CC near-duplicate rate — same method as Theme near-duplicate rate, using CC_DEDUP_THRESHOLD.
- Referential-integrity rate — percentage of classifications, mappings, bucket records, arguments, and index links whose referenced IDs/anchors exist; target 100%.
- Theme-index completeness — percentage of canonical Themes, CC × T pairs, and canonical argument conclusions represented in theme_index.md; target 100%.
- Provenance coverage — percentage of canonical argument conclusions and evidence items with at least one valid source speech reference and, where required, a matching source excerpt.
- Classification confidence and uncategorised rate — report distributions rather than hiding low-confidence assignments.
- Canonical stability across reruns — proportion of materially unchanged canonical entities that retain their IDs or have an explicit supersession mapping.
- Target-count compliance must be reported as a diagnostic only; it must not override semantic quality or cause the evaluation script to label a coherent corpus model as failed solely because entity counts fall outside the heuristic range.

