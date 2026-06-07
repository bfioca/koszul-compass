# No-Go Atlas v0

Status: `no_go_atlas_v0_built`
Scope: Existing verified 5259/7914 radius-9, 7484, and 2544 artifacts; scoped obstruction rules, not global landscape theorems except where marked global-looking.

## Summary

- syndrome_count: `48`
- scope_class_counts: `{'candidate-specific': 11, 'geometry-local': 1, 'global-looking': 1, 'grammar-local': 24, 'presentation-local': 11}`
- prefilter_ids: `['chain_contraction_fallback_closed_current_engine', 'charge_defect_guided_no_improvement', 'computed_anchor_missing_one_higgs_and_cup', 'cubic_yukawa_absent', 'cup_target_missing_one_higgs', 'degree_one_doublet_triplet_inseparable', 'degree_zero_bilinear_not_top_cup', 'direct_split_witness_missing_current_data', 'first_pair_positive_generator_no_seed', 'geometry_specific_engine_missing_current_data', 'higher_degree_yukawa_charge_mismatch', 'higher_map_order_no_realization', 'higher_monoid_downstream_obstructed', 'local_deformation_first_pair_no_homotopy_seed', 'multistage_first_pair_no_homotopy_seed', 'no_recorded_free_symmetry', 'one_higgs_proton_safety_disjoint', 'one_higgs_proton_unsafe', 'preferred_effective_routes_no_homotopy_seed', 'raw_free_action_data_missing_current_data', 'representative_character_mismatch', 's42_boundary_only_no_non_s42_survivor', 's42_doublet_contamination_motif', 'single_anchor_effective_routes_no_homotopy_seed', 'split_action_lift_missing_current_data', 'standard_m4_four_h1_not_top_cup', 'transferred_m3_direct_tree_no_survivor', 'upstream_direct_e1_requires_transferred_m3', 'vectorlike_excess', 'verified_overlap_first_pair_seed_absent']`
- survivor_count: `0`

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
- nearest_escape_or_boundary: `{'minimal_change': 'select the representative-compatible candidate status and then compute the pending higher-order mass map', 'followup_result': 'branch radius6_broad_adjacency_filtered_10_branch_50 was later reclassified as a standard m4 degree-law negative control'}`

### branch50_standard_m4_four_h1_not_cy3_top_cup

- title: Branch 50 four-H1 standard m4 route lands in H2, not H3(O_X)
- geometry: `CICY5259 via favourable split 7914`
- scope_class: `candidate-specific`
- stage: `standard_cochain_m4_degree_gate`
- cheap_prefilter: `standard_m4_four_h1_not_top_cup`
- replay_counts: `{'source': 'reports/phenomenology_guided_q1_radius9_homotopy_transfer_degree_audit.json', 'tree_degree_record_count': 5, 'transferred_output_degrees': [2], 'direct_binary_product_count': 6, 'nonzero_H2_H2_pair_partitions': 1, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find a representative-compatible ordinary cubic H1 x H1 x H1 -> H3(O_X) route, or add a separately justified nonstandard physical convention', 'surviving_escape_hatches': ['derive and justify a physics-specific effective operator whose algebraic degree is not standard cochain m4', 'find a representative-compatible degree-one singlet/cubic top-cup mass route', 'change the candidate/geometry so the mass operator has a valid H3 target under ordinary or transferred degree accounting'], 'followup_result': 'cubic-top-cup-first replay finds zero cup-product-eligible candidates in the current radius-9 grammar'}`

### cicy6927_model874_s42_doublet_contamination_basin

- title: Model 874 one-Higgs safe Wilson slice is trapped by an S_42 doublet-only mass motif
- geometry: `CICY6927/model 874 option 4`
- scope_class: `grammar-local`
- stage: `one_higgs_doublet_triplet_selection_gate`
- cheap_prefilter: `s42_doublet_contamination_motif`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy6927_model874_latent_atlas.json', 'fixed_model_embedding_vectors': 768, 'one_higgs_proton_safe_vectors': 96, 'universal_contamination_cluster_count': 1, 'motif_count': 96, 'active_touching_frontier_size': 750, 'active_touching_q1_candidates': 3, 'active_touching_one_higgs_precup_survivors': 0, 'latent_active_frontier_size': 131, 'latent_active_q1_candidates': 1, 'latent_active_one_higgs_precup_survivors': 0, 'latent_compensated_frontier_size': 23183, 'latent_compensated_q1_candidates': 15, 'latent_compensated_completed_one_higgs_precup_survivors': 0, 'latent_compensated_promotion_timeout_count': 3, 'timeout_closure_resolved_count': 3, 'timeout_closure_unresolved_count': 0, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find a q=1 one-Higgs/proton-safe branch whose mass-channel motif does not contain the 5bar_23*5_34*S_42 top_cup_doublet_only_mass signature, or change the geometry/presentation/mass mechanism', 'recommended_generator': 'cross-model latent retrieval seeded against absence of the S_42 doublet-contamination motif, with symbolic promotion retained as judge', 'closed_timeout_boundary': 'frontiers 2651, 4803, and 8857 resolve after skipping ordinary H1=0 singlets before expensive equivariant singlet audits; all three have 0 one-Higgs pre-cup survivors'}`

### cicy6927_non_s42_cup_boundary_missing_one_higgs_radius2

- title: Non-S_42 proton-safe triplet-cup boundary retains cup targets but has no one-Higgs sector
- geometry: `CICY6927/model 237 and 583 option 4`
- scope_class: `grammar-local`
- stage: `one_higgs_recovery_after_triplet_cup_gate`
- cheap_prefilter: `cup_target_missing_one_higgs`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy6927_non_s42_cup_to_one_higgs_search.json', 'frontier_size': 772, 'q1_candidate_count': 3, 'screened_candidate_count': 3, 'promotion_timeout_count': 0, 'non_s42_precup_survivor_count': 0, 'one_higgs_proton_safe_intersection_count': 0, 'cup_product_eligible_triplet_target_count': 256, 'one_higgs_pair_triplet_free_embeddings': 0, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'recover a positive one-Higgs/triplet-free Wilson sector while preserving q1, proton safety, non-S_42 motif avoidance, and the triplet-only cup target', 'next_generator': 'use a broader or different move grammar than radius-2 pair-delta, or pivot to the non-S_42 one-Higgs-but-proton-unsafe boundary class'}`

### cicy6927_model252_s42_boundary_only_radius2

- title: CICY6927 model 252 only recovers the known S_42 one-Higgs boundary
- geometry: `CICY6927/model 252 option 4`
- scope_class: `grammar-local`
- stage: `non_s42_one_higgs_precup_survivor_gate`
- cheap_prefilter: `s42_boundary_only_no_non_s42_survivor`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy6927_model252_intersection_forcing_search.json', 'frontier_size': 1750, 'q1_candidate_count': 7, 'screened_candidate_count': 7, 'promotion_timeout_count': 0, 'one_higgs_proton_safe_intersection_count': 1, 'non_s42_precup_survivor_count': 0, 'total_one_higgs_pair_triplet_free_embeddings': 192, 'total_one_higgs_proton_safe_embeddings': 96, 'total_pre_cup_survivor_count': 352, 'total_cup_product_eligible_triplet_target_count': 352, 'closest_detail_s42_motif_hit_count': 8, 'only_intersection_frontier': 0, 'only_intersection_source_models': [874], 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find a CICY6927 option-4 q1 branch with a same-embedding one-Higgs/proton-safe overlap and a non-S_42 pre-cup survivor', 'next_generator': 'advance to the next queue target, or broaden CICY6927 only with a generator explicitly ranked by non-S_42 one-Higgs pre-cup survival rather than by recovering the model-874 boundary'}`

### cicy6927_model254_s42_boundary_only_radius2

- title: CICY6927 model 254 only recovers the known S_42 one-Higgs boundary
- geometry: `CICY6927/model 254 option 4`
- scope_class: `grammar-local`
- stage: `non_s42_one_higgs_precup_survivor_gate`
- cheap_prefilter: `s42_boundary_only_no_non_s42_survivor`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy6927_model254_intersection_forcing_search.json', 'frontier_size': 1962, 'q1_candidate_count': 10, 'screened_candidate_count': 10, 'promotion_timeout_count': 0, 'one_higgs_proton_safe_intersection_count': 1, 'non_s42_precup_survivor_count': 0, 'total_one_higgs_pair_triplet_free_embeddings': 192, 'total_one_higgs_proton_safe_embeddings': 96, 'total_pre_cup_survivor_count': 352, 'total_cup_product_eligible_triplet_target_count': 352, 'closest_detail_s42_motif_hit_count': 8, 'only_intersection_frontier': 0, 'only_intersection_source_models': [874], 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find a CICY6927 option-4 q1 branch with a same-embedding one-Higgs/proton-safe overlap and a non-S_42 pre-cup survivor', 'next_generator': 'advance to the next queue target, or broaden CICY6927 only with a generator explicitly ranked by non-S_42 one-Higgs pre-cup survival rather than by recovering the model-874 boundary'}`

