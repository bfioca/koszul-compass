# Radius-9 Representative Obstruction And Escape Report

Status: `no_representative_compatible_escape_target_in_bounded_materialized_scan`

## Obstruction Anatomy

- `5_12:cup_H1_wedge2_V_dual` weight `1512` operators `['5bar_12*5_12']`: branch `{'+': 0, '-': 2}` vs representative `{'+': 1, '-': 1}`; avoid cup-dual branch assignments that request a non-regular character when dimension-certified E2 gives a regular representative
- `5bar_02:physical_H1_wedge2_V` weight `9` operators `['5bar_02*5_24']`: branch `{'+': 2, '-': 0}` vs representative `{'+': 1, '-': 1}`; avoid branch completions that demand image rank beyond an eigenspace source/target bound; require rank-feasible requested characters before promotion
- `5bar_04:physical_H1_wedge2_V` weight `252` operators `['5bar_04*5_34']`: branch `{'+': 2, '-': 4}` vs representative `{'+': 3, '-': 3}`; avoid branch completions that demand image rank beyond an eigenspace source/target bound; require rank-feasible requested characters before promotion
- `5bar_23:physical_H1_wedge2_V` weight `189` operators `['5bar_23*5_23']`: branch `{'+': 2, '-': 0}` vs representative `{'+': 2, '-': 1}`; avoid branch kernels whose requested dimension/character is smaller than the explicit equivariant d1 kernel

## Bounded Escape Scan

- bounds: `{'windows': 45, 'max_unique_operators': 24, 'max_audits': 24, 'known_failure_operators_excluded_from_escape_audit': ['5bar_02*5_24', '5bar_04*5_34', '5bar_12*5_12', '5bar_23*5_23']}`
- scanned: `{'materialized_records': 4065, 'represented_weight': 549038, 'records_with_triplet_only_shadow_operator': 1530, 'records_skipped_because_only_known_failure_operators': 609, 'classification_status_weight': {'character_refined_doublet_mass_obstruction': 33072, 'no_character_refined_triplet_mass_operator_found': 510611, 'passes_refined_charge_character_dt_and_proton_filter': 1962, 'selective_dt_but_proton_unprotected': 3393}}`
- triplet-only operator rows: `{'5bar_01*5_12': 324, '5bar_01*5_14': 140, '5bar_02*5_12': 88, '5bar_02*5_24': 9, '5bar_02*5_34': 88, '5bar_03*5_03': 54, '5bar_03*5_34': 13, '5bar_04*5_24': 30, '5bar_04*5_34': 30, '5bar_12*5_12': 609, '5bar_13*5_34': 64, '5bar_14*5_12': 2, '5bar_14*5_14': 126, '5bar_23*5_23': 17, '5bar_24*5_12': 6, '5bar_34*5_34': 98}`
- selected escape operator count: `12`
- audited escape target count: `12`
- representative-compatible targets: `0`
- representative-unresolved targets: `1`
- representative-obstructed targets: `11`

## Interpretation

- active_bottleneck: `representative-realizability, not cup-product rank`
- search_guidance: `future search should prefilter branch-completed characters by rank-feasible and E2-certified representative characters before lead/cup-product promotion`
- grind_assessment: `blind radius expansion is low-value until the grammar can generate mass operators outside the observed representative-failure shapes`

## Gates

- imports_verified_prefilter: `True` - classifier starts from the verified representative-prefilter closure
- obstruction_classes_cover_closed_frontier: `True` - four representative obstruction classes account for all shadow-viable weight
- escape_scan_is_bounded: `True` - escape scan is explicitly bounded and does not expand the radius frontier
- escape_scan_covers_materialized_q1_records: `True` - escape scan traversed existing materialized q=1 source records
- no_representative_compatible_escape_target: `True` - bounded escape scan found no representative-compatible triplet mass target
