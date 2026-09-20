% ============================================================
% DIRECTIVES — Control: how the system may behave, not what is true
% ============================================================

% --- Principle of Fidelity to Underlying Data ---
:- fidelity_principle(
     preserve_source_data(fully),
     augment_only([labels, mappings, ids, confidence_scores]),
     forbid([rewrite, paraphrase, discard])
   ).

:- forall(
     pipeline_checkpoint(Boundary),
     require(mechanically_checkable_operation(Boundary))
   ).

:- fidelity_technique(schema_constrained_extraction).
:- fidelity_technique(verbatim_span_extraction_with_offsets).
:- fidelity_technique(diff_based_roundtrip_validation_gate).
:- fidelity_technique(structured_immutable_fields_contract).

:- output_fidelity_rule(no_shallow_summary).
:- output_fidelity_rule(preserve_structure([evidence, analogies, devices,
                                             recurring_claims, evolution])).
:- output_fidelity_rule(forbid(section(uncategorised_speeches))).
:- output_fidelity_rule(require(evolution_over_time, when(span > 1yr))).
:- output_fidelity_rule(forbid(fabricate(evidence)); require(omit_if_unextractable)).
:- output_fidelity_rule(tagline(concise, distinct_from(full_proposition))).
:- output_fidelity_rule(authoritative(cc_chapter); navigation_only(theme_index)).
:- output_fidelity_rule(preserve(minority_or_contradictory_arguments)).
:- output_fidelity_rule(forbid(argument_conclusion, unless(supported_by(local_argument)))).

% --- Principle of Least Agency ---
:- least_agency_rule(validate_against(fixed_enumerated_set)).
:- least_agency_rule(one_decision_per_llm_call).
:- least_agency_rule(scope(llm_call, assigned_content_only)).
:- least_agency_rule(llm_output_is(proposal); require(python_validates_before_accept)).
:- least_agency_rule(python_owns([counting, grouping, id_assignment, ordering, cross_referencing])).
:- least_agency_rule(determinism_claim_must_be(verifiable)).

% --- Many-to-Many Relationship Materialization ---
:- forall(
     ( er_relationship(R, many_to_many),
       ( depends_on(R, judgment_call(canonical_discovery))
       ; depends_on(R, judgment_call(speech_classification)) )
     ),
     ( materialize(R, persistent_artifact),
       tag(R, canonical_model_version),
       version_source(content_derived, not(manual_increment)),
       version_trigger([canonical_entity_change, classification_change,
                        relationship_type_change, relationship_explanation_change,
                        pair_definition_change, classification_prompt_schema_version_change,
                        bucket_prompt_schema_version_change]),
       forbid(rederive(R, from(unstructured_speech_text))),
       forbid(reinterpret_or_reassign(stored_relationship_type)),
       require(version_match_before_consume(R))
     )
   ).
% concrete embodiment: cc_theme_pairs.json, speech_classifications.json,
% secondary_cc_contributions.json (active only when allow_secondary = true)

% --- Relationship-Type Preservation ---
:- forbid(llm, change(controlled_relationship_type)).
:- forbid(llm, reassign(source_contribution, different_role)).
:- forbid(llm, invent(consensus)).
:- forbid(llm, add(source_record)).
:- forbid(llm, move(content, different_cc_theme_pair)).
:- forbid(llm, convert(qualification_or_opposition, into(support))).
% checkable consequence -> see RULES: relationship_type_integrity/1

% --- Roles and Persona ---
:- persona(expert_python_programmer).
:- persona(expert_financial_speech_analyst).
:- persona(expert_investment_theorist).

% --- Tools ---
:- permit(llm_semantic_reasoning(deepseek_v4_flash)).
:- permit(cosine_similarity).
:- permit(string_matching).
:- permit(sentence_embeddings(one_configured_model, consistent_use)).
:- permit(python_deterministic([grouping, indexing, anchors, referential_checks,
                                 hashing, checkpoint_dependency_validation])).
:- forbid(web_search).

% --- Model & API Configuration ---
:- config(model, "deepseek-v4-flash").
:- config(temperature, 0).
:- config(min_max_tokens, 8000).
:- require(sdk, openai_compatible); forbid(custom_http_client).
:- forbid(expose_as_user_configurable(temperature)).