### cicy6927_model369_s42_boundary_only_radius2

- title: CICY6927 model 369 only recovers the known S_42 one-Higgs boundary
- geometry: `CICY6927/model 369 option 4`
- scope_class: `grammar-local`
- stage: `non_s42_one_higgs_precup_survivor_gate`
- cheap_prefilter: `s42_boundary_only_no_non_s42_survivor`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy6927_model369_intersection_forcing_search.json', 'frontier_size': 1973, 'q1_candidate_count': 12, 'screened_candidate_count': 12, 'model369_screened_count': 6, 'promotion_timeout_count': 0, 'one_higgs_proton_safe_intersection_count': 1, 'non_s42_precup_survivor_count': 0, 'total_one_higgs_pair_triplet_free_embeddings': 192, 'total_one_higgs_proton_safe_embeddings': 96, 'total_pre_cup_survivor_count': 352, 'total_cup_product_eligible_triplet_target_count': 352, 'closest_detail_s42_motif_hit_count': 8, 'only_intersection_frontier': 0, 'only_intersection_source_models': [874], 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find a CICY6927 option-4 q1 branch with a same-embedding one-Higgs/proton-safe overlap and a non-S_42 pre-cup survivor', 'next_generator': 'advance to the next queue target, or broaden CICY6927 only with a generator explicitly ranked by non-S_42 one-Higgs pre-cup survival rather than by recovering the model-874 boundary'}`

### cicy6927_model52_s42_boundary_only_radius2

- title: CICY6927 model 52 only recovers the known S_42 one-Higgs boundary
- geometry: `CICY6927/model 52 option 4`
- scope_class: `grammar-local`
- stage: `non_s42_one_higgs_precup_survivor_gate`
- cheap_prefilter: `s42_boundary_only_no_non_s42_survivor`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy6927_model52_intersection_forcing_search.json', 'frontier_size': 1962, 'q1_candidate_count': 8, 'screened_candidate_count': 8, 'model52_screened_count': 2, 'promotion_timeout_count': 0, 'one_higgs_proton_safe_intersection_count': 1, 'non_s42_precup_survivor_count': 0, 'total_one_higgs_pair_triplet_free_embeddings': 192, 'total_one_higgs_proton_safe_embeddings': 96, 'total_pre_cup_survivor_count': 352, 'total_cup_product_eligible_triplet_target_count': 352, 'closest_detail_s42_motif_hit_count': 8, 'only_intersection_frontier': 0, 'only_intersection_source_models': [874], 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find a CICY6927 option-4 q1 branch with a same-embedding one-Higgs/proton-safe overlap and a non-S_42 pre-cup survivor', 'next_generator': 'advance to the next queue target, or broaden CICY6927 only with a generator explicitly ranked by non-S_42 one-Higgs pre-cup survival rather than by recovering the model-874 boundary'}`

### cicy6836_one_higgs_proton_safety_disjoint_radius2

- title: CICY6836 one-Higgs and proton-safe cup structures exist, but do not intersect
- geometry: `CICY6836/model 95 and 139 option 23`
- scope_class: `grammar-local`
- stage: `one_higgs_proton_safety_intersection_gate`
- cheap_prefilter: `one_higgs_proton_safety_disjoint`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy6836_one_higgs_proton_intersection_search.json', 'frontier_size': 981, 'q1_candidate_count': 4, 'screened_candidate_count': 4, 'promotion_timeout_count': 0, 'one_higgs_precup_survivor_record_count': 0, 'one_higgs_proton_safe_intersection_record_count': 0, 'one_higgs_pair_triplet_free_embeddings': 384, 'one_higgs_proton_safe_embeddings': 0, 'cup_product_eligible_triplet_target_count': 128, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find a q=1 branch where one-Higgs/triplet-free Wilson embeddings land inside the proton-safe slice, then retain a triplet-only top-cup target', 'next_generator': 'either broaden the CICY6836 move grammar beyond radius-2 pair-delta or pivot to a geometry where one-Higgs and proton-safe/cup features already overlap in the same q1 row'}`

### cicy6836_model87_one_higgs_proton_safety_disjoint_radius2

- title: CICY6836 model 87 keeps one-Higgs and proton-safe slices disjoint
- geometry: `CICY6836/model 87 option 23`
- scope_class: `grammar-local`
- stage: `one_higgs_proton_safety_intersection_gate`
- cheap_prefilter: `one_higgs_proton_safety_disjoint`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy6836_model87_intersection_forcing_search.json', 'frontier_size': 1361, 'q1_candidate_count': 10, 'screened_candidate_count': 10, 'promotion_timeout_count': 0, 'one_higgs_precup_survivor_record_count': 0, 'one_higgs_proton_safe_intersection_record_count': 0, 'one_higgs_pair_triplet_free_embeddings': 1024, 'one_higgs_proton_safe_embeddings': 0, 'proton_safe_embeddings': 1536, 'cup_product_eligible_triplet_target_count': 128, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find a CICY6836 q=1 branch whose one-Higgs/triplet-free embeddings also have zero dangerous 10*5bar*5bar operators', 'next_generator': 'advance the cross-geometry queue to the next open target, or build a broader CICY6836 generator only if it is explicitly ranked by one-Higgs/proton-safe intersection before first-pair scoring'}`

### cicy6836_model186_frontier691_followup_disjoint_radius2

- title: CICY6836 model 186 improves to frontier 691, then stays one-Higgs/proton disjoint
- geometry: `CICY6836/model 186 option 23 plus frontier 691`
- scope_class: `grammar-local`
- stage: `one_higgs_proton_safety_intersection_gate`
- cheap_prefilter: `one_higgs_proton_safety_disjoint`
- replay_counts: `{'first_pass_source': 'experiments/latent_atlas/reports/cicy6836_model186_intersection_forcing_search.json', 'followup_source': 'experiments/latent_atlas/reports/cicy6836_model186_frontier691_followup_search.json', 'first_pass_frontier_size': 1961, 'first_pass_q1_candidate_count': 13, 'first_pass_boundary_improvement_record_count': 11, 'followup_frontier_size': 1359, 'followup_q1_candidate_count': 7, 'followup_screened_candidate_count': 7, 'followup_promotion_timeout_count': 0, 'one_higgs_pair_triplet_free_embeddings': 384, 'proton_safe_embeddings': 3264, 'one_higgs_proton_safe_embeddings': 0, 'cup_product_eligible_triplet_target_count': 128, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find a CICY6836 q1 branch whose one-Higgs/triplet-free embeddings also have zero dangerous 10*5bar*5bar operators, or improve frontier-691 beyond dangerous-count 1 and doublet-support 0', 'next_generator': 'advance the cross-geometry queue to the next open target, or expand CICY6836 only with a move grammar explicitly ranked by same-embedding one-Higgs/proton-safe intersection'}`

