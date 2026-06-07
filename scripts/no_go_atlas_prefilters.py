#!/usr/bin/env python3
"""Cheap executable prefilters for the No-Go Atlas v0.

These predicates intentionally operate on small normalized dictionaries, not on
full CICY/cohomology records.  The atlas builder records the evidence scope and
replay counts for each predicate.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def no_recorded_free_symmetry(record: dict[str, Any]) -> bool:
    """Reject Wilson-line goals when no recorded free action is available."""

    return bool(record.get("requires_wilson_line_descent", True)) and int(
        record.get("free_symmetry_option_count", 0)
    ) == 0


def vectorlike_excess(record: dict[str, Any]) -> bool:
    """Reject character-certified spectra with too many vectorlike 5/5bar pairs."""

    pair = (
        record.get("actual_per_character_pair")
        or record.get("best_actual_pair")
        or record.get("vectorlike_pair")
    )
    if not pair or len(pair) != 2:
        return False
    allowed_pairs = {
        tuple(item)
        for item in record.get("allowed_pairs", [[3, 0], [4, 1]])
    }
    return tuple(pair) not in allowed_pairs and int(pair[1]) > int(
        record.get("max_vectorlike_pairs", 1)
    )


def representative_character_mismatch(record: dict[str, Any]) -> bool:
    """Reject branch shadows whose requested character is not realized."""

    return (
        record.get("leg_type") == "physical_5bar_H1"
        and record.get("requested_multiplicities")
        != record.get("computed_multiplicities")
        and record.get("representative_status") == "representative_obstructed"
    )


def degree_zero_bilinear_not_top_cup(record: dict[str, Any]) -> bool:
    """Reject neutral degree-zero bilinears that miss H3(O_X)."""

    return (
        int(record.get("monomial_degree", -1)) == 0
        and int(record.get("direct_total_cohomological_degree", -1)) == 2
        and record.get("direct_target_group") == "H2(O_X)"
        and int(record.get("direct_target_dimension", -1)) == 0
        and int(record.get("required_singlet_degree_for_top_cubic", -1)) == 1
    )


def degree_one_doublet_triplet_inseparable(record: dict[str, Any]) -> bool:
    """Reject degree-one top-cup mass channels that also support doublets."""

    return (
        int(record.get("singlet_degree", 1)) == 1
        and int(record.get("triplet_pair_support", 0)) > 0
        and int(record.get("doublet_pair_support", 0)) > 0
    )


def standard_m4_four_h1_not_top_cup(record: dict[str, Any]) -> bool:
    """Reject standard cochain m4 routes whose four H1 inputs land in H2."""

    return (
        int(record.get("arity", -1)) == 4
        and record.get("input_degrees") == [1, 1, 1, 1]
        and int(record.get("standard_mn_degree", 0)) == -2
        and int(record.get("output_degree", -1)) == 2
        and record.get("desired_target_group", "H3(O_X)") == "H3(O_X)"
        and int(record.get("target_H2_dimension", -1)) == 0
        and int(record.get("target_H3_dimension", 0)) > 0
        and int(record.get("standard_m4_to_H3_rank", -1)) == 0
    )


def higher_monoid_downstream_obstructed(record: dict[str, Any]) -> bool:
    """Reject higher-degree monoid operators that fail downstream safety gates."""

    return record.get("status") in {
        "higher_monoid_doublet_support_obstruction",
        "higher_monoid_triplet_only_but_proton_unprotected",
        "higher_monoid_triplet_only_proton_safe_but_cup_5_unrealizable",
        "higher_monoid_no_triplet_component_support",
        "no_invariant_monoid_le_bound",
    }


def s42_doublet_contamination_motif(record: dict[str, Any]) -> bool:
    """Reject the model-874 S_42 doublet-only mass motif inside its scope."""

    return (
        record.get("operator") == "5bar_23*5_34*S"
        and "S_42" in set(record.get("singlets", []))
        and record.get("support_class") == "top_cup_doublet_only_mass"
        and int(record.get("doublet_pair_support", 0)) > 0
        and int(record.get("triplet_pair_support", 0)) == 0
    )


def cup_target_missing_one_higgs(record: dict[str, Any]) -> bool:
    """Reject cup-target records that lack one-Higgs/triplet-free structure."""

    return (
        bool(record.get("requires_one_higgs", True))
        and int(record.get("cup_product_eligible_triplet_target_count", 0)) > 0
        and int(record.get("one_higgs_pair_triplet_free_count", 0)) == 0
    )


def s42_boundary_only_no_non_s42_survivor(record: dict[str, Any]) -> bool:
    """Reject local CICY6927 overlaps that only recover the known S_42 basin."""

    return (
        bool(record.get("requires_non_s42_survivor", True))
        and int(record.get("one_higgs_proton_safe_intersection_count", 0)) > 0
        and int(record.get("non_s42_precup_survivor_count", -1)) == 0
        and int(record.get("closest_detail_s42_motif_hit_count", 0)) > 0
    )


def computed_anchor_missing_one_higgs_and_cup(record: dict[str, Any]) -> bool:
    """Reject computed proton-safe anchors with no one-Higgs or cup target."""

    proton_safe = bool(record.get("all_embeddings_proton_safe")) or int(
        record.get("proton_safe_embedding_count", 0)
    ) > 0
    return (
        bool(record.get("requires_one_higgs_or_cup", True))
        and bool(record.get("component_characters_computed", True))
        and proton_safe
        and int(record.get("one_higgs_pair_triplet_free_count", -1)) == 0
        and int(record.get("pre_cup_survivor_count", -1)) == 0
        and int(record.get("cup_product_eligible_triplet_target_count", -1)) == 0
    )


def one_higgs_proton_safety_disjoint(record: dict[str, Any]) -> bool:
    """Reject one-Higgs records whose proton-safe slice is disjoint."""

    return (
        bool(record.get("requires_one_higgs_proton_safe", True))
        and int(record.get("one_higgs_pair_triplet_free_count", 0)) > 0
        and int(record.get("proton_safe_embedding_count", 0)) > 0
        and int(record.get("one_higgs_proton_safe_count", 0)) == 0
    )


def one_higgs_proton_unsafe(record: dict[str, Any]) -> bool:
    """Reject one-Higgs records with no proton-safe one-Higgs embedding."""

    min_danger = record.get("min_dangerous_operator_count_among_one_higgs")
    return (
        bool(record.get("requires_one_higgs_proton_safe", True))
        and int(record.get("one_higgs_pair_triplet_free_count", 0)) > 0
        and int(record.get("one_higgs_proton_safe_count", 0)) == 0
        and min_danger is not None
        and int(min_danger) > 0
    )


def cubic_yukawa_absent(record: dict[str, Any]) -> bool:
    """Reject renormalizable-cubic-Yukawa goals with no allowed cubic Yukawa."""

    return (
        bool(record.get("requires_renormalizable_cubic_yukawa", True))
        and int(record.get("up_type_cubic_allowed_count", -1)) == 0
        and int(record.get("down_lepton_cubic_allowed_count", -1)) == 0
        and int(record.get("proton_decay_allowed_count", -1)) == 0
        and bool(record.get("higher_degree_yukawa_escape_allowed", True))
    )


def higher_degree_yukawa_charge_mismatch(record: dict[str, Any]) -> bool:
    """Reject bounded singlet-dressed Yukawa searches with no neutral rows."""

    return (
        bool(record.get("requires_higher_degree_yukawa", True))
        and int(record.get("max_singlet_monoid_degree", 0))
        <= int(record.get("degree_bound", 3))
        and int(record.get("up_type_charge_neutral_count", -1)) == 0
        and int(record.get("down_lepton_charge_neutral_count", -1)) == 0
        and int(record.get("safe_yukawa_operator_monoid_count", -1)) == 0
    )


def charge_defect_guided_no_improvement(record: dict[str, Any]) -> bool:
    """Reject bounded defect-guided searches that find no downhill q1 branch."""

    return (
        bool(record.get("requires_charge_defect_escape", True))
        and int(record.get("frontier_size", 0)) > 0
        and int(record.get("q1_candidate_count", 0)) > 0
        and int(record.get("promotion_timeout_count", -1)) == 0
        and int(record.get("safe_yukawa_record_count", -1)) == 0
        and int(record.get("charge_defect_improved_record_count", -1)) == 0
    )


def upstream_direct_e1_requires_transferred_m3(record: dict[str, Any]) -> bool:
    """Flag upstream Yukawa routes whose direct E1 product misses H2."""

    return (
        bool(record.get("requires_effective_complement_map", True))
        and record.get("direct_E1_triple_product_status")
        == "blocked_by_koszul_origin_duplication"
        and int(record.get("direct_origin_wedge_survivor_count", -1)) == 0
        and int(record.get("source_koszul_degree_sum", -1)) > int(
            record.get("target_koszul_degree", -1)
        )
        and record.get("transferred_m3_complement_map_status")
        == "required_pending"
    )


def transferred_m3_direct_tree_no_survivor(record: dict[str, Any]) -> bool:
    """Flag transferred-m3 routes with no homotopy-eligible direct tree term."""

    return (
        bool(record.get("requires_transferred_m3", True))
        and int(record.get("route_count", 0)) >= 3
        and int(record.get("homotopy_eligible_direct_product_total", -1)) == 0
        and int(record.get("final_direct_tree_survivor_total", -1)) == 0
        and record.get("standard_m3_direct_tree_inventory_status")
        == "no_direct_tree_survivor"
    )


def preferred_effective_routes_no_homotopy_seed(record: dict[str, Any]) -> bool:
    """Flag preferred effective-complement route sets with no homotopy seed."""

    return (
        bool(record.get("requires_effective_complement_route", True))
        and int(record.get("factorization_count", 0)) > 0
        and int(record.get("homotopy_eligible_factorization_count", -1)) == 0
        and int(record.get("max_homotopy_eligible_direct_products", -1)) == 0
        and record.get("route_ranker_status")
        == "no_homotopy_eligible_routes_in_preferred_factorizations"
    )


def single_anchor_effective_routes_no_homotopy_seed(record: dict[str, Any]) -> bool:
    """Flag single-anchor route queues with no promotable homotopy seed."""

    return (
        bool(record.get("requires_single_anchor_effective_route", True))
        and int(record.get("single_anchor_route_count", 0)) > 0
        and int(record.get("selection_valid_matter_anchor_count", 0)) > 0
        and int(record.get("promotable_homotopy_seed_count", -1)) == 0
        and int(record.get("max_homotopy_eligible_direct_products", -1)) == 0
        and record.get("single_anchor_route_queue_status")
        == "no_promotable_homotopy_seed_in_single_anchor_frontier"
    )


def multistage_first_pair_no_homotopy_seed(record: dict[str, Any]) -> bool:
    """Flag multi-stage direct-tree grammars blocked at first H1-H1 pair."""

    return (
        bool(record.get("requires_multistage_direct_tree_route", True))
        and int(record.get("valid_first_pair_slot_count", 0)) > 0
        and int(record.get("valid_homotopy_eligible_first_pair_slot_count", -1)) == 0
        and int(record.get("valid_direct_target_first_pair_slot_count", 0)) > 0
        and record.get("multi_stage_direct_tree_status")
        == "blocked_at_first_h1_h1_pair"
    )


def local_deformation_first_pair_no_homotopy_seed(record: dict[str, Any]) -> bool:
    """Flag local deformation scouts that find no positive first-pair seed."""

    return (
        bool(record.get("requires_local_deformation_first_pair_seed", True))
        and int(record.get("frontier_size", 0)) > 0
        and int(record.get("q1_candidate_count", 0)) > 0
        and int(record.get("safe_up_down_yukawa_record_count", 0)) > 0
        and int(record.get("positive_first_pair_seed_record_count", -1)) == 0
        and int(record.get("max_valid_homotopy_eligible_first_pair_slot_count", -1))
        == 0
        and record.get("deformation_scout_status")
        == "no_positive_first_pair_homotopy_seed_in_radius4_frontier"
    )


def verified_overlap_first_pair_seed_absent(record: dict[str, Any]) -> bool:
    """Flag verified overlap queues with no positive first-pair seed."""

    return (
        bool(record.get("requires_verified_overlap_first_pair_seed", True))
        and int(record.get("scored_record_count", 0)) > 0
        and int(record.get("safe_up_down_yukawa_record_count", 0)) > 0
        and int(record.get("positive_first_pair_seed_record_count", -1)) == 0
        and int(record.get("max_valid_homotopy_eligible_first_pair_slot_count", -1))
        == 0
        and record.get("first_pair_seed_scout_status")
        == "no_positive_first_pair_seed_in_verified_overlap_queue"
    )


def first_pair_positive_generator_no_seed(record: dict[str, Any]) -> bool:
    """Flag finite first-pair-positive generator expansions with no seed."""

    return (
        bool(record.get("requires_first_pair_positive_generator_seed", True))
        and int(record.get("frontier_size", 0)) > 0
        and int(record.get("q1_candidate_count", 0)) > 0
        and int(record.get("safe_up_down_yukawa_record_count", 0)) > 0
        and int(record.get("positive_first_pair_seed_record_count", -1)) == 0
        and int(record.get("max_valid_homotopy_eligible_first_pair_slot_count", -1))
        == 0
        and record.get("generator_expansion_status")
        == "no_positive_first_pair_seed_in_radius4_expansion"
    )


def higher_map_order_no_realization(record: dict[str, Any]) -> bool:
    """Flag representative branches not realized by finite higher-map order scans."""

    return (
        bool(record.get("requires_representative_resolution", True))
        and bool(record.get("complete_permutation_scan"))
        and int(record.get("permutation_count_tested", 0)) > 0
        and not bool(record.get("branch_representative_certified"))
        and int(record.get("required_rank_total", -1)) >= 0
        and int(record.get("pycicy_raw_rank", -1))
        == int(record.get("required_rank_total", -2))
        and int(record.get("averaged_rank", -1))
        > int(record.get("required_rank_total", -1))
    )


def chain_contraction_fallback_closed_current_engine(record: dict[str, Any]) -> bool:
    """Flag exact-engine fallbacks closed by zero standard m3 and missing chain API."""

    return (
        bool(record.get("requires_chain_contraction_fallback", True))
        and record.get("fallback_status")
        == "cicy6784_frontier48_chain_contraction_fallback_closed_current_engine"
        and int(record.get("standard_m3_tree_count", 0)) > 0
        and int(record.get("standard_m3_matrix_rank", -1)) == 0
        and int(record.get("direct_binary_target_piece_total", -1)) == 0
        and int(record.get("homotopy_eligible_direct_product_total", -1)) == 0
        and not bool(record.get("has_exposed_product_plus_chain_contraction_api"))
    )


def split_action_lift_missing_current_data(record: dict[str, Any]) -> bool:
    """Flag split bridges whose action-transfer data is absent locally."""

    return (
        bool(record.get("requires_split_action_lift", True))
        and int(record.get("parent_free_action_count", 0)) > 0
        and int(record.get("direct_one_step_split_hit_count", 0)) == 1
        and record.get("selected_split_symmetry_status") == "unknown"
        and int(record.get("selected_split_free_symmetry_option_count", -1)) == 0
        and int(record.get("same_hodge_favourable_known_free_count", -1)) == 0
        and int(record.get("inherited_slope_feasible_count", -1)) == 0
        and record.get("bridge_status", "").endswith("blocked_current_data")
    )


def direct_split_witness_missing_current_data(record: dict[str, Any]) -> bool:
    """Flag bridge rows with no current direct favourable split witness."""

    return (
        bool(record.get("requires_concrete_split_witness", True))
        and int(record.get("parent_free_action_count", 0)) > 0
        and int(record.get("same_hodge_pool_count", 0)) > 0
        and int(record.get("same_hodge_favourable_unknown_count", 0)) > 0
        and int(record.get("same_hodge_favourable_known_free_count", -1)) == 0
        and int(record.get("direct_one_step_split_hit_count", -1)) == 0
        and record.get("bridge_status", "").endswith("blocked_current_data")
    )


def geometry_specific_engine_missing_current_data(record: dict[str, Any]) -> bool:
    """Flag clean benchmark pools whose current promotion engine is absent."""

    return (
        bool(record.get("requires_geometry_specific_promotion_engine", True))
        and int(record.get("model_count", 0)) > 0
        and int(record.get("algebraic_benchmark_failure_count", -1)) == 0
        and int(record.get("raw_free_action_count", 0)) > 0
        and bool(
            record.get(
                "generic_ambient_line_bundle_lift_readiness_engine_available",
                False,
            )
        )
        and not bool(record.get("geometry_specific_wilson_component_engine_available"))
        and not bool(record.get("geometry_specific_representative_mass_engine_available"))
        and not bool(record.get("generic_representative_promotion_engine_available"))
        and record.get("engine_gap_status", "").endswith("current_data")
    )


def raw_free_action_data_missing_current_data(record: dict[str, Any]) -> bool:
    """Flag GUTall pools whose local raw free-action data is absent."""

    return (
        bool(record.get("requires_raw_free_action_data", True))
        and int(record.get("model_count", 0)) > 0
        and int(record.get("algebraic_benchmark_failure_count", -1)) == 0
        and bool(record.get("gutall_symmetry_orders"))
        and int(record.get("raw_symmetry_option_count", 0)) > 0
        and int(record.get("raw_free_action_count", -1)) == 0
        and record.get("raw_action_gap_status", "").endswith("current_data")
    )


PREFILTERS: dict[str, Callable[[dict[str, Any]], bool]] = {
    "no_recorded_free_symmetry": no_recorded_free_symmetry,
    "vectorlike_excess": vectorlike_excess,
    "representative_character_mismatch": representative_character_mismatch,
    "degree_zero_bilinear_not_top_cup": degree_zero_bilinear_not_top_cup,
    "degree_one_doublet_triplet_inseparable": degree_one_doublet_triplet_inseparable,
    "standard_m4_four_h1_not_top_cup": standard_m4_four_h1_not_top_cup,
    "higher_monoid_downstream_obstructed": higher_monoid_downstream_obstructed,
    "s42_doublet_contamination_motif": s42_doublet_contamination_motif,
    "cup_target_missing_one_higgs": cup_target_missing_one_higgs,
    "s42_boundary_only_no_non_s42_survivor": s42_boundary_only_no_non_s42_survivor,
    "computed_anchor_missing_one_higgs_and_cup": computed_anchor_missing_one_higgs_and_cup,
    "one_higgs_proton_safety_disjoint": one_higgs_proton_safety_disjoint,
    "one_higgs_proton_unsafe": one_higgs_proton_unsafe,
    "cubic_yukawa_absent": cubic_yukawa_absent,
    "higher_degree_yukawa_charge_mismatch": higher_degree_yukawa_charge_mismatch,
    "charge_defect_guided_no_improvement": charge_defect_guided_no_improvement,
    "upstream_direct_e1_requires_transferred_m3": upstream_direct_e1_requires_transferred_m3,
    "transferred_m3_direct_tree_no_survivor": transferred_m3_direct_tree_no_survivor,
    "preferred_effective_routes_no_homotopy_seed": preferred_effective_routes_no_homotopy_seed,
    "single_anchor_effective_routes_no_homotopy_seed": single_anchor_effective_routes_no_homotopy_seed,
    "multistage_first_pair_no_homotopy_seed": multistage_first_pair_no_homotopy_seed,
    "local_deformation_first_pair_no_homotopy_seed": local_deformation_first_pair_no_homotopy_seed,
    "verified_overlap_first_pair_seed_absent": verified_overlap_first_pair_seed_absent,
    "first_pair_positive_generator_no_seed": first_pair_positive_generator_no_seed,
    "higher_map_order_no_realization": higher_map_order_no_realization,
    "chain_contraction_fallback_closed_current_engine": chain_contraction_fallback_closed_current_engine,
    "split_action_lift_missing_current_data": split_action_lift_missing_current_data,
    "direct_split_witness_missing_current_data": direct_split_witness_missing_current_data,
    "geometry_specific_engine_missing_current_data": geometry_specific_engine_missing_current_data,
    "raw_free_action_data_missing_current_data": raw_free_action_data_missing_current_data,
}


def evaluate_prefilter(prefilter_id: str, record: dict[str, Any]) -> bool:
    return PREFILTERS[prefilter_id](record)


def describe_prefilters() -> dict[str, dict[str, Any]]:
    return {
        "no_recorded_free_symmetry": {
            "callable": "no_go_atlas_prefilters.no_recorded_free_symmetry",
            "inputs_required": [
                "requires_wilson_line_descent",
                "free_symmetry_option_count",
            ],
            "scope_note": "geometry-selection prefilter for Wilson-line descent goals",
        },
        "vectorlike_excess": {
            "callable": "no_go_atlas_prefilters.vectorlike_excess",
            "inputs_required": [
                "actual_per_character_pair or best_actual_pair",
                "allowed_pairs",
                "max_vectorlike_pairs",
            ],
            "scope_note": "spectrum/character prefilter after Wilson-line character decomposition",
        },
        "representative_character_mismatch": {
            "callable": "no_go_atlas_prefilters.representative_character_mismatch",
            "inputs_required": [
                "leg_type",
                "requested_multiplicities",
                "computed_multiplicities",
                "representative_status",
            ],
            "scope_note": "representative-realizability prefilter for branch-completed character shadows",
        },
        "degree_zero_bilinear_not_top_cup": {
            "callable": "no_go_atlas_prefilters.degree_zero_bilinear_not_top_cup",
            "inputs_required": [
                "monomial_degree",
                "direct_total_cohomological_degree",
                "direct_target_group",
                "direct_target_dimension",
                "required_singlet_degree_for_top_cubic",
            ],
            "scope_note": "CY3 top-degree prefilter before mass-rank claims",
        },
        "degree_one_doublet_triplet_inseparable": {
            "callable": "no_go_atlas_prefilters.degree_one_doublet_triplet_inseparable",
            "inputs_required": [
                "singlet_degree",
                "triplet_pair_support",
                "doublet_pair_support",
            ],
            "scope_note": "doublet-triplet selection prefilter for degree-one top-cup channels",
        },
        "standard_m4_four_h1_not_top_cup": {
            "callable": "no_go_atlas_prefilters.standard_m4_four_h1_not_top_cup",
            "inputs_required": [
                "arity",
                "input_degrees",
                "standard_mn_degree",
                "output_degree",
                "target_H2_dimension",
                "target_H3_dimension",
                "standard_m4_to_H3_rank",
            ],
            "scope_note": "standard cochain A-infinity m4 degree-law prefilter before higher-order mass promotion",
        },
        "higher_monoid_downstream_obstructed": {
            "callable": "no_go_atlas_prefilters.higher_monoid_downstream_obstructed",
            "inputs_required": ["status"],
            "scope_note": "higher-degree monoid status prefilter before candidate promotion",
        },
        "s42_doublet_contamination_motif": {
            "callable": "no_go_atlas_prefilters.s42_doublet_contamination_motif",
            "inputs_required": [
                "operator",
                "singlets",
                "support_class",
                "triplet_pair_support",
                "doublet_pair_support",
            ],
            "scope_note": "CICY6927/model-874 local motif prefilter for the verified S_42 doublet-contamination basin",
        },
        "cup_target_missing_one_higgs": {
            "callable": "no_go_atlas_prefilters.cup_target_missing_one_higgs",
            "inputs_required": [
                "requires_one_higgs",
                "cup_product_eligible_triplet_target_count",
                "one_higgs_pair_triplet_free_count",
            ],
            "scope_note": "one-Higgs MSSM-goal prefilter after triplet-cup promotion",
        },
        "s42_boundary_only_no_non_s42_survivor": {
            "callable": "no_go_atlas_prefilters.s42_boundary_only_no_non_s42_survivor",
            "inputs_required": [
                "requires_non_s42_survivor",
                "one_higgs_proton_safe_intersection_count",
                "non_s42_precup_survivor_count",
                "closest_detail_s42_motif_hit_count",
            ],
            "scope_note": "CICY6927 option-4 local prefilter when an overlap exists only in the known S_42 doublet-contamination basin",
        },
        "computed_anchor_missing_one_higgs_and_cup": {
            "callable": "no_go_atlas_prefilters.computed_anchor_missing_one_higgs_and_cup",
            "inputs_required": [
                "requires_one_higgs_or_cup",
                "component_characters_computed",
                "all_embeddings_proton_safe or proton_safe_embedding_count",
                "one_higgs_pair_triplet_free_count",
                "pre_cup_survivor_count",
                "cup_product_eligible_triplet_target_count",
            ],
            "scope_note": "computed-anchor prefilter when a q1 Wilson slice is proton-safe but cannot reach either one-Higgs or triplet-cup promotion gates",
        },
        "one_higgs_proton_safety_disjoint": {
            "callable": "no_go_atlas_prefilters.one_higgs_proton_safety_disjoint",
            "inputs_required": [
                "requires_one_higgs_proton_safe",
                "one_higgs_pair_triplet_free_count",
                "proton_safe_embedding_count",
                "one_higgs_proton_safe_count",
            ],
            "scope_note": "one-Higgs/proton-safety intersection prefilter for q1 Wilson embedding scans",
        },
        "one_higgs_proton_unsafe": {
            "callable": "no_go_atlas_prefilters.one_higgs_proton_unsafe",
            "inputs_required": [
                "requires_one_higgs_proton_safe",
                "one_higgs_pair_triplet_free_count",
                "one_higgs_proton_safe_count",
                "min_dangerous_operator_count_among_one_higgs",
            ],
            "scope_note": "one-Higgs proton-safety prefilter when every one-Higgs embedding has dangerous operators",
        },
        "cubic_yukawa_absent": {
            "callable": "no_go_atlas_prefilters.cubic_yukawa_absent",
            "inputs_required": [
                "requires_renormalizable_cubic_yukawa",
                "up_type_cubic_allowed_count",
                "down_lepton_cubic_allowed_count",
                "proton_decay_allowed_count",
                "higher_degree_yukawa_escape_allowed",
            ],
            "scope_note": "operator-frontier prefilter for goals requiring renormalizable cubic Yukawa channels; higher-degree singlet-dressed Yukawas remain an escape hatch",
        },
        "higher_degree_yukawa_charge_mismatch": {
            "callable": "no_go_atlas_prefilters.higher_degree_yukawa_charge_mismatch",
            "inputs_required": [
                "requires_higher_degree_yukawa",
                "max_singlet_monoid_degree",
                "degree_bound",
                "up_type_charge_neutral_count",
                "down_lepton_charge_neutral_count",
                "safe_yukawa_operator_monoid_count",
            ],
            "scope_note": "bounded singlet-dressed Yukawa prefilter after finite monoid enumeration; higher degree or altered charge structure remain escape hatches",
        },
        "charge_defect_guided_no_improvement": {
            "callable": "no_go_atlas_prefilters.charge_defect_guided_no_improvement",
            "inputs_required": [
                "requires_charge_defect_escape",
                "frontier_size",
                "q1_candidate_count",
                "promotion_timeout_count",
                "safe_yukawa_record_count",
                "charge_defect_improved_record_count",
            ],
            "scope_note": "bounded local generator prefilter after charge-defect-guided replay; broader radius, different move grammar, higher degree, or different geometry remain escape hatches",
        },
        "upstream_direct_e1_requires_transferred_m3": {
            "callable": "no_go_atlas_prefilters.upstream_direct_e1_requires_transferred_m3",
            "inputs_required": [
                "requires_effective_complement_map",
                "direct_E1_triple_product_status",
                "direct_origin_wedge_survivor_count",
                "source_koszul_degree_sum",
                "target_koszul_degree",
                "transferred_m3_complement_map_status",
            ],
            "scope_note": "exact-engine boundary prefilter for effective-complement Yukawa routes whose plain E1 product is killed by Koszul-origin collision and therefore requires transferred m3/homotopy machinery",
        },
        "transferred_m3_direct_tree_no_survivor": {
            "callable": "no_go_atlas_prefilters.transferred_m3_direct_tree_no_survivor",
            "inputs_required": [
                "requires_transferred_m3",
                "route_count",
                "homotopy_eligible_direct_product_total",
                "final_direct_tree_survivor_total",
                "standard_m3_direct_tree_inventory_status",
            ],
            "scope_note": "exact-engine boundary prefilter for transferred-m3 attempts whose standard direct-tree terms have no homotopy-eligible binary subproduct; full chain contraction or a different factorization remains an escape hatch",
        },
        "preferred_effective_routes_no_homotopy_seed": {
            "callable": "no_go_atlas_prefilters.preferred_effective_routes_no_homotopy_seed",
            "inputs_required": [
                "requires_effective_complement_route",
                "factorization_count",
                "homotopy_eligible_factorization_count",
                "max_homotopy_eligible_direct_products",
                "route_ranker_status",
            ],
            "scope_note": "generator-ranking prefilter for preferred effective-complement route sets whose binary subproducts never expose a homotopy-eligible seed; search should pivot to routes with positive homotopy_eligible_direct_product_total or implement full chain contraction",
        },
        "single_anchor_effective_routes_no_homotopy_seed": {
            "callable": "no_go_atlas_prefilters.single_anchor_effective_routes_no_homotopy_seed",
            "inputs_required": [
                "requires_single_anchor_effective_route",
                "single_anchor_route_count",
                "selection_valid_matter_anchor_count",
                "promotable_homotopy_seed_count",
                "max_homotopy_eligible_direct_products",
                "single_anchor_route_queue_status",
            ],
            "scope_note": "generator-ranking prefilter for all single-anchor effective-complement routes when neither valid nor shadow anchors expose a homotopy-eligible binary seed; multi-stage route grammars, deformation search, other geometries, or full chain contraction remain escape hatches",
        },
        "multistage_first_pair_no_homotopy_seed": {
            "callable": "no_go_atlas_prefilters.multistage_first_pair_no_homotopy_seed",
            "inputs_required": [
                "requires_multistage_direct_tree_route",
                "valid_first_pair_slot_count",
                "valid_homotopy_eligible_first_pair_slot_count",
                "valid_direct_target_first_pair_slot_count",
                "multi_stage_direct_tree_status",
            ],
            "scope_note": "direct-tree grammar prefilter for multi-stage H1-leaf complement routes whose first internal H1-H1 pair never has a homotopy-eligible direct product; full chain contraction and non-direct-tree conventions remain outside scope",
        },
        "local_deformation_first_pair_no_homotopy_seed": {
            "callable": "no_go_atlas_prefilters.local_deformation_first_pair_no_homotopy_seed",
            "inputs_required": [
                "requires_local_deformation_first_pair_seed",
                "frontier_size",
                "q1_candidate_count",
                "safe_up_down_yukawa_record_count",
                "positive_first_pair_seed_record_count",
                "max_valid_homotopy_eligible_first_pair_slot_count",
                "deformation_scout_status",
            ],
            "scope_note": "local-deformation generator prefilter when a finite q1 scout contains safe up/down Yukawa branches but no positive H1-H1 first-pair homotopy seed; broader radius, different move grammar, different geometry, or full chain contraction remain escape hatches",
        },
        "verified_overlap_first_pair_seed_absent": {
            "callable": "no_go_atlas_prefilters.verified_overlap_first_pair_seed_absent",
            "inputs_required": [
                "requires_verified_overlap_first_pair_seed",
                "scored_record_count",
                "safe_up_down_yukawa_record_count",
                "positive_first_pair_seed_record_count",
                "max_valid_homotopy_eligible_first_pair_slot_count",
                "first_pair_seed_scout_status",
            ],
            "scope_note": "verified-overlap queue prefilter when reconstruction-authoritative rows and their local extension contain no positive H1-H1 first-pair homotopy seed; expanding the reconstruction-authoritative pool, changing the generator, or full chain contraction remain escape hatches",
        },
        "first_pair_positive_generator_no_seed": {
            "callable": "no_go_atlas_prefilters.first_pair_positive_generator_no_seed",
            "inputs_required": [
                "requires_first_pair_positive_generator_seed",
                "frontier_size",
                "q1_candidate_count",
                "safe_up_down_yukawa_record_count",
                "positive_first_pair_seed_record_count",
                "max_valid_homotopy_eligible_first_pair_slot_count",
                "generator_expansion_status",
            ],
            "scope_note": "first-pair-positive generator prefilter when a finite multi-seed expansion reaches q1 and safe up/down Yukawa support but still has no homotopy-eligible H1-H1 first-pair seed; broader geometry, different move grammar, or full chain contraction remain escape hatches",
        },
        "higher_map_order_no_realization": {
            "callable": "no_go_atlas_prefilters.higher_map_order_no_realization",
            "inputs_required": [
                "requires_representative_resolution",
                "complete_permutation_scan",
                "permutation_count_tested",
                "branch_representative_certified",
                "required_rank_total",
                "pycicy_raw_rank",
                "averaged_rank",
            ],
            "scope_note": "representative-resolution prefilter when a finite higher-map equation-order scan never realizes the requested equivariant rank split under the current verifier; alternative higher-map conventions remain outside scope",
        },
        "chain_contraction_fallback_closed_current_engine": {
            "callable": "no_go_atlas_prefilters.chain_contraction_fallback_closed_current_engine",
            "inputs_required": [
                "requires_chain_contraction_fallback",
                "fallback_status",
                "standard_m3_tree_count",
                "standard_m3_matrix_rank",
                "direct_binary_target_piece_total",
                "homotopy_eligible_direct_product_total",
                "has_exposed_product_plus_chain_contraction_api",
            ],
            "scope_note": "exact-engine fallback prefilter when the standard transferred-m3 route is zero before homotopy and the current engine exposes no product-plus-chain-contraction API; adding a real chain-contraction implementation remains an escape hatch",
        },
        "split_action_lift_missing_current_data": {
            "callable": "no_go_atlas_prefilters.split_action_lift_missing_current_data",
            "inputs_required": [
                "requires_split_action_lift",
                "parent_free_action_count",
                "direct_one_step_split_hit_count",
                "selected_split_symmetry_status",
                "selected_split_free_symmetry_option_count",
                "same_hodge_favourable_known_free_count",
                "inherited_slope_feasible_count",
                "bridge_status",
            ],
            "scope_note": "presentation-bridge prefilter when a unique favourable split witness exists but no local split-action transfer data or inherited slope-feasible lead exists; adding an explicit action-transfer engine remains an escape hatch",
        },
        "direct_split_witness_missing_current_data": {
            "callable": "no_go_atlas_prefilters.direct_split_witness_missing_current_data",
            "inputs_required": [
                "requires_concrete_split_witness",
                "parent_free_action_count",
                "same_hodge_pool_count",
                "same_hodge_favourable_unknown_count",
                "same_hodge_favourable_known_free_count",
                "direct_one_step_split_hit_count",
                "bridge_status",
            ],
            "scope_note": "presentation-bridge prefilter when same-Hodge favourable rows exist but the current ordinary one-step split-witness audit finds no concrete favourable presentation witness; broader isomorphism or multi-step split searches remain escape hatches",
        },
        "geometry_specific_engine_missing_current_data": {
            "callable": "no_go_atlas_prefilters.geometry_specific_engine_missing_current_data",
            "inputs_required": [
                "requires_geometry_specific_promotion_engine",
                "model_count",
                "algebraic_benchmark_failure_count",
                "raw_free_action_count",
                "generic_ambient_line_bundle_lift_readiness_engine_available",
                "geometry_specific_wilson_component_engine_available",
                "geometry_specific_representative_mass_engine_available",
                "generic_representative_promotion_engine_available",
                "engine_gap_status",
            ],
            "scope_note": "benchmark-pool prefilter when algebraic/index/anomaly and raw-action layers are available but no current Wilson-component or equivariant representative promotion engine exists for that geometry; implementing the engine remains the intended escape hatch",
        },
        "raw_free_action_data_missing_current_data": {
            "callable": "no_go_atlas_prefilters.raw_free_action_data_missing_current_data",
            "inputs_required": [
                "requires_raw_free_action_data",
                "model_count",
                "algebraic_benchmark_failure_count",
                "gutall_symmetry_orders",
                "raw_symmetry_option_count",
                "raw_free_action_count",
                "raw_action_gap_status",
            ],
            "scope_note": "benchmark-pool prefilter when GUTall records quotient-compatible models but the local cicylist.m action block has no free-action option to feed Wilson/component descent; recovering explicit raw free-action data remains the escape hatch",
        },
    }
