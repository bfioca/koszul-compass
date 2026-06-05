# No-Go Atlas v0

Status: `no_go_atlas_v0_built`
Scope: Existing verified 5259/7914 radius-9, 7484, and 2544 artifacts; scoped obstruction rules, not global landscape theorems except where marked global-looking.

## Summary

- syndrome_count: `7`
- scope_class_counts: `{'geometry-local': 1, 'global-looking': 1, 'grammar-local': 4, 'presentation-local': 1}`
- prefilter_ids: `['degree_one_doublet_triplet_inseparable', 'degree_zero_bilinear_not_top_cup', 'higher_monoid_downstream_obstructed', 'no_recorded_free_symmetry', 'representative_character_mismatch', 'vectorlike_excess']`
- survivor_count: `1`

## Syndromes

### geometry_no_recorded_free_symmetry

- title: Clean upstairs SU(5), but no recorded free action for Wilson-line descent
- geometry: `CICY2544`
- scope_class: `geometry-local`
- stage: `geometry_selection_for_wilson_line`
- cheap_prefilter: `no_recorded_free_symmetry`
- replay_counts: `{'source': 'reports/outside_regime_free_symmetry_no_go.json', 'favourable_h11_ge_7_known_symmetry_rows': 3, 'rows_with_no_recorded_free_symmetry': 3, 'cicy2544_free_symmetry_option_count': 0, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'supply a verified free action, or move to a quotient-compatible geometry/presentation', 'would_promote_to': 'Wilson-line character descent audit'}`

### z2_regular_vectorlike_excess_5259_7914

- title: Certified quotient lift, but regular H2(wedge2 V) gives five vectorlike pairs
- geometry: `CICY5259 via favourable split 7914`
- scope_class: `presentation-local`
- stage: `wilson_line_character_projection`
- cheap_prefilter: `vectorlike_excess`
- replay_counts: `{'source': 'reports/cicy5259_quotient_wilson_line_report.json', 'admissible_nontrivial_embeddings': 1, 'standard_model_like_embeddings': 0, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'lower H2(wedge2 V) regular multiplicity from 5 to 1 or 0 while preserving q=1 and quotient lift', 'historical_boundary': 'the later radius-9 branch-50 search achieves one vectorlike pair only after moving to a different local bundle branch and higher-degree monoid support'}`

### z2xz2_regular_vectorlike_excess_7484

- title: Quotient-compatible 7484 descent works, but character-certified vectorlike content is too large
- geometry: `CICY7484`
- scope_class: `grammar-local`
- stage: `order4_wilson_line_character_projection`
- cheap_prefilter: `vectorlike_excess`
- replay_counts: `{'source': 'reports/cicy7484_selected_kappa_zero_allowed_bound15.json', 'selected_zero_allowed_spectrum_lift_count': 12, 'actual_character_count': 12, 'has_actual_three_family_no_vectorlike_pair': False, 'has_actual_one_higgs_pair_without_triplets': False, 'local_best_zero_allowed_pair': [6, 3], 'local_best_nontrivial_pair': [9, 6], 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find a character-certified 7484 branch with per-character pair [4,1] or [3,0] and no trivial-summand caveat', 'known_frontier': 'local pair deformations to delta12 still bottom out at [6,3] for zero-allowed and [9,6] for nontrivial regular candidates'}`

### degree_zero_bilinear_not_cy3_top_cup

- title: Charge-neutral bilinear shadow misses CY3 top degree
- geometry: `CICY5259 via favourable split 7914`
- scope_class: `global-looking`
- stage: `top_degree_superpotential_gate`
- cheap_prefilter: `degree_zero_bilinear_not_top_cup`
- replay_counts: `{'source': 'reports/phenomenology_guided_q1_radius9_degree_aware_main_frontier_search.json', 'records_scanned': 4065, 'represented_q1_weight': 549038, 'degree_zero_bilinear_rows': 1452, 'degree_zero_bilinear_weight': 29021, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'add a neutralizing H1 singlet insertion so the ordinary product lands in H3(O_X)', 'followup_result': 'degree-aware replay found 333 selection survivors with degree-one support, but all failed representative realizability'}`

### physical_5bar_representative_character_mismatch