### cicy6836_model136_existing_boundary_floor_radius2

- title: CICY6836 model 136 only rediscovers the existing frontier-691 boundary floor
- geometry: `CICY6836/model 136 option 23 plus frontier 691`
- scope_class: `grammar-local`
- stage: `one_higgs_proton_safety_intersection_gate`
- cheap_prefilter: `one_higgs_proton_safety_disjoint`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy6836_model136_intersection_forcing_search.json', 'frontier_size': 2169, 'q1_candidate_count': 14, 'screened_candidate_count': 14, 'model136_screened_count': 2, 'promotion_timeout_count': 0, 'one_higgs_precup_survivor_record_count': 0, 'one_higgs_proton_safe_intersection_record_count': 0, 'boundary_improvement_record_count': 11, 'best_frontier': 691, 'best_source_models': [95], 'one_higgs_pair_triplet_free_embeddings': 1408, 'proton_safe_embeddings': 1024, 'one_higgs_proton_safe_embeddings': 0, 'cup_product_eligible_triplet_target_count': 128, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find a CICY6836 q1 branch whose one-Higgs/triplet-free embeddings also have zero dangerous operators, or improve beyond the already-followed frontier-691 floor', 'next_generator': 'with existing-boundary targets exhausted, pivot to presentation bridge engines or exact product machinery rather than repeatedly rediscovering frontier 691'}`

### cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2

- title: CICY6715 computed proton-safe anchors miss both one-Higgs and triplet-cup gates
- geometry: `CICY6715/model 215 and 336 option 1`
- scope_class: `grammar-local`
- stage: `one_higgs_and_triplet_cup_gate`
- cheap_prefilter: `computed_anchor_missing_one_higgs_and_cup`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy6715_model215_intersection_forcing_search.json', 'frontier_size': 1192, 'q1_candidate_count': 16, 'screened_candidate_count': 16, 'promotion_timeout_count': 0, 'promotion_error_count': 0, 'component_unresolved_record_count': 0, 'one_higgs_record_count': 0, 'one_higgs_proton_safe_intersection_record_count': 0, 'one_higgs_precup_survivor_record_count': 0, 'cup_target_record_count': 0, 'total_embeddings_screened': 12288, 'total_one_higgs_pair_triplet_free_embeddings': 0, 'total_pre_cup_survivor_count': 0, 'total_cup_product_eligible_triplet_target_count': 0, 'unresolved_envelope_used_as_seed': False, 'unresolved_envelope_remains_live': True, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find a computed CICY6715 q1 branch with one-Higgs/triplet-free structure or a triplet-cup target while preserving proton safety; alternatively resolve the model-766 representative ambiguity', 'next_generator': 'advance the cross-geometry queue to the next open target, or run a representative-resolution pass on the CICY6715 model-766 envelope if prioritizing that live ambiguity'}`

### cicy6715_model766_branch99_higher_map_order_no_realization

- title: CICY6715 model-766 branch99 shadow fails finite equivariant higher-map order scan
- geometry: `CICY6715/model 766 option 1 branch 99`
- scope_class: `candidate-specific`
- stage: `representative_equivariant_higher_map_realization`
- cheap_prefilter: `higher_map_order_no_realization`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy6715_model766_branch99_representative_resolution.json', 'clean_one_higgs_precup_shadow_count': 192, 'permutation_count_tested': 5040, 'complete_permutation_scan': True, 'branch_representative_certified': False, 'required_rank_total': 7, 'pycicy_raw_rank': 7, 'averaged_rank': 9, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'construct an explicitly equivariant higher-map convention whose rank-7 image has irrep split 1/2/2/2, or find another branch whose representative split is resolved without this collision', 'next_generator': 'advance the verified queue to the CICY6784 frontier-48 full chain-contraction fallback or to presentation-bridge targets'}`

### cicy6788_wall_breaker_one_higgs_proton_unsafe

- title: CICY6788 targeted wall-breaker keeps one-Higgs slices proton-unsafe
- geometry: `CICY6788/model 227 and 620 option 0`
- scope_class: `grammar-local`
- stage: `one_higgs_proton_safety_wall_breaker_gate`
- cheap_prefilter: `one_higgs_proton_unsafe`
- replay_counts: `{'source': 'reports/cicy6788_obstruction_targeted_wall_breaker_search.json', 'frontier_size': 2523, 'q1_candidate_count': 16, 'screened_candidate_count': 16, 'promoted_metric_improvement_count': 0, 'total_one_higgs_pair_triplet_free_embeddings': 1536, 'total_one_higgs_proton_safe_embeddings': 0, 'total_pre_cup_survivor_count': 0, 'total_cup_product_eligible_triplet_target_count': 0, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find a CICY6788 option-0 q1 branch with positive one-Higgs count and zero dangerous operators in the same Wilson slice, then recover a triplet-cup/pre-cup target', 'next_generator': 'avoid replaying this active-column wall-breaker grammar; use exact same-embedding overlap as an early gate on a broader geometry or presentation scan'}`

### cicy6784_strict_precup_cubic_yukawa_absent

- title: Strict pre-cup survivor, but no renormalizable cubic Yukawa channel
- geometry: `CICY6784/model 31 option 2`
- scope_class: `candidate-specific`
- stage: `cubic_operator_yukawa_gate`
- cheap_prefilter: `cubic_yukawa_absent`
- replay_counts: `{'source': 'reports/cicy6784_model31_operator_yukawa_frontier.json', 'up_type_operator_count': 2, 'up_type_cubic_allowed_count': 0, 'down_lepton_operator_count': 15, 'down_lepton_cubic_allowed_count': 0, 'proton_decay_allowed_count': 0, 'higgs_bilinear_degree_one_hits': 0, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'allow finite-degree singlet monoids to dress 10*10*5 or 10*5bar*5bar operators while preserving proton safety and Higgs doublet protection', 'next_generator': 'Search higher-degree singlet-dressed Yukawa operators for the CICY6784 strict survivor. Require finite monoid degree bounds, charge neutrality, Wilson-character support for up/down Yukawas, proton safety, representative-compatible singlet legs, and a clear rank-readiness statement.', 'stop_rule': 'Continue only if a higher-degree monoid creates at least one allowed up-type or down/lepton Yukawa channel without enabling proton decay or Higgs doublet mass contamination; otherwise promote cubic_yukawa_absent to an atlas skip/feature rule for strict pre-cup survivors.'}`

### cicy6784_higher_degree_le3_yukawa_charge_mismatch

- title: Degree<=3 singlet-dressed Yukawa monoids never reach charge neutrality
- geometry: `CICY6784/model 31 option 2`
- scope_class: `candidate-specific`
- stage: `bounded_singlet_dressed_yukawa_charge_gate`
- cheap_prefilter: `higher_degree_yukawa_charge_mismatch`
- replay_counts: `{'source': 'reports/cicy6784_model31_higher_degree_yukawa_search.json', 'monoid_degree_counts': {'1': 7, '2': 28, '3': 84}, 'up_type_operator_monoid_count': 238, 'down_lepton_operator_monoid_count': 1785, 'up_type_charge_neutral_count': 0, 'down_lepton_charge_neutral_count': 0, 'safe_yukawa_operator_monoid_count': 0, 'nearest_up_type_charge_defect': 4, 'nearest_down_lepton_charge_defect': 2, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'lower the down/lepton trace-neutral L1 defect from 2 to 0 or the up-type defect from 4 to 0 while preserving the strict one-Higgs/proton-safe pre-cup gates', 'escape_hatches': ['extend singlet monoids beyond degree 3', 'alter the singlet charge span through a local bundle move', 'switch Wilson embedding or geometry while preserving exact overlap'], 'next_generator': 'charge-defect-guided exact-overlap search seeded by the nearest CICY6784 higher-degree Yukawa boundaries'}`