% --- LLM Prompt Rules ---
:- require(json_only_response).
:- require(declared_top_level_shape(object_or_array)); forbid(shape_inference_heuristic).
:- require(semantic_validation_after_parse).
:- forbid(llm, generate([deterministic_indexes, anchors, cc_theme_memberships])).
:- forbid(llm_phase4, rewrite(source_content)).
:- require(stamp(every_checkpoint_record, [prompt_version, schema_version])).

% --- Compatibility Rules ---
:- require(spyder_compatible); forbid(top_level_asyncio_run).
:- require(only_libraries_in(conda_list_txt)).
:- require(pathlib_or_os_path); forbid(hardcoded_path_separators).

% --- Logging & Error Handling ---
:- require(log(phase_start_end, speech_count, api_call_count)).
:- require(log_level(retry, warning); log_level(idempotency_skip, debug)).
:- forbid(silently_swallow_exception).


% ============================================================
% FACTS — Logic: static domain vocabulary and given data
% ============================================================

% --- Attached Files ---
fact(requirements_file, "conda_list.md").
fact(example_input, "20211111_The Cost of Money.md").
fact(structural_description_file, "compendium_StructuralDescription_relationshiptypes.md").
fact(governs, structural_description_file, over(implementation_conflicts)).

% --- Definitions ---
fact(central_claim(cc), full_proposition_with_verb).
fact(theme(t), noun_phrase_no_verb).
fact(argument, has([premises, conclusion]), scoped_to(one_cc, one_theme)).
fact(evidence, empirical_or_illustrative_grounding).
fact(cc_theme_bucket, runtime_aggregation_container, not(text), not(inside_speech)).
fact(primary_cc, exactly_one, per(categorised_speech)).
fact(secondary_cc_contribution, optional, disabled_by_default,
     scope(specific_source_item), forbid(alter(primary_cc))).
fact(publication_architecture, cc_chapters(authoritative), themes(sections_within)).
fact(theme_index, complete_secondary_view, forbid(duplicate_full_synthesis)).
fact(provenance, traceable_to([source_filenames, excerpt_or_location]),
     also_requires(source_contribution_ids, distinct_from(filenames))).

% --- Speech-to-Canonical-CC Relationship Type ---
fact(relationship_type, supports).
fact(relationship_type, specific_instance).
fact(relationship_type, mechanism).
fact(relationship_type, consequence).
fact(relationship_type, qualification).
fact(relationship_type, opposition).
fact(relationship_type, historical_example).
fact(relationship_type, application).
fact(relationship_type, evidence).
fact(controlled_vocabulary_closed(relationship_type)).

% --- Inputs ---
fact(input_type, plain_text_txt).
fact(filename_pattern, "YYYYMMDD_Title.md").
fact(corpus_size_approx, 900).
fact(title_is_hint_not_literal_cc).

% --- Configuration Block ---
fact(config(cc_dedup_threshold, 0.85)).
fact(config(theme_dedup_threshold, 0.85)).
fact(config(classification_confidence_min, 0.70)).
fact(config(max_themes_per_speech, 3)).
fact(config(allow_secondary_cc_contributions, false)).
fact(config(cc_ratio, 0.06-0.08)).
fact(config(theme_ratio, 0.12-0.16)).


% ============================================================
% RULES — Logic: checkable properties of a correct finished output
% ============================================================

targets_diagnostic_not_forced(cc_count) :-
    within_ratio(cc_count, corpus_size, 0.06, 0.08) ; semantic_coherence_overrides.
targets_diagnostic_not_forced(theme_count) :-
    within_ratio(theme_count, corpus_size, 0.12, 0.16) ; semantic_coherence_overrides.

er_cardinality(cc, theme, many_to_many, via(cc_theme_pair)).
er_cardinality(cc_theme_pair, argument_conclusion, one_to_many).
er_cardinality(speech, primary_cc, exactly_one_or_zero_if_uncategorised).
er_cardinality(speech, theme, one_to(1,3)).
er_cardinality(speech, default_pair_membership, under_same_primary_cc).
er_cardinality(source_contribution, secondary_pair, zero_to_many, disabled_by_default).
distinct_argument_ids(A1, A2) :- \+ same_exact_pair(A1, A2).

relationship_type_assignment(Speech) :-
    exactly_one(controlled_type(Speech)),
    non_empty(relationship_explanation(Speech)).

