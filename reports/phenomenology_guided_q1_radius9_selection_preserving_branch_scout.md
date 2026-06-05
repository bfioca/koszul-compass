# Radius-9 Selection-Preserving Representative-Feasible Branch Scout

Status: `selection_preserving_branch_scout_found_representative_compatible_candidate`

## Summary

- windows_closed: `45`
- seed_rows: `14`
- seed_weight: `1962`
- observed_triplet_only_operator_shape_count: `16`
- feasible_pattern_count: `37`
- branch_replacement_variant_count: `28`
- matrix_certified_variant_count: `26`
- q1_preserving_variant_count: `4`
- q1_and_matrix_certified_variant_count: `4`
- selection_preserving_variant_count: `4`
- representative_compatible_count: `4`
- representative_unresolved_count: `0`
- cup_product_eligible_count: `4`
- failure_class_rows: `{'q1_signature_lost': 24, 'representative_compatible': 4}`
- failure_class_weight: `{'q1_signature_lost': 900, 'representative_compatible': 3024}`
- representative_status_rows: `{'not_evaluated_q1_not_preserved': 24, 'representative_compatible': 4}`

## Pattern Compatibility

- `5bar_02*5_24|all_obstructed_legs_feasible`: failures `{'q1_signature_lost': 9}`, selection-preserving weight `0`, compatible weight `0`
- `5bar_02*5_24|first_obstructed_leg_feasible`: failures `{'q1_signature_lost': 9}`, selection-preserving weight `0`, compatible weight `0`
- `5bar_04*5_34|all_obstructed_legs_feasible`: failures `{'q1_signature_lost': 252}`, selection-preserving weight `0`, compatible weight `0`
- `5bar_04*5_34|first_obstructed_leg_feasible`: failures `{'q1_signature_lost': 252}`, selection-preserving weight `0`, compatible weight `0`
- `5bar_12*5_12|all_obstructed_legs_feasible`: failures `{'representative_compatible': 1512}`, selection-preserving weight `1512`, compatible weight `1512`
- `5bar_12*5_12|first_obstructed_leg_feasible`: failures `{'representative_compatible': 1512}`, selection-preserving weight `1512`, compatible weight `1512`
- `5bar_23*5_23|all_obstructed_legs_feasible`: failures `{'q1_signature_lost': 189}`, selection-preserving weight `0`, compatible weight `0`
- `5bar_23*5_23|first_obstructed_leg_feasible`: failures `{'q1_signature_lost': 189}`, selection-preserving weight `0`, compatible weight `0`

## Compatible Branch-Scout Rows

- `radius6_broad_adjacency_filtered_1_large_branch_q1_representative_selection_preserving_branch_0`: seed `radius6_broad_adjacency_filtered_1_large_branch_q1_representative`, window `32`, operator `5bar_12*5_12`, replacement `5_12:cup_H1_wedge2_V_dual`, net families `3`, vectorlike pairs `T=1, D=1`, max normalized slope `6.812705686994303e-08`
- `radius6_broad_adjacency_filtered_1_large_branch_q1_representative_selection_preserving_branch_1`: seed `radius6_broad_adjacency_filtered_1_large_branch_q1_representative`, window `32`, operator `5bar_12*5_12`, replacement `5_12:cup_H1_wedge2_V_dual`, net families `3`, vectorlike pairs `T=1, D=1`, max normalized slope `6.812705686994303e-08`
- `radius6_broad_adjacency_filtered_3_large_branch_q1_representative_selection_preserving_branch_0`: seed `radius6_broad_adjacency_filtered_3_large_branch_q1_representative`, window `36`, operator `5bar_12*5_12`, replacement `5_12:cup_H1_wedge2_V_dual`, net families `3`, vectorlike pairs `T=1, D=1`, max normalized slope `6.812705689222004e-08`
- `radius6_broad_adjacency_filtered_3_large_branch_q1_representative_selection_preserving_branch_1`: seed `radius6_broad_adjacency_filtered_3_large_branch_q1_representative`, window `36`, operator `5bar_12*5_12`, replacement `5_12:cup_H1_wedge2_V_dual`, net families `3`, vectorlike pairs `T=1, D=1`, max normalized slope `6.812705689222004e-08`

## Interpretation

- active_obstruction: `most representative-feasible branch replacements destroy q=1; the surviving selection-preserving replacements are representative-compatible scout targets`
- current_result: `selection-preserving branch replacement finds representative-compatible, cup-product-eligible branch-character scout targets pending full realization checks`
- caveat: `compatible rows are synthetic branch-character replacements over fixed matrices; they are not yet new full matrix/cup-product certificates`

## Gates

- imports_verified_generation_replay: `True` - branch scout starts from the verified representative-gated generation replay
- imports_verified_feasible_patterns: `True` - branch scout imports the verified observed operator inventory
- mines_requested_seed_and_pattern_sets: `True` - the scout covers the requested 14 pruned survivors and 16 observed operator shapes
- enumerates_branch_character_replacements: `True` - the scout enumerates representative-feasible branch-character replacements
- selection_preservation_is_tested: `True` - the scout distinguishes q1 loss from matrix-certified selection-preserving variants
- matrix_gates_are_recomputed: `True` - index, anomaly, and slope gates are recomputed before representative promotion
- representative_audit_is_selection_gated: `True` - promotion is only allowed after q=1, refined selection, and proton gates
- outcome_is_resolved: `True` - the scout either emits selection-gated survivors or proves zero promotion-ready replacements