### cicy6784_radius1_charge_defect_no_improvement

- title: Charge-defect-guided local moves do not lower the Yukawa charge boundary
- geometry: `CICY6784/model 31 option 2`
- scope_class: `candidate-specific`
- stage: `charge_defect_guided_local_escape_gate`
- cheap_prefilter: `charge_defect_guided_no_improvement`
- replay_counts: `{'source': 'reports/cicy6784_charge_defect_guided_yukawa_escape_search.json', 'frontier_size': 130, 'stage_counts': {'failed_index_target': 103, 'failed_no_trivial_summand': 6, 'failed_option2_lift': 10, 'failed_q1_no_anti10_gate': 10, 'q1_candidate': 1}, 'q1_candidate_count': 1, 'screened_candidate_count': 1, 'promotion_timeout_count': 0, 'strict_pre_cup_record_count': 1, 'safe_yukawa_record_count': 0, 'charge_defect_improved_record_count': 0, 'nearest_up_type_charge_defect': 4, 'nearest_down_lepton_charge_defect': 2, 'higher_degree_prefilter_hits': ['higher_degree_yukawa_charge_mismatch'], 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find a q=1 branch that lowers the down/lepton defect from 2 to 0 or the up-type defect from 4 to 0 while preserving the strict one-Higgs/proton-safe pre-cup gates', 'closed_boundary': 'within radius-1 pair-delta plus rectangle moves, every q1 candidate is the original seed, so no local downhill defect move is available in this grammar', 'next_pivots': ['increase radius with an early charge-defect target', 'use multi-column or singlet-charge-span-aware moves', 'extend monoids beyond degree 3', 'pivot to another exact-overlap seed or geometry']}`

### cicy6784_upstream_direct_e1_requires_transferred_m3

- title: Effective complement route has final top pairing, but upstream direct E1 product vanishes
- geometry: `CICY6784/model 31 option 2`
- scope_class: `candidate-specific`
- stage: `effective_complement_exact_engine_gate`
- cheap_prefilter: `upstream_direct_e1_requires_transferred_m3`
- replay_counts: `{'source': 'reports/cicy6784_upstream_complement_map_audit.json', 'target_top_pairing_rank': 4, 'direct_origin_piece_count': 2, 'direct_origin_wedge_survivor_count': 0, 'ten_kernel_dimension': 12, 'transferred_m3_output_degree': 2, 'coefficient_rank_status': 'pending', 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'compute a transferred m3 matrix into the 4-dimensional H2 complement, or find a factorization whose upstream product has a direct E1 survivor into the complement', 'next_engine_requirement': 'implement_transferred_m3_homotopy_for_upstream_complement', 'first_target': '10_4*5bar_12*S_34_to_H2_[0,-1,3,0]', 'stop_rule': 'continue only if a transferred m3 matrix can be computed into the 4-dimensional complement, or if the required homotopy/projector convention is shown to be unavailable and converted into an exact-engine obstruction feature'}`

### cicy6784_transferred_m3_no_direct_tree_survivor

- title: Transferred-m3 route has no homotopy-eligible direct tree term
- geometry: `CICY6784/model 31 option 2`
- scope_class: `candidate-specific`
- stage: `transferred_m3_direct_tree_inventory_gate`
- cheap_prefilter: `transferred_m3_direct_tree_no_survivor`
- replay_counts: `{'source': 'reports/cicy6784_transferred_m3_route_inventory.json', 'route_count': 3, 'direct_binary_target_piece_total': 0, 'homotopy_eligible_direct_product_total': 0, 'final_direct_tree_survivor_total': 0, 'route_status_counts': {'no_homotopy_eligible_binary_direct_product': 3}, 'coefficient_rank_status': 'pending', 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find an effective-complement route with at least one homotopy-eligible binary direct product, or implement the full chain-contraction/homotopy-transfer convention', 'next_engine_requirement': 'implement_full_chain_contraction_or_pivot_to_direct_tree_survivor_search', 'first_engine_target': 'transferred_m3_chain_contraction_for_10_4_5bar_12_S_34', 'search_escape': 'rank future effective-complement routes by the presence of a homotopy-eligible binary direct product before attempting full coefficient evaluation', 'stop_rule': 'continue only if a full chain-contraction convention is implemented, or if a new factorization/geometry supplies a direct-tree survivor that bypasses this missing primitive'}`

### cicy6784_preferred_effective_routes_no_homotopy_seed

- title: Preferred effective-complement routes lack homotopy-eligible binary seeds
- geometry: `CICY6784/model 31 option 2`
- scope_class: `candidate-specific`
- stage: `effective_complement_route_ranking_gate`
- cheap_prefilter: `preferred_effective_routes_no_homotopy_seed`
- replay_counts: `{'source': 'reports/cicy6784_effective_complement_route_ranker.json', 'factorization_count': 6, 'priority_class_counts': {'direct_binary_target_without_homotopy_source': 5, 'no_direct_binary_target': 1}, 'homotopy_eligible_factorization_count': 0, 'direct_binary_target_factorization_count': 5, 'max_homotopy_eligible_direct_products': 0, 'max_direct_binary_target_pieces': 4, 'route_ranker_status': 'no_homotopy_eligible_routes_in_preferred_factorizations', 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'increase homotopy_eligible_direct_product_total above zero for at least one effective-complement route', 'next_generator_feature': 'homotopy_eligible_direct_product_total', 'next_pivot': 'search_for_homotopy_eligible_effective_complement_routes', 'stop_rule': 'continue only if the next batch increases the best homotopy-eligible binary count, finds a higher-tier survivor, or proves that preferred routes in the scoped frontier cannot supply such a subproduct'}`

### cicy6784_single_anchor_effective_routes_no_homotopy_seed

- title: Single-anchor effective-complement queue has no promotable homotopy seed
- geometry: `CICY6784/model 31 option 2`
- scope_class: `candidate-specific`
- stage: `single_anchor_effective_route_queue_gate`
- cheap_prefilter: `single_anchor_effective_routes_no_homotopy_seed`
- replay_counts: `{'source': 'reports/cicy6784_single_anchor_homotopy_seed_queue.json', 'single_anchor_route_count': 11, 'selection_valid_matter_anchor_count': 6, 'shadow_route_count': 5, 'route_status_counts': {'shadow_direct_target_not_matter_anchor': 4, 'shadow_no_seed_not_matter_anchor': 1, 'valid_direct_target_no_homotopy_seed': 5, 'valid_no_direct_target_no_homotopy_seed': 1}, 'homotopy_positive_route_count': 0, 'promotable_homotopy_seed_count': 0, 'max_homotopy_eligible_direct_products': 0, 'single_anchor_route_queue_status': 'no_promotable_homotopy_seed_in_single_anchor_frontier', 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find at least one valid effective-complement route with positive homotopy_eligible_direct_product_total', 'next_generator_feature': 'homotopy_eligible_direct_product_total', 'next_pivot': 'search_beyond_single_anchor_routes_for_homotopy_seed', 'escape_hatches': ['multi-stage complement partitions rather than single-anchor factorizations', 'different frontier-48 deformations that preserve safe up/down Yukawa selection', 'other exact-overlap geometries with same-embedding one-Higgs/proton-safe seeds', 'full chain-contraction implementation if no cheap homotopy-seed grammar survives'], 'stop_rule': 'continue only if a new finite queue finds positive homotopy_eligible_direct_product_total, improves another nearest-boundary metric, or proves a scoped route grammar cannot supply such a seed'}`