best_argumentative_home_standard(Speech, CC) :-
    \+ requires_paraphrase_equivalence(Speech, CC),
    \+ (topical_similarity_only(Speech, CC)),
    ( meaningful_argumentative_home(Speech, CC) ; classify(Speech, unclassified) ),
    independent_of(confidence_threshold_relaxation).

relationship_type_integrity(Argument) :-
    forall(contribution(C, Argument), inherits_unchanged(C, speech_classification(C))),
    role_set(Argument, Roles),
    contribution_ids(Argument, IDs),
    covers_exactly(Roles, IDs),               % no omission, no unauthorized addition
    equal(pair_counts(Argument), accepted_classification_counts(Argument)),
    ( has_role(Argument, qualification) ; has_role(Argument, opposition)
      -> represented_in(Argument, disagreements_and_qualifications)
      ;  true ).

evidence_tag(Item, verified) :- has(Item, verification_basis), transcript_supported(Item).
evidence_tag(Item, unverifiable) :- \+ transcript_supported(Item).
evidence_tag(Item, disputed) :- contradicted_within_corpus(Item).

provenance_coverage(Argument) :-
    non_empty(source_contribution_ids(Argument)),
    non_empty(source_speech_filenames(Argument)),
    forall(filename(F, Argument), real_speech(F)).

consistency_check(unverifiable_completeness) :-
    forall(phase1_unverifiable(U), appears_in(U, unverifiable_claims_md)).
consistency_check(theme_index_completeness) :-
    set_equal(theme_index_pairs, persistent_pairs).
consistency_check(anchor_integrity) :-
    forall(pair(P), unique(anchor(P))), forall(pair(P), rendered_in(anchor(P), compendium_md)).
consistency_check(pair_referential_integrity) :-
    \+ duplicate(pair_id), \+ orphaned(pair).


% ============================================================
% QUERY — the actual ask, plus its elaboration
% ============================================================

?- write_program(
     five_phase_pipeline(summarize, inventory, consolidate, remap, assemble),
     conforming_to(directives, facts, rules),
     produces([compendium_md, theme_index_md, unverifiable_claims_md,
               integrity_report_json])
   ).

% --- Final Outputs and Verification ---
final_output(compendium_md, hierarchy(cc_chapter > theme_section > argument_conclusion)),
   renders(argument_conclusion, [relationship_roles_subsection,
                                  disagreements_and_qualifications_subsection]).
final_output(theme_index_md, lists(every_theme, every_pair, every_argument)).
final_output(unverifiable_claims_md, preserves(every_phase1_unverifiable_claim)).
final_output(integrity_report_json,
   fields([status, errors, warnings, checks(seven_named_booleans),
           referential_integrity_rate, counts]),
   mandatory, gates(run_completion),
   distinct_from(optional_standalone_evaluation_script)).

% --- Query Elaboration: how the ask gets fulfilled and checked ---

phase(1, summarize, per_speech_extraction, must_not(canonicalise)).
phase(2, inventory, aggregate(master_inventory_json), dedup_diagnostics_only).
phase(3, consolidate, [discover_cc, discover_theme, classify_speech,
                        build(cc_theme_pairs_json)]).
phase(4, remap, deepcopy(phase1_record), append_canonical_fields_only).
phase(5, assemble, [construct_buckets_deterministically,
                     group_by(relationship_type),
                     synthesize(per_bucket),
                     run(integrity_checks), write(integrity_report_json)]).

idempotency(phase1, skip_if(checkpoint_exists)).
idempotency(phase3, reuse_if(dependencies_unchanged)).
idempotency(phase4, invalidate_if(canonical_model_version_mismatch)).
idempotency(phase5, always_rebuild_from(current_validated_state)).

intermediate_artifact(phase1_json, checkpoints_phase1).
intermediate_artifact(phase4_remapped_json, checkpoints_phase4).
intermediate_artifact(cc_theme_pairs_json, checkpoints_phase3, authoritative_junction).
% ^ persistent + authoritative, not a discardable intermediate, per
%   Many-to-Many Relationship Materialization directive above.

evaluation_metric(referential_integrity_rate, target(1.0)).
evaluation_metric(theme_index_completeness, target(1.0)).
evaluation_metric(provenance_coverage).
evaluation_metric(canonical_stability_across_reruns).
optional_standalone(evaluation_script).