- title: Triplet-only branch character asks for +2/-0, but representatives give +1/-1
- geometry: `CICY5259 via favourable split 7914`
- scope_class: `grammar-local`
- stage: `representative_realizability_gate`
- cheap_prefilter: `representative_character_mismatch`
- replay_counts: `{'source': 'reports/phenomenology_guided_q1_radius9_representative_first_degree_aware_search.json', 'degree_aware_failure_records': 333, 'degree_aware_failure_weight': 333, 'representative_first_template_records': 479, 'representative_first_template_weight': 1077, 'representative_compatible_template_records': 0, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'seed generator with representative-compatible physical 5bar H1 templates before asking for triplet-only mass support', 'followup_result': 'physical-5bar-first replay found representative-compatible 5bar sectors, but degree-one triplet-only operators did not intersect them'}`

### degree_one_representative_intersection_not_triplet_only

- title: Representative-compatible degree-one intersections fail triplet-only DT separation
- geometry: `CICY5259 via favourable split 7914`
- scope_class: `grammar-local`
- stage: `degree_one_intersection_forcing_gate`
- cheap_prefilter: `degree_one_doublet_triplet_inseparable`
- replay_counts: `{'source': 'reports/phenomenology_guided_q1_radius9_intersection_forcing_search.json', 'records_scanned': 4065, 'intersection_forced_operator_records': 10004, 'doublet_support_obstruction_rows': 1139, 'cup_product_eligible_records': 0, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'allow higher-degree singlet monoids while retaining representative-compatible 5bar/cup-5 and proton safety', 'followup_result': 'degree <=3 monoids produced 136 representative-compatible higher-degree selection candidates'}`

### higher_degree_monoid_downstream_obstructions

- title: Higher-degree monoids reopen the corridor, but most operators still die at downstream gates
- geometry: `CICY5259 via favourable split 7914`
- scope_class: `grammar-local`
- stage: `higher_degree_monoid_selection_gate`
- cheap_prefilter: `higher_monoid_downstream_obstructed`
- replay_counts: `{'source': 'reports/phenomenology_guided_q1_radius9_higher_degree_intersection_search.json', 'higher_degree_forced_operator_records': 10004, 'downstream_obstructed_operator_records': 9868, 'representative_candidate_records': 136, 'degree2_candidate_records': 120, 'degree3_candidate_records': 16, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'select the representative-compatible candidate status and then compute the pending higher-order mass map', 'followup_result': 'branch radius6_broad_adjacency_filtered_10_branch_50 is frozen in the survivor dossier'}`

## Survivor Certificate

- survivor_id: `survivor_radius6_broad_adjacency_filtered_10_branch_50`
- candidate: `radius6_broad_adjacency_filtered_10_branch_50`
- status: `higher_order_mass_map_pending_for_frozen_candidate`
- operator: `5bar_02*5_34`
- monomial: `['e3-e2', 'e4-e0']`
- pending_gate: `{'gate': 'higher_order_effective_mass_map_rank', 'ordinary_cup_status': 'not_a_simple_CY3_cubic_top_product', 'triplet_rank_condition': {'matrix_dimensions_after_fixed_singlet_vevs': [1, 1], 'rank_needed_to_lift_colored_triplet_pair': 1, 'rank_status': 'pending_higher_order_mass_map', 'selection_rule_shape': ['+1/-1', '+1/-0']}, 'doublet_rank_condition': {'matrix_dimensions_after_fixed_singlet_vevs': [1, 0], 'rank_needed_to_preserve_light_doublet_pair': 0, 'rank_status': 'selection_rule_forces_zero_for_this_operator', 'selection_rule_shape': [1, 0]}, 'not_claimed': 'simple CY3 cubic cup-product mass-rank verification'}`

Nearest no-go boundaries:
- `cubic_only_gate`: forbid degree-2/3 singlet monoids and require a simple CY3 cubic cup product
- `doublet_support`: same higher-monoid grammar but triplet support also hits the doublet component
- `proton_unprotected`: keep triplet-only support but allow dangerous 10*5bar*5bar operators
- `cup_5_unrealizable`: keep representative-compatible 5bar and proton safety but fail the cup-dual 5 representative character

## Gates

- source_verifications_pass: `True` - all imported source verifications pass
- covers_requested_artifact_families: `True` - atlas covers 2544, 7484, and 5259/7914 artifacts
- every_syndrome_has_scoped_prefilter_and_replay: `True` - each no-go syndrome has scope class, executable prefilter, replay counts, and evidence
- prefilter_self_tests_pass: `True` - each atlas prefilter fires on its representative obstruction sample
- survivor_certificate_is_branch50: `True` - branch-50 higher-degree survivor and pending mass-map gate are included
- nearest_no_go_boundaries_present: `True` - survivor carries nearest no-go boundary examples