### cicy6784_multistage_first_pair_no_homotopy_seed

- title: Cheap multi-stage direct-tree routes are blocked at the first H1-H1 pair
- geometry: `CICY6784/model 31 option 2`
- scope_class: `candidate-specific`
- stage: `multi_stage_direct_tree_first_pair_gate`
- cheap_prefilter: `multistage_first_pair_no_homotopy_seed`
- replay_counts: `{'source': 'reports/cicy6784_multistage_homotopy_seed_closure.json', 'all_first_pair_slot_count': 117, 'valid_first_pair_slot_count': 54, 'valid_direct_target_first_pair_slot_count': 10, 'valid_homotopy_eligible_first_pair_slot_count': 0, 'multi_stage_direct_tree_status': 'blocked_at_first_h1_h1_pair', 'coefficient_rank_status': 'pending', 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find a valid first H1-H1 pair with positive homotopy_eligible_direct_product_count', 'next_pivot': 'pivot_from_cheap_direct_tree_grammar', 'generator_feature': 'homotopy_eligible_first_pair_slot_count', 'recommended_next_pass': 'either implement full chain-contraction/homotopy-transfer machinery, or run a deformation/geometry scout whose primary rank feature is positive first-pair homotopy eligibility', 'stop_rule': 'continue only if a finite pass finds a positive first-pair homotopy seed, proves a scoped grammar closure, or produces a higher-tier survivor under symbolic verification'}`

### cicy6784_frontier48_chain_contraction_fallback_closed_current_engine

- title: Frontier-48 exact-engine fallback closes: standard m3 zero, no chain API
- geometry: `CICY6784/model 31 option 2 frontier 48`
- scope_class: `candidate-specific`
- stage: `exact_engine_chain_contraction_fallback_gate`
- cheap_prefilter: `chain_contraction_fallback_closed_current_engine`
- replay_counts: `{'source': 'reports/cicy6784_frontier48_chain_contraction_fallback.json', 'standard_m3_tree_count': 3, 'product_piece_count': 5, 'direct_binary_target_piece_total': 0, 'homotopy_eligible_direct_product_total': 0, 'standard_m3_matrix_rank': 0, 'has_exposed_product_plus_chain_contraction_api': False, 'queue_target_closed_under_current_engine': True, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'add a genuine product-plus-chain-contraction implementation or move to a geometry/presentation whose first-pair route is positive before exact coefficient evaluation', 'next_pivot': 'advance_queue_to_presentation_bridge_targets', 'recommended_next_pass': 'retire the exact-engine fallback and advance to the next presentation-bridge target, unless a new chain-contraction engine is explicitly added', 'stop_rule': 'continue CICY6784 frontier-48 only if a real product-plus-chain contraction implementation is added; otherwise pivot geometry or presentation'}`

### cicy4185_7910_split_action_lift_missing_current_data

- title: Unique favourable split witness, but no local split-action lift data
- geometry: `CICY4185 via favourable split 7910`
- scope_class: `presentation-local`
- stage: `presentation_bridge_split_action_lift_gate`
- cheap_prefilter: `split_action_lift_missing_current_data`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy4185_bridge_lift_audit.json', 'requires_split_action_lift': True, 'parent_free_action_count': 8, 'direct_one_step_split_hit_count': 1, 'selected_split_symmetry_status': 'unknown', 'selected_split_free_symmetry_option_count': 0, 'same_hodge_favourable_known_free_count': 0, 'inherited_slope_feasible_count': 0, 'bridge_status': 'cicy4185_7910_split_found_action_lift_blocked_current_data', 'same_hodge_pool_count': 165, 'favourable_unknown_nums': [7907, 7908, 7909, 7910], 'inherited_c1_zero_count': 20, 'inherited_index_pair_minus6_count': 20, 'inherited_anomaly_nonnegative_count': 20, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'construct an explicit action-transfer map from a selected CICY4185 free Z2 action to the CICY7910 split coordinates and equations', 'recommended_next_pass': 'retire this parent bridge from the queue under current data and advance to the next presentation bridge, unless a split-action transfer engine is explicitly added', 'engine_escape_hatch': 'construct a CICY4185-to-CICY7910 action-transfer map for one of the eight row-trivial free Z2 options, then rerun the bundle/slope/character promotion ladder on the 7910 split', 'stop_rule': 'return to CICY4185 only if the split action lift, full Picard action, and equivariant representative data can be computed'}`

### cicy6187_7899_split_action_lift_missing_current_data

- title: Unique favourable split witness, but no local split-action lift data
- geometry: `CICY6187 via favourable split 7899`
- scope_class: `presentation-local`
- stage: `presentation_bridge_split_action_lift_gate`
- cheap_prefilter: `split_action_lift_missing_current_data`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy6187_bridge_lift_audit.json', 'requires_split_action_lift': True, 'parent_free_action_count': 4, 'direct_one_step_split_hit_count': 1, 'selected_split_symmetry_status': 'unknown', 'selected_split_free_symmetry_option_count': 0, 'same_hodge_favourable_known_free_count': 0, 'inherited_slope_feasible_count': 0, 'bridge_status': 'cicy6187_7899_split_found_action_lift_blocked_current_data', 'same_hodge_pool_count': 98, 'favourable_unknown_nums': [7899, 7900, 7901, 7902, 7903, 7904], 'ambient_breadcrumb_target_report_count': 0, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'construct an explicit action-transfer map from a selected CICY6187 free Z2 action to the CICY7899 split coordinates and equations', 'recommended_next_pass': 'retire this parent bridge from the queue under current data and advance to the next presentation bridge, unless a split-action transfer engine is explicitly added', 'engine_escape_hatch': 'construct a CICY6187-to-CICY7899 action-transfer map for one of the four row-trivial free Z2 options, including split equation characters for the three merged columns, then rerun the bundle/slope/character promotion ladder on the 7899 split', 'stop_rule': 'return to CICY6187 only if the split action lift, full Picard action, and equivariant representative data can be computed'}`

### cicy6201_7900_split_action_lift_missing_current_data

- title: Unique favourable split witness, but no local split-action lift data
- geometry: `CICY6201 via favourable split 7900`
- scope_class: `presentation-local`
- stage: `presentation_bridge_split_action_lift_gate`
- cheap_prefilter: `split_action_lift_missing_current_data`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy6201_bridge_lift_audit.json', 'requires_split_action_lift': True, 'parent_free_action_count': 4, 'direct_one_step_split_hit_count': 1, 'selected_split_symmetry_status': 'unknown', 'selected_split_free_symmetry_option_count': 0, 'same_hodge_favourable_known_free_count': 0, 'inherited_slope_feasible_count': 0, 'bridge_status': 'cicy6201_7900_split_found_action_lift_blocked_current_data', 'same_hodge_pool_count': 98, 'favourable_unknown_nums': [7899, 7900, 7901, 7902, 7903, 7904], 'ambient_breadcrumb_target_report_count': 0, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'construct an explicit action-transfer map from a selected CICY6201 free Z2 action to the CICY7900 split coordinates and equations', 'recommended_next_pass': 'retire this parent bridge from the queue under current data and advance to the next presentation bridge, unless a split-action transfer engine is explicitly added', 'engine_escape_hatch': 'construct a CICY6201-to-CICY7900 action-transfer map for one of the four row-trivial free Z2 options, including split equation characters for the three merged columns, then rerun the bundle/slope/character promotion ladder on the 7900 split', 'stop_rule': 'return to CICY6201 only if the split action lift, full Picard action, and equivariant representative data can be computed'}`

