# CICY5256 GUTall Benchmark Pool Engine Audit

Status: `cicy5256_gutall_benchmark_pool_engine_gap_current_data`
Scope: finite audit of the CICY5256 favourable GUTall benchmark pool and current promotion-engine availability

## Classification

- candidate_status: `not_a_candidate_claim`
- mssm_candidate_verified: `False`
- pool_status: `cicy5256_gutall_benchmark_pool_engine_gap_current_data`
- claim_boundary: `This certifies a clean algebraic GUTall pool, recorded row-trivial free actions, and bounded ambient lift readiness. It does not rule out CICY5256 physically; it says the current pipeline cannot promote this pool without new geometry-specific component/representative machinery.`

## Geometry

- num: `5256`
- h11: `5`
- h21: `29`
- eta: `-48`
- symmetry_orders_in_cicy_entry: `[2, 4]`
- ambient_dimensions: `(1, 1, 1, 1, 3)`
- ambient_coordinate_block_sizes: `[2, 2, 2, 2, 4]`
- c2_tx: `[24, 24, 24, 24, 40]`

## Algebraic Pool

- model_count: `2891`
- model_counts_by_symmetry_order: `{'2': 763, '4': 2128}`
- unique_model_key_count: `2891`
- failure_count: `0`

## Raw Free Actions

- free_option_count: `6`
- free_order_counts: `{'2': 2, '4': 4}`
- free_group_structure_counts: `{'2': 2, '2x2': 4}`
- all_free_options_row_trivial: `True`

## Ambient Lift Readiness

### order 2
- model_count: `763`
- any_direct_sum_equivariant_lift_count: `763`
- no_direct_sum_equivariant_lift_count: `0`
- lift_option_count_distribution: `{'2': 763}`
### order 4
- model_count: `2128`
- any_direct_sum_equivariant_lift_count: `544`
- no_direct_sum_equivariant_lift_count: `1584`
- lift_option_count_distribution: `{'0': 1584, '4': 544}`

## Promotion Engine Inventory

- generic_algebraic_index_anomaly_engine_available: `True`
- generic_raw_free_action_parser_available: `True`
- generic_ambient_line_bundle_lift_readiness_engine_available: `True`
- geometry_specific_wilson_component_engine_available: `False`
- geometry_specific_representative_mass_engine_available: `False`
- generic_representative_promotion_engine_available: `False`
- cicy5256_specific_engine_artifacts: `[]`
- matched_current_engine_artifacts: `[]`
- known_geometry_specific_engine_families: `['CICY5259 via favourable split 7914', 'CICY6715/CICY6927 same-Hodge lateral', 'CICY6784', 'CICY6788', 'CICY6836', 'CICY7484']`
- first_missing_gate: `geometry_specific_equivariant_representative_and_component_mass_engine`
- cheapest_next_primitive: `Implement a CICY5256 Wilson-component and equivariant Koszul representative engine for the row-trivial P1^4 x P3 free Z2/Z2xZ2 actions, then rerun bounded q1/one-Higgs/proton-safe promotion.`

## No-Go Atlas Extension

- syndrome_id: `cicy5256_gutall_benchmark_pool_engine_gap_current_data`
- scope_class: `grammar-local`
- cheap_prefilter: `geometry_specific_engine_missing_current_data`
- nearest_escape: Add a CICY5256-specific Wilson-component and equivariant Koszul representative promotion engine, or pivot to the next GUTall benchmark pool while preserving this pool as an algebraically clean future target.

## Next Step

- recommended_next_target_id: `CICY5452_gutall_benchmark_pool_engine_audit`
- return_condition: `Return to CICY5256 only after adding a geometry-specific Wilson/component/representative/mass-channel engine or a generic engine that verifies CICY5256 promotion gates.`
- stop_rule: `Do not call any CICY5256 row MSSM-like until component characters, representative realizability, operator safety, and mass-channel eligibility are computed by a CICY5256-compatible engine.`

## Gates

- source_verifications_pass: `True` - audit imports only verified source artifacts
- queue_target_matches_cicy5256: `True` - audit starts from the CICY5256 queue target
- raw_record_matches_gutall_pool: `True` - selected raw-source row is the expected CICY5256 GUTall pool
- algebraic_pool_reproduced: `True` - all CICY5256 GUTall rows pass c1/index/anomaly/duplicate algebraic gates
- raw_free_actions_reproduced: `True` - CICY5256 raw cicylist actions are recorded and row-trivial
- ambient_lift_readiness_is_bounded: `True` - ambient line-bundle lift readiness is counted before promotion
- promotion_engine_gap_is_current: `True` - no current CICY5256 component/representative promotion engine is registered
- no_candidate_overclaimed: `True` - engine audit remains below candidate promotion
