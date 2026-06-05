# Radius-9 Representative-Gated Generation Replay Rollup

Status: `radius9_representative_generation_replay_zero_promotion_ready_candidates`

## Summary

- windows_closed: `45`
- materialized_q1_records_generated: `4065`
- materialized_q1_weight_generated: `549038`
- selection_rule_candidate_rows: `14`
- selection_rule_candidate_weight: `1962`
- representative_grammar_pruned_rows: `14`
- representative_grammar_pruned_weight: `1962`
- representative_grammar_unresolved_rows: `0`
- representative_grammar_unresolved_weight: `0`
- representative_compatible_rows: `0`
- representative_compatible_weight: `0`
- cup_product_eligible_rows: `0`
- cup_product_eligible_weight: `0`
- selection_rule_status_rows: `{'character_refined_doublet_mass_obstruction': 3269, 'no_character_refined_triplet_mass_operator_found': 383, 'passes_refined_charge_character_dt_and_proton_filter': 14, 'selective_dt_but_proton_unprotected': 399}`
- selection_rule_status_weight: `{'character_refined_doublet_mass_obstruction': 33072, 'no_character_refined_triplet_mass_operator_found': 510611, 'passes_refined_charge_character_dt_and_proton_filter': 1962, 'selective_dt_but_proton_unprotected': 3393}`
- representative_status_rows: `{'not_evaluated_selection_rule_not_viable': 4051, 'representative_obstructed': 14}`
- representative_status_weight: `{'not_evaluated_selection_rule_not_viable': 547076, 'representative_obstructed': 1962}`

## Regression Controls

- branch18 `5bar_02*5_24`: `representative_obstructed`
- five12 `5bar_12*5_12` targets: `2`
- five23 `5bar_23*5_23`: `representative_obstructed`

## Interpretation

- generation_boundary: `character-shadow viable branches are no longer promotion-ready; representative compatibility is required before lead or cup-product labels`
- current_frontier_result: `the repaired generation grammar yields zero representative-compatible candidates on the materialized radius-9 frontier`

## Gates

- imports_verified_broad_rollup: `True` - generation replay starts from the verified materialized radius-9 frontier
- generated_weight_matches_frontier: `True` - all materialized q=1 candidate records are replayed exactly once
- selection_rule_candidates_match_shadow_frontier: `True` - the replay regenerates the corrected character-shadow survivor set
- representative_gate_prunes_all_shadow_candidates: `True` - no current radius-9 character-shadow survivor is promotion-ready
- no_unresolved_selection_rule_survivor: `True` - every refined survivor is resolved, not merely postponed
- branch18_regression_control: `True` - branch 18 remains pruned by the representative shadow-collision gate
- five12_e2_regression_control: `True` - the 5_12 cup-dual E2 mismatch remains a generation-time prune
- five23_kernel_regression_control: `True` - the 5bar_23 first-page kernel mismatch remains a generation-time prune