### cicy6281_7904_split_action_lift_missing_current_data

- title: Unique favourable split witness, but no local split-action lift data
- geometry: `CICY6281 via favourable split 7904`
- scope_class: `presentation-local`
- stage: `presentation_bridge_split_action_lift_gate`
- cheap_prefilter: `split_action_lift_missing_current_data`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy6281_bridge_lift_audit.json', 'requires_split_action_lift': True, 'parent_free_action_count': 4, 'direct_one_step_split_hit_count': 1, 'selected_split_symmetry_status': 'unknown', 'selected_split_free_symmetry_option_count': 0, 'same_hodge_favourable_known_free_count': 0, 'inherited_slope_feasible_count': 0, 'bridge_status': 'cicy6281_7904_split_found_action_lift_blocked_current_data', 'same_hodge_pool_count': 98, 'favourable_unknown_nums': [7899, 7900, 7901, 7902, 7903, 7904], 'ambient_breadcrumb_target_report_count': 0, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'construct an explicit action-transfer map from a selected CICY6281 free Z2 action to the CICY7904 split coordinates and equations', 'recommended_next_pass': 'retire this parent bridge from the queue under current data and advance to the next presentation bridge, unless a split-action transfer engine is explicitly added', 'engine_escape_hatch': 'construct a CICY6281-to-CICY7904 action-transfer map for one of the four row-trivial free Z2 options, including split equation characters for the three merged columns, then rerun the bundle/slope/character promotion ladder on the 7904 split', 'stop_rule': 'return to CICY6281 only if the split action lift, full Picard action, and equivariant representative data can be computed'}`

### cicy4078_7908_split_action_lift_missing_current_data

- title: Unique favourable split witness, but no local split-action lift data
- geometry: `CICY4078 via favourable split 7908`
- scope_class: `presentation-local`
- stage: `presentation_bridge_split_action_lift_gate`
- cheap_prefilter: `split_action_lift_missing_current_data`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy4078_bridge_lift_audit.json', 'requires_split_action_lift': True, 'parent_free_action_count': 4, 'direct_one_step_split_hit_count': 1, 'selected_split_symmetry_status': 'unknown', 'selected_split_free_symmetry_option_count': 0, 'same_hodge_favourable_known_free_count': 0, 'inherited_slope_feasible_count': 0, 'bridge_status': 'cicy4078_7908_split_found_action_lift_blocked_current_data', 'same_hodge_pool_count': 165, 'favourable_unknown_nums': [7907, 7908, 7909, 7910], 'inherited_c1_zero_count': 20, 'inherited_index_pair_minus6_count': 20, 'inherited_anomaly_nonnegative_count': 20, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'construct an explicit action-transfer map from a selected CICY4078 free Z2 action to the CICY7908 split coordinates and equations', 'recommended_next_pass': 'retire this parent bridge from the queue under current data and advance to the next presentation bridge, unless a split-action transfer engine is explicitly added', 'engine_escape_hatch': 'construct a CICY4078-to-CICY7908 action-transfer map for one of the four row-trivial free Z2 options, then rerun the bundle/slope/character promotion ladder on the 7908 split', 'stop_rule': 'return to CICY4078 only if the split action lift, full Picard action, and equivariant representative data can be computed'}`

### cicy5141_7912_split_action_lift_missing_current_data

- title: Unique favourable split witness, but no local split-action lift data
- geometry: `CICY5141 via favourable split 7912`
- scope_class: `presentation-local`
- stage: `presentation_bridge_split_action_lift_gate`
- cheap_prefilter: `split_action_lift_missing_current_data`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy5141_bridge_lift_audit.json', 'requires_split_action_lift': True, 'parent_free_action_count': 4, 'direct_one_step_split_hit_count': 1, 'selected_split_symmetry_status': 'unknown', 'selected_split_free_symmetry_option_count': 0, 'same_hodge_favourable_known_free_count': 0, 'inherited_slope_feasible_count': 0, 'bridge_status': 'cicy5141_7912_split_found_action_lift_blocked_current_data', 'same_hodge_pool_count': 59, 'favourable_unknown_nums': [7912, 7913, 7914, 7915, 7916, 7917, 7918, 7919], 'ambient_breadcrumb_target_report_count': 0, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'construct an explicit action-transfer map from a selected CICY5141 free Z2 action to the CICY7912 split coordinates and equations', 'recommended_next_pass': 'retire this parent bridge from the queue under current data; all queued presentation bridges are now closed unless a split-action transfer engine is explicitly added', 'engine_escape_hatch': 'construct a CICY5141-to-CICY7912 action-transfer map for one of the four row-trivial free Z2 options, including split equation characters for the three merged columns, then rerun the bundle/slope/character promotion ladder on the 7912 split', 'stop_rule': 'return to CICY5141 only if the split action lift, full Picard action, and equivariant representative data can be computed'}`

### cicy5248_7913_split_action_lift_missing_current_data

- title: Unique favourable split witness, but no local split-action lift data
- geometry: `CICY5248 via favourable split 7913`
- scope_class: `presentation-local`
- stage: `presentation_bridge_split_action_lift_gate`
- cheap_prefilter: `split_action_lift_missing_current_data`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy5248_bridge_action_transfer_audit.json', 'requires_split_action_lift': True, 'parent_free_action_count': 4, 'direct_one_step_split_hit_count': 1, 'selected_split_symmetry_status': 'unknown', 'selected_split_free_symmetry_option_count': 0, 'same_hodge_favourable_known_free_count': 0, 'inherited_slope_feasible_count': 0, 'bridge_status': 'cicy5248_7913_split_found_action_lift_blocked_current_data', 'same_hodge_pool_count': 59, 'favourable_unknown_nums': [7912, 7913, 7914, 7915, 7916, 7917, 7918, 7919], 'ambient_breadcrumb_target_report_count': 0, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'construct an explicit action-transfer map from a selected CICY5248 free Z2 action to the CICY7913 split coordinates and equations', 'recommended_next_pass': 'CICY5406_same_hodge_bridge_action_transfer_audit', 'engine_escape_hatch': 'return to CICY5248 only if an explicit action-transfer engine is implemented for the CICY7913 split equations', 'stop_rule': 'Do not promote CICY5248 until a documented transfer realizes the parent free action on the CICY7913 split data.'}`

### cicy5406_7918_split_action_lift_missing_current_data

- title: Unique favourable split witness, but no local split-action lift data
- geometry: `CICY5406 via favourable split 7918`
- scope_class: `presentation-local`
- stage: `presentation_bridge_split_action_lift_gate`
- cheap_prefilter: `split_action_lift_missing_current_data`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy5406_bridge_action_transfer_audit.json', 'requires_split_action_lift': True, 'parent_free_action_count': 4, 'direct_one_step_split_hit_count': 1, 'selected_split_symmetry_status': 'unknown', 'selected_split_free_symmetry_option_count': 0, 'same_hodge_favourable_known_free_count': 0, 'inherited_slope_feasible_count': 0, 'bridge_status': 'cicy5406_7918_split_found_action_lift_blocked_current_data', 'same_hodge_pool_count': 59, 'favourable_unknown_nums': [7912, 7913, 7914, 7915, 7916, 7917, 7918, 7919], 'ambient_breadcrumb_target_report_count': 0, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'construct an explicit action-transfer map from a selected CICY5406 free Z2 action to the CICY7918 split coordinates and equations', 'recommended_next_pass': 'CICY5449_same_hodge_bridge_action_transfer_audit', 'engine_escape_hatch': 'return to CICY5406 only if an explicit action-transfer engine is implemented for the CICY7918 split equations', 'stop_rule': 'Do not promote CICY5406 until a documented transfer realizes the parent free action on the CICY7918 split data.'}`

### cicy5449_no_direct_split_witness_current_data

