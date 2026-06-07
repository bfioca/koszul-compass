#!/usr/bin/env python3
"""Verify the No-Go Atlas v0 artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from no_go_atlas_prefilters import describe_prefilters, evaluate_prefilter  # noqa: E402


REQUIRED_SYNDROMES = {
    "geometry_no_recorded_free_symmetry",
    "z2_regular_vectorlike_excess_5259_7914",
    "z2xz2_regular_vectorlike_excess_7484",
    "degree_zero_bilinear_not_cy3_top_cup",
    "physical_5bar_representative_character_mismatch",
    "degree_one_representative_intersection_not_triplet_only",
    "higher_degree_monoid_downstream_obstructions",
    "branch50_standard_m4_four_h1_not_cy3_top_cup",
    "cicy6927_model874_s42_doublet_contamination_basin",
    "cicy6927_non_s42_cup_boundary_missing_one_higgs_radius2",
    "cicy6927_model252_s42_boundary_only_radius2",
    "cicy6927_model254_s42_boundary_only_radius2",
    "cicy6927_model369_s42_boundary_only_radius2",
    "cicy6927_model52_s42_boundary_only_radius2",
    "cicy6836_one_higgs_proton_safety_disjoint_radius2",
    "cicy6836_model87_one_higgs_proton_safety_disjoint_radius2",
    "cicy6836_model186_frontier691_followup_disjoint_radius2",
    "cicy6836_model136_existing_boundary_floor_radius2",
    "cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2",
    "cicy6715_model766_branch99_higher_map_order_no_realization",
    "cicy6788_wall_breaker_one_higgs_proton_unsafe",
    "cicy6784_strict_precup_cubic_yukawa_absent",
    "cicy6784_higher_degree_le3_yukawa_charge_mismatch",
    "cicy6784_radius1_charge_defect_no_improvement",
    "cicy6784_upstream_direct_e1_requires_transferred_m3",
    "cicy6784_transferred_m3_no_direct_tree_survivor",
    "cicy6784_preferred_effective_routes_no_homotopy_seed",
    "cicy6784_single_anchor_effective_routes_no_homotopy_seed",
    "cicy6784_multistage_first_pair_no_homotopy_seed",
    "cicy6784_frontier48_chain_contraction_fallback_closed_current_engine",
    "cicy4185_7910_split_action_lift_missing_current_data",
    "cicy6187_7899_split_action_lift_missing_current_data",
    "cicy6201_7900_split_action_lift_missing_current_data",
    "cicy6281_7904_split_action_lift_missing_current_data",
    "cicy4078_7908_split_action_lift_missing_current_data",
    "cicy5141_7912_split_action_lift_missing_current_data",
    "cicy5248_7913_split_action_lift_missing_current_data",
    "cicy5406_7918_split_action_lift_missing_current_data",
    "cicy5449_no_direct_split_witness_current_data",
    "cicy7810_no_direct_split_witness_current_data",
    "cicy5302_gutall_benchmark_pool_engine_gap_current_data",
    "cicy5256_gutall_benchmark_pool_engine_gap_current_data",
    "cicy5273_gutall_benchmark_pool_raw_action_gap_current_data",
    "cicy6738_gutall_benchmark_pool_raw_action_gap_current_data",
    "cicy5425_gutall_benchmark_pool_raw_action_gap_current_data",
    "cicy6784_radius4_local_deformation_no_first_pair_seed",
    "verified_overlap_first_pair_seed_absent",
    "first_pair_positive_generator_no_seed_radius4",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def syndrome_by_id(report: dict[str, Any], syndrome_id: str) -> dict[str, Any]:
    for item in report["syndromes"]:
        if item["syndrome_id"] == syndrome_id:
            return item
    raise KeyError(syndrome_id)


def verify(report_json: Path, report_md: Path) -> dict[str, Any]:
    report = load_json(report_json)
    md_text = report_md.read_text(encoding="utf-8")
    syndromes = {item["syndrome_id"]: item for item in report["syndromes"]}
    prefilters = describe_prefilters()
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"]
            and all(item["pass"] for item in report["gates"].values()),
            str(report_json),
            "builder-side atlas gates all pass",
        ),
        "required_syndromes_present": gate(
            set(syndromes) == REQUIRED_SYNDROMES
            and report["summary"]["syndrome_count"] == len(REQUIRED_SYNDROMES),
            str(report_json),
            "atlas contains the required v0 syndrome set",
        ),
        "scope_classes_are_honest": gate(
            report["summary"]["scope_class_counts"]
            == {
                "candidate-specific": 11,
                "geometry-local": 1,
                "global-looking": 1,
                "grammar-local": 24,
                "presentation-local": 11,
            }
            and all(
                item["scope_class"]
                in {
                    "candidate-specific",
                    "grammar-local",
                    "presentation-local",
                    "geometry-local",
                    "global-looking",
                }
                for item in report["syndromes"]
            )
            and "must not be cited as a manifold-level impossibility theorem"
            in report["atlas_policy"]["scope_warning"],
            str(report_json),
            "scope classes and warning prevent local rules from being overstated",
        ),
        "source_verifications_imported": gate(
            all(
                item["all_gates_pass"]
                for item in report["source_verifications"].values()
            )
            and len(report["source_verifications"]) >= 35,
            str(report_json),
            "all imported source verifications are present and passing",
        ),
        "prefilters_are_executable_and_registered": gate(
            set(report["prefilter_registry"]) == set(prefilters)
            and set(report["summary"]["prefilter_ids"]).issubset(set(prefilters))
            and evaluate_prefilter(
                "no_recorded_free_symmetry",
                {
                    "requires_wilson_line_descent": True,
                    "free_symmetry_option_count": 0,
                },
            )
            and evaluate_prefilter(
                "vectorlike_excess",
                {
                    "actual_per_character_pair": [6, 3],
                    "allowed_pairs": [[3, 0], [4, 1]],
                    "max_vectorlike_pairs": 1,
                },
            )
            and evaluate_prefilter(
                "representative_character_mismatch",
                {
                    "leg_type": "physical_5bar_H1",
                    "requested_multiplicities": {"+": 2, "-": 0},
                    "computed_multiplicities": {"+": 1, "-": 1},
                    "representative_status": "representative_obstructed",
                },
            )
            and evaluate_prefilter(
                "degree_zero_bilinear_not_top_cup",
                {
                    "monomial_degree": 0,
                    "direct_total_cohomological_degree": 2,
                    "direct_target_group": "H2(O_X)",
                    "direct_target_dimension": 0,
                    "required_singlet_degree_for_top_cubic": 1,
                },
            )
            and evaluate_prefilter(
                "degree_one_doublet_triplet_inseparable",
                {
                    "singlet_degree": 1,
                    "triplet_pair_support": 1,
                    "doublet_pair_support": 1,
                },
            )
            and evaluate_prefilter(
                "standard_m4_four_h1_not_top_cup",
                {
                    "arity": 4,
                    "input_degrees": [1, 1, 1, 1],
                    "standard_mn_degree": -2,
                    "output_degree": 2,
                    "target_H2_dimension": 0,
                    "target_H3_dimension": 1,
                    "standard_m4_to_H3_rank": 0,
                },
            )
            and evaluate_prefilter(
                "higher_monoid_downstream_obstructed",
                {
                    "status": "higher_monoid_triplet_only_proton_safe_but_cup_5_unrealizable"
                },
            )
            and evaluate_prefilter(
                "s42_doublet_contamination_motif",
                {
                    "operator": "5bar_23*5_34*S",
                    "singlets": ["S_42"],
                    "support_class": "top_cup_doublet_only_mass",
                    "triplet_pair_support": 0,
                    "doublet_pair_support": 1,
                },
            )
            and evaluate_prefilter(
                "cup_target_missing_one_higgs",
                {
                    "requires_one_higgs": True,
                    "cup_product_eligible_triplet_target_count": 256,
                    "one_higgs_pair_triplet_free_count": 0,
                },
            )
            and evaluate_prefilter(
                "computed_anchor_missing_one_higgs_and_cup",
                {
                    "requires_one_higgs_or_cup": True,
                    "component_characters_computed": True,
                    "all_embeddings_proton_safe": True,
                    "one_higgs_pair_triplet_free_count": 0,
                    "pre_cup_survivor_count": 0,
                    "cup_product_eligible_triplet_target_count": 0,
                },
            )
            and evaluate_prefilter(
                "one_higgs_proton_safety_disjoint",
                {
                    "requires_one_higgs_proton_safe": True,
                    "one_higgs_pair_triplet_free_count": 128,
                    "proton_safe_embedding_count": 64,
                    "one_higgs_proton_safe_count": 0,
                },
            )
            and evaluate_prefilter(
                "one_higgs_proton_unsafe",
                {
                    "requires_one_higgs_proton_safe": True,
                    "one_higgs_pair_triplet_free_count": 128,
                    "one_higgs_proton_safe_count": 0,
                    "min_dangerous_operator_count_among_one_higgs": 2,
                },
            )
            and evaluate_prefilter(
                "cubic_yukawa_absent",
                {
                    "requires_renormalizable_cubic_yukawa": True,
                    "up_type_cubic_allowed_count": 0,
                    "down_lepton_cubic_allowed_count": 0,
                    "proton_decay_allowed_count": 0,
                    "higher_degree_yukawa_escape_allowed": True,
                },
            )
            and evaluate_prefilter(
                "higher_degree_yukawa_charge_mismatch",
                {
                    "requires_higher_degree_yukawa": True,
                    "max_singlet_monoid_degree": 3,
                    "degree_bound": 3,
                    "up_type_charge_neutral_count": 0,
                    "down_lepton_charge_neutral_count": 0,
                    "safe_yukawa_operator_monoid_count": 0,
                },
            )
            and evaluate_prefilter(
                "charge_defect_guided_no_improvement",
                {
                    "requires_charge_defect_escape": True,
                    "frontier_size": 130,
                    "q1_candidate_count": 1,
                    "promotion_timeout_count": 0,
                    "safe_yukawa_record_count": 0,
                    "charge_defect_improved_record_count": 0,
                },
            )
            and evaluate_prefilter(
                "upstream_direct_e1_requires_transferred_m3",
                {
                    "requires_effective_complement_map": True,
                    "direct_E1_triple_product_status": "blocked_by_koszul_origin_duplication",
                    "direct_origin_wedge_survivor_count": 0,
                    "source_koszul_degree_sum": 4,
                    "target_koszul_degree": 3,
                    "transferred_m3_complement_map_status": "required_pending",
                },
            )
            and evaluate_prefilter(
                "transferred_m3_direct_tree_no_survivor",
                {
                    "requires_transferred_m3": True,
                    "route_count": 3,
                    "homotopy_eligible_direct_product_total": 0,
                    "final_direct_tree_survivor_total": 0,
                    "standard_m3_direct_tree_inventory_status": "no_direct_tree_survivor",
                },
            )
            and evaluate_prefilter(
                "preferred_effective_routes_no_homotopy_seed",
                {
                    "requires_effective_complement_route": True,
                    "factorization_count": 6,
                    "homotopy_eligible_factorization_count": 0,
                    "max_homotopy_eligible_direct_products": 0,
                    "route_ranker_status": "no_homotopy_eligible_routes_in_preferred_factorizations",
                },
            )
            and evaluate_prefilter(
                "single_anchor_effective_routes_no_homotopy_seed",
                {
                    "requires_single_anchor_effective_route": True,
                    "single_anchor_route_count": 11,
                    "selection_valid_matter_anchor_count": 6,
                    "promotable_homotopy_seed_count": 0,
                    "max_homotopy_eligible_direct_products": 0,
                    "single_anchor_route_queue_status": "no_promotable_homotopy_seed_in_single_anchor_frontier",
                },
            )
            and evaluate_prefilter(
                "multistage_first_pair_no_homotopy_seed",
                {
                    "requires_multistage_direct_tree_route": True,
                    "valid_first_pair_slot_count": 54,
                    "valid_homotopy_eligible_first_pair_slot_count": 0,
                    "valid_direct_target_first_pair_slot_count": 10,
                    "multi_stage_direct_tree_status": "blocked_at_first_h1_h1_pair",
                },
            )
            and evaluate_prefilter(
                "local_deformation_first_pair_no_homotopy_seed",
                {
                    "requires_local_deformation_first_pair_seed": True,
                    "frontier_size": 2009,
                    "q1_candidate_count": 2,
                    "safe_up_down_yukawa_record_count": 1,
                    "positive_first_pair_seed_record_count": 0,
                    "max_valid_homotopy_eligible_first_pair_slot_count": 0,
                    "deformation_scout_status": "no_positive_first_pair_homotopy_seed_in_radius4_frontier",
                },
            )
            and evaluate_prefilter(
                "verified_overlap_first_pair_seed_absent",
                {
                    "requires_verified_overlap_first_pair_seed": True,
                    "scored_record_count": 5,
                    "safe_up_down_yukawa_record_count": 1,
                    "positive_first_pair_seed_record_count": 0,
                    "max_valid_homotopy_eligible_first_pair_slot_count": 0,
                    "first_pair_seed_scout_status": "no_positive_first_pair_seed_in_verified_overlap_queue",
                },
            )
            and evaluate_prefilter(
                "first_pair_positive_generator_no_seed",
                {
                    "requires_first_pair_positive_generator_seed": True,
                    "frontier_size": 9891,
                    "q1_candidate_count": 4,
                    "safe_up_down_yukawa_record_count": 1,
                    "positive_first_pair_seed_record_count": 0,
                    "max_valid_homotopy_eligible_first_pair_slot_count": 0,
                    "generator_expansion_status": "no_positive_first_pair_seed_in_radius4_expansion",
                },
            )
            and evaluate_prefilter(
                "higher_map_order_no_realization",
                {
                    "requires_representative_resolution": True,
                    "complete_permutation_scan": True,
                    "permutation_count_tested": 5040,
                    "branch_representative_certified": False,
                    "required_rank_total": 7,
                    "pycicy_raw_rank": 7,
                    "averaged_rank": 9,
                },
            )
            and evaluate_prefilter(
                "chain_contraction_fallback_closed_current_engine",
                {
                    "requires_chain_contraction_fallback": True,
                    "fallback_status": "cicy6784_frontier48_chain_contraction_fallback_closed_current_engine",
                    "standard_m3_tree_count": 3,
                    "standard_m3_matrix_rank": 0,
                    "direct_binary_target_piece_total": 0,
                    "homotopy_eligible_direct_product_total": 0,
                    "has_exposed_product_plus_chain_contraction_api": False,
                },
            )
            and evaluate_prefilter(
                "split_action_lift_missing_current_data",
                {
                    "requires_split_action_lift": True,
                    "parent_free_action_count": 8,
                    "direct_one_step_split_hit_count": 1,
                    "selected_split_symmetry_status": "unknown",
                    "selected_split_free_symmetry_option_count": 0,
                    "same_hodge_favourable_known_free_count": 0,
                    "inherited_slope_feasible_count": 0,
                    "bridge_status": "cicy4185_7910_split_found_action_lift_blocked_current_data",
                },
            )
            and not evaluate_prefilter(
                "higher_monoid_downstream_obstructed",
                {"status": "higher_monoid_representative_compatible_candidate"},
            ),
            str(report_json),
            "prefilter registry is importable and predicate samples behave as expected",
        ),
        "cicy6187_split_action_lift_missing_has_replay": gate(
            syndromes["cicy6187_7899_split_action_lift_missing_current_data"][
                "geometry"
            ]
            == "CICY6187 via favourable split 7899"
            and syndromes["cicy6187_7899_split_action_lift_missing_current_data"][
                "scope_class"
            ]
            == "presentation-local"
            and syndromes["cicy6187_7899_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["parent_cicy"]
            == 6187
            and syndromes["cicy6187_7899_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["selected_split"]
            == 7899
            and syndromes["cicy6187_7899_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["same_hodge_pool_count"]
            == 98
            and syndromes["cicy6187_7899_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["direct_one_step_split_hit_count"]
            == 1
            and syndromes["cicy6187_7899_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["parent_free_z2_option_count"]
            == 4
            and syndromes["cicy6187_7899_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["ambient_restricted_bundle_breadcrumb_available"]
            is False
            and syndromes["cicy6187_7899_split_action_lift_missing_current_data"][
                "replay_counts"
            ]["prefilter_sample_passes"],
            str(report_json),
            "CICY6187/7899 records the finite split-action-lift current-data boundary",
        ),
        "cicy6201_split_action_lift_missing_has_replay": gate(
            syndromes["cicy6201_7900_split_action_lift_missing_current_data"][
                "geometry"
            ]
            == "CICY6201 via favourable split 7900"
            and syndromes["cicy6201_7900_split_action_lift_missing_current_data"][
                "scope_class"
            ]
            == "presentation-local"
            and syndromes["cicy6201_7900_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["parent_cicy"]
            == 6201
            and syndromes["cicy6201_7900_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["selected_split"]
            == 7900
            and syndromes["cicy6201_7900_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["same_hodge_pool_count"]
            == 98
            and syndromes["cicy6201_7900_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["direct_one_step_split_hit_count"]
            == 1
            and syndromes["cicy6201_7900_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["parent_free_z2_option_count"]
            == 4
            and syndromes["cicy6201_7900_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["ambient_restricted_bundle_breadcrumb_available"]
            is False
            and syndromes["cicy6201_7900_split_action_lift_missing_current_data"][
                "replay_counts"
            ]["prefilter_sample_passes"],
            str(report_json),
            "CICY6201/7900 records the finite split-action-lift current-data boundary",
        ),
        "cicy6281_split_action_lift_missing_has_replay": gate(
            syndromes["cicy6281_7904_split_action_lift_missing_current_data"][
                "geometry"
            ]
            == "CICY6281 via favourable split 7904"
            and syndromes["cicy6281_7904_split_action_lift_missing_current_data"][
                "scope_class"
            ]
            == "presentation-local"
            and syndromes["cicy6281_7904_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["parent_cicy"]
            == 6281
            and syndromes["cicy6281_7904_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["selected_split"]
            == 7904
            and syndromes["cicy6281_7904_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["same_hodge_pool_count"]
            == 98
            and syndromes["cicy6281_7904_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["direct_one_step_split_hit_count"]
            == 1
            and syndromes["cicy6281_7904_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["parent_free_z2_option_count"]
            == 4
            and syndromes["cicy6281_7904_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["ambient_restricted_bundle_breadcrumb_available"]
            is False
            and syndromes["cicy6281_7904_split_action_lift_missing_current_data"][
                "replay_counts"
            ]["prefilter_sample_passes"],
            str(report_json),
            "CICY6281/7904 records the finite split-action-lift current-data boundary",
        ),
        "cicy4078_split_action_lift_missing_has_replay": gate(
            syndromes["cicy4078_7908_split_action_lift_missing_current_data"][
                "geometry"
            ]
            == "CICY4078 via favourable split 7908"
            and syndromes["cicy4078_7908_split_action_lift_missing_current_data"][
                "scope_class"
            ]
            == "presentation-local"
            and syndromes["cicy4078_7908_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["parent_cicy"]
            == 4078
            and syndromes["cicy4078_7908_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["selected_split"]
            == 7908
            and syndromes["cicy4078_7908_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["same_hodge_pool_count"]
            == 165
            and syndromes["cicy4078_7908_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["direct_one_step_split_hit_count"]
            == 1
            and syndromes["cicy4078_7908_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["parent_free_z2_option_count"]
            == 4
            and syndromes["cicy4078_7908_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["inherited_topology_gate_counts"].get("slope_feasible_count", 0)
            == 0
            and syndromes["cicy4078_7908_split_action_lift_missing_current_data"][
                "replay_counts"
            ]["prefilter_sample_passes"],
            str(report_json),
            "CICY4078/7908 records the finite split-action-lift current-data boundary",
        ),
        "cicy5141_split_action_lift_missing_has_replay": gate(
            syndromes["cicy5141_7912_split_action_lift_missing_current_data"][
                "geometry"
            ]
            == "CICY5141 via favourable split 7912"
            and syndromes["cicy5141_7912_split_action_lift_missing_current_data"][
                "scope_class"
            ]
            == "presentation-local"
            and syndromes["cicy5141_7912_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["parent_cicy"]
            == 5141
            and syndromes["cicy5141_7912_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["selected_split"]
            == 7912
            and syndromes["cicy5141_7912_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["same_hodge_pool_count"]
            == 59
            and syndromes["cicy5141_7912_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["direct_one_step_split_hit_count"]
            == 1
            and syndromes["cicy5141_7912_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["parent_free_z2_option_count"]
            == 4
            and syndromes["cicy5141_7912_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["ambient_restricted_bundle_breadcrumb_available"]
            is False
            and syndromes["cicy5141_7912_split_action_lift_missing_current_data"][
                "replay_counts"
            ]["prefilter_sample_passes"],
            str(report_json),
            "CICY5141/7912 records the finite split-action-lift current-data boundary",
        ),
        "cicy5248_split_action_lift_missing_has_replay": gate(
            syndromes["cicy5248_7913_split_action_lift_missing_current_data"][
                "geometry"
            ]
            == "CICY5248 via favourable split 7913"
            and syndromes["cicy5248_7913_split_action_lift_missing_current_data"][
                "scope_class"
            ]
            == "presentation-local"
            and syndromes["cicy5248_7913_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["parent_cicy"]
            == 5248
            and syndromes["cicy5248_7913_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["selected_split"]
            == 7913
            and syndromes["cicy5248_7913_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["same_hodge_pool_count"]
            == 59
            and syndromes["cicy5248_7913_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["direct_one_step_split_hit_count"]
            == 1
            and syndromes["cicy5248_7913_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["parent_free_z2_option_count"]
            == 4
            and syndromes["cicy5248_7913_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["ambient_restricted_bundle_breadcrumb_available"]
            is False
            and syndromes["cicy5248_7913_split_action_lift_missing_current_data"][
                "replay_counts"
            ]["prefilter_sample_passes"],
            str(report_json),
            "CICY5248/7913 records the finite split-action-lift current-data boundary",
        ),
        "cicy5406_split_action_lift_missing_has_replay": gate(
            syndromes["cicy5406_7918_split_action_lift_missing_current_data"][
                "geometry"
            ]
            == "CICY5406 via favourable split 7918"
            and syndromes["cicy5406_7918_split_action_lift_missing_current_data"][
                "scope_class"
            ]
            == "presentation-local"
            and syndromes["cicy5406_7918_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["parent_cicy"]
            == 5406
            and syndromes["cicy5406_7918_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["selected_split"]
            == 7918
            and syndromes["cicy5406_7918_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["same_hodge_pool_count"]
            == 59
            and syndromes["cicy5406_7918_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["direct_one_step_split_hit_count"]
            == 1
            and syndromes["cicy5406_7918_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["parent_free_z2_option_count"]
            == 4
            and syndromes["cicy5406_7918_split_action_lift_missing_current_data"][
                "minimal_obstruction_core"
            ]["ambient_restricted_bundle_breadcrumb_available"]
            is False
            and syndromes["cicy5406_7918_split_action_lift_missing_current_data"][
                "replay_counts"
            ]["prefilter_sample_passes"],
            str(report_json),
            "CICY5406/7918 records the finite split-action-lift current-data boundary",
        ),
        "cicy5449_no_direct_split_witness_has_replay": gate(
            syndromes["cicy5449_no_direct_split_witness_current_data"]["geometry"]
            == "CICY5449 no direct favourable split witness"
            and syndromes["cicy5449_no_direct_split_witness_current_data"][
                "scope_class"
            ]
            == "presentation-local"
            and syndromes["cicy5449_no_direct_split_witness_current_data"][
                "minimal_obstruction_core"
            ]["parent_cicy"]
            == 5449
            and syndromes["cicy5449_no_direct_split_witness_current_data"][
                "minimal_obstruction_core"
            ]["same_hodge_pool_count"]
            == 59
            and syndromes["cicy5449_no_direct_split_witness_current_data"][
                "minimal_obstruction_core"
            ]["direct_one_step_split_hit_count"]
            == 0
            and syndromes["cicy5449_no_direct_split_witness_current_data"][
                "minimal_obstruction_core"
            ]["parent_free_z2_option_count"]
            == 4
            and syndromes["cicy5449_no_direct_split_witness_current_data"][
                "minimal_obstruction_core"
            ]["same_hodge_favourable_unknown_nums"]
            == list(range(7912, 7920))
            and syndromes["cicy5449_no_direct_split_witness_current_data"][
                "minimal_obstruction_core"
            ]["ambient_restricted_bundle_breadcrumb_available"]
            is False
            and syndromes["cicy5449_no_direct_split_witness_current_data"][
                "replay_counts"
            ]["prefilter_sample_passes"],
            str(report_json),
            "CICY5449 records the finite no-direct-split-witness current-data boundary",
        ),
        "cicy7810_no_direct_split_witness_has_replay": gate(
            syndromes["cicy7810_no_direct_split_witness_current_data"]["geometry"]
            == "CICY7810 no direct favourable split witness"
            and syndromes["cicy7810_no_direct_split_witness_current_data"][
                "scope_class"
            ]
            == "presentation-local"
            and syndromes["cicy7810_no_direct_split_witness_current_data"][
                "minimal_obstruction_core"
            ]["parent_cicy"]
            == 7810
            and syndromes["cicy7810_no_direct_split_witness_current_data"][
                "minimal_obstruction_core"
            ]["same_hodge_pool_count"]
            == 2
            and syndromes["cicy7810_no_direct_split_witness_current_data"][
                "minimal_obstruction_core"
            ]["direct_one_step_split_hit_count"]
            == 0
            and syndromes["cicy7810_no_direct_split_witness_current_data"][
                "minimal_obstruction_core"
            ]["parent_free_z3_option_count"]
            == 3
            and syndromes["cicy7810_no_direct_split_witness_current_data"][
                "minimal_obstruction_core"
            ]["same_hodge_favourable_unknown_nums"]
            == [7894, 7895]
            and syndromes["cicy7810_no_direct_split_witness_current_data"][
                "minimal_obstruction_core"
            ]["ambient_restricted_bundle_breadcrumb_available"]
            is False
            and syndromes["cicy7810_no_direct_split_witness_current_data"][
                "replay_counts"
            ]["prefilter_sample_passes"],
            str(report_json),
            "CICY7810 records the finite no-direct-split-witness current-data boundary",
        ),
        "cicy5302_gutall_benchmark_pool_engine_gap_has_replay": gate(
            syndromes["cicy5302_gutall_benchmark_pool_engine_gap_current_data"][
                "geometry"
            ]
            == "CICY5302 GUTall benchmark pool"
            and syndromes[
                "cicy5302_gutall_benchmark_pool_engine_gap_current_data"
            ]["scope_class"]
            == "grammar-local"
            and syndromes[
                "cicy5302_gutall_benchmark_pool_engine_gap_current_data"
            ]["cheap_prefilter"]["prefilter_id"]
            == "geometry_specific_engine_missing_current_data"
            and syndromes[
                "cicy5302_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"]["model_count"]
            == 23623
            and syndromes[
                "cicy5302_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"]["model_counts_by_symmetry_order"]
            == {"2": 6294, "4": 17329}
            and syndromes[
                "cicy5302_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"]["algebraic_benchmark_failure_count"]
            == 0
            and syndromes[
                "cicy5302_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"]["raw_free_action_count"]
            == 20
            and syndromes[
                "cicy5302_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"]["raw_free_order_counts"]
            == {"2": 4, "4": 16}
            and syndromes[
                "cicy5302_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"]["all_free_options_row_trivial"]
            and syndromes[
                "cicy5302_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"][
                "ambient_lift_readiness_by_symmetry_order"
            ]["2"]["any_direct_sum_equivariant_lift_count"]
            == 6294
            and syndromes[
                "cicy5302_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"][
                "ambient_lift_readiness_by_symmetry_order"
            ]["4"]["any_direct_sum_equivariant_lift_count"]
            == 3879
            and syndromes[
                "cicy5302_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"][
                "ambient_lift_readiness_by_symmetry_order"
            ]["4"]["no_direct_sum_equivariant_lift_count"]
            == 13450
            and not syndromes[
                "cicy5302_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"][
                "geometry_specific_representative_mass_engine_available"
            ]
            and syndromes[
                "cicy5302_gutall_benchmark_pool_engine_gap_current_data"
            ]["replay_counts"]["prefilter_sample_passes"],
            str(report_json),
            "CICY5302 records a clean GUTall pool blocked by current promotion-engine availability",
        ),
        "cicy5256_gutall_benchmark_pool_engine_gap_has_replay": gate(
            syndromes["cicy5256_gutall_benchmark_pool_engine_gap_current_data"][
                "geometry"
            ]
            == "CICY5256 GUTall benchmark pool"
            and syndromes[
                "cicy5256_gutall_benchmark_pool_engine_gap_current_data"
            ]["scope_class"]
            == "grammar-local"
            and syndromes[
                "cicy5256_gutall_benchmark_pool_engine_gap_current_data"
            ]["cheap_prefilter"]["prefilter_id"]
            == "geometry_specific_engine_missing_current_data"
            and syndromes[
                "cicy5256_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"]["model_count"]
            == 2891
            and syndromes[
                "cicy5256_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"]["model_counts_by_symmetry_order"]
            == {"2": 763, "4": 2128}
            and syndromes[
                "cicy5256_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"]["algebraic_benchmark_failure_count"]
            == 0
            and syndromes[
                "cicy5256_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"]["raw_free_action_count"]
            == 6
            and syndromes[
                "cicy5256_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"]["raw_free_order_counts"]
            == {"2": 2, "4": 4}
            and syndromes[
                "cicy5256_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"]["raw_free_group_structure_counts"]
            == {"2": 2, "2x2": 4}
            and syndromes[
                "cicy5256_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"]["all_free_options_row_trivial"]
            and syndromes[
                "cicy5256_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"][
                "ambient_lift_readiness_by_symmetry_order"
            ]["2"]["any_direct_sum_equivariant_lift_count"]
            == 763
            and syndromes[
                "cicy5256_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"][
                "ambient_lift_readiness_by_symmetry_order"
            ]["4"]["any_direct_sum_equivariant_lift_count"]
            == 544
            and syndromes[
                "cicy5256_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"][
                "ambient_lift_readiness_by_symmetry_order"
            ]["4"]["no_direct_sum_equivariant_lift_count"]
            == 1584
            and not syndromes[
                "cicy5256_gutall_benchmark_pool_engine_gap_current_data"
            ]["minimal_obstruction_core"][
                "geometry_specific_representative_mass_engine_available"
            ]
            and syndromes[
                "cicy5256_gutall_benchmark_pool_engine_gap_current_data"
            ]["replay_counts"]["prefilter_sample_passes"],
            str(report_json),
            "CICY5256 records a clean GUTall pool blocked by current promotion-engine availability",
        ),
        "cicy5273_gutall_benchmark_pool_raw_action_gap_has_replay": gate(
            syndromes[
                "cicy5273_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["geometry"]
            == "CICY5273 GUTall benchmark pool"
            and syndromes[
                "cicy5273_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["scope_class"]
            == "grammar-local"
            and syndromes[
                "cicy5273_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["cheap_prefilter"]["prefilter_id"]
            == "raw_free_action_data_missing_current_data"
            and syndromes[
                "cicy5273_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"]["model_count"]
            == 6753
            and syndromes[
                "cicy5273_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"]["model_counts_by_symmetry_order"]
            == {"2": 6753}
            and syndromes[
                "cicy5273_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"]["algebraic_benchmark_failure_count"]
            == 0
            and syndromes[
                "cicy5273_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"]["gutall_symmetry_orders"]
            == [2]
            and syndromes[
                "cicy5273_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"]["raw_symmetry_option_count"]
            == 1
            and syndromes[
                "cicy5273_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"]["raw_free_action_count"]
            == 0
            and syndromes[
                "cicy5273_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"][
                "ambient_lift_readiness_by_symmetry_order"
            ]["2"]["any_direct_sum_equivariant_lift_count"]
            == 0
            and syndromes[
                "cicy5273_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"][
                "ambient_lift_readiness_by_symmetry_order"
            ]["2"]["no_direct_sum_equivariant_lift_count"]
            == 6753
            and syndromes[
                "cicy5273_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["replay_counts"]["prefilter_sample_passes"],
            str(report_json),
            "CICY5273 records a clean GUTall pool blocked by missing local raw free-action data",
        ),
        "cicy6738_gutall_benchmark_pool_raw_action_gap_has_replay": gate(
            syndromes[
                "cicy6738_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["geometry"]
            == "CICY6738 GUTall benchmark pool"
            and syndromes[
                "cicy6738_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["scope_class"]
            == "grammar-local"
            and syndromes[
                "cicy6738_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["cheap_prefilter"]["prefilter_id"]
            == "raw_free_action_data_missing_current_data"
            and syndromes[
                "cicy6738_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"]["model_count"]
            == 4243
            and syndromes[
                "cicy6738_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"]["model_counts_by_symmetry_order"]
            == {"2": 4243}
            and syndromes[
                "cicy6738_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"]["algebraic_benchmark_failure_count"]
            == 0
            and syndromes[
                "cicy6738_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"]["gutall_symmetry_orders"]
            == [2]
            and syndromes[
                "cicy6738_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"]["raw_symmetry_option_count"]
            == 1
            and syndromes[
                "cicy6738_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"]["raw_free_action_count"]
            == 0
            and syndromes[
                "cicy6738_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"][
                "ambient_lift_readiness_by_symmetry_order"
            ]["2"]["any_direct_sum_equivariant_lift_count"]
            == 0
            and syndromes[
                "cicy6738_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"][
                "ambient_lift_readiness_by_symmetry_order"
            ]["2"]["no_direct_sum_equivariant_lift_count"]
            == 4243
            and syndromes[
                "cicy6738_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["replay_counts"]["prefilter_sample_passes"],
            str(report_json),
            "CICY6738 records a clean GUTall pool blocked by missing local raw free-action data",
        ),
        "cicy5425_gutall_benchmark_pool_raw_action_gap_has_replay": gate(
            syndromes[
                "cicy5425_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["geometry"]
            == "CICY5425 GUTall benchmark pool"
            and syndromes[
                "cicy5425_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["scope_class"]
            == "grammar-local"
            and syndromes[
                "cicy5425_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["cheap_prefilter"]["prefilter_id"]
            == "raw_free_action_data_missing_current_data"
            and syndromes[
                "cicy5425_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"]["model_count"]
            == 3128
            and syndromes[
                "cicy5425_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"]["model_counts_by_symmetry_order"]
            == {"2": 3128}
            and syndromes[
                "cicy5425_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"]["algebraic_benchmark_failure_count"]
            == 0
            and syndromes[
                "cicy5425_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"]["gutall_symmetry_orders"]
            == [2]
            and syndromes[
                "cicy5425_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"]["raw_symmetry_option_count"]
            == 1
            and syndromes[
                "cicy5425_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"]["raw_free_action_count"]
            == 0
            and syndromes[
                "cicy5425_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"][
                "ambient_lift_readiness_by_symmetry_order"
            ]["2"]["any_direct_sum_equivariant_lift_count"]
            == 0
            and syndromes[
                "cicy5425_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["minimal_obstruction_core"][
                "ambient_lift_readiness_by_symmetry_order"
            ]["2"]["no_direct_sum_equivariant_lift_count"]
            == 3128
            and syndromes[
                "cicy5425_gutall_benchmark_pool_raw_action_gap_current_data"
            ]["replay_counts"]["prefilter_sample_passes"],
            str(report_json),
            "CICY5425 records a clean GUTall pool blocked by missing local raw free-action data",
        ),
        "2544_geometry_gate_has_replay": gate(
            syndromes["geometry_no_recorded_free_symmetry"]["geometry"] == "CICY2544"
            and syndromes["geometry_no_recorded_free_symmetry"]["scope_class"]
            == "geometry-local"
            and syndromes["geometry_no_recorded_free_symmetry"]["replay_counts"][
                "favourable_h11_ge_7_known_symmetry_rows"
            ]
            == 3
            and syndromes["geometry_no_recorded_free_symmetry"]["replay_counts"][
                "rows_with_no_recorded_free_symmetry"
            ]
            == 3
            and syndromes["geometry_no_recorded_free_symmetry"][
                "minimal_obstruction_core"
            ]["raw_free_symmetry_option_count"]
            == 0,
            str(report_json),
            "2544 syndrome records the no-recorded-free-symmetry replay",
        ),
        "7484_vectorlike_gate_has_replay": gate(
            syndromes["z2xz2_regular_vectorlike_excess_7484"]["geometry"]
            == "CICY7484"
            and syndromes["z2xz2_regular_vectorlike_excess_7484"][
                "minimal_obstruction_core"
            ]["best_actual_per_character_pair"]
            == [6, 3]
            and syndromes["z2xz2_regular_vectorlike_excess_7484"]["replay_counts"][
                "actual_character_count"
            ]
            == 12
            and not syndromes["z2xz2_regular_vectorlike_excess_7484"][
                "replay_counts"
            ]["has_actual_three_family_no_vectorlike_pair"],
            str(report_json),
            "7484 syndrome records the character-certified vectorlike near-miss",
        ),
        "5259_frontier_replay_counts_are_stable": gate(
            syndromes["degree_zero_bilinear_not_cy3_top_cup"]["replay_counts"][
                "degree_zero_bilinear_rows"
            ]
            == 1452
            and syndromes["physical_5bar_representative_character_mismatch"][
                "replay_counts"
            ]["degree_aware_failure_records"]
            == 333
            and syndromes["physical_5bar_representative_character_mismatch"][
                "minimal_obstruction_core"
            ]["requested"]["multiplicities"]
            == {"+": 2, "-": 0}
            and syndromes["physical_5bar_representative_character_mismatch"][
                "minimal_obstruction_core"
            ]["computed"]["multiplicities"]
            == {"+": 1, "-": 1}
            and syndromes["degree_one_representative_intersection_not_triplet_only"][
                "replay_counts"
            ]["intersection_forced_operator_records"]
            == 10004
            and syndromes["degree_one_representative_intersection_not_triplet_only"][
                "replay_counts"
            ]["cup_product_eligible_records"]
            == 0,
            str(report_json),
            "5259/7914 degree, representative, and degree-one intersection replay counts are stable",
        ),
        "higher_degree_counts_and_survivor_boundary": gate(
            syndromes["higher_degree_monoid_downstream_obstructions"][
                "replay_counts"
            ]["higher_degree_forced_operator_records"]
            == 10004
            and syndromes["higher_degree_monoid_downstream_obstructions"][
                "replay_counts"
            ]["downstream_obstructed_operator_records"]
            == 9868
            and syndromes["higher_degree_monoid_downstream_obstructions"][
                "replay_counts"
            ]["representative_candidate_records"]
            == 136,
            str(report_json),
            "higher-degree replay counts remain stable before the Branch 50 degree audit",
        ),
        "branch50_m4_degree_gate_has_replay": gate(
            syndromes["branch50_standard_m4_four_h1_not_cy3_top_cup"][
                "minimal_obstruction_core"
            ]["candidate_label"]
            == "radius6_broad_adjacency_filtered_10_branch_50"
            and syndromes["branch50_standard_m4_four_h1_not_cy3_top_cup"][
                "minimal_obstruction_core"
            ]["operator"]
            == "5bar_02*5_34"
            and syndromes["branch50_standard_m4_four_h1_not_cy3_top_cup"][
                "minimal_obstruction_core"
            ]["monomial"]
            == ["e3-e2", "e4-e0"]
            and syndromes["branch50_standard_m4_four_h1_not_cy3_top_cup"][
                "minimal_obstruction_core"
            ]["input_degrees"]
            == [1, 1, 1, 1]
            and syndromes["branch50_standard_m4_four_h1_not_cy3_top_cup"][
                "minimal_obstruction_core"
            ]["output_degree"]
            == 2
            and syndromes["branch50_standard_m4_four_h1_not_cy3_top_cup"][
                "minimal_obstruction_core"
            ]["target_H3_dimension"]
            == 1
            and syndromes["branch50_standard_m4_four_h1_not_cy3_top_cup"][
                "minimal_obstruction_core"
            ]["standard_m4_to_H3_rank"]
            == 0
            and syndromes["branch50_standard_m4_four_h1_not_cy3_top_cup"][
                "replay_counts"
            ]["tree_degree_record_count"]
            == 5,
            str(report_json),
            "Branch 50 records the standard m4 degree-law no-go replay",
        ),
        "model874_s42_basin_has_replay": gate(
            syndromes["cicy6927_model874_s42_doublet_contamination_basin"][
                "geometry"
            ]
            == "CICY6927/model 874 option 4"
            and syndromes["cicy6927_model874_s42_doublet_contamination_basin"][
                "minimal_obstruction_core"
            ]["universal_operator"]
            == "5bar_23*5_34*S"
            and syndromes["cicy6927_model874_s42_doublet_contamination_basin"][
                "minimal_obstruction_core"
            ]["singlets"]
            == ["S_42"]
            and syndromes["cicy6927_model874_s42_doublet_contamination_basin"][
                "replay_counts"
            ]["fixed_model_embedding_vectors"]
            == 768
            and syndromes["cicy6927_model874_s42_doublet_contamination_basin"][
                "replay_counts"
            ]["one_higgs_proton_safe_vectors"]
            == 96
            and syndromes["cicy6927_model874_s42_doublet_contamination_basin"][
                "replay_counts"
            ]["latent_compensated_frontier_size"]
            == 23183
            and syndromes["cicy6927_model874_s42_doublet_contamination_basin"][
                "replay_counts"
            ]["latent_compensated_promotion_timeout_count"]
            == 3
            and syndromes["cicy6927_model874_s42_doublet_contamination_basin"][
                "replay_counts"
            ]["timeout_closure_resolved_count"]
            == 3
            and syndromes["cicy6927_model874_s42_doublet_contamination_basin"][
                "replay_counts"
            ]["timeout_closure_unresolved_count"]
            == 0,
            str(report_json),
            "CICY6927/model-874 syndrome records the S_42 motif and closed timeout boundary",
        ),
        "cicy6927_non_s42_cup_boundary_has_replay": gate(
            syndromes["cicy6927_non_s42_cup_boundary_missing_one_higgs_radius2"][
                "geometry"
            ]
            == "CICY6927/model 237 and 583 option 4"
            and syndromes["cicy6927_non_s42_cup_boundary_missing_one_higgs_radius2"][
                "minimal_obstruction_core"
            ]["source_models"]
            == [237, 583]
            and syndromes["cicy6927_non_s42_cup_boundary_missing_one_higgs_radius2"][
                "minimal_obstruction_core"
            ]["radius"]
            == 2
            and syndromes["cicy6927_non_s42_cup_boundary_missing_one_higgs_radius2"][
                "replay_counts"
            ]["frontier_size"]
            == 772
            and syndromes["cicy6927_non_s42_cup_boundary_missing_one_higgs_radius2"][
                "replay_counts"
            ]["q1_candidate_count"]
            == 3
            and syndromes["cicy6927_non_s42_cup_boundary_missing_one_higgs_radius2"][
                "replay_counts"
            ]["cup_product_eligible_triplet_target_count"]
            == 256
            and syndromes["cicy6927_non_s42_cup_boundary_missing_one_higgs_radius2"][
                "replay_counts"
            ]["one_higgs_pair_triplet_free_embeddings"]
            == 0,
            str(report_json),
            "CICY6927 non-S42 cup boundary records the radius-2 missing-one-Higgs no-go",
        ),
        "cicy6927_model252_s42_boundary_only_has_replay": gate(
            syndromes["cicy6927_model252_s42_boundary_only_radius2"]["geometry"]
            == "CICY6927/model 252 option 4"
            and syndromes["cicy6927_model252_s42_boundary_only_radius2"][
                "minimal_obstruction_core"
            ]["focus_model"]
            == 252
            and syndromes["cicy6927_model252_s42_boundary_only_radius2"][
                "minimal_obstruction_core"
            ]["source_models"]
            == [252, 237, 583, 874]
            and syndromes["cicy6927_model252_s42_boundary_only_radius2"][
                "minimal_obstruction_core"
            ]["radius"]
            == 2
            and syndromes["cicy6927_model252_s42_boundary_only_radius2"][
                "replay_counts"
            ]["frontier_size"]
            == 1750
            and syndromes["cicy6927_model252_s42_boundary_only_radius2"][
                "replay_counts"
            ]["q1_candidate_count"]
            == 7
            and syndromes["cicy6927_model252_s42_boundary_only_radius2"][
                "replay_counts"
            ]["one_higgs_proton_safe_intersection_count"]
            == 1
            and syndromes["cicy6927_model252_s42_boundary_only_radius2"][
                "replay_counts"
            ]["non_s42_precup_survivor_count"]
            == 0
            and syndromes["cicy6927_model252_s42_boundary_only_radius2"][
                "replay_counts"
            ]["closest_detail_s42_motif_hit_count"]
            == 8
            and syndromes["cicy6927_model252_s42_boundary_only_radius2"][
                "replay_counts"
            ]["only_intersection_frontier"]
            == 0
            and syndromes["cicy6927_model252_s42_boundary_only_radius2"][
                "replay_counts"
            ]["only_intersection_source_models"]
            == [874]
            and syndromes["cicy6927_model252_s42_boundary_only_radius2"][
                "replay_counts"
            ]["prefilter_sample_passes"],
            str(report_json),
            "CICY6927 model-252 radius-2 pass records only the known S42 boundary and no non-S42 survivor",
        ),
        "cicy6927_model254_s42_boundary_only_has_replay": gate(
            syndromes["cicy6927_model254_s42_boundary_only_radius2"]["geometry"]
            == "CICY6927/model 254 option 4"
            and syndromes["cicy6927_model254_s42_boundary_only_radius2"][
                "minimal_obstruction_core"
            ]["focus_model"]
            == 254
            and syndromes["cicy6927_model254_s42_boundary_only_radius2"][
                "minimal_obstruction_core"
            ]["source_models"]
            == [254, 237, 583, 874]
            and syndromes["cicy6927_model254_s42_boundary_only_radius2"][
                "minimal_obstruction_core"
            ]["radius"]
            == 2
            and syndromes["cicy6927_model254_s42_boundary_only_radius2"][
                "replay_counts"
            ]["frontier_size"]
            == 1962
            and syndromes["cicy6927_model254_s42_boundary_only_radius2"][
                "replay_counts"
            ]["q1_candidate_count"]
            == 10
            and syndromes["cicy6927_model254_s42_boundary_only_radius2"][
                "replay_counts"
            ]["one_higgs_proton_safe_intersection_count"]
            == 1
            and syndromes["cicy6927_model254_s42_boundary_only_radius2"][
                "replay_counts"
            ]["non_s42_precup_survivor_count"]
            == 0
            and syndromes["cicy6927_model254_s42_boundary_only_radius2"][
                "replay_counts"
            ]["closest_detail_s42_motif_hit_count"]
            == 8
            and syndromes["cicy6927_model254_s42_boundary_only_radius2"][
                "replay_counts"
            ]["only_intersection_frontier"]
            == 0
            and syndromes["cicy6927_model254_s42_boundary_only_radius2"][
                "replay_counts"
            ]["only_intersection_source_models"]
            == [874]
            and syndromes["cicy6927_model254_s42_boundary_only_radius2"][
                "replay_counts"
            ]["prefilter_sample_passes"],
            str(report_json),
            "CICY6927 model-254 radius-2 pass records only the known S42 boundary and no non-S42 survivor",
        ),
        "cicy6927_model369_s42_boundary_only_has_replay": gate(
            syndromes["cicy6927_model369_s42_boundary_only_radius2"]["geometry"]
            == "CICY6927/model 369 option 4"
            and syndromes["cicy6927_model369_s42_boundary_only_radius2"][
                "minimal_obstruction_core"
            ]["focus_model"]
            == 369
            and syndromes["cicy6927_model369_s42_boundary_only_radius2"][
                "minimal_obstruction_core"
            ]["source_models"]
            == [369, 237, 583, 874]
            and syndromes["cicy6927_model369_s42_boundary_only_radius2"][
                "minimal_obstruction_core"
            ]["radius"]
            == 2
            and syndromes["cicy6927_model369_s42_boundary_only_radius2"][
                "replay_counts"
            ]["frontier_size"]
            == 1973
            and syndromes["cicy6927_model369_s42_boundary_only_radius2"][
                "replay_counts"
            ]["q1_candidate_count"]
            == 12
            and syndromes["cicy6927_model369_s42_boundary_only_radius2"][
                "replay_counts"
            ]["model369_screened_count"]
            == 6
            and syndromes["cicy6927_model369_s42_boundary_only_radius2"][
                "minimal_obstruction_core"
            ]["model369_screen_status_counts"]
            == {"all_embeddings_pre_cup_obstructed": 6}
            and syndromes["cicy6927_model369_s42_boundary_only_radius2"][
                "replay_counts"
            ]["one_higgs_proton_safe_intersection_count"]
            == 1
            and syndromes["cicy6927_model369_s42_boundary_only_radius2"][
                "replay_counts"
            ]["non_s42_precup_survivor_count"]
            == 0
            and syndromes["cicy6927_model369_s42_boundary_only_radius2"][
                "replay_counts"
            ]["closest_detail_s42_motif_hit_count"]
            == 8
            and syndromes["cicy6927_model369_s42_boundary_only_radius2"][
                "replay_counts"
            ]["only_intersection_frontier"]
            == 0
            and syndromes["cicy6927_model369_s42_boundary_only_radius2"][
                "replay_counts"
            ]["only_intersection_source_models"]
            == [874]
            and syndromes["cicy6927_model369_s42_boundary_only_radius2"][
                "replay_counts"
            ]["prefilter_sample_passes"],
            str(report_json),
            "CICY6927 model-369 radius-2 pass records only the known S42 boundary and no non-S42 survivor",
        ),
        "cicy6927_model52_s42_boundary_only_has_replay": gate(
            syndromes["cicy6927_model52_s42_boundary_only_radius2"]["geometry"]
            == "CICY6927/model 52 option 4"
            and syndromes["cicy6927_model52_s42_boundary_only_radius2"][
                "minimal_obstruction_core"
            ]["focus_model"]
            == 52
            and syndromes["cicy6927_model52_s42_boundary_only_radius2"][
                "minimal_obstruction_core"
            ]["source_models"]
            == [52, 237, 583, 874]
            and syndromes["cicy6927_model52_s42_boundary_only_radius2"][
                "minimal_obstruction_core"
            ]["radius"]
            == 2
            and syndromes["cicy6927_model52_s42_boundary_only_radius2"][
                "replay_counts"
            ]["frontier_size"]
            == 1962
            and syndromes["cicy6927_model52_s42_boundary_only_radius2"][
                "replay_counts"
            ]["q1_candidate_count"]
            == 8
            and syndromes["cicy6927_model52_s42_boundary_only_radius2"][
                "replay_counts"
            ]["model52_screened_count"]
            == 2
            and syndromes["cicy6927_model52_s42_boundary_only_radius2"][
                "minimal_obstruction_core"
            ]["model52_screen_status_counts"]
            == {"all_embeddings_pre_cup_obstructed": 2}
            and syndromes["cicy6927_model52_s42_boundary_only_radius2"][
                "replay_counts"
            ]["one_higgs_proton_safe_intersection_count"]
            == 1
            and syndromes["cicy6927_model52_s42_boundary_only_radius2"][
                "replay_counts"
            ]["non_s42_precup_survivor_count"]
            == 0
            and syndromes["cicy6927_model52_s42_boundary_only_radius2"][
                "replay_counts"
            ]["closest_detail_s42_motif_hit_count"]
            == 8
            and syndromes["cicy6927_model52_s42_boundary_only_radius2"][
                "replay_counts"
            ]["only_intersection_frontier"]
            == 0
            and syndromes["cicy6927_model52_s42_boundary_only_radius2"][
                "replay_counts"
            ]["only_intersection_source_models"]
            == [874]
            and syndromes["cicy6927_model52_s42_boundary_only_radius2"][
                "replay_counts"
            ]["prefilter_sample_passes"],
            str(report_json),
            "CICY6927 model-52 radius-2 pass records only the known S42 boundary and no non-S42 survivor",
        ),
        "cicy6836_one_higgs_proton_disjoint_has_replay": gate(
            syndromes["cicy6836_one_higgs_proton_safety_disjoint_radius2"][
                "geometry"
            ]
            == "CICY6836/model 95 and 139 option 23"
            and syndromes["cicy6836_one_higgs_proton_safety_disjoint_radius2"][
                "minimal_obstruction_core"
            ]["source_models"]
            == [95, 139]
            and syndromes["cicy6836_one_higgs_proton_safety_disjoint_radius2"][
                "minimal_obstruction_core"
            ]["radius"]
            == 2
            and syndromes["cicy6836_one_higgs_proton_safety_disjoint_radius2"][
                "replay_counts"
            ]["frontier_size"]
            == 981
            and syndromes["cicy6836_one_higgs_proton_safety_disjoint_radius2"][
                "replay_counts"
            ]["q1_candidate_count"]
            == 4
            and syndromes["cicy6836_one_higgs_proton_safety_disjoint_radius2"][
                "replay_counts"
            ]["screened_candidate_count"]
            == 4
            and syndromes["cicy6836_one_higgs_proton_safety_disjoint_radius2"][
                "replay_counts"
            ]["promotion_timeout_count"]
            == 0
            and syndromes["cicy6836_one_higgs_proton_safety_disjoint_radius2"][
                "replay_counts"
            ]["one_higgs_pair_triplet_free_embeddings"]
            == 384
            and syndromes["cicy6836_one_higgs_proton_safety_disjoint_radius2"][
                "replay_counts"
            ]["one_higgs_proton_safe_embeddings"]
            == 0
            and syndromes["cicy6836_one_higgs_proton_safety_disjoint_radius2"][
                "replay_counts"
            ]["cup_product_eligible_triplet_target_count"]
            == 128,
            str(report_json),
            "CICY6836 radius-2 records the one-Higgs/proton-safe disjointness no-go",
        ),
        "cicy6836_model87_intersection_forcing_has_replay": gate(
            syndromes["cicy6836_model87_one_higgs_proton_safety_disjoint_radius2"][
                "geometry"
            ]
            == "CICY6836/model 87 option 23"
            and syndromes["cicy6836_model87_one_higgs_proton_safety_disjoint_radius2"][
                "minimal_obstruction_core"
            ]["focus_model"]
            == 87
            and syndromes["cicy6836_model87_one_higgs_proton_safety_disjoint_radius2"][
                "minimal_obstruction_core"
            ]["source_models"]
            == [87, 139, 186]
            and syndromes["cicy6836_model87_one_higgs_proton_safety_disjoint_radius2"][
                "minimal_obstruction_core"
            ]["radius"]
            == 2
            and syndromes["cicy6836_model87_one_higgs_proton_safety_disjoint_radius2"][
                "minimal_obstruction_core"
            ]["first_pair_gate_status"]
            == "not_evaluated_for_cicy6836_current_engine"
            and syndromes["cicy6836_model87_one_higgs_proton_safety_disjoint_radius2"][
                "replay_counts"
            ]["frontier_size"]
            == 1361
            and syndromes["cicy6836_model87_one_higgs_proton_safety_disjoint_radius2"][
                "replay_counts"
            ]["q1_candidate_count"]
            == 10
            and syndromes["cicy6836_model87_one_higgs_proton_safety_disjoint_radius2"][
                "replay_counts"
            ]["screened_candidate_count"]
            == 10
            and syndromes["cicy6836_model87_one_higgs_proton_safety_disjoint_radius2"][
                "replay_counts"
            ]["promotion_timeout_count"]
            == 0
            and syndromes["cicy6836_model87_one_higgs_proton_safety_disjoint_radius2"][
                "replay_counts"
            ]["one_higgs_pair_triplet_free_embeddings"]
            == 1024
            and syndromes["cicy6836_model87_one_higgs_proton_safety_disjoint_radius2"][
                "replay_counts"
            ]["proton_safe_embeddings"]
            == 1536
            and syndromes["cicy6836_model87_one_higgs_proton_safety_disjoint_radius2"][
                "replay_counts"
            ]["one_higgs_proton_safe_embeddings"]
            == 0
            and syndromes["cicy6836_model87_one_higgs_proton_safety_disjoint_radius2"][
                "replay_counts"
            ]["cup_product_eligible_triplet_target_count"]
            == 128,
            str(report_json),
            "CICY6836 model-87 queue target is closed by a radius-2 one-Higgs/proton-safe disjointness replay",
        ),
        "cicy6836_model186_frontier691_followup_has_replay": gate(
            syndromes["cicy6836_model186_frontier691_followup_disjoint_radius2"][
                "geometry"
            ]
            == "CICY6836/model 186 option 23 plus frontier 691"
            and syndromes["cicy6836_model186_frontier691_followup_disjoint_radius2"][
                "minimal_obstruction_core"
            ]["focus_model"]
            == 186
            and syndromes["cicy6836_model186_frontier691_followup_disjoint_radius2"][
                "minimal_obstruction_core"
            ]["source_models"]
            == [186, 87, 95, 139]
            and syndromes["cicy6836_model186_frontier691_followup_disjoint_radius2"][
                "minimal_obstruction_core"
            ]["first_pass_frontier_size"]
            == 1961
            and syndromes["cicy6836_model186_frontier691_followup_disjoint_radius2"][
                "minimal_obstruction_core"
            ]["first_pass_boundary_improvement_record_count"]
            == 11
            and syndromes["cicy6836_model186_frontier691_followup_disjoint_radius2"][
                "minimal_obstruction_core"
            ]["first_pass_best_frontier"]
            == 691
            and syndromes["cicy6836_model186_frontier691_followup_disjoint_radius2"][
                "minimal_obstruction_core"
            ]["first_pass_best_metrics"]["min_one_higgs_doublet_support"]
            == 0
            and syndromes["cicy6836_model186_frontier691_followup_disjoint_radius2"][
                "minimal_obstruction_core"
            ]["followup_source_models"]
            == [691, 186, 139]
            and syndromes["cicy6836_model186_frontier691_followup_disjoint_radius2"][
                "minimal_obstruction_core"
            ]["followup_frontier_size"]
            == 1359
            and syndromes["cicy6836_model186_frontier691_followup_disjoint_radius2"][
                "minimal_obstruction_core"
            ]["followup_q1_candidate_count"]
            == 7
            and syndromes["cicy6836_model186_frontier691_followup_disjoint_radius2"][
                "minimal_obstruction_core"
            ]["followup_screened_candidate_count"]
            == 7
            and syndromes["cicy6836_model186_frontier691_followup_disjoint_radius2"][
                "minimal_obstruction_core"
            ]["followup_promotion_timeout_count"]
            == 0
            and syndromes["cicy6836_model186_frontier691_followup_disjoint_radius2"][
                "minimal_obstruction_core"
            ]["followup_one_higgs_proton_safe_intersection_record_count"]
            == 0
            and syndromes["cicy6836_model186_frontier691_followup_disjoint_radius2"][
                "minimal_obstruction_core"
            ]["followup_boundary_improvement_record_count"]
            == 0
            and syndromes["cicy6836_model186_frontier691_followup_disjoint_radius2"][
                "replay_counts"
            ]["prefilter_sample_passes"],
            str(report_json),
            "CICY6836 model-186 frontier-691 follow-up records a stable local floor with no one-Higgs/proton-safe intersection",
        ),
        "cicy6836_model136_existing_boundary_floor_has_replay": gate(
            syndromes["cicy6836_model136_existing_boundary_floor_radius2"][
                "geometry"
            ]
            == "CICY6836/model 136 option 23 plus frontier 691"
            and syndromes["cicy6836_model136_existing_boundary_floor_radius2"][
                "minimal_obstruction_core"
            ]["focus_model"]
            == 136
            and syndromes["cicy6836_model136_existing_boundary_floor_radius2"][
                "minimal_obstruction_core"
            ]["source_models"]
            == [136, 87, 95, 139]
            and syndromes["cicy6836_model136_existing_boundary_floor_radius2"][
                "replay_counts"
            ]["frontier_size"]
            == 2169
            and syndromes["cicy6836_model136_existing_boundary_floor_radius2"][
                "replay_counts"
            ]["q1_candidate_count"]
            == 14
            and syndromes["cicy6836_model136_existing_boundary_floor_radius2"][
                "replay_counts"
            ]["screened_candidate_count"]
            == 14
            and syndromes["cicy6836_model136_existing_boundary_floor_radius2"][
                "replay_counts"
            ]["model136_screened_count"]
            == 2
            and syndromes["cicy6836_model136_existing_boundary_floor_radius2"][
                "minimal_obstruction_core"
            ]["model136_screen_status_counts"]
            == {"all_embeddings_pre_cup_obstructed": 2}
            and syndromes["cicy6836_model136_existing_boundary_floor_radius2"][
                "replay_counts"
            ]["one_higgs_proton_safe_intersection_record_count"]
            == 0
            and syndromes["cicy6836_model136_existing_boundary_floor_radius2"][
                "replay_counts"
            ]["boundary_improvement_record_count"]
            == 11
            and syndromes["cicy6836_model136_existing_boundary_floor_radius2"][
                "replay_counts"
            ]["best_frontier"]
            == 691
            and syndromes["cicy6836_model136_existing_boundary_floor_radius2"][
                "replay_counts"
            ]["best_source_models"]
            == [95]
            and syndromes["cicy6836_model136_existing_boundary_floor_radius2"][
                "replay_counts"
            ]["one_higgs_pair_triplet_free_embeddings"]
            == 1408
            and syndromes["cicy6836_model136_existing_boundary_floor_radius2"][
                "replay_counts"
            ]["proton_safe_embeddings"]
            == 1024
            and syndromes["cicy6836_model136_existing_boundary_floor_radius2"][
                "replay_counts"
            ]["one_higgs_proton_safe_embeddings"]
            == 0
            and syndromes["cicy6836_model136_existing_boundary_floor_radius2"][
                "replay_counts"
            ]["prefilter_sample_passes"],
            str(report_json),
            "CICY6836 model-136 pass records focus obstruction and only rediscovers the frontier-691 boundary floor",
        ),
        "cicy6715_model215_computed_anchor_missing_higgs_cup_has_replay": gate(
            syndromes[
                "cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2"
            ]["geometry"]
            == "CICY6715/model 215 and 336 option 1"
            and syndromes[
                "cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2"
            ]["minimal_obstruction_core"]["focus_model"]
            == 215
            and syndromes[
                "cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2"
            ]["minimal_obstruction_core"]["source_models"]
            == [215, 336]
            and syndromes[
                "cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2"
            ]["minimal_obstruction_core"]["radius"]
            == 2
            and syndromes[
                "cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2"
            ]["minimal_obstruction_core"]["stage_counts"]
            == {
                "failed_index_target": 1022,
                "failed_no_trivial_summand": 8,
                "failed_option1_lift": 37,
                "failed_q1_no_anti10_gate": 109,
                "q1_candidate": 16,
            }
            and syndromes[
                "cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2"
            ]["replay_counts"]["frontier_size"]
            == 1192
            and syndromes[
                "cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2"
            ]["replay_counts"]["q1_candidate_count"]
            == 16
            and syndromes[
                "cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2"
            ]["replay_counts"]["screened_candidate_count"]
            == 16
            and syndromes[
                "cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2"
            ]["replay_counts"]["promotion_timeout_count"]
            == 0
            and syndromes[
                "cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2"
            ]["replay_counts"]["component_unresolved_record_count"]
            == 0
            and syndromes[
                "cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2"
            ]["replay_counts"]["total_embeddings_screened"]
            == 12288
            and syndromes[
                "cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2"
            ]["replay_counts"]["total_one_higgs_pair_triplet_free_embeddings"]
            == 0
            and syndromes[
                "cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2"
            ]["replay_counts"]["total_pre_cup_survivor_count"]
            == 0
            and syndromes[
                "cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2"
            ]["replay_counts"]["total_cup_product_eligible_triplet_target_count"]
            == 0
            and syndromes[
                "cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2"
            ]["replay_counts"]["unresolved_envelope_used_as_seed"]
            is False
            and syndromes[
                "cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2"
            ]["replay_counts"]["unresolved_envelope_remains_live"]
            is True,
            str(report_json),
            "CICY6715 model-215/336 computed anchors are closed locally without touching the live model-766 unresolved envelope",
        ),
        "cicy6715_branch99_higher_map_order_has_replay": gate(
            syndromes[
                "cicy6715_model766_branch99_higher_map_order_no_realization"
            ]["geometry"]
            == "CICY6715/model 766 option 1 branch 99"
            and syndromes[
                "cicy6715_model766_branch99_higher_map_order_no_realization"
            ]["scope_class"]
            == "candidate-specific"
            and syndromes[
                "cicy6715_model766_branch99_higher_map_order_no_realization"
            ]["minimal_obstruction_core"]["unresolved_pair"]
            == [3, 4]
            and syndromes[
                "cicy6715_model766_branch99_higher_map_order_no_realization"
            ]["minimal_obstruction_core"]["required_rank_split"]
            == {"1": 1, "a": 2, "b": 2, "ab": 2}
            and syndromes[
                "cicy6715_model766_branch99_higher_map_order_no_realization"
            ]["replay_counts"]["permutation_count_tested"]
            == 5040
            and syndromes[
                "cicy6715_model766_branch99_higher_map_order_no_realization"
            ]["replay_counts"]["complete_permutation_scan"]
            and not syndromes[
                "cicy6715_model766_branch99_higher_map_order_no_realization"
            ]["replay_counts"]["branch_representative_certified"]
            and syndromes[
                "cicy6715_model766_branch99_higher_map_order_no_realization"
            ]["replay_counts"]["pycicy_raw_rank"]
            == 7
            and syndromes[
                "cicy6715_model766_branch99_higher_map_order_no_realization"
            ]["replay_counts"]["averaged_rank"]
            == 9
            and syndromes[
                "cicy6715_model766_branch99_higher_map_order_no_realization"
            ]["replay_counts"]["prefilter_sample_passes"],
            str(report_json),
            "CICY6715 model-766 branch99 records the finite higher-map order shadow collision",
        ),
        "cicy6788_wall_breaker_has_replay": gate(
            syndromes["cicy6788_wall_breaker_one_higgs_proton_unsafe"][
                "geometry"
            ]
            == "CICY6788/model 227 and 620 option 0"
            and syndromes["cicy6788_wall_breaker_one_higgs_proton_unsafe"][
                "minimal_obstruction_core"
            ]["frontier_size"]
            == 2523
            and syndromes["cicy6788_wall_breaker_one_higgs_proton_unsafe"][
                "minimal_obstruction_core"
            ]["q1_candidate_count"]
            == 16
            and syndromes["cicy6788_wall_breaker_one_higgs_proton_unsafe"][
                "minimal_obstruction_core"
            ]["screened_candidate_count"]
            == 16
            and syndromes["cicy6788_wall_breaker_one_higgs_proton_unsafe"][
                "minimal_obstruction_core"
            ]["promoted_metric_improvement_count"]
            == 0
            and syndromes["cicy6788_wall_breaker_one_higgs_proton_unsafe"][
                "replay_counts"
            ]["total_one_higgs_pair_triplet_free_embeddings"]
            == 1536
            and syndromes["cicy6788_wall_breaker_one_higgs_proton_unsafe"][
                "replay_counts"
            ]["total_one_higgs_proton_safe_embeddings"]
            == 0
            and syndromes["cicy6788_wall_breaker_one_higgs_proton_unsafe"][
                "replay_counts"
            ]["total_pre_cup_survivor_count"]
            == 0,
            str(report_json),
            "CICY6788 wall-breaker records the one-Higgs proton-unsafe no-go",
        ),
        "cicy6784_cubic_yukawa_absent_has_replay": gate(
            syndromes["cicy6784_strict_precup_cubic_yukawa_absent"][
                "geometry"
            ]
            == "CICY6784/model 31 option 2"
            and syndromes["cicy6784_strict_precup_cubic_yukawa_absent"][
                "scope_class"
            ]
            == "candidate-specific"
            and syndromes["cicy6784_strict_precup_cubic_yukawa_absent"][
                "minimal_obstruction_core"
            ]["selected_embedding"]
            == "cicy6784_model31_option2_wilson_004"
            and syndromes["cicy6784_strict_precup_cubic_yukawa_absent"][
                "minimal_obstruction_core"
            ]["up_type_cubic_allowed_count"]
            == 0
            and syndromes["cicy6784_strict_precup_cubic_yukawa_absent"][
                "minimal_obstruction_core"
            ]["down_lepton_cubic_allowed_count"]
            == 0
            and syndromes["cicy6784_strict_precup_cubic_yukawa_absent"][
                "minimal_obstruction_core"
            ]["proton_decay_allowed_count"]
            == 0
            and syndromes["cicy6784_strict_precup_cubic_yukawa_absent"][
                "minimal_obstruction_core"
            ]["neutral_down_lepton_forbidden_reason"]
            == "wilson_line_component_character_mismatch"
            and syndromes["cicy6784_strict_precup_cubic_yukawa_absent"][
                "replay_counts"
            ]["up_type_operator_count"]
            == 2
            and syndromes["cicy6784_strict_precup_cubic_yukawa_absent"][
                "replay_counts"
            ]["down_lepton_operator_count"]
            == 15
            and syndromes["cicy6784_strict_precup_cubic_yukawa_absent"][
                "replay_counts"
            ]["higgs_bilinear_degree_one_hits"]
            == 0,
            str(report_json),
            "CICY6784 strict survivor records the cubic-Yukawa absence frontier",
        ),
        "cicy6784_higher_degree_yukawa_charge_mismatch_has_replay": gate(
            syndromes["cicy6784_higher_degree_le3_yukawa_charge_mismatch"][
                "geometry"
            ]
            == "CICY6784/model 31 option 2"
            and syndromes["cicy6784_higher_degree_le3_yukawa_charge_mismatch"][
                "scope_class"
            ]
            == "candidate-specific"
            and syndromes["cicy6784_higher_degree_le3_yukawa_charge_mismatch"][
                "minimal_obstruction_core"
            ]["selected_embedding"]
            == "cicy6784_model31_option2_wilson_004"
            and syndromes["cicy6784_higher_degree_le3_yukawa_charge_mismatch"][
                "minimal_obstruction_core"
            ]["monoid_count"]
            == 119
            and syndromes["cicy6784_higher_degree_le3_yukawa_charge_mismatch"][
                "minimal_obstruction_core"
            ]["up_type_charge_neutral_count"]
            == 0
            and syndromes["cicy6784_higher_degree_le3_yukawa_charge_mismatch"][
                "minimal_obstruction_core"
            ]["down_lepton_charge_neutral_count"]
            == 0
            and syndromes["cicy6784_higher_degree_le3_yukawa_charge_mismatch"][
                "minimal_obstruction_core"
            ]["safe_yukawa_operator_monoid_count"]
            == 0
            and syndromes["cicy6784_higher_degree_le3_yukawa_charge_mismatch"][
                "replay_counts"
            ]["up_type_operator_monoid_count"]
            == 238
            and syndromes["cicy6784_higher_degree_le3_yukawa_charge_mismatch"][
                "replay_counts"
            ]["down_lepton_operator_monoid_count"]
            == 1785
            and syndromes["cicy6784_higher_degree_le3_yukawa_charge_mismatch"][
                "replay_counts"
            ]["nearest_up_type_charge_defect"]
            == 4
            and syndromes["cicy6784_higher_degree_le3_yukawa_charge_mismatch"][
                "replay_counts"
            ]["nearest_down_lepton_charge_defect"]
            == 2,
            str(report_json),
            "CICY6784 strict survivor records the bounded degree<=3 Yukawa charge-mismatch frontier",
        ),
        "cicy6784_charge_defect_no_improvement_has_replay": gate(
            syndromes["cicy6784_radius1_charge_defect_no_improvement"][
                "geometry"
            ]
            == "CICY6784/model 31 option 2"
            and syndromes["cicy6784_radius1_charge_defect_no_improvement"][
                "scope_class"
            ]
            == "candidate-specific"
            and syndromes["cicy6784_radius1_charge_defect_no_improvement"][
                "minimal_obstruction_core"
            ]["pair_delta_radius"]
            == 1
            and syndromes["cicy6784_radius1_charge_defect_no_improvement"][
                "minimal_obstruction_core"
            ]["include_rectangles"]
            is True
            and syndromes["cicy6784_radius1_charge_defect_no_improvement"][
                "minimal_obstruction_core"
            ]["frontier_size"]
            == 130
            and syndromes["cicy6784_radius1_charge_defect_no_improvement"][
                "minimal_obstruction_core"
            ]["stage_counts"]
            == {
                "failed_index_target": 103,
                "failed_no_trivial_summand": 6,
                "failed_option2_lift": 10,
                "failed_q1_no_anti10_gate": 10,
                "q1_candidate": 1,
            }
            and syndromes["cicy6784_radius1_charge_defect_no_improvement"][
                "replay_counts"
            ]["q1_candidate_count"]
            == 1
            and syndromes["cicy6784_radius1_charge_defect_no_improvement"][
                "replay_counts"
            ]["promotion_timeout_count"]
            == 0
            and syndromes["cicy6784_radius1_charge_defect_no_improvement"][
                "replay_counts"
            ]["safe_yukawa_record_count"]
            == 0
            and syndromes["cicy6784_radius1_charge_defect_no_improvement"][
                "replay_counts"
            ]["charge_defect_improved_record_count"]
            == 0
            and syndromes["cicy6784_radius1_charge_defect_no_improvement"][
                "replay_counts"
            ]["nearest_up_type_charge_defect"]
            == 4
            and syndromes["cicy6784_radius1_charge_defect_no_improvement"][
                "replay_counts"
            ]["nearest_down_lepton_charge_defect"]
            == 2,
            str(report_json),
            "CICY6784 radius-1 charge-defect replay records no safe Yukawa and no boundary improvement",
        ),
        "cicy6784_upstream_transferred_m3_boundary_has_replay": gate(
            syndromes["cicy6784_upstream_direct_e1_requires_transferred_m3"][
                "geometry"
            ]
            == "CICY6784/model 31 option 2"
            and syndromes["cicy6784_upstream_direct_e1_requires_transferred_m3"][
                "scope_class"
            ]
            == "candidate-specific"
            and syndromes["cicy6784_upstream_direct_e1_requires_transferred_m3"][
                "minimal_obstruction_core"
            ]["target_channel"]
            == "safe_down_lepton_degree1"
            and syndromes["cicy6784_upstream_direct_e1_requires_transferred_m3"][
                "minimal_obstruction_core"
            ]["target_anchor"]
            == "5bar_04"
            and syndromes["cicy6784_upstream_direct_e1_requires_transferred_m3"][
                "minimal_obstruction_core"
            ]["top_pairing_rank"]
            == 4
            and syndromes["cicy6784_upstream_direct_e1_requires_transferred_m3"][
                "minimal_obstruction_core"
            ]["source_entries"]
            == {"10_4": [3, 4], "5bar_12": [0, 1], "S_34": [1, 2]}
            and syndromes["cicy6784_upstream_direct_e1_requires_transferred_m3"][
                "minimal_obstruction_core"
            ]["target_entry"]
            == [3, 5]
            and syndromes["cicy6784_upstream_direct_e1_requires_transferred_m3"][
                "minimal_obstruction_core"
            ]["source_koszul_degree_sum"]
            == 4
            and syndromes["cicy6784_upstream_direct_e1_requires_transferred_m3"][
                "minimal_obstruction_core"
            ]["target_koszul_degree"]
            == 3
            and syndromes["cicy6784_upstream_direct_e1_requires_transferred_m3"][
                "minimal_obstruction_core"
            ]["direct_origin_wedge_survivor_count"]
            == 0
            and syndromes["cicy6784_upstream_direct_e1_requires_transferred_m3"][
                "minimal_obstruction_core"
            ]["ten_kernel_dimension"]
            == 12
            and syndromes["cicy6784_upstream_direct_e1_requires_transferred_m3"][
                "replay_counts"
            ]["coefficient_rank_status"]
            == "pending",
            str(report_json),
            "CICY6784 upstream complement audit records the direct-E1 collision and transferred-m3 boundary",
        ),
        "cicy6784_transferred_m3_no_direct_tree_has_replay": gate(
            syndromes["cicy6784_transferred_m3_no_direct_tree_survivor"][
                "geometry"
            ]
            == "CICY6784/model 31 option 2"
            and syndromes["cicy6784_transferred_m3_no_direct_tree_survivor"][
                "scope_class"
            ]
            == "candidate-specific"
            and syndromes["cicy6784_transferred_m3_no_direct_tree_survivor"][
                "minimal_obstruction_core"
            ]["target_line_bundle"]
            == [0, -1, 3, 0]
            and syndromes["cicy6784_transferred_m3_no_direct_tree_survivor"][
                "minimal_obstruction_core"
            ]["target_cohomology"]
            == [0, 0, 4, 0]
            and syndromes["cicy6784_transferred_m3_no_direct_tree_survivor"][
                "minimal_obstruction_core"
            ]["route_count"]
            == 3
            and syndromes["cicy6784_transferred_m3_no_direct_tree_survivor"][
                "minimal_obstruction_core"
            ]["route_status_counts"]
            == {"no_homotopy_eligible_binary_direct_product": 3}
            and syndromes["cicy6784_transferred_m3_no_direct_tree_survivor"][
                "minimal_obstruction_core"
            ]["homotopy_eligible_direct_product_total"]
            == 0
            and syndromes["cicy6784_transferred_m3_no_direct_tree_survivor"][
                "minimal_obstruction_core"
            ]["final_direct_tree_survivor_total"]
            == 0
            and syndromes["cicy6784_transferred_m3_no_direct_tree_survivor"][
                "replay_counts"
            ]["coefficient_rank_status"]
            == "pending",
            str(report_json),
            "CICY6784 transferred-m3 inventory records zero homotopy-eligible direct-tree survivors",
        ),
        "cicy6784_preferred_routes_no_homotopy_seed_has_replay": gate(
            syndromes["cicy6784_preferred_effective_routes_no_homotopy_seed"][
                "geometry"
            ]
            == "CICY6784/model 31 option 2"
            and syndromes["cicy6784_preferred_effective_routes_no_homotopy_seed"][
                "scope_class"
            ]
            == "candidate-specific"
            and syndromes["cicy6784_preferred_effective_routes_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["factorization_count"]
            == 6
            and syndromes["cicy6784_preferred_effective_routes_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["priority_class_counts"]
            == {
                "direct_binary_target_without_homotopy_source": 5,
                "no_direct_binary_target": 1,
            }
            and syndromes["cicy6784_preferred_effective_routes_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["homotopy_eligible_factorization_count"]
            == 0
            and syndromes["cicy6784_preferred_effective_routes_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["direct_binary_target_factorization_count"]
            == 5
            and syndromes["cicy6784_preferred_effective_routes_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["max_direct_binary_target_pieces"]
            == 4
            and syndromes["cicy6784_preferred_effective_routes_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["best_near_boundary"]["channel_id"]
            == "safe_up_type_degree4"
            and syndromes["cicy6784_preferred_effective_routes_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["best_near_boundary"]["anchor_leg_id"]
            == "5_12",
            str(report_json),
            "CICY6784 route ranker records no homotopy-eligible seed across all preferred routes",
        ),
        "cicy6784_single_anchor_no_homotopy_seed_has_replay": gate(
            syndromes["cicy6784_single_anchor_effective_routes_no_homotopy_seed"][
                "geometry"
            ]
            == "CICY6784/model 31 option 2"
            and syndromes["cicy6784_single_anchor_effective_routes_no_homotopy_seed"][
                "scope_class"
            ]
            == "candidate-specific"
            and syndromes["cicy6784_single_anchor_effective_routes_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["single_anchor_route_count"]
            == 11
            and syndromes["cicy6784_single_anchor_effective_routes_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["selection_valid_matter_anchor_count"]
            == 6
            and syndromes["cicy6784_single_anchor_effective_routes_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["shadow_route_count"]
            == 5
            and syndromes["cicy6784_single_anchor_effective_routes_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["route_status_counts"]
            == {
                "shadow_direct_target_not_matter_anchor": 4,
                "shadow_no_seed_not_matter_anchor": 1,
                "valid_direct_target_no_homotopy_seed": 5,
                "valid_no_direct_target_no_homotopy_seed": 1,
            }
            and syndromes["cicy6784_single_anchor_effective_routes_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["homotopy_positive_route_count"]
            == 0
            and syndromes["cicy6784_single_anchor_effective_routes_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["promotable_homotopy_seed_count"]
            == 0
            and syndromes["cicy6784_single_anchor_effective_routes_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["best_valid_route"]["anchor_leg_id"]
            == "5_12"
            and syndromes["cicy6784_single_anchor_effective_routes_no_homotopy_seed"][
                "replay_counts"
            ]["single_anchor_route_queue_status"]
            == "no_promotable_homotopy_seed_in_single_anchor_frontier",
            str(report_json),
            "CICY6784 single-anchor queue records no promotable homotopy seed across valid or shadow routes",
        ),
        "cicy6784_multistage_first_pair_no_homotopy_seed_has_replay": gate(
            syndromes["cicy6784_multistage_first_pair_no_homotopy_seed"][
                "geometry"
            ]
            == "CICY6784/model 31 option 2"
            and syndromes["cicy6784_multistage_first_pair_no_homotopy_seed"][
                "scope_class"
            ]
            == "candidate-specific"
            and syndromes["cicy6784_multistage_first_pair_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["all_first_pair_slot_count"]
            == 117
            and syndromes["cicy6784_multistage_first_pair_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["valid_first_pair_slot_count"]
            == 54
            and syndromes["cicy6784_multistage_first_pair_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["valid_direct_target_first_pair_slot_count"]
            == 10
            and syndromes["cicy6784_multistage_first_pair_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["valid_homotopy_eligible_first_pair_slot_count"]
            == 0
            and syndromes["cicy6784_multistage_first_pair_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["best_valid_first_pair_boundary"]["pair"]
            == ["10_4", "S_13"]
            and syndromes["cicy6784_multistage_first_pair_no_homotopy_seed"][
                "minimal_obstruction_core"
            ]["best_valid_first_pair_boundary"]["direct_binary_product_rank_sum"]
            == 24
            and syndromes["cicy6784_multistage_first_pair_no_homotopy_seed"][
                "replay_counts"
            ]["multi_stage_direct_tree_status"]
            == "blocked_at_first_h1_h1_pair"
            and syndromes["cicy6784_multistage_first_pair_no_homotopy_seed"][
                "replay_counts"
            ]["coefficient_rank_status"]
            == "pending",
            str(report_json),
            "CICY6784 multi-stage direct-tree grammar is blocked at the first H1-H1 pair",
        ),
        "cicy6784_chain_contraction_fallback_has_replay": gate(
            syndromes[
                "cicy6784_frontier48_chain_contraction_fallback_closed_current_engine"
            ]["geometry"]
            == "CICY6784/model 31 option 2 frontier 48"
            and syndromes[
                "cicy6784_frontier48_chain_contraction_fallback_closed_current_engine"
            ]["scope_class"]
            == "candidate-specific"
            and syndromes[
                "cicy6784_frontier48_chain_contraction_fallback_closed_current_engine"
            ]["minimal_obstruction_core"]["queue_target"]
            == "CICY6784_frontier48_full_chain_contraction_fallback"
            and syndromes[
                "cicy6784_frontier48_chain_contraction_fallback_closed_current_engine"
            ]["minimal_obstruction_core"]["product_status_counts"]
            == {
                "blocked_by_origin_collision": 2,
                "no_matching_intermediate_target_piece": 3,
            }
            and syndromes[
                "cicy6784_frontier48_chain_contraction_fallback_closed_current_engine"
            ]["replay_counts"]["standard_m3_tree_count"]
            == 3
            and syndromes[
                "cicy6784_frontier48_chain_contraction_fallback_closed_current_engine"
            ]["replay_counts"]["standard_m3_matrix_rank"]
            == 0
            and not syndromes[
                "cicy6784_frontier48_chain_contraction_fallback_closed_current_engine"
            ]["replay_counts"]["has_exposed_product_plus_chain_contraction_api"]
            and syndromes[
                "cicy6784_frontier48_chain_contraction_fallback_closed_current_engine"
            ]["replay_counts"]["queue_target_closed_under_current_engine"]
            and syndromes[
                "cicy6784_frontier48_chain_contraction_fallback_closed_current_engine"
            ]["replay_counts"]["prefilter_sample_passes"],
            str(report_json),
            "CICY6784 frontier-48 exact-engine fallback records zero standard m3 and missing chain API",
        ),
        "cicy6784_radius4_local_deformation_no_first_pair_seed_has_replay": gate(
            syndromes["cicy6784_radius4_local_deformation_no_first_pair_seed"][
                "geometry"
            ]
            == "CICY6784/model 31 option 2"
            and syndromes["cicy6784_radius4_local_deformation_no_first_pair_seed"][
                "scope_class"
            ]
            == "grammar-local"
            and syndromes["cicy6784_radius4_local_deformation_no_first_pair_seed"][
                "minimal_obstruction_core"
            ]["frontier_size"]
            == 2009
            and syndromes["cicy6784_radius4_local_deformation_no_first_pair_seed"][
                "minimal_obstruction_core"
            ]["stage_counts"]
            == {
                "failed_index_target": 1853,
                "failed_no_trivial_summand": 6,
                "failed_option2_lift": 47,
                "failed_q1_no_anti10_gate": 101,
                "q1_candidate": 2,
            }
            and syndromes["cicy6784_radius4_local_deformation_no_first_pair_seed"][
                "minimal_obstruction_core"
            ]["q1_candidate_count"]
            == 2
            and syndromes["cicy6784_radius4_local_deformation_no_first_pair_seed"][
                "minimal_obstruction_core"
            ]["safe_up_down_yukawa_record_count"]
            == 1
            and syndromes["cicy6784_radius4_local_deformation_no_first_pair_seed"][
                "minimal_obstruction_core"
            ]["positive_first_pair_seed_record_count"]
            == 0
            and syndromes["cicy6784_radius4_local_deformation_no_first_pair_seed"][
                "minimal_obstruction_core"
            ]["max_valid_homotopy_eligible_first_pair_slot_count"]
            == 0
            and syndromes["cicy6784_radius4_local_deformation_no_first_pair_seed"][
                "minimal_obstruction_core"
            ]["max_valid_direct_target_first_pair_slot_count"]
            == 10
            and syndromes["cicy6784_radius4_local_deformation_no_first_pair_seed"][
                "minimal_obstruction_core"
            ]["top_ranked_record"]["frontier_index"]
            == 0
            and syndromes["cicy6784_radius4_local_deformation_no_first_pair_seed"][
                "minimal_obstruction_core"
            ]["top_ranked_record"]["safe_up_down_yukawa_selection"]
            is True
            and syndromes["cicy6784_radius4_local_deformation_no_first_pair_seed"][
                "replay_counts"
            ]["deformation_scout_status"]
            == "no_positive_first_pair_homotopy_seed_in_radius4_frontier",
            str(report_json),
            "CICY6784 radius-4 local deformation scout has q1 records but no positive first-pair homotopy seed",
        ),
        "verified_overlap_first_pair_seed_absent_has_replay": gate(
            syndromes["verified_overlap_first_pair_seed_absent"]["scope_class"]
            == "grammar-local"
            and syndromes["verified_overlap_first_pair_seed_absent"][
                "minimal_obstruction_core"
            ]["retrieval_relevant_row_count"]
            == 43
            and syndromes["verified_overlap_first_pair_seed_absent"][
                "minimal_obstruction_core"
            ]["retrieval_only_without_first_pair_reconstruction_count"]
            == 40
            and syndromes["verified_overlap_first_pair_seed_absent"][
                "minimal_obstruction_core"
            ]["exact_overlap_promoted_row_count"]
            == 3
            and syndromes["verified_overlap_first_pair_seed_absent"][
                "minimal_obstruction_core"
            ]["radius4_local_promoted_row_count"]
            == 2
            and syndromes["verified_overlap_first_pair_seed_absent"][
                "minimal_obstruction_core"
            ]["scored_record_count"]
            == 5
            and syndromes["verified_overlap_first_pair_seed_absent"][
                "minimal_obstruction_core"
            ]["first_pair_seed_status_counts"]
            == {
                "no_safe_up_down_yukawa_selection": 2,
                "safe_up_down_no_first_pair_homotopy_seed": 1,
                "safe_up_type_only_missing_down_lepton_yukawa": 2,
            }
            and syndromes["verified_overlap_first_pair_seed_absent"][
                "minimal_obstruction_core"
            ]["safe_up_down_yukawa_record_count"]
            == 1
            and syndromes["verified_overlap_first_pair_seed_absent"][
                "minimal_obstruction_core"
            ]["positive_first_pair_seed_record_count"]
            == 0
            and syndromes["verified_overlap_first_pair_seed_absent"][
                "minimal_obstruction_core"
            ]["max_valid_homotopy_eligible_first_pair_slot_count"]
            == 0
            and syndromes["verified_overlap_first_pair_seed_absent"][
                "minimal_obstruction_core"
            ]["top_ranked_record"]["model_index"]
            == "radius4_frontier_0"
            and syndromes["verified_overlap_first_pair_seed_absent"][
                "replay_counts"
            ]["first_pair_seed_scout_status"]
            == "no_positive_first_pair_seed_in_verified_overlap_queue",
            str(report_json),
            "verified overlap first-pair scout records no positive first-pair seed in the current reconstruction-authoritative queue",
        ),
        "first_pair_positive_generator_no_seed_radius4_has_replay": gate(
            syndromes["first_pair_positive_generator_no_seed_radius4"][
                "scope_class"
            ]
            == "grammar-local"
            and syndromes["first_pair_positive_generator_no_seed_radius4"][
                "minimal_obstruction_core"
            ]["seed_count"]
            == 4
            and syndromes["first_pair_positive_generator_no_seed_radius4"][
                "minimal_obstruction_core"
            ]["frontier_size"]
            == 9891
            and syndromes["first_pair_positive_generator_no_seed_radius4"][
                "minimal_obstruction_core"
            ]["stage_counts"]
            == {
                "failed_index_target": 9122,
                "failed_no_trivial_summand": 26,
                "failed_option2_lift": 178,
                "failed_q1_no_anti10_gate": 561,
                "q1_candidate": 4,
            }
            and syndromes["first_pair_positive_generator_no_seed_radius4"][
                "minimal_obstruction_core"
            ]["first_pair_seed_status_counts"]
            == {
                "no_safe_up_down_yukawa_selection": 1,
                "safe_up_down_no_first_pair_homotopy_seed": 1,
                "safe_up_type_only_missing_down_lepton_yukawa": 2,
            }
            and syndromes["first_pair_positive_generator_no_seed_radius4"][
                "minimal_obstruction_core"
            ]["safe_up_down_yukawa_record_count"]
            == 1
            and syndromes["first_pair_positive_generator_no_seed_radius4"][
                "minimal_obstruction_core"
            ]["positive_first_pair_seed_record_count"]
            == 0
            and syndromes["first_pair_positive_generator_no_seed_radius4"][
                "minimal_obstruction_core"
            ]["max_valid_homotopy_eligible_first_pair_slot_count"]
            == 0
            and syndromes["first_pair_positive_generator_no_seed_radius4"][
                "minimal_obstruction_core"
            ]["top_ranked_record"]["frontier_index"]
            == 320
            and syndromes["first_pair_positive_generator_no_seed_radius4"][
                "replay_counts"
            ]["generator_expansion_status"]
            == "no_positive_first_pair_seed_in_radius4_expansion",
            str(report_json),
            "radius-4 first-pair-positive generator expansion records no positive first-pair seed",
        ),
        "no_active_survivor_certificates": gate(
            report["summary"]["survivor_count"] == 0
            and report["survivor_certificates"] == []
            and syndromes["branch50_standard_m4_four_h1_not_cy3_top_cup"][
                "representative_examples"
            ][0]["verdict"]["branch50_killed_for_standard_cochain_m4_mass"]
            and not syndromes["branch50_standard_m4_four_h1_not_cy3_top_cup"][
                "representative_examples"
            ][0]["verdict"]["mssm_candidate_verified"],
            str(report_json),
            "the previous Branch 50 survivor is retired into the no-go atlas",
        ),
        "markdown_summarizes_atlas": gate(
            "Status: `no_go_atlas_v0_built`" in md_text
            and "syndrome_count: `48`" in md_text
            and "No Active Survivor Certificates" in md_text
            and "branch50_standard_m4_four_h1_not_cy3_top_cup"
            in md_text
            and "cicy6927_model874_s42_doublet_contamination_basin"
            in md_text
            and "cicy6927_non_s42_cup_boundary_missing_one_higgs_radius2"
            in md_text
            and "cicy6927_model252_s42_boundary_only_radius2" in md_text
            and "cicy6927_model254_s42_boundary_only_radius2" in md_text
            and "cicy6927_model369_s42_boundary_only_radius2" in md_text
            and "cicy6927_model52_s42_boundary_only_radius2" in md_text
            and "cicy6836_one_higgs_proton_safety_disjoint_radius2"
            in md_text
            and "cicy6836_model87_one_higgs_proton_safety_disjoint_radius2"
            in md_text
            and "cicy6836_model186_frontier691_followup_disjoint_radius2"
            in md_text
            and "cicy6836_model136_existing_boundary_floor_radius2" in md_text
            and "cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2"
            in md_text
            and "cicy6715_model766_branch99_higher_map_order_no_realization"
            in md_text
            and "cicy6788_wall_breaker_one_higgs_proton_unsafe"
            in md_text
            and "cicy6784_strict_precup_cubic_yukawa_absent"
            in md_text
            and "cicy6784_higher_degree_le3_yukawa_charge_mismatch"
            in md_text
            and "cicy6784_radius1_charge_defect_no_improvement"
            in md_text
            and "cicy6784_upstream_direct_e1_requires_transferred_m3"
            in md_text
            and "cicy6784_transferred_m3_no_direct_tree_survivor"
            in md_text
            and "cicy6784_preferred_effective_routes_no_homotopy_seed"
            in md_text
            and "cicy6784_single_anchor_effective_routes_no_homotopy_seed"
            in md_text
            and "cicy6784_multistage_first_pair_no_homotopy_seed"
            in md_text
            and "cicy6784_frontier48_chain_contraction_fallback_closed_current_engine"
            in md_text
            and "cicy4185_7910_split_action_lift_missing_current_data"
            in md_text
            and "cicy6187_7899_split_action_lift_missing_current_data"
            in md_text
            and "cicy6201_7900_split_action_lift_missing_current_data"
            in md_text
            and "cicy6281_7904_split_action_lift_missing_current_data"
            in md_text
            and "cicy4078_7908_split_action_lift_missing_current_data"
            in md_text
            and "cicy5141_7912_split_action_lift_missing_current_data"
            in md_text
            and "cicy5248_7913_split_action_lift_missing_current_data"
            in md_text
            and "cicy5406_7918_split_action_lift_missing_current_data"
            in md_text
            and "cicy5449_no_direct_split_witness_current_data"
            in md_text
            and "cicy7810_no_direct_split_witness_current_data"
            in md_text
            and "cicy5302_gutall_benchmark_pool_engine_gap_current_data"
            in md_text
            and "cicy5256_gutall_benchmark_pool_engine_gap_current_data"
            in md_text
            and "cicy5273_gutall_benchmark_pool_raw_action_gap_current_data"
            in md_text
            and "cicy6738_gutall_benchmark_pool_raw_action_gap_current_data"
            in md_text
            and "cicy5425_gutall_benchmark_pool_raw_action_gap_current_data"
            in md_text
            and "cicy6784_radius4_local_deformation_no_first_pair_seed"
            in md_text
            and "verified_overlap_first_pair_seed_absent" in md_text
            and "first_pair_positive_generator_no_seed_radius4" in md_text
            and "geometry_no_recorded_free_symmetry" in md_text
            and "z2xz2_regular_vectorlike_excess_7484" in md_text,
            str(report_md),
            "markdown exposes atlas summary, 2544/7484 syndromes, and Branch 50 no-go control",
        ),
    }
    return {
        "scope": "verification for No-Go Atlas v0",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json",
        default=str(REPORTS / "no_go_atlas_v0.json"),
    )
    parser.add_argument(
        "--report-md",
        default=str(REPORTS / "no_go_atlas_v0.md"),
    )
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "no_go_atlas_v0_verification.json"),
    )
    args = parser.parse_args()
    result = verify(report_json=Path(args.report_json), report_md=Path(args.report_md))
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