- title: Same-Hodge favourable pool exists, but no direct split witness
- geometry: `CICY5449 no direct favourable split witness`
- scope_class: `presentation-local`
- stage: `presentation_bridge_witness_selection_gate`
- cheap_prefilter: `direct_split_witness_missing_current_data`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy5449_bridge_action_transfer_audit.json', 'requires_concrete_split_witness': True, 'parent_free_action_count': 4, 'same_hodge_pool_count': 59, 'same_hodge_favourable_unknown_count': 8, 'same_hodge_favourable_known_free_count': 0, 'direct_one_step_split_hit_count': 0, 'bridge_status': 'cicy5449_no_direct_split_witness_blocked_current_data', 'ambient_breadcrumb_target_report_count': 0, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find a concrete favourable presentation witness for CICY5449 by broadening beyond ordinary one-step P2 split contractions', 'recommended_next_pass': 'CICY7810_same_hodge_bridge_action_transfer_audit', 'engine_escape_hatch': 'return to CICY5449 only if a broader split/isomorphism search finds a concrete favourable presentation witness', 'stop_rule': 'Do not promote CICY5449 until a concrete favourable witness or presentation isomorphism is documented.'}`

### cicy7810_no_direct_split_witness_current_data

- title: Z3 same-Hodge favourable pool exists, but no direct split witness
- geometry: `CICY7810 no direct favourable split witness`
- scope_class: `presentation-local`
- stage: `presentation_bridge_witness_selection_gate`
- cheap_prefilter: `direct_split_witness_missing_current_data`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy7810_bridge_action_transfer_audit.json', 'requires_concrete_split_witness': True, 'parent_free_action_count': 3, 'same_hodge_pool_count': 2, 'same_hodge_favourable_unknown_count': 2, 'same_hodge_favourable_known_free_count': 0, 'direct_one_step_split_hit_count': 0, 'bridge_status': 'cicy7810_no_direct_split_witness_blocked_current_data', 'ambient_breadcrumb_target_report_count': 0, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find a concrete favourable presentation witness for CICY7810 by broadening beyond ordinary one-step split-row contractions', 'recommended_next_pass': 'CICY5302_gutall_benchmark_pool_engine_audit', 'engine_escape_hatch': 'return to CICY7810 only if an explicit split/isomorphism route to a favourable same-Hodge witness is documented', 'stop_rule': 'Do not promote CICY7810 until a concrete favourable witness or presentation isomorphism is documented.'}`

### cicy5302_gutall_benchmark_pool_engine_gap_current_data

- title: Large clean GUTall benchmark pool, but no current CICY5302 promotion engine
- geometry: `CICY5302 GUTall benchmark pool`
- scope_class: `grammar-local`
- stage: `geometry_specific_equivariant_representative_and_component_mass_engine_gate`
- cheap_prefilter: `geometry_specific_engine_missing_current_data`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy5302_gutall_benchmark_pool_engine_audit.json', 'requires_geometry_specific_promotion_engine': True, 'model_count': 23623, 'algebraic_benchmark_failure_count': 0, 'raw_free_action_count': 20, 'generic_ambient_line_bundle_lift_readiness_engine_available': True, 'geometry_specific_wilson_component_engine_available': False, 'geometry_specific_representative_mass_engine_available': False, 'generic_representative_promotion_engine_available': False, 'engine_gap_status': 'cicy5302_gutall_benchmark_pool_engine_gap_current_data', 'order2_ambient_lift_ready_count': 6294, 'order4_ambient_lift_ready_count': 3879, 'order4_ambient_lift_obstructed_count': 13450, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'implement a CICY5302 Wilson-component and equivariant Koszul representative mass-channel engine', 'recommended_next_pass': 'CICY5273_gutall_benchmark_pool_engine_audit', 'engine_escape_hatch': 'Return to CICY5302 only after adding a geometry-specific Wilson/component/representative/mass-channel engine or a generic engine that verifies CICY5302 promotion gates.', 'stop_rule': 'Do not call any CICY5302 row MSSM-like until component characters, representative realizability, operator safety, and mass-channel eligibility are computed by a CICY5302-compatible engine.'}`

### cicy5273_gutall_benchmark_pool_raw_action_gap_current_data

- title: Clean GUTall benchmark pool, but no local raw free-action option
- geometry: `CICY5273 GUTall benchmark pool`
- scope_class: `grammar-local`
- stage: `raw_free_action_data_gate`
- cheap_prefilter: `raw_free_action_data_missing_current_data`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy5273_gutall_benchmark_pool_engine_audit.json', 'algebraic_benchmark_failure_count': 0, 'gutall_symmetry_orders': [2], 'model_count': 6753, 'raw_action_gap_status': 'cicy5273_gutall_benchmark_pool_raw_action_gap_current_data', 'raw_free_action_count': 0, 'raw_symmetry_option_count': 1, 'requires_raw_free_action_data': True, 'order2_ambient_lift_ready_count': 0, 'order2_ambient_lift_obstructed_count': 6753, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'recover explicit raw free-action data for CICY5273 or provide an external quotient-action certificate compatible with Wilson descent', 'recommended_next_pass': 'CICY6738_gutall_benchmark_pool_engine_audit', 'engine_escape_hatch': 'Return to CICY5273 only after adding explicit raw free-action data or an external quotient-action certificate compatible with Wilson/component descent.', 'stop_rule': 'Do not call any CICY5273 row quotient-compatible beyond the algebraic GUTall benchmark layer until a concrete free-action option is available locally or externally certified.'}`

### cicy6738_gutall_benchmark_pool_raw_action_gap_current_data

- title: Clean GUTall benchmark pool, but no local raw free-action option
- geometry: `CICY6738 GUTall benchmark pool`
- scope_class: `grammar-local`
- stage: `raw_free_action_data_gate`
- cheap_prefilter: `raw_free_action_data_missing_current_data`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy6738_gutall_benchmark_pool_engine_audit.json', 'algebraic_benchmark_failure_count': 0, 'gutall_symmetry_orders': [2], 'model_count': 4243, 'raw_action_gap_status': 'cicy6738_gutall_benchmark_pool_raw_action_gap_current_data', 'raw_free_action_count': 0, 'raw_symmetry_option_count': 1, 'requires_raw_free_action_data': True, 'order2_ambient_lift_ready_count': 0, 'order2_ambient_lift_obstructed_count': 4243, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'recover explicit raw free-action data for CICY6738 or provide an external quotient-action certificate compatible with Wilson descent', 'recommended_next_pass': 'CICY5425_gutall_benchmark_pool_engine_audit', 'engine_escape_hatch': 'Return to CICY6738 only after adding explicit raw free-action data or an external quotient-action certificate compatible with Wilson/component descent.', 'stop_rule': 'Do not call any CICY6738 row quotient-compatible beyond the algebraic GUTall benchmark layer until a concrete free-action option is available locally or externally certified.'}`

### cicy5425_gutall_benchmark_pool_raw_action_gap_current_data

- title: Clean GUTall benchmark pool, but no local raw free-action option
- geometry: `CICY5425 GUTall benchmark pool`
- scope_class: `grammar-local`
- stage: `raw_free_action_data_gate`
- cheap_prefilter: `raw_free_action_data_missing_current_data`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy5425_gutall_benchmark_pool_engine_audit.json', 'algebraic_benchmark_failure_count': 0, 'gutall_symmetry_orders': [2], 'model_count': 3128, 'raw_action_gap_status': 'cicy5425_gutall_benchmark_pool_raw_action_gap_current_data', 'raw_free_action_count': 0, 'raw_symmetry_option_count': 1, 'requires_raw_free_action_data': True, 'order2_ambient_lift_ready_count': 0, 'order2_ambient_lift_obstructed_count': 3128, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'recover explicit raw free-action data for CICY5425 or provide an external quotient-action certificate compatible with Wilson descent', 'recommended_next_pass': 'CICY5256_gutall_benchmark_pool_engine_audit', 'engine_escape_hatch': 'Return to CICY5425 only after adding explicit raw free-action data or an external quotient-action certificate compatible with Wilson/component descent.', 'stop_rule': 'Do not call any CICY5425 row quotient-compatible beyond the algebraic GUTall benchmark layer until a concrete free-action option is available locally or externally certified.'}`

### cicy5256_gutall_benchmark_pool_engine_gap_current_data

- title: Clean GUTall benchmark pool, but no current CICY5256 promotion engine
- geometry: `CICY5256 GUTall benchmark pool`
- scope_class: `grammar-local`
- stage: `geometry_specific_equivariant_representative_and_component_mass_engine_gate`
- cheap_prefilter: `geometry_specific_engine_missing_current_data`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/cicy5256_gutall_benchmark_pool_engine_audit.json', 'algebraic_benchmark_failure_count': 0, 'engine_gap_status': 'cicy5256_gutall_benchmark_pool_engine_gap_current_data', 'generic_ambient_line_bundle_lift_readiness_engine_available': True, 'generic_representative_promotion_engine_available': False, 'geometry_specific_representative_mass_engine_available': False, 'geometry_specific_wilson_component_engine_available': False, 'model_count': 2891, 'raw_free_action_count': 6, 'requires_geometry_specific_promotion_engine': True, 'order2_ambient_lift_ready_count': 763, 'order4_ambient_lift_ready_count': 544, 'order4_ambient_lift_obstructed_count': 1584, 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'implement a CICY5256 Wilson-component and equivariant Koszul representative mass-channel engine', 'recommended_next_pass': 'CICY5452_gutall_benchmark_pool_engine_audit', 'engine_escape_hatch': 'Return to CICY5256 only after adding a geometry-specific Wilson/component/representative/mass-channel engine or a generic engine that verifies CICY5256 promotion gates.', 'stop_rule': 'Do not call any CICY5256 row MSSM-like until component characters, representative realizability, operator safety, and mass-channel eligibility are computed by a CICY5256-compatible engine.'}`

### cicy6784_radius4_local_deformation_no_first_pair_seed

- title: Radius-4 local q=1 deformation scout finds no positive first-pair homotopy seed
- geometry: `CICY6784/model 31 option 2`
- scope_class: `grammar-local`
- stage: `local_deformation_first_pair_seed_gate`
- cheap_prefilter: `local_deformation_first_pair_no_homotopy_seed`
- replay_counts: `{'source': 'reports/cicy6784_radius4_first_pair_seed_scout.json', 'frontier_size': 2009, 'stage_counts': {'failed_index_target': 1853, 'failed_no_trivial_summand': 6, 'failed_option2_lift': 47, 'failed_q1_no_anti10_gate': 101, 'q1_candidate': 2}, 'q1_candidate_count': 2, 'promoted_q1_count': 2, 'promotion_timeout_count': 0, 'safe_up_down_yukawa_record_count': 1, 'positive_first_pair_seed_record_count': 0, 'max_valid_homotopy_eligible_first_pair_slot_count': 0, 'max_valid_direct_target_first_pair_slot_count': 10, 'deformation_scout_status': 'no_positive_first_pair_homotopy_seed_in_radius4_frontier', 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find a q=1 local deformation with safe up/down Yukawa selection and positive valid_homotopy_eligible_first_pair_slot_count', 'current_stop_rule': 'continue this deformation grammar only if the next finite pass finds a positive first-pair seed, improves the safe-up/down frontier, or resolves a higher-tier symbolic gate', 'recommended_pivot': 'search cross-geometry or broader generators that rank by positive first-pair homotopy eligibility before promotion, or implement full chain contraction for the current lead'}`

### verified_overlap_first_pair_seed_absent

- title: Verified overlap queue has no positive first-pair homotopy seed
- geometry: `Verified order-4 overlap queue and CICY6784 radius-4 extension`
- scope_class: `grammar-local`
- stage: `verified_overlap_first_pair_seed_gate`
- cheap_prefilter: `verified_overlap_first_pair_seed_absent`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/verified_overlap_first_pair_seed_scout.json', 'retrieval_relevant_row_count': 43, 'scored_record_count': 5, 'safe_up_type_only_record_count': 2, 'safe_up_down_yukawa_record_count': 1, 'positive_first_pair_seed_record_count': 0, 'max_valid_homotopy_eligible_first_pair_slot_count': 0, 'first_pair_seed_scout_status': 'no_positive_first_pair_seed_in_verified_overlap_queue', 'coefficient_rank_status': 'pending', 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find at least one reconstruction-authoritative row with safe up/down Yukawa support and positive first-pair homotopy eligibility', 'recommended_pivot': 'broaden the generator around first-pair homotopy eligibility as a primary feature, or implement full chain contraction for the existing CICY6784 frontier-48 lead', 'stop_rule': 'continue only if a finite pass finds positive first-pair homotopy eligibility, expands the reconstruction-authoritative overlap pool, or resolves the full chain-contraction gate'}`

### first_pair_positive_generator_no_seed_radius4

- title: Radius-4 first-pair-positive generator expansion finds no seed
- geometry: `CICY6784/model 7, 14, 31 option 2 plus radius-4 frontier boundary`
- scope_class: `grammar-local`
- stage: `first_pair_positive_generator_gate`
- cheap_prefilter: `first_pair_positive_generator_no_seed`
- replay_counts: `{'source': 'experiments/latent_atlas/reports/first_pair_positive_generator_expansion.json', 'seed_count': 4, 'frontier_size': 9891, 'q1_candidate_count': 4, 'promoted_q1_count': 4, 'safe_up_type_only_record_count': 2, 'safe_up_down_yukawa_record_count': 1, 'positive_first_pair_seed_record_count': 0, 'max_valid_homotopy_eligible_first_pair_slot_count': 0, 'generator_expansion_status': 'no_positive_first_pair_seed_in_radius4_expansion', 'coefficient_rank_status': 'pending', 'prefilter_sample_passes': True}`
- nearest_escape_or_boundary: `{'minimal_change': 'find a q1 promotion in this or a broader generator with safe up/down Yukawa support and positive first-pair homotopy eligibility', 'recommended_pivot': 'either implement full chain contraction for the current CICY6784 lead, or expand beyond this CICY6784 radius-4 option-2 grammar to geometries/generators whose first scored feature is positive H1-H1 homotopy eligibility', 'stop_rule': 'continue this generator only if it finds positive first-pair homotopy eligibility, adds a new q1/safe-up-down branch, or resolves a higher-tier chain-level gate'}`

## No Active Survivor Certificates

Branch 50 is now recorded as `branch50_standard_m4_four_h1_not_cy3_top_cup`, a candidate-specific negative control.


## Gates

- source_verifications_pass: `True` - all imported source verifications pass
- covers_requested_artifact_families: `True` - atlas covers 2544, 7484, 5259/7914, 6927/model-874/model-252/model-254/model-369/model-52, 6836/model-136, 6836, 6715, 6788, 6784, presentation-bridge artifacts, CICY5302, CICY5273, CICY6738, CICY5425, and CICY5256
- every_syndrome_has_scoped_prefilter_and_replay: `True` - each no-go syndrome has scope class, executable prefilter, replay counts, and evidence
- prefilter_self_tests_pass: `True` - each atlas prefilter fires on its representative obstruction sample
- branch50_negative_control_is_present: `True` - Branch 50 is preserved as a negative control, not a survivor certificate
- no_active_survivor_after_degree_audit: `True` - the previous pending survivor is retired by the standard m4 degree-law audit
