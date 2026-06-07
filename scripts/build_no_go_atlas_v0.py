#!/usr/bin/env python3
"""Build the No-Go Atlas v0.

The atlas compresses verified failed searches into scoped obstruction
syndromes and executable cheap prefilters.  Candidate breadcrumbs that fail a
later algebraic gate are preserved as negative controls, not survivors.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
LATENT_REPORTS = ROOT / "experiments" / "latent_atlas" / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from no_go_atlas_prefilters import (  # noqa: E402
    describe_prefilters,
    evaluate_prefilter,
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def artifact(name: str) -> Path:
    return REPORTS / name


def latent_artifact(name: str) -> Path:
    return LATENT_REPORTS / name


def verified_artifacts() -> dict[str, Path]:
    return {
        "degree_aware_main": artifact(
            "phenomenology_guided_q1_radius9_degree_aware_main_frontier_search_verification.json"
        ),
        "representative_first": artifact(
            "phenomenology_guided_q1_radius9_representative_first_degree_aware_search_verification.json"
        ),
        "physical_5bar_first": artifact(
            "phenomenology_guided_q1_radius9_physical_5bar_first_search_verification.json"
        ),
        "intersection_forcing": artifact(
            "phenomenology_guided_q1_radius9_intersection_forcing_search_verification.json"
        ),
        "higher_degree_intersection": artifact(
            "phenomenology_guided_q1_radius9_higher_degree_intersection_search_verification.json"
        ),
        "higher_degree_candidate_dossier": artifact(
            "phenomenology_guided_q1_radius9_higher_degree_candidate_dossier_verification.json"
        ),
        "higher_order_mass_proxy": artifact(
            "phenomenology_guided_q1_radius9_higher_order_mass_map_probe_verification.json"
        ),
        "branch50_quartic_scalar_attempt": artifact(
            "phenomenology_guided_q1_radius9_quartic_scalar_attempt_verification.json"
        ),
        "branch50_m4_degree": artifact(
            "phenomenology_guided_q1_radius9_homotopy_transfer_degree_audit_verification.json"
        ),
        "cubic_top_cup_first": artifact(
            "phenomenology_guided_q1_radius9_cubic_top_cup_first_search_verification.json"
        ),
        "cicy5259_quotient": artifact("cicy5259_quotient_wilson_line_verification.json"),
        "outside_regime_free_symmetry": artifact(
            "outside_regime_free_symmetry_no_go_verification.json"
        ),
        "cicy6927_model874_doublet_escape": artifact(
            "cicy6927_model874_doublet_escape_search_verification.json"
        ),
        "model874_latent_atlas": latent_artifact(
            "cicy6927_model874_latent_atlas_verification.json"
        ),
        "model874_latent_guided": latent_artifact(
            "cicy6927_model874_latent_guided_escape_search_verification.json"
        ),
        "model874_latent_compensated": latent_artifact(
            "cicy6927_model874_latent_compensated_escape_search_verification.json"
        ),
        "model874_timeout_closure": latent_artifact(
            "cicy6927_model874_latent_timeout_closure_verification.json"
        ),
        "cicy6927_non_s42_cup_to_one_higgs": latent_artifact(
            "cicy6927_non_s42_cup_to_one_higgs_search_verification.json"
        ),
        "cicy6927_model252_intersection_forcing": latent_artifact(
            "cicy6927_model252_intersection_forcing_search_verification.json"
        ),
        "cicy6927_model254_intersection_forcing": latent_artifact(
            "cicy6927_model254_intersection_forcing_search_verification.json"
        ),
        "cicy6927_model369_intersection_forcing": latent_artifact(
            "cicy6927_model369_intersection_forcing_search_verification.json"
        ),
        "cicy6927_model52_intersection_forcing": latent_artifact(
            "cicy6927_model52_intersection_forcing_search_verification.json"
        ),
        "cicy6836_one_higgs_proton_intersection": latent_artifact(
            "cicy6836_one_higgs_proton_intersection_search_verification.json"
        ),
        "cicy6836_model87_intersection_forcing": latent_artifact(
            "cicy6836_model87_intersection_forcing_search_verification.json"
        ),
        "cicy6836_model186_intersection_forcing": latent_artifact(
            "cicy6836_model186_intersection_forcing_search_verification.json"
        ),
        "cicy6836_model186_frontier691_followup": latent_artifact(
            "cicy6836_model186_frontier691_followup_search_verification.json"
        ),
        "cicy6836_model136_intersection_forcing": latent_artifact(
            "cicy6836_model136_intersection_forcing_search_verification.json"
        ),
        "cicy6715_6927_lateral_wall_metric": artifact(
            "cicy6715_6927_same_hodge_lateral_wall_metric_pass_verification.json"
        ),
        "cicy6715_component_unresolved_envelope": artifact(
            "cicy6715_component_unresolved_envelope_verification.json"
        ),
        "cicy6715_model215_intersection_forcing": latent_artifact(
            "cicy6715_model215_intersection_forcing_search_verification.json"
        ),
        "cicy6715_branch99_resolution": latent_artifact(
            "cicy6715_model766_branch99_representative_resolution_verification.json"
        ),
        "overlap_first_seed_queue": latent_artifact(
            "overlap_first_seed_queue_verification.json"
        ),
        "cicy6788_wall_breaker": artifact(
            "cicy6788_obstruction_targeted_wall_breaker_search_verification.json"
        ),
        "cicy6784_operator_yukawa_frontier": artifact(
            "cicy6784_model31_operator_yukawa_frontier_verification.json"
        ),
        "cicy6784_higher_degree_yukawa": artifact(
            "cicy6784_model31_higher_degree_yukawa_search_verification.json"
        ),
        "cicy6784_charge_defect_escape": artifact(
            "cicy6784_charge_defect_guided_yukawa_escape_search_verification.json"
        ),
        "cicy6784_upstream_complement_map": artifact(
            "cicy6784_upstream_complement_map_audit_verification.json"
        ),
        "cicy6784_transferred_m3_route_inventory": artifact(
            "cicy6784_transferred_m3_route_inventory_verification.json"
        ),
        "cicy6784_effective_complement_route_ranker": artifact(
            "cicy6784_effective_complement_route_ranker_verification.json"
        ),
        "cicy6784_single_anchor_homotopy_seed_queue": artifact(
            "cicy6784_single_anchor_homotopy_seed_queue_verification.json"
        ),
        "cicy6784_multistage_homotopy_seed_closure": artifact(
            "cicy6784_multistage_homotopy_seed_closure_verification.json"
        ),
        "cicy6784_chain_contraction_fallback": artifact(
            "cicy6784_frontier48_chain_contraction_fallback_verification.json"
        ),
        "cicy4185_bridge_lift_audit": latent_artifact(
            "cicy4185_bridge_lift_audit_verification.json"
        ),
        "cicy6187_bridge_lift_audit": latent_artifact(
            "cicy6187_bridge_lift_audit_verification.json"
        ),
        "cicy6201_bridge_lift_audit": latent_artifact(
            "cicy6201_bridge_lift_audit_verification.json"
        ),
        "cicy6281_bridge_lift_audit": latent_artifact(
            "cicy6281_bridge_lift_audit_verification.json"
        ),
        "cicy4078_bridge_lift_audit": latent_artifact(
            "cicy4078_bridge_lift_audit_verification.json"
        ),
        "cicy5141_bridge_lift_audit": latent_artifact(
            "cicy5141_bridge_lift_audit_verification.json"
        ),
        "cicy5248_bridge_action_transfer_audit": latent_artifact(
            "cicy5248_bridge_action_transfer_audit_verification.json"
        ),
        "cicy5406_bridge_action_transfer_audit": latent_artifact(
            "cicy5406_bridge_action_transfer_audit_verification.json"
        ),
        "cicy5449_bridge_action_transfer_audit": latent_artifact(
            "cicy5449_bridge_action_transfer_audit_verification.json"
        ),
        "cicy7810_bridge_action_transfer_audit": latent_artifact(
            "cicy7810_bridge_action_transfer_audit_verification.json"
        ),
        "cicy5302_gutall_benchmark_pool_engine_audit": latent_artifact(
            "cicy5302_gutall_benchmark_pool_engine_audit_verification.json"
        ),
        "cicy5273_gutall_benchmark_pool_engine_audit": latent_artifact(
            "cicy5273_gutall_benchmark_pool_engine_audit_verification.json"
        ),
        "cicy6738_gutall_benchmark_pool_engine_audit": latent_artifact(
            "cicy6738_gutall_benchmark_pool_engine_audit_verification.json"
        ),
        "cicy5425_gutall_benchmark_pool_engine_audit": latent_artifact(
            "cicy5425_gutall_benchmark_pool_engine_audit_verification.json"
        ),
        "cicy5256_gutall_benchmark_pool_engine_audit": latent_artifact(
            "cicy5256_gutall_benchmark_pool_engine_audit_verification.json"
        ),
        "cicy6784_radius4_first_pair_seed_scout": artifact(
            "cicy6784_radius4_first_pair_seed_scout_verification.json"
        ),
        "verified_overlap_first_pair_seed_scout": latent_artifact(
            "verified_overlap_first_pair_seed_scout_verification.json"
        ),
        "first_pair_positive_generator_expansion": latent_artifact(
            "first_pair_positive_generator_expansion_verification.json"
        ),
    }


def all_verifications_pass(paths: dict[str, Path]) -> bool:
    return all(path.exists() and load_json(path).get("all_gates_pass") for path in paths.values())


def syndrome(
    *,
    syndrome_id: str,
    title: str,
    geometry: str,
    scope_class: str,
    claim_scope: str,
    stage: str,
    minimal_obstruction_core: dict[str, Any],
    cheap_prefilter: str,
    replay_counts: dict[str, Any],
    evidence_artifacts: list[str],
    representative_examples: list[dict[str, Any]],
    nearest_escape: dict[str, Any],
) -> dict[str, Any]:
    return {
        "syndrome_id": syndrome_id,
        "title": title,
        "geometry": geometry,
        "scope_class": scope_class,
        "claim_scope": claim_scope,
        "stage": stage,
        "minimal_obstruction_core": minimal_obstruction_core,
        "cheap_prefilter": {
            "prefilter_id": cheap_prefilter,
            **describe_prefilters()[cheap_prefilter],
        },
        "replay_counts": replay_counts,
        "evidence_artifacts": evidence_artifacts,
        "representative_examples": representative_examples,
        "nearest_escape_or_boundary": nearest_escape,
    }


def outside_regime_syndrome() -> dict[str, Any]:
    no_go = load_json(artifact("outside_regime_free_symmetry_no_go.json"))
    higgs = load_json(artifact("outside_regime_higgs_candidate_certificate.json"))
    target_rows = no_go["favourable_geometry_gate_table"]
    row_2544 = next(row for row in target_rows if row["num"] == 2544)
    wilson = higgs["wilson_line_applicability"]
    return syndrome(
        syndrome_id="geometry_no_recorded_free_symmetry",
        title="Clean upstairs SU(5), but no recorded free action for Wilson-line descent",
        geometry="CICY2544",
        scope_class="geometry-local",
        claim_scope=(
            "Current cicylist.m recorded-symmetry data for favourable h11>=7 targets; "
            "not a theorem that CICY2544 admits no free action in any presentation."
        ),
        stage="geometry_selection_for_wilson_line",
        minimal_obstruction_core={
            "candidate_label": higgs["construction"]["label"],
            "upstairs_spectrum": higgs["spectrum"],
            "regular_nontrivial_quality": higgs["quality"],
            "raw_free_symmetry_option_count": wilson["raw_free_symmetry_option_count"],
            "wilson_line_descent_applicable_from_recorded_raw_symmetry": wilson[
                "wilson_line_descent_applicable_from_recorded_raw_symmetry"
            ],
            "first_failing_gate": row_2544[
                "first_failing_gate_for_quotient_compatible_goal"
            ],
        },
        cheap_prefilter="no_recorded_free_symmetry",
        replay_counts={
            "source": "reports/outside_regime_free_symmetry_no_go.json",
            "favourable_h11_ge_7_known_symmetry_rows": len(target_rows),
            "rows_with_no_recorded_free_symmetry": sum(
                1 for row in target_rows if row["free_symmetry_option_count"] == 0
            ),
            "cicy2544_free_symmetry_option_count": row_2544[
                "free_symmetry_option_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "no_recorded_free_symmetry",
                {
                    "requires_wilson_line_descent": True,
                    "free_symmetry_option_count": row_2544[
                        "free_symmetry_option_count"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "reports/outside_regime_higgs_candidate_certificate.json",
            "reports/outside_regime_free_symmetry_no_go.json",
            "reports/outside_regime_free_symmetry_no_go_verification.json",
        ],
        representative_examples=[
            {
                "cicy": 2544,
                "label": higgs["construction"]["label"],
                "spectrum": higgs["spectrum"],
                "first_failing_gate": row_2544[
                    "first_failing_gate_for_quotient_compatible_goal"
                ],
            }
        ],
        nearest_escape={
            "minimal_change": "supply a verified free action, or move to a quotient-compatible geometry/presentation",
            "would_promote_to": "Wilson-line character descent audit",
        },
    )


def cicy5259_vectorlike_syndrome() -> dict[str, Any]:
    report = load_json(artifact("cicy5259_quotient_wilson_line_report.json"))
    embedding = report["wilson_line_enumeration"]["admissible_nontrivial_embeddings"][0]
    sectors = embedding["fivebar_and_five_sector"]
    return syndrome(
        syndrome_id="z2_regular_vectorlike_excess_5259_7914",
        title="Certified quotient lift, but regular H2(wedge2 V) gives five vectorlike pairs",
        geometry="CICY5259 via favourable split 7914",
        scope_class="presentation-local",
        claim_scope=(
            "Selected recorded CICY5259 free Z2 action option 0, lifted through the "
            "7914 ineffective split, for the zero-extended bundle in this certificate."
        ),
        stage="wilson_line_character_projection",
        minimal_obstruction_core={
            "split_action_lift_certified": report["conclusion"][
                "split_action_lift_certified"
            ],
            "line_bundle_equivariance_certified": report["conclusion"][
                "line_bundle_equivariance_certified"
            ],
            "H1_V_regular_multiplicity": report["equivariant_cohomology_characters"][
                "V"
            ]["cohomology_characters"]["H1"]["regular_multiplicity"],
            "H1_wedge2_V_regular_multiplicity": report[
                "equivariant_cohomology_characters"
            ]["wedge2_V"]["cohomology_characters"]["H1"][
                "regular_multiplicity"
            ],
            "H2_wedge2_V_regular_multiplicity": report[
                "equivariant_cohomology_characters"
            ]["wedge2_V"]["cohomology_characters"]["H2"][
                "regular_multiplicity"
            ],
            "colored_triplet_vectorlike_pairs": sectors[
                "colored_triplet_vectorlike_pairs"
            ],
            "electroweak_doublet_vectorlike_pairs": sectors[
                "electroweak_doublet_vectorlike_pairs"
            ],
        },
        cheap_prefilter="vectorlike_excess",
        replay_counts={
            "source": "reports/cicy5259_quotient_wilson_line_report.json",
            "admissible_nontrivial_embeddings": len(
                report["wilson_line_enumeration"]["admissible_nontrivial_embeddings"]
            ),
            "standard_model_like_embeddings": sum(
                1
                for item in report["wilson_line_enumeration"][
                    "admissible_nontrivial_embeddings"
                ]
                if item["standard_model_like"]
            ),
            "prefilter_sample_passes": evaluate_prefilter(
                "vectorlike_excess",
                {
                    "actual_per_character_pair": [
                        sectors["dbar_triplets_from_H1_wedge2V"],
                        sectors["triplets_from_H2_wedge2V"],
                    ],
                    "allowed_pairs": [[3, 0], [4, 1]],
                    "max_vectorlike_pairs": 1,
                },
            ),
        },
        evidence_artifacts=[
            "reports/cicy5259_quotient_wilson_line_report.json",
            "reports/cicy5259_quotient_wilson_line_verification.json",
        ],
        representative_examples=[
            {
                "wilson_line": embedding["label"],
                "fivebar_and_five_sector": sectors,
                "obstruction": embedding["obstruction"],
            }
        ],
        nearest_escape={
            "minimal_change": "lower H2(wedge2 V) regular multiplicity from 5 to 1 or 0 while preserving q=1 and quotient lift",
            "historical_boundary": "the later radius-9 branch-50 search achieves one vectorlike pair only after moving to a different local bundle branch and higher-degree monoid support",
        },
    )


def cicy7484_vectorlike_syndrome() -> dict[str, Any]:
    best = load_json(artifact("best_candidate_certificate.json"))
    selected = load_json(artifact("cicy7484_selected_kappa_zero_allowed_bound15.json"))
    pair_deformations = load_json(artifact("cicy7484_pair_deformations_delta12_n5.json"))
    actual_certificate = selected["best_candidate"][
        "conditional_order4_descent_constraints"
    ]["actual_z2xz2_wedge2_character_certificate"]
    return syndrome(
        syndrome_id="z2xz2_regular_vectorlike_excess_7484",
        title="Quotient-compatible 7484 descent works, but character-certified vectorlike content is too large",
        geometry="CICY7484",
        scope_class="grammar-local",
        claim_scope=(
            "CICY7484 kappa-plane and local deformation searches recorded in the "
            "current artifacts; not a global no-go for all 7484 bundles."
        ),
        stage="order4_wilson_line_character_projection",
        minimal_obstruction_core={
            "best_label": best["construction"]["label"],
            "symmetry_order": best["construction"]["symmetry_order"],
            "upstairs_spectrum": best["spectrum"],
            "best_actual_per_character_pair": best["spectrum"][
                "actual_per_character_pair"
            ],
            "h1_regular_multiplicity": actual_certificate[
                "h1_regular_multiplicity"
            ],
            "h2_regular_multiplicity": actual_certificate[
                "h2_regular_multiplicity"
            ],
            "trivial_summand_count": best["quality_caveat"][
                "trivial_summand_count"
            ],
        },
        cheap_prefilter="vectorlike_excess",
        replay_counts={
            "source": "reports/cicy7484_selected_kappa_zero_allowed_bound15.json",
            "selected_zero_allowed_spectrum_lift_count": selected["search"][
                "spectrum_lift_count"
            ],
            "actual_character_count": selected["search"]["actual_character_count"],
            "has_actual_three_family_no_vectorlike_pair": best[
                "comparison_evidence"
            ]["zero_allowed_selected_bound15"][
                "has_actual_three_family_no_vectorlike_pair"
            ],
            "has_actual_one_higgs_pair_without_triplets": best[
                "comparison_evidence"
            ]["zero_allowed_selected_bound15"][
                "has_actual_one_higgs_pair_without_triplets"
            ],
            "local_best_zero_allowed_pair": pair_deformations[
                "best_zero_allowed_candidate"
            ]["actual_wedge2_character_certificate"]["best_per_character_pair"],
            "local_best_nontrivial_pair": pair_deformations[
                "best_nontrivial_candidate"
            ]["actual_wedge2_character_certificate"]["best_per_character_pair"],
            "prefilter_sample_passes": evaluate_prefilter(
                "vectorlike_excess",
                {
                    "actual_per_character_pair": best["spectrum"][
                        "actual_per_character_pair"
                    ],
                    "allowed_pairs": [[3, 0], [4, 1]],
                    "max_vectorlike_pairs": 1,
                },
            ),
        },
        evidence_artifacts=[
            "reports/best_candidate_certificate.json",
            "reports/cicy7484_selected_kappa_zero_allowed_bound15.json",
            "reports/cicy7484_pair_deformations_delta12_n5.json",
        ],
        representative_examples=[
            {
                "label": best["construction"]["label"],
                "actual_per_character_pair": best["spectrum"][
                    "actual_per_character_pair"
                ],
                "quality_caveat": best["quality_caveat"],
            }
        ],
        nearest_escape={
            "minimal_change": "find a character-certified 7484 branch with per-character pair [4,1] or [3,0] and no trivial-summand caveat",
            "known_frontier": "local pair deformations to delta12 still bottom out at [6,3] for zero-allowed and [9,6] for nontrivial regular candidates",
        },
    )


def degree_zero_top_cup_syndrome() -> dict[str, Any]:
    main = load_json(artifact("phenomenology_guided_q1_radius9_degree_aware_main_frontier_search.json"))
    probe = load_json(artifact("phenomenology_guided_q1_radius9_realized_lead_mass_rank_probe.json"))
    audit = probe["exact_cup_product_degree_audit"]
    return syndrome(
        syndrome_id="degree_zero_bilinear_not_cy3_top_cup",
        title="Charge-neutral bilinear shadow misses CY3 top degree",
        geometry="CICY5259 via favourable split 7914",
        scope_class="global-looking",
        claim_scope=(
            "The cohomological-degree rule is CY3-general for ordinary cup products; "
            "the replay counts are only for the represented radius-9 5259/7914 frontier."
        ),
        stage="top_degree_superpotential_gate",
        minimal_obstruction_core={
            "candidate": probe["candidate"]["label"],
            "operator": probe["operator"]["label"],
            "listed_monomial_degree_counts": probe["operator"][
                "listed_monomial_degree_counts"
            ],
            "direct_total_cohomological_degree": audit[
                "direct_total_cohomological_degree"
            ],
            "direct_target_group": audit["direct_target_group"],
            "top_target_group": audit["top_target_group"],
            "has_required_degree_one_neutral_singlet_hit": audit[
                "has_required_degree_one_neutral_singlet_hit"
            ],
            "verdict": probe["verdict"],
        },
        cheap_prefilter="degree_zero_bilinear_not_top_cup",
        replay_counts={
            "source": "reports/phenomenology_guided_q1_radius9_degree_aware_main_frontier_search.json",
            "records_scanned": main["summary"]["records_scanned"],
            "represented_q1_weight": main["summary"]["represented_q1_weight"],
            "degree_zero_bilinear_rows": main["summary"]["final_status_rows"][
                "degree_zero_bilinear_not_top_cup_product"
            ],
            "degree_zero_bilinear_weight": main["summary"]["final_status_weight"][
                "degree_zero_bilinear_not_top_cup_product"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "degree_zero_bilinear_not_top_cup",
                {
                    "monomial_degree": 0,
                    "direct_total_cohomological_degree": audit[
                        "direct_total_cohomological_degree"
                    ],
                    "direct_target_group": audit["direct_target_group"]["sector"],
                    "direct_target_dimension": audit["direct_target_group"][
                        "cohomology_dimension"
                    ],
                    "required_singlet_degree_for_top_cubic": audit[
                        "required_singlet_degree_for_top_cubic"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "reports/phenomenology_guided_q1_radius9_realized_lead_mass_rank_probe.json",
            "reports/phenomenology_guided_q1_radius9_realized_lead_mass_rank_probe_verification.json",
            "reports/phenomenology_guided_q1_radius9_degree_aware_main_frontier_search.json",
        ],
        representative_examples=[
            {
                "candidate": probe["candidate"]["label"],
                "operator": probe["operator"]["label"],
                "obstruction": probe["verdict"]["obstruction"],
                "reason": probe["verdict"]["reason"],
            }
        ],
        nearest_escape={
            "minimal_change": "add a neutralizing H1 singlet insertion so the ordinary product lands in H3(O_X)",
            "followup_result": "degree-aware replay found 333 selection survivors with degree-one support, but all failed representative realizability",
        },
    )


def representative_mismatch_syndrome() -> dict[str, Any]:
    rep = load_json(artifact("phenomenology_guided_q1_radius9_representative_first_degree_aware_search.json"))
    example = rep["obstruction_grammar"]["minimal_cluster_examples"][
        "leg_type:physical_5bar_H1"
    ]
    first_failure = rep["degree_aware_failure_records"][0]["first_failure"]
    return syndrome(
        syndrome_id="physical_5bar_representative_character_mismatch",
        title="Triplet-only branch character asks for +2/-0, but representatives give +1/-1",
        geometry="CICY5259 via favourable split 7914",
        scope_class="grammar-local",
        claim_scope="Current represented radius-9 q=1 5259/7914 frontier with degree-one top-cup target grammar.",
        stage="representative_realizability_gate",
        minimal_obstruction_core={
            "leg_type": example["leg_type"],
            "role": example["role"],
            "requested": example["requested"],
            "computed": example["computed"],
            "reason": example["reason"],
            "required_image_ranks_for_branch": first_failure[
                "required_image_ranks_for_branch"
            ],
            "required_image_ranks_feasible": first_failure[
                "required_image_ranks_feasible"
            ],
            "source_dimension": first_failure["source_dimension"],
        },
        cheap_prefilter="representative_character_mismatch",
        replay_counts={
            "source": "reports/phenomenology_guided_q1_radius9_representative_first_degree_aware_search.json",
            "degree_aware_failure_records": rep["summary"][
                "degree_aware_failure_records"
            ],
            "degree_aware_failure_weight": rep["summary"]["degree_aware_failure_weight"],
            "representative_first_template_records": rep["summary"][
                "representative_first_template_records"
            ],
            "representative_first_template_weight": rep["summary"][
                "representative_first_template_weight"
            ],
            "representative_compatible_template_records": rep["summary"][
                "representative_compatible_template_records"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "representative_character_mismatch",
                {
                    "leg_type": example["leg_type"],
                    "requested_multiplicities": example["requested"][
                        "multiplicities"
                    ],
                    "computed_multiplicities": example["computed"][
                        "multiplicities"
                    ],
                    "representative_status": "representative_obstructed",
                },
            ),
        },
        evidence_artifacts=[
            "reports/phenomenology_guided_q1_radius9_representative_first_degree_aware_search.json",
            "reports/phenomenology_guided_q1_radius9_representative_first_degree_aware_search_verification.json",
        ],
        representative_examples=[example],
        nearest_escape={
            "minimal_change": "seed generator with representative-compatible physical 5bar H1 templates before asking for triplet-only mass support",
            "followup_result": "physical-5bar-first replay found representative-compatible 5bar sectors, but degree-one triplet-only operators did not intersect them",
        },
    )


def degree_one_intersection_syndrome() -> dict[str, Any]:
    intersection = load_json(artifact("phenomenology_guided_q1_radius9_intersection_forcing_search.json"))
    example = intersection["minimal_forced_operator_examples"][
        "doublet_support_obstruction"
    ]
    return syndrome(
        syndrome_id="degree_one_representative_intersection_not_triplet_only",
        title="Representative-compatible degree-one intersections fail triplet-only DT separation",
        geometry="CICY5259 via favourable split 7914",
        scope_class="grammar-local",
        claim_scope="Current represented radius-9 q=1 5259/7914 frontier with representative-compatible physical 5bar seeding and degree-one singlet insertion.",
        stage="degree_one_intersection_forcing_gate",
        minimal_obstruction_core={
            "representative_compatible_physical_5bar_template_rows": intersection[
                "summary"
            ]["representative_compatible_physical_5bar_template_rows"],
            "intersection_forced_operator_records": intersection["summary"][
                "intersection_forced_operator_records"
            ],
            "forced_support_class_rows": intersection["summary"][
                "forced_support_class_rows"
            ],
            "doublet_example": {
                "candidate_label": example["candidate_label"],
                "operator": example["operator"],
                "singlet_hits": example["degree_one_singlet_hits"],
                "triplet_pair_support": example["triplet_pair_support"],
                "doublet_pair_support": example["doublet_pair_support"],
            },
        },
        cheap_prefilter="degree_one_doublet_triplet_inseparable",
        replay_counts={
            "source": "reports/phenomenology_guided_q1_radius9_intersection_forcing_search.json",
            "records_scanned": intersection["summary"]["records_scanned"],
            "intersection_forced_operator_records": intersection["summary"][
                "intersection_forced_operator_records"
            ],
            "doublet_support_obstruction_rows": intersection["summary"][
                "forced_operator_status_rows"
            ]["doublet_support_obstruction"],
            "cup_product_eligible_records": intersection["summary"][
                "cup_product_eligible_intersection_forced_records"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "degree_one_doublet_triplet_inseparable",
                {
                    "singlet_degree": 1,
                    "triplet_pair_support": example["triplet_pair_support"],
                    "doublet_pair_support": example["doublet_pair_support"],
                },
            ),
        },
        evidence_artifacts=[
            "reports/phenomenology_guided_q1_radius9_intersection_forcing_search.json",
            "reports/phenomenology_guided_q1_radius9_intersection_forcing_search_verification.json",
        ],
        representative_examples=[
            intersection["minimal_forced_operator_examples"][key]
            for key in [
                "doublet_support_obstruction",
                "degree_one_singlet_character_not_invariant",
                "no_degree_one_charge_neutral_singlet",
            ]
        ],
        nearest_escape={
            "minimal_change": "allow higher-degree singlet monoids while retaining representative-compatible 5bar/cup-5 and proton safety",
            "followup_result": "degree <=3 monoids produced 136 representative-compatible higher-degree selection candidates",
        },
    )


def higher_degree_downstream_syndrome() -> dict[str, Any]:
    higher = load_json(artifact("phenomenology_guided_q1_radius9_higher_degree_intersection_search.json"))
    obstructed_statuses = {
        key: value
        for key, value in higher["summary"]["operator_status_rows"].items()
        if key != "higher_monoid_representative_compatible_candidate"
    }
    return syndrome(
        syndrome_id="higher_degree_monoid_downstream_obstructions",
        title="Higher-degree monoids reopen the corridor, but most operators still die at downstream gates",
        geometry="CICY5259 via favourable split 7914",
        scope_class="grammar-local",
        claim_scope="Degree <=3 singlet-monoid replay of the represented radius-9 q=1 5259/7914 frontier.",
        stage="higher_degree_monoid_selection_gate",
        minimal_obstruction_core={
            "max_singlet_monoid_degree": higher["summary"][
                "max_singlet_monoid_degree"
            ],
            "operator_status_rows": higher["summary"]["operator_status_rows"],
            "candidate_compatible_monomial_degrees_rows": higher["summary"][
                "candidate_compatible_monomial_degrees_rows"
            ],
            "simple_cy3_cubic_top_cup_eligible_records": higher["summary"][
                "simple_cy3_cubic_top_cup_eligible_records"
            ],
        },
        cheap_prefilter="higher_monoid_downstream_obstructed",
        replay_counts={
            "source": "reports/phenomenology_guided_q1_radius9_higher_degree_intersection_search.json",
            "higher_degree_forced_operator_records": higher["summary"][
                "higher_degree_forced_operator_records"
            ],
            "downstream_obstructed_operator_records": sum(
                obstructed_statuses.values()
            ),
            "representative_candidate_records": higher["summary"][
                "higher_monoid_representative_candidate_records"
            ],
            "degree2_candidate_records": higher["summary"][
                "candidate_compatible_monomial_degrees_rows"
            ].get("2", 0),
            "degree3_candidate_records": higher["summary"][
                "candidate_compatible_monomial_degrees_rows"
            ].get("3", 0),
            "prefilter_sample_passes": evaluate_prefilter(
                "higher_monoid_downstream_obstructed",
                {"status": "higher_monoid_triplet_only_proton_safe_but_cup_5_unrealizable"},
            ),
        },
        evidence_artifacts=[
            "reports/phenomenology_guided_q1_radius9_higher_degree_intersection_search.json",
            "reports/phenomenology_guided_q1_radius9_higher_degree_intersection_search_verification.json",
        ],
        representative_examples=[
            higher["minimal_operator_examples"][key]
            for key in [
                "higher_monoid_doublet_support_obstruction",
                "higher_monoid_triplet_only_but_proton_unprotected",
                "higher_monoid_triplet_only_proton_safe_but_cup_5_unrealizable",
                "higher_monoid_representative_compatible_candidate",
            ]
        ],
        nearest_escape={
            "minimal_change": "select the representative-compatible candidate status and then compute the pending higher-order mass map",
            "followup_result": "branch radius6_broad_adjacency_filtered_10_branch_50 was later reclassified as a standard m4 degree-law negative control",
        },
    )


def branch50_standard_m4_syndrome() -> dict[str, Any]:
    audit = load_json(artifact("phenomenology_guided_q1_radius9_homotopy_transfer_degree_audit.json"))
    quartic = load_json(artifact("phenomenology_guided_q1_radius9_quartic_scalar_attempt.json"))
    proxy = load_json(artifact("phenomenology_guided_q1_radius9_higher_order_mass_map_probe.json"))
    degree_law = audit["standard_homotopy_transfer_degree_law"]
    direct_audit = quartic["direct_chain_product_audit"]
    return syndrome(
        syndrome_id="branch50_standard_m4_four_h1_not_cy3_top_cup",
        title="Branch 50 four-H1 standard m4 route lands in H2, not H3(O_X)",
        geometry="CICY5259 via favourable split 7914",
        scope_class="candidate-specific",
        claim_scope=(
            "Branch radius6_broad_adjacency_filtered_10_branch_50 under the "
            "standard cochain A-infinity transfer convention. This does not "
            "exclude a separately derived nonstandard physical effective operator."
        ),
        stage="standard_cochain_m4_degree_gate",
        minimal_obstruction_core={
            "candidate_label": audit["candidate_identity"]["label"],
            "operator": audit["operator_certificate"]["operator"],
            "monomial": audit["operator_certificate"]["monomial"],
            "input_degrees": degree_law["input_degrees"],
            "standard_mn_degree": degree_law["standard_mn_degree"],
            "output_degree": degree_law["output_degree"],
            "target_H2_dimension": degree_law["target_H2_dimension"],
            "target_E1_degree2_dimension": degree_law[
                "target_E1_degree2_dimension"
            ],
            "target_H3_dimension": degree_law["target_H3_dimension"],
            "standard_m4_to_H3_rank": degree_law["standard_m4_to_H3_rank"],
            "standard_m4_to_H3_status": degree_law[
                "standard_m4_to_H3_status"
            ],
            "direct_fourfold_orderings_have_origin_collision": direct_audit[
                "all_fourfold_orderings_have_origin_collision"
            ],
            "previous_H2_H2_proxy": audit["previous_H2_H2_proxy"],
            "proxy_triplet_rank_interval": proxy["component_mass_blocks"][
                "triplet_block"
            ]["rank_proxy_interval"],
        },
        cheap_prefilter="standard_m4_four_h1_not_top_cup",
        replay_counts={
            "source": "reports/phenomenology_guided_q1_radius9_homotopy_transfer_degree_audit.json",
            "tree_degree_record_count": len(audit["tree_degree_records"]),
            "transferred_output_degrees": sorted(
                {item["transferred_output_degree"] for item in audit["tree_degree_records"]}
            ),
            "direct_binary_product_count": len(direct_audit["binary_products"]),
            "nonzero_H2_H2_pair_partitions": audit["previous_H2_H2_proxy"][
                "nonzero_H2_H2_pair_partitions"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "standard_m4_four_h1_not_top_cup",
                {
                    "arity": degree_law["arity"],
                    "input_degrees": degree_law["input_degrees"],
                    "standard_mn_degree": degree_law["standard_mn_degree"],
                    "output_degree": degree_law["output_degree"],
                    "target_H2_dimension": degree_law["target_H2_dimension"],
                    "target_H3_dimension": degree_law["target_H3_dimension"],
                    "standard_m4_to_H3_rank": degree_law[
                        "standard_m4_to_H3_rank"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "reports/phenomenology_guided_q1_radius9_homotopy_transfer_degree_audit.json",
            "reports/phenomenology_guided_q1_radius9_homotopy_transfer_degree_audit_verification.json",
            "reports/phenomenology_guided_q1_radius9_quartic_scalar_attempt.json",
            "reports/phenomenology_guided_q1_radius9_higher_order_mass_map_probe.json",
        ],
        representative_examples=[
            {
                "candidate_label": audit["candidate_identity"]["label"],
                "operator": audit["operator_certificate"]["operator"],
                "monomial": audit["operator_certificate"]["monomial"],
                "degree_law": degree_law,
                "verdict": audit["verdict"],
            }
        ],
        nearest_escape={
            "minimal_change": "find a representative-compatible ordinary cubic H1 x H1 x H1 -> H3(O_X) route, or add a separately justified nonstandard physical convention",
            "surviving_escape_hatches": audit["verdict"]["surviving_escape_hatches"],
            "followup_result": "cubic-top-cup-first replay finds zero cup-product-eligible candidates in the current radius-9 grammar",
        },
    )


def cicy6927_model874_s42_basin_syndrome() -> dict[str, Any]:
    latent = load_json(latent_artifact("cicy6927_model874_latent_atlas.json"))
    active = load_json(latent_artifact("cicy6927_model874_latent_guided_escape_search.json"))
    compensated = load_json(
        latent_artifact("cicy6927_model874_latent_compensated_escape_search.json")
    )
    timeout = load_json(latent_artifact("cicy6927_model874_latent_timeout_closure.json"))
    parent = load_json(artifact("cicy6927_model874_doublet_escape_search.json"))
    motif = latent["universal_contamination_motif"]["signature"][0]
    return syndrome(
        syndrome_id="cicy6927_model874_s42_doublet_contamination_basin",
        title="Model 874 one-Higgs safe Wilson slice is trapped by an S_42 doublet-only mass motif",
        geometry="CICY6927/model 874 option 4",
        scope_class="grammar-local",
        claim_scope=(
            "Frozen CICY6927 model 874 with free Z2xZ2 option 4, all determinant-"
            "trivial Wilson branches in the fixed model, plus the audited active-"
            "touching, latent-active, and passive-compensated local grammars. The "
            "three compensated hard-promotion records are closed by targeted "
            "timeout replay. This is still not a global CICY6927 no-go."
        ),
        stage="one_higgs_doublet_triplet_selection_gate",
        minimal_obstruction_core={
            "cicy": 6927,
            "model_index": 874,
            "selected_free_option_index": 4,
            "universal_operator": motif["operator"],
            "fivebar": motif["fivebar"],
            "five": motif["five"],
            "singlets": motif["singlets"],
            "support_class": motif["support_class"],
            "triplet_shape": motif["triplet_shape"],
            "doublet_shape": motif["doublet_shape"],
            "active_columns": motif["active_columns"],
            "one_higgs_proton_safe_vector_count": latent["summary"][
                "one_higgs_proton_safe_vector_count"
            ],
            "wilson_only_escape_possible_in_fixed_model": latent["summary"][
                "wilson_only_escape_possible_in_fixed_model"
            ],
            "compensated_hard_promotion_frontiers": timeout["parameters"][
                "source_timeout_indices"
            ],
            "compensated_hard_promotion_status": timeout["status"],
        },
        cheap_prefilter="s42_doublet_contamination_motif",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy6927_model874_latent_atlas.json",
            "fixed_model_embedding_vectors": latent["summary"]["embedding_vector_count"],
            "one_higgs_proton_safe_vectors": latent["summary"][
                "one_higgs_proton_safe_vector_count"
            ],
            "universal_contamination_cluster_count": latent["summary"][
                "universal_contamination_cluster_count"
            ],
            "motif_count": latent["universal_contamination_motif"]["count"],
            "active_touching_frontier_size": parent["summary"]["frontier_size"],
            "active_touching_q1_candidates": parent["summary"]["q1_candidate_count"],
            "active_touching_one_higgs_precup_survivors": parent["summary"][
                "total_one_higgs_pre_cup_survivor_count"
            ],
            "latent_active_frontier_size": active["summary"]["frontier_size"],
            "latent_active_q1_candidates": active["summary"]["q1_candidate_count"],
            "latent_active_one_higgs_precup_survivors": active["summary"][
                "total_one_higgs_pre_cup_survivor_count"
            ],
            "latent_compensated_frontier_size": compensated["summary"][
                "frontier_size"
            ],
            "latent_compensated_q1_candidates": compensated["summary"][
                "q1_candidate_count"
            ],
            "latent_compensated_completed_one_higgs_precup_survivors": compensated[
                "summary"
            ]["total_one_higgs_pre_cup_survivor_count"],
            "latent_compensated_promotion_timeout_count": compensated["summary"][
                "promotion_timeout_count"
            ],
            "timeout_closure_resolved_count": timeout["summary"]["resolved_count"],
            "timeout_closure_unresolved_count": timeout["summary"]["unresolved_count"],
            "prefilter_sample_passes": evaluate_prefilter(
                "s42_doublet_contamination_motif",
                {
                    "operator": motif["operator"],
                    "singlets": motif["singlets"],
                    "support_class": motif["support_class"],
                    "triplet_pair_support": 0,
                    "doublet_pair_support": 1,
                },
            ),
        },
        evidence_artifacts=[
            "reports/cicy6927_model874_doublet_escape_search.json",
            "reports/cicy6927_model874_doublet_escape_search_verification.json",
            "experiments/latent_atlas/reports/cicy6927_model874_latent_atlas.json",
            "experiments/latent_atlas/reports/cicy6927_model874_latent_atlas_verification.json",
            "experiments/latent_atlas/reports/cicy6927_model874_latent_guided_escape_search.json",
            "experiments/latent_atlas/reports/cicy6927_model874_latent_guided_escape_search_verification.json",
            "experiments/latent_atlas/reports/cicy6927_model874_latent_compensated_escape_search.json",
            "experiments/latent_atlas/reports/cicy6927_model874_latent_compensated_escape_search_verification.json",
            "experiments/latent_atlas/reports/cicy6927_model874_latent_timeout_closure.json",
            "experiments/latent_atlas/reports/cicy6927_model874_latent_timeout_closure_verification.json",
        ],
        representative_examples=[
            {
                "universal_contamination_motif": motif,
                "weak_character_counts_in_one_higgs_safe_slice": latent["summary"][
                    "weak_character_counts_in_one_higgs_safe_slice"
                ],
                "nearest_boundary_loss": latent["summary"]["minimum_boundary_loss"],
            },
            {
                "timeout_closure": timeout["summary"],
                "status": timeout["status"],
                "interpretation": timeout["interpretation"],
            },
        ],
        nearest_escape={
            "minimal_change": (
                "find a q=1 one-Higgs/proton-safe branch whose mass-channel motif "
                "does not contain the 5bar_23*5_34*S_42 top_cup_doublet_only_mass "
                "signature, or change the geometry/presentation/mass mechanism"
            ),
            "recommended_generator": (
                "cross-model latent retrieval seeded against absence of the S_42 "
                "doublet-contamination motif, with symbolic promotion retained as judge"
            ),
            "closed_timeout_boundary": (
                "frontiers 2651, 4803, and 8857 resolve after skipping ordinary "
                "H1=0 singlets before expensive equivariant singlet audits; all "
                "three have 0 one-Higgs pre-cup survivors"
            ),
        },
    )


def cicy6927_non_s42_cup_missing_one_higgs_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("cicy6927_non_s42_cup_to_one_higgs_search.json"))
    source_examples = [
        item
        for item in report["closest_records"]
        if item["metrics"]
        and item["metrics"]["cup_product_eligible_triplet_target_count"] > 0
    ]
    return syndrome(
        syndrome_id="cicy6927_non_s42_cup_boundary_missing_one_higgs_radius2",
        title="Non-S_42 proton-safe triplet-cup boundary retains cup targets but has no one-Higgs sector",
        geometry="CICY6927/model 237 and 583 option 4",
        scope_class="grammar-local",
        claim_scope=(
            "CICY6927 option-4 local pair-delta radius-2 grammar around models "
            "237 and 583. This is a bounded local no-go for recovering one-Higgs "
            "structure from this non-S_42 cup-target boundary, not a global "
            "CICY6927 statement."
        ),
        stage="one_higgs_recovery_after_triplet_cup_gate",
        minimal_obstruction_core={
            "source_models": report["parameters"]["source_models"],
            "radius": report["parameters"]["radius"],
            "frontier_size": report["summary"]["frontier_size"],
            "q1_candidate_count": report["summary"]["q1_candidate_count"],
            "screened_candidate_count": report["summary"]["screened_candidate_count"],
            "promotion_timeout_count": report["summary"]["promotion_timeout_count"],
            "total_cup_product_eligible_triplet_target_count": report["summary"][
                "total_cup_product_eligible_triplet_target_count"
            ],
            "aggregate_dangerous_allowed_count_distribution": report["summary"][
                "aggregate_dangerous_allowed_count_distribution"
            ],
            "total_one_higgs_pair_triplet_free_embeddings": report["summary"][
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "closest_detail_s42_motif_hit_count": report["summary"][
                "closest_detail_s42_motif_hit_count"
            ],
        },
        cheap_prefilter="cup_target_missing_one_higgs",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy6927_non_s42_cup_to_one_higgs_search.json",
            "frontier_size": report["summary"]["frontier_size"],
            "q1_candidate_count": report["summary"]["q1_candidate_count"],
            "screened_candidate_count": report["summary"]["screened_candidate_count"],
            "promotion_timeout_count": report["summary"]["promotion_timeout_count"],
            "non_s42_precup_survivor_count": report["summary"][
                "non_s42_precup_survivor_count"
            ],
            "one_higgs_proton_safe_intersection_count": report["summary"][
                "one_higgs_proton_safe_intersection_count"
            ],
            "cup_product_eligible_triplet_target_count": report["summary"][
                "total_cup_product_eligible_triplet_target_count"
            ],
            "one_higgs_pair_triplet_free_embeddings": report["summary"][
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "cup_target_missing_one_higgs",
                {
                    "requires_one_higgs": True,
                    "cup_product_eligible_triplet_target_count": report["summary"][
                        "total_cup_product_eligible_triplet_target_count"
                    ],
                    "one_higgs_pair_triplet_free_count": report["summary"][
                        "total_one_higgs_pair_triplet_free_embeddings"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy6927_non_s42_cup_to_one_higgs_search.json",
            "experiments/latent_atlas/reports/cicy6927_non_s42_cup_to_one_higgs_search_verification.json",
            "experiments/latent_atlas/reports/cross_model_latent_retrieval.json",
            "experiments/latent_atlas/reports/cross_model_latent_retrieval_verification.json",
        ],
        representative_examples=source_examples[:2],
        nearest_escape={
            "minimal_change": (
                "recover a positive one-Higgs/triplet-free Wilson sector while "
                "preserving q1, proton safety, non-S_42 motif avoidance, and the "
                "triplet-only cup target"
            ),
            "next_generator": (
                "use a broader or different move grammar than radius-2 pair-delta, "
                "or pivot to the non-S_42 one-Higgs-but-proton-unsafe boundary class"
            ),
        },
    )


def cicy6927_model252_s42_boundary_only_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("cicy6927_model252_intersection_forcing_search.json"))
    summary = report["summary"]
    intersection = report["intersection_records"][0]
    return syndrome(
        syndrome_id="cicy6927_model252_s42_boundary_only_radius2",
        title="CICY6927 model 252 only recovers the known S_42 one-Higgs boundary",
        geometry="CICY6927/model 252 option 4",
        scope_class="grammar-local",
        claim_scope=(
            "CICY6927 option-4 local pair-delta radius-2 grammar around the "
            "model-252 queue target, seeded with cup anchors 237/583 and the "
            "known model-874 one-Higgs S_42 boundary. This retires model 252 "
            "from this queue grammar only; it is not a global CICY6927 no-go."
        ),
        stage="non_s42_one_higgs_precup_survivor_gate",
        minimal_obstruction_core={
            "focus_model": report["parameters"]["focus_model"],
            "source_models": report["parameters"]["source_models"],
            "radius": report["parameters"]["radius"],
            "frontier_size": summary["frontier_size"],
            "stage_counts": summary["stage_counts"],
            "q1_candidate_count": summary["q1_candidate_count"],
            "screened_candidate_count": summary["screened_candidate_count"],
            "promotion_timeout_count": summary["promotion_timeout_count"],
            "total_embeddings_screened": summary["total_embeddings_screened"],
            "total_one_higgs_pair_triplet_free_embeddings": summary[
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "total_one_higgs_proton_safe_embeddings": summary[
                "total_one_higgs_proton_safe_embeddings"
            ],
            "total_one_higgs_pre_cup_survivor_count": summary[
                "total_one_higgs_pre_cup_survivor_count"
            ],
            "total_pre_cup_survivor_count": summary["total_pre_cup_survivor_count"],
            "total_cup_product_eligible_triplet_target_count": summary[
                "total_cup_product_eligible_triplet_target_count"
            ],
            "one_higgs_proton_safe_intersection_count": summary[
                "one_higgs_proton_safe_intersection_count"
            ],
            "non_s42_precup_survivor_count": summary[
                "non_s42_precup_survivor_count"
            ],
            "closest_detail_s42_motif_hit_count": summary[
                "closest_detail_s42_motif_hit_count"
            ],
            "only_intersection_frontier": intersection["frontier_index"],
            "only_intersection_source_models": intersection["source_models"],
            "only_intersection_metrics": intersection["metrics"],
        },
        cheap_prefilter="s42_boundary_only_no_non_s42_survivor",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy6927_model252_intersection_forcing_search.json",
            "frontier_size": summary["frontier_size"],
            "q1_candidate_count": summary["q1_candidate_count"],
            "screened_candidate_count": summary["screened_candidate_count"],
            "promotion_timeout_count": summary["promotion_timeout_count"],
            "one_higgs_proton_safe_intersection_count": summary[
                "one_higgs_proton_safe_intersection_count"
            ],
            "non_s42_precup_survivor_count": summary[
                "non_s42_precup_survivor_count"
            ],
            "total_one_higgs_pair_triplet_free_embeddings": summary[
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "total_one_higgs_proton_safe_embeddings": summary[
                "total_one_higgs_proton_safe_embeddings"
            ],
            "total_pre_cup_survivor_count": summary["total_pre_cup_survivor_count"],
            "total_cup_product_eligible_triplet_target_count": summary[
                "total_cup_product_eligible_triplet_target_count"
            ],
            "closest_detail_s42_motif_hit_count": summary[
                "closest_detail_s42_motif_hit_count"
            ],
            "only_intersection_frontier": intersection["frontier_index"],
            "only_intersection_source_models": intersection["source_models"],
            "prefilter_sample_passes": evaluate_prefilter(
                "s42_boundary_only_no_non_s42_survivor",
                {
                    "requires_non_s42_survivor": True,
                    "one_higgs_proton_safe_intersection_count": summary[
                        "one_higgs_proton_safe_intersection_count"
                    ],
                    "non_s42_precup_survivor_count": summary[
                        "non_s42_precup_survivor_count"
                    ],
                    "closest_detail_s42_motif_hit_count": summary[
                        "closest_detail_s42_motif_hit_count"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy6927_model252_intersection_forcing_search.json",
            "experiments/latent_atlas/reports/cicy6927_model252_intersection_forcing_search_verification.json",
            "experiments/latent_atlas/reports/cicy6927_non_s42_cup_to_one_higgs_search.json",
            "experiments/latent_atlas/reports/cicy6927_non_s42_cup_to_one_higgs_search_verification.json",
            "experiments/latent_atlas/reports/cicy6927_model874_latent_atlas.json",
            "experiments/latent_atlas/reports/cicy6927_model874_latent_atlas_verification.json",
        ],
        representative_examples=[intersection] + report["closest_records"][:2],
        nearest_escape={
            "minimal_change": (
                "find a CICY6927 option-4 q1 branch with a same-embedding "
                "one-Higgs/proton-safe overlap and a non-S_42 pre-cup survivor"
            ),
            "next_generator": (
                "advance to the next queue target, or broaden CICY6927 only with "
                "a generator explicitly ranked by non-S_42 one-Higgs pre-cup "
                "survival rather than by recovering the model-874 boundary"
            ),
        },
    )


def cicy6927_model254_s42_boundary_only_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("cicy6927_model254_intersection_forcing_search.json"))
    summary = report["summary"]
    intersection = report["intersection_records"][0]
    return syndrome(
        syndrome_id="cicy6927_model254_s42_boundary_only_radius2",
        title="CICY6927 model 254 only recovers the known S_42 one-Higgs boundary",
        geometry="CICY6927/model 254 option 4",
        scope_class="grammar-local",
        claim_scope=(
            "CICY6927 option-4 local pair-delta radius-2 grammar around the "
            "model-254 queue target, seeded with cup anchors 237/583 and the "
            "known model-874 one-Higgs S_42 boundary. This retires model 254 "
            "from this queue grammar only; it is not a global CICY6927 no-go."
        ),
        stage="non_s42_one_higgs_precup_survivor_gate",
        minimal_obstruction_core={
            "focus_model": report["parameters"]["focus_model"],
            "source_models": report["parameters"]["source_models"],
            "radius": report["parameters"]["radius"],
            "frontier_size": summary["frontier_size"],
            "stage_counts": summary["stage_counts"],
            "q1_candidate_count": summary["q1_candidate_count"],
            "screened_candidate_count": summary["screened_candidate_count"],
            "promotion_timeout_count": summary["promotion_timeout_count"],
            "total_embeddings_screened": summary["total_embeddings_screened"],
            "total_one_higgs_pair_triplet_free_embeddings": summary[
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "total_one_higgs_proton_safe_embeddings": summary[
                "total_one_higgs_proton_safe_embeddings"
            ],
            "total_one_higgs_pre_cup_survivor_count": summary[
                "total_one_higgs_pre_cup_survivor_count"
            ],
            "total_pre_cup_survivor_count": summary["total_pre_cup_survivor_count"],
            "total_cup_product_eligible_triplet_target_count": summary[
                "total_cup_product_eligible_triplet_target_count"
            ],
            "one_higgs_proton_safe_intersection_count": summary[
                "one_higgs_proton_safe_intersection_count"
            ],
            "non_s42_precup_survivor_count": summary[
                "non_s42_precup_survivor_count"
            ],
            "closest_detail_s42_motif_hit_count": summary[
                "closest_detail_s42_motif_hit_count"
            ],
            "only_intersection_frontier": intersection["frontier_index"],
            "only_intersection_source_models": intersection["source_models"],
            "only_intersection_metrics": intersection["metrics"],
        },
        cheap_prefilter="s42_boundary_only_no_non_s42_survivor",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy6927_model254_intersection_forcing_search.json",
            "frontier_size": summary["frontier_size"],
            "q1_candidate_count": summary["q1_candidate_count"],
            "screened_candidate_count": summary["screened_candidate_count"],
            "promotion_timeout_count": summary["promotion_timeout_count"],
            "one_higgs_proton_safe_intersection_count": summary[
                "one_higgs_proton_safe_intersection_count"
            ],
            "non_s42_precup_survivor_count": summary[
                "non_s42_precup_survivor_count"
            ],
            "total_one_higgs_pair_triplet_free_embeddings": summary[
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "total_one_higgs_proton_safe_embeddings": summary[
                "total_one_higgs_proton_safe_embeddings"
            ],
            "total_pre_cup_survivor_count": summary["total_pre_cup_survivor_count"],
            "total_cup_product_eligible_triplet_target_count": summary[
                "total_cup_product_eligible_triplet_target_count"
            ],
            "closest_detail_s42_motif_hit_count": summary[
                "closest_detail_s42_motif_hit_count"
            ],
            "only_intersection_frontier": intersection["frontier_index"],
            "only_intersection_source_models": intersection["source_models"],
            "prefilter_sample_passes": evaluate_prefilter(
                "s42_boundary_only_no_non_s42_survivor",
                {
                    "requires_non_s42_survivor": True,
                    "one_higgs_proton_safe_intersection_count": summary[
                        "one_higgs_proton_safe_intersection_count"
                    ],
                    "non_s42_precup_survivor_count": summary[
                        "non_s42_precup_survivor_count"
                    ],
                    "closest_detail_s42_motif_hit_count": summary[
                        "closest_detail_s42_motif_hit_count"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy6927_model254_intersection_forcing_search.json",
            "experiments/latent_atlas/reports/cicy6927_model254_intersection_forcing_search_verification.json",
            "experiments/latent_atlas/reports/cicy6927_model252_intersection_forcing_search.json",
            "experiments/latent_atlas/reports/cicy6927_model252_intersection_forcing_search_verification.json",
            "experiments/latent_atlas/reports/cicy6927_model874_latent_atlas.json",
            "experiments/latent_atlas/reports/cicy6927_model874_latent_atlas_verification.json",
        ],
        representative_examples=[intersection] + report["closest_records"][:2],
        nearest_escape={
            "minimal_change": (
                "find a CICY6927 option-4 q1 branch with a same-embedding "
                "one-Higgs/proton-safe overlap and a non-S_42 pre-cup survivor"
            ),
            "next_generator": (
                "advance to the next queue target, or broaden CICY6927 only with "
                "a generator explicitly ranked by non-S_42 one-Higgs pre-cup "
                "survival rather than by recovering the model-874 boundary"
            ),
        },
    )


def cicy6927_model369_s42_boundary_only_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("cicy6927_model369_intersection_forcing_search.json"))
    summary = report["summary"]
    intersection = report["intersection_records"][0]
    model369_records = [
        item for item in report["screened_records"] if item.get("source_models") == [369]
    ]
    return syndrome(
        syndrome_id="cicy6927_model369_s42_boundary_only_radius2",
        title="CICY6927 model 369 only recovers the known S_42 one-Higgs boundary",
        geometry="CICY6927/model 369 option 4",
        scope_class="grammar-local",
        claim_scope=(
            "CICY6927 option-4 local pair-delta radius-2 grammar around the "
            "model-369 queue target, seeded with cup anchors 237/583 and the "
            "known model-874 one-Higgs S_42 boundary. This retires model 369 "
            "from this queue grammar only; it is not a global CICY6927 no-go."
        ),
        stage="non_s42_one_higgs_precup_survivor_gate",
        minimal_obstruction_core={
            "focus_model": report["parameters"]["focus_model"],
            "source_models": report["parameters"]["source_models"],
            "radius": report["parameters"]["radius"],
            "frontier_size": summary["frontier_size"],
            "stage_counts": summary["stage_counts"],
            "q1_candidate_count": summary["q1_candidate_count"],
            "screened_candidate_count": summary["screened_candidate_count"],
            "model369_screened_count": len(model369_records),
            "model369_screen_status_counts": dict(
                Counter(item["screen_status"] for item in model369_records)
            ),
            "promotion_timeout_count": summary["promotion_timeout_count"],
            "total_embeddings_screened": summary["total_embeddings_screened"],
            "total_one_higgs_pair_triplet_free_embeddings": summary[
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "total_one_higgs_proton_safe_embeddings": summary[
                "total_one_higgs_proton_safe_embeddings"
            ],
            "total_one_higgs_pre_cup_survivor_count": summary[
                "total_one_higgs_pre_cup_survivor_count"
            ],
            "total_pre_cup_survivor_count": summary["total_pre_cup_survivor_count"],
            "total_cup_product_eligible_triplet_target_count": summary[
                "total_cup_product_eligible_triplet_target_count"
            ],
            "one_higgs_proton_safe_intersection_count": summary[
                "one_higgs_proton_safe_intersection_count"
            ],
            "non_s42_precup_survivor_count": summary[
                "non_s42_precup_survivor_count"
            ],
            "closest_detail_s42_motif_hit_count": summary[
                "closest_detail_s42_motif_hit_count"
            ],
            "only_intersection_frontier": intersection["frontier_index"],
            "only_intersection_source_models": intersection["source_models"],
            "only_intersection_metrics": intersection["metrics"],
        },
        cheap_prefilter="s42_boundary_only_no_non_s42_survivor",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy6927_model369_intersection_forcing_search.json",
            "frontier_size": summary["frontier_size"],
            "q1_candidate_count": summary["q1_candidate_count"],
            "screened_candidate_count": summary["screened_candidate_count"],
            "model369_screened_count": len(model369_records),
            "promotion_timeout_count": summary["promotion_timeout_count"],
            "one_higgs_proton_safe_intersection_count": summary[
                "one_higgs_proton_safe_intersection_count"
            ],
            "non_s42_precup_survivor_count": summary[
                "non_s42_precup_survivor_count"
            ],
            "total_one_higgs_pair_triplet_free_embeddings": summary[
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "total_one_higgs_proton_safe_embeddings": summary[
                "total_one_higgs_proton_safe_embeddings"
            ],
            "total_pre_cup_survivor_count": summary["total_pre_cup_survivor_count"],
            "total_cup_product_eligible_triplet_target_count": summary[
                "total_cup_product_eligible_triplet_target_count"
            ],
            "closest_detail_s42_motif_hit_count": summary[
                "closest_detail_s42_motif_hit_count"
            ],
            "only_intersection_frontier": intersection["frontier_index"],
            "only_intersection_source_models": intersection["source_models"],
            "prefilter_sample_passes": evaluate_prefilter(
                "s42_boundary_only_no_non_s42_survivor",
                {
                    "requires_non_s42_survivor": True,
                    "one_higgs_proton_safe_intersection_count": summary[
                        "one_higgs_proton_safe_intersection_count"
                    ],
                    "non_s42_precup_survivor_count": summary[
                        "non_s42_precup_survivor_count"
                    ],
                    "closest_detail_s42_motif_hit_count": summary[
                        "closest_detail_s42_motif_hit_count"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy6927_model369_intersection_forcing_search.json",
            "experiments/latent_atlas/reports/cicy6927_model369_intersection_forcing_search_verification.json",
            "experiments/latent_atlas/reports/cicy6927_model254_intersection_forcing_search.json",
            "experiments/latent_atlas/reports/cicy6927_model254_intersection_forcing_search_verification.json",
            "experiments/latent_atlas/reports/cicy6927_model874_latent_atlas.json",
            "experiments/latent_atlas/reports/cicy6927_model874_latent_atlas_verification.json",
        ],
        representative_examples=[intersection] + report["closest_records"][:2],
        nearest_escape={
            "minimal_change": (
                "find a CICY6927 option-4 q1 branch with a same-embedding "
                "one-Higgs/proton-safe overlap and a non-S_42 pre-cup survivor"
            ),
            "next_generator": (
                "advance to the next queue target, or broaden CICY6927 only with "
                "a generator explicitly ranked by non-S_42 one-Higgs pre-cup "
                "survival rather than by recovering the model-874 boundary"
            ),
        },
    )


def cicy6927_model52_s42_boundary_only_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("cicy6927_model52_intersection_forcing_search.json"))
    summary = report["summary"]
    intersection = report["intersection_records"][0]
    model52_records = [
        item for item in report["screened_records"] if item.get("source_models") == [52]
    ]
    return syndrome(
        syndrome_id="cicy6927_model52_s42_boundary_only_radius2",
        title="CICY6927 model 52 only recovers the known S_42 one-Higgs boundary",
        geometry="CICY6927/model 52 option 4",
        scope_class="grammar-local",
        claim_scope=(
            "CICY6927 option-4 local pair-delta radius-2 grammar around the "
            "model-52 queue target, seeded with cup anchors 237/583 and the "
            "known model-874 one-Higgs S_42 boundary. This retires model 52 "
            "from this queue grammar only; it is not a global CICY6927 no-go."
        ),
        stage="non_s42_one_higgs_precup_survivor_gate",
        minimal_obstruction_core={
            "focus_model": report["parameters"]["focus_model"],
            "source_models": report["parameters"]["source_models"],
            "radius": report["parameters"]["radius"],
            "frontier_size": summary["frontier_size"],
            "stage_counts": summary["stage_counts"],
            "q1_candidate_count": summary["q1_candidate_count"],
            "screened_candidate_count": summary["screened_candidate_count"],
            "model52_screened_count": len(model52_records),
            "model52_screen_status_counts": dict(
                Counter(item["screen_status"] for item in model52_records)
            ),
            "promotion_timeout_count": summary["promotion_timeout_count"],
            "total_embeddings_screened": summary["total_embeddings_screened"],
            "total_one_higgs_pair_triplet_free_embeddings": summary[
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "total_one_higgs_proton_safe_embeddings": summary[
                "total_one_higgs_proton_safe_embeddings"
            ],
            "total_one_higgs_pre_cup_survivor_count": summary[
                "total_one_higgs_pre_cup_survivor_count"
            ],
            "total_pre_cup_survivor_count": summary["total_pre_cup_survivor_count"],
            "total_cup_product_eligible_triplet_target_count": summary[
                "total_cup_product_eligible_triplet_target_count"
            ],
            "one_higgs_proton_safe_intersection_count": summary[
                "one_higgs_proton_safe_intersection_count"
            ],
            "non_s42_precup_survivor_count": summary[
                "non_s42_precup_survivor_count"
            ],
            "closest_detail_s42_motif_hit_count": summary[
                "closest_detail_s42_motif_hit_count"
            ],
            "only_intersection_frontier": intersection["frontier_index"],
            "only_intersection_source_models": intersection["source_models"],
            "only_intersection_metrics": intersection["metrics"],
        },
        cheap_prefilter="s42_boundary_only_no_non_s42_survivor",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy6927_model52_intersection_forcing_search.json",
            "frontier_size": summary["frontier_size"],
            "q1_candidate_count": summary["q1_candidate_count"],
            "screened_candidate_count": summary["screened_candidate_count"],
            "model52_screened_count": len(model52_records),
            "promotion_timeout_count": summary["promotion_timeout_count"],
            "one_higgs_proton_safe_intersection_count": summary[
                "one_higgs_proton_safe_intersection_count"
            ],
            "non_s42_precup_survivor_count": summary[
                "non_s42_precup_survivor_count"
            ],
            "total_one_higgs_pair_triplet_free_embeddings": summary[
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "total_one_higgs_proton_safe_embeddings": summary[
                "total_one_higgs_proton_safe_embeddings"
            ],
            "total_pre_cup_survivor_count": summary["total_pre_cup_survivor_count"],
            "total_cup_product_eligible_triplet_target_count": summary[
                "total_cup_product_eligible_triplet_target_count"
            ],
            "closest_detail_s42_motif_hit_count": summary[
                "closest_detail_s42_motif_hit_count"
            ],
            "only_intersection_frontier": intersection["frontier_index"],
            "only_intersection_source_models": intersection["source_models"],
            "prefilter_sample_passes": evaluate_prefilter(
                "s42_boundary_only_no_non_s42_survivor",
                {
                    "requires_non_s42_survivor": True,
                    "one_higgs_proton_safe_intersection_count": summary[
                        "one_higgs_proton_safe_intersection_count"
                    ],
                    "non_s42_precup_survivor_count": summary[
                        "non_s42_precup_survivor_count"
                    ],
                    "closest_detail_s42_motif_hit_count": summary[
                        "closest_detail_s42_motif_hit_count"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy6927_model52_intersection_forcing_search.json",
            "experiments/latent_atlas/reports/cicy6927_model52_intersection_forcing_search_verification.json",
            "experiments/latent_atlas/reports/cicy6927_model369_intersection_forcing_search.json",
            "experiments/latent_atlas/reports/cicy6927_model369_intersection_forcing_search_verification.json",
            "experiments/latent_atlas/reports/cicy6927_model874_latent_atlas.json",
            "experiments/latent_atlas/reports/cicy6927_model874_latent_atlas_verification.json",
        ],
        representative_examples=[intersection] + report["closest_records"][:2],
        nearest_escape={
            "minimal_change": (
                "find a CICY6927 option-4 q1 branch with a same-embedding "
                "one-Higgs/proton-safe overlap and a non-S_42 pre-cup survivor"
            ),
            "next_generator": (
                "advance to the next queue target, or broaden CICY6927 only with "
                "a generator explicitly ranked by non-S_42 one-Higgs pre-cup "
                "survival rather than by recovering the model-874 boundary"
            ),
        },
    )


def cicy6836_one_higgs_proton_disjoint_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("cicy6836_one_higgs_proton_intersection_search.json"))
    one_higgs_examples = [
        item
        for item in report["closest_records"]
        if item["metrics"]
        and item["metrics"]["one_higgs_pair_triplet_free_count"] > 0
    ]
    cup_examples = [
        item
        for item in report["closest_records"]
        if item["metrics"]
        and item["metrics"]["cup_product_eligible_triplet_target_count"] > 0
    ]
    return syndrome(
        syndrome_id="cicy6836_one_higgs_proton_safety_disjoint_radius2",
        title="CICY6836 one-Higgs and proton-safe cup structures exist, but do not intersect",
        geometry="CICY6836/model 95 and 139 option 23",
        scope_class="grammar-local",
        claim_scope=(
            "CICY6836 option-23 local pair-delta radius-2 grammar around the "
            "complementary model-95 one-Higgs/proton-near boundary and model-139 "
            "proton-safe cup-target boundary. This is not a global CICY6836 no-go."
        ),
        stage="one_higgs_proton_safety_intersection_gate",
        minimal_obstruction_core={
            "source_models": report["parameters"]["source_models"],
            "radius": report["parameters"]["radius"],
            "frontier_size": report["summary"]["frontier_size"],
            "q1_candidate_count": report["summary"]["q1_candidate_count"],
            "screened_candidate_count": report["summary"]["screened_candidate_count"],
            "promotion_timeout_count": report["summary"]["promotion_timeout_count"],
            "total_one_higgs_pair_triplet_free_embeddings": report["summary"][
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "total_proton_safe_embeddings": report["summary"][
                "total_proton_safe_embeddings"
            ],
            "total_pre_cup_survivor_count": report["summary"][
                "total_pre_cup_survivor_count"
            ],
            "total_cup_product_eligible_triplet_target_count": report["summary"][
                "total_cup_product_eligible_triplet_target_count"
            ],
            "total_one_higgs_proton_safe_embeddings": report["summary"][
                "total_one_higgs_proton_safe_embeddings"
            ],
            "total_one_higgs_pre_cup_survivor_count": report["summary"][
                "total_one_higgs_pre_cup_survivor_count"
            ],
            "best_min_one_higgs_dangerous_operator_count": report["summary"][
                "best_min_one_higgs_dangerous_operator_count"
            ],
            "one_higgs_dangerous_signature": one_higgs_examples[0]["summary"][
                "one_higgs_dangerous_signature_counts"
            ]
            if one_higgs_examples
            else {},
        },
        cheap_prefilter="one_higgs_proton_safety_disjoint",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy6836_one_higgs_proton_intersection_search.json",
            "frontier_size": report["summary"]["frontier_size"],
            "q1_candidate_count": report["summary"]["q1_candidate_count"],
            "screened_candidate_count": report["summary"]["screened_candidate_count"],
            "promotion_timeout_count": report["summary"]["promotion_timeout_count"],
            "one_higgs_precup_survivor_record_count": report["summary"][
                "one_higgs_precup_survivor_record_count"
            ],
            "one_higgs_proton_safe_intersection_record_count": report["summary"][
                "one_higgs_proton_safe_intersection_record_count"
            ],
            "one_higgs_pair_triplet_free_embeddings": report["summary"][
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "one_higgs_proton_safe_embeddings": report["summary"][
                "total_one_higgs_proton_safe_embeddings"
            ],
            "cup_product_eligible_triplet_target_count": report["summary"][
                "total_cup_product_eligible_triplet_target_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "one_higgs_proton_safety_disjoint",
                {
                    "requires_one_higgs_proton_safe": True,
                    "one_higgs_pair_triplet_free_count": one_higgs_examples[0][
                        "metrics"
                    ]["one_higgs_pair_triplet_free_count"]
                    if one_higgs_examples
                    else 0,
                    "proton_safe_embedding_count": one_higgs_examples[0]["metrics"][
                        "proton_safe_embedding_count"
                    ]
                    if one_higgs_examples
                    else 0,
                    "one_higgs_proton_safe_count": one_higgs_examples[0]["metrics"][
                        "one_higgs_proton_safe_count"
                    ]
                    if one_higgs_examples
                    else 0,
                },
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy6836_one_higgs_proton_intersection_search.json",
            "experiments/latent_atlas/reports/cicy6836_one_higgs_proton_intersection_search_verification.json",
            "reports/cicy6836_family_precup_promotion_gate.json",
            "reports/cicy6836_family_precup_promotion_gate_verification.json",
            "experiments/latent_atlas/reports/cross_model_latent_retrieval.json",
            "experiments/latent_atlas/reports/cross_model_latent_retrieval_verification.json",
        ],
        representative_examples=(one_higgs_examples[:2] + cup_examples[:1]),
        nearest_escape={
            "minimal_change": (
                "find a q=1 branch where one-Higgs/triplet-free Wilson embeddings "
                "land inside the proton-safe slice, then retain a triplet-only "
                "top-cup target"
            ),
            "next_generator": (
                "either broaden the CICY6836 move grammar beyond radius-2 pair-delta "
                "or pivot to a geometry where one-Higgs and proton-safe/cup features "
                "already overlap in the same q1 row"
            ),
        },
    )


def cicy6836_model87_intersection_forcing_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("cicy6836_model87_intersection_forcing_search.json"))
    one_higgs_examples = [
        item
        for item in report["closest_records"]
        if item["metrics"]
        and item["metrics"]["one_higgs_pair_triplet_free_count"] > 0
    ]
    cup_examples = [
        item
        for item in report["closest_records"]
        if item["metrics"]
        and item["metrics"]["cup_product_eligible_triplet_target_count"] > 0
    ]
    source = report["source_boundary_metrics"]
    return syndrome(
        syndrome_id="cicy6836_model87_one_higgs_proton_safety_disjoint_radius2",
        title="CICY6836 model 87 keeps one-Higgs and proton-safe slices disjoint",
        geometry="CICY6836/model 87 option 23",
        scope_class="grammar-local",
        claim_scope=(
            "CICY6836 option-23 local pair-delta radius-2 grammar around the "
            "advanced queue target model 87 and proton-safe anchors 139/186. "
            "This retires the current queue target, not all CICY6836 searches."
        ),
        stage="one_higgs_proton_safety_intersection_gate",
        minimal_obstruction_core={
            "focus_model": report["parameters"]["focus_model"],
            "source_models": report["parameters"]["source_models"],
            "radius": report["parameters"]["radius"],
            "frontier_size": report["summary"]["frontier_size"],
            "q1_candidate_count": report["summary"]["q1_candidate_count"],
            "screened_candidate_count": report["summary"]["screened_candidate_count"],
            "promotion_timeout_count": report["summary"]["promotion_timeout_count"],
            "model87_one_higgs_pair_triplet_free_count": source["model87"][
                "one_higgs_pair_triplet_free_count"
            ],
            "model139_proton_safe_embedding_count": source["model139"][
                "proton_safe_embedding_count"
            ],
            "model186_proton_safe_embedding_count": source["model186"][
                "proton_safe_embedding_count"
            ],
            "total_one_higgs_pair_triplet_free_embeddings": report["summary"][
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "total_proton_safe_embeddings": report["summary"][
                "total_proton_safe_embeddings"
            ],
            "total_pre_cup_survivor_count": report["summary"][
                "total_pre_cup_survivor_count"
            ],
            "total_cup_product_eligible_triplet_target_count": report["summary"][
                "total_cup_product_eligible_triplet_target_count"
            ],
            "total_one_higgs_proton_safe_embeddings": report["summary"][
                "total_one_higgs_proton_safe_embeddings"
            ],
            "total_one_higgs_pre_cup_survivor_count": report["summary"][
                "total_one_higgs_pre_cup_survivor_count"
            ],
            "best_min_one_higgs_dangerous_operator_count": report["summary"][
                "best_min_one_higgs_dangerous_operator_count"
            ],
            "best_min_one_higgs_doublet_support": report["summary"][
                "best_min_one_higgs_doublet_support"
            ],
            "first_pair_gate_status": report["parameters"]["first_pair_gate_status"],
        },
        cheap_prefilter="one_higgs_proton_safety_disjoint",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy6836_model87_intersection_forcing_search.json",
            "frontier_size": report["summary"]["frontier_size"],
            "q1_candidate_count": report["summary"]["q1_candidate_count"],
            "screened_candidate_count": report["summary"]["screened_candidate_count"],
            "promotion_timeout_count": report["summary"]["promotion_timeout_count"],
            "one_higgs_precup_survivor_record_count": report["summary"][
                "one_higgs_precup_survivor_record_count"
            ],
            "one_higgs_proton_safe_intersection_record_count": report["summary"][
                "one_higgs_proton_safe_intersection_record_count"
            ],
            "one_higgs_pair_triplet_free_embeddings": report["summary"][
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "one_higgs_proton_safe_embeddings": report["summary"][
                "total_one_higgs_proton_safe_embeddings"
            ],
            "proton_safe_embeddings": report["summary"][
                "total_proton_safe_embeddings"
            ],
            "cup_product_eligible_triplet_target_count": report["summary"][
                "total_cup_product_eligible_triplet_target_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "one_higgs_proton_safety_disjoint",
                {
                    "requires_one_higgs_proton_safe": True,
                    "one_higgs_pair_triplet_free_count": report["summary"][
                        "total_one_higgs_pair_triplet_free_embeddings"
                    ],
                    "proton_safe_embedding_count": report["summary"][
                        "total_proton_safe_embeddings"
                    ],
                    "one_higgs_proton_safe_count": report["summary"][
                        "total_one_higgs_proton_safe_embeddings"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy6836_model87_intersection_forcing_search.json",
            "experiments/latent_atlas/reports/cicy6836_model87_intersection_forcing_search_verification.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement_verification.json",
            "reports/cicy6836_family_precup_promotion_gate.json",
            "reports/cicy6836_family_precup_promotion_gate_verification.json",
        ],
        representative_examples=(one_higgs_examples[:2] + cup_examples[:1]),
        nearest_escape={
            "minimal_change": (
                "find a CICY6836 q=1 branch whose one-Higgs/triplet-free embeddings "
                "also have zero dangerous 10*5bar*5bar operators"
            ),
            "next_generator": (
                "advance the cross-geometry queue to the next open target, or build "
                "a broader CICY6836 generator only if it is explicitly ranked by "
                "one-Higgs/proton-safe intersection before first-pair scoring"
            ),
        },
    )


def cicy6836_model186_frontier691_followup_syndrome() -> dict[str, Any]:
    first = load_json(latent_artifact("cicy6836_model186_intersection_forcing_search.json"))
    follow = load_json(latent_artifact("cicy6836_model186_frontier691_followup_search.json"))
    first_summary = first["summary"]
    follow_summary = follow["summary"]
    seed = first["closest_records"][0]
    retained = follow["closest_records"][0]
    return syndrome(
        syndrome_id="cicy6836_model186_frontier691_followup_disjoint_radius2",
        title="CICY6836 model 186 improves to frontier 691, then stays one-Higgs/proton disjoint",
        geometry="CICY6836/model 186 option 23 plus frontier 691",
        scope_class="grammar-local",
        claim_scope=(
            "CICY6836 option-23 radius-2 pair-delta search around model 186, "
            "followed by a radius-2 follow-up around the verified frontier-691 "
            "boundary improvement and anchors 186/139. This retires the current "
            "model-186 queue target under this grammar, not all CICY6836 searches."
        ),
        stage="one_higgs_proton_safety_intersection_gate",
        minimal_obstruction_core={
            "focus_model": first["parameters"]["focus_model"],
            "source_models": first["parameters"]["source_models"],
            "first_pass_frontier_size": first_summary["frontier_size"],
            "first_pass_q1_candidate_count": first_summary["q1_candidate_count"],
            "first_pass_boundary_improvement_record_count": first_summary[
                "boundary_improvement_record_count"
            ],
            "first_pass_best_frontier": seed["frontier_index"],
            "first_pass_best_metrics": seed["metrics"],
            "followup_source_models": follow["parameters"]["source_models"],
            "followup_radius": follow["parameters"]["radius"],
            "followup_frontier_size": follow_summary["frontier_size"],
            "followup_q1_candidate_count": follow_summary["q1_candidate_count"],
            "followup_screened_candidate_count": follow_summary[
                "screened_candidate_count"
            ],
            "followup_promotion_timeout_count": follow_summary[
                "promotion_timeout_count"
            ],
            "followup_one_higgs_proton_safe_intersection_record_count": follow_summary[
                "one_higgs_proton_safe_intersection_record_count"
            ],
            "followup_boundary_improvement_record_count": follow_summary[
                "boundary_improvement_record_count"
            ],
            "followup_total_one_higgs_pair_triplet_free_embeddings": follow_summary[
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "followup_total_proton_safe_embeddings": follow_summary[
                "total_proton_safe_embeddings"
            ],
            "followup_total_cup_product_eligible_triplet_target_count": follow_summary[
                "total_cup_product_eligible_triplet_target_count"
            ],
            "followup_best_retained_frontier": retained["frontier_index"],
            "followup_best_retained_metrics": retained["metrics"],
        },
        cheap_prefilter="one_higgs_proton_safety_disjoint",
        replay_counts={
            "first_pass_source": "experiments/latent_atlas/reports/cicy6836_model186_intersection_forcing_search.json",
            "followup_source": "experiments/latent_atlas/reports/cicy6836_model186_frontier691_followup_search.json",
            "first_pass_frontier_size": first_summary["frontier_size"],
            "first_pass_q1_candidate_count": first_summary["q1_candidate_count"],
            "first_pass_boundary_improvement_record_count": first_summary[
                "boundary_improvement_record_count"
            ],
            "followup_frontier_size": follow_summary["frontier_size"],
            "followup_q1_candidate_count": follow_summary["q1_candidate_count"],
            "followup_screened_candidate_count": follow_summary[
                "screened_candidate_count"
            ],
            "followup_promotion_timeout_count": follow_summary[
                "promotion_timeout_count"
            ],
            "one_higgs_pair_triplet_free_embeddings": follow_summary[
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "proton_safe_embeddings": follow_summary["total_proton_safe_embeddings"],
            "one_higgs_proton_safe_embeddings": follow_summary[
                "total_one_higgs_proton_safe_embeddings"
            ],
            "cup_product_eligible_triplet_target_count": follow_summary[
                "total_cup_product_eligible_triplet_target_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "one_higgs_proton_safety_disjoint",
                {
                    "requires_one_higgs_proton_safe": True,
                    "one_higgs_pair_triplet_free_count": follow_summary[
                        "total_one_higgs_pair_triplet_free_embeddings"
                    ],
                    "proton_safe_embedding_count": follow_summary[
                        "total_proton_safe_embeddings"
                    ],
                    "one_higgs_proton_safe_count": follow_summary[
                        "total_one_higgs_proton_safe_embeddings"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy6836_model186_intersection_forcing_search.json",
            "experiments/latent_atlas/reports/cicy6836_model186_intersection_forcing_search_verification.json",
            "experiments/latent_atlas/reports/cicy6836_model186_frontier691_followup_search.json",
            "experiments/latent_atlas/reports/cicy6836_model186_frontier691_followup_search_verification.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement_verification.json",
            "reports/cicy6836_family_precup_promotion_gate.json",
            "reports/cicy6836_family_precup_promotion_gate_verification.json",
        ],
        representative_examples=[seed, retained],
        nearest_escape={
            "minimal_change": (
                "find a CICY6836 q1 branch whose one-Higgs/triplet-free embeddings "
                "also have zero dangerous 10*5bar*5bar operators, or improve "
                "frontier-691 beyond dangerous-count 1 and doublet-support 0"
            ),
            "next_generator": (
                "advance the cross-geometry queue to the next open target, or "
                "expand CICY6836 only with a move grammar explicitly ranked by "
                "same-embedding one-Higgs/proton-safe intersection"
            ),
        },
    )


def cicy6836_model136_existing_boundary_floor_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("cicy6836_model136_intersection_forcing_search.json"))
    summary = report["summary"]
    source = report["source_boundary_metrics"]
    closest = report["closest_records"][0]
    focus_records = [
        item for item in report["screened_records"] if item.get("source_models") == [136]
    ]
    return syndrome(
        syndrome_id="cicy6836_model136_existing_boundary_floor_radius2",
        title="CICY6836 model 136 only rediscovers the existing frontier-691 boundary floor",
        geometry="CICY6836/model 136 option 23 plus frontier 691",
        scope_class="grammar-local",
        claim_scope=(
            "CICY6836 option-23 local pair-delta radius-2 grammar around the "
            "advanced queue target model 136 and anchors 87/95/139. Model 136 "
            "is retired under this grammar because focus-sourced q1 promotions "
            "are pre-cup obstructed and the only metric improvement is the "
            "already-followed frontier-691 one-Higgs boundary floor."
        ),
        stage="one_higgs_proton_safety_intersection_gate",
        minimal_obstruction_core={
            "focus_model": report["parameters"]["focus_model"],
            "source_models": report["parameters"]["source_models"],
            "radius": report["parameters"]["radius"],
            "frontier_size": summary["frontier_size"],
            "stage_counts": summary["stage_counts"],
            "q1_candidate_count": summary["q1_candidate_count"],
            "screened_candidate_count": summary["screened_candidate_count"],
            "model136_screened_count": len(focus_records),
            "model136_screen_status_counts": dict(
                Counter(item["screen_status"] for item in focus_records)
            ),
            "promotion_timeout_count": summary["promotion_timeout_count"],
            "boundary_improvement_record_count": summary[
                "boundary_improvement_record_count"
            ],
            "boundary_improvement_sources": sorted(
                {tuple(item["source_models"]) for item in report["boundary_improvement_records"]}
            ),
            "best_frontier": closest["frontier_index"],
            "best_source_models": closest["source_models"],
            "best_metrics": closest["metrics"],
            "model136_proton_safe_embedding_count": source["model136"][
                "proton_safe_embedding_count"
            ],
            "model87_one_higgs_pair_triplet_free_count": source["model87"][
                "one_higgs_pair_triplet_free_count"
            ],
            "model95_one_higgs_pair_triplet_free_count": source["model95"][
                "one_higgs_pair_triplet_free_count"
            ],
            "model139_cup_product_eligible_triplet_target_count": source[
                "model139"
            ]["cup_product_eligible_triplet_target_count"],
            "total_one_higgs_pair_triplet_free_embeddings": summary[
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "total_proton_safe_embeddings": summary["total_proton_safe_embeddings"],
            "total_one_higgs_proton_safe_embeddings": summary[
                "total_one_higgs_proton_safe_embeddings"
            ],
            "total_one_higgs_pre_cup_survivor_count": summary[
                "total_one_higgs_pre_cup_survivor_count"
            ],
            "total_pre_cup_survivor_count": summary["total_pre_cup_survivor_count"],
            "total_cup_product_eligible_triplet_target_count": summary[
                "total_cup_product_eligible_triplet_target_count"
            ],
            "first_pair_gate_status": report["parameters"]["first_pair_gate_status"],
        },
        cheap_prefilter="one_higgs_proton_safety_disjoint",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy6836_model136_intersection_forcing_search.json",
            "frontier_size": summary["frontier_size"],
            "q1_candidate_count": summary["q1_candidate_count"],
            "screened_candidate_count": summary["screened_candidate_count"],
            "model136_screened_count": len(focus_records),
            "promotion_timeout_count": summary["promotion_timeout_count"],
            "one_higgs_precup_survivor_record_count": summary[
                "one_higgs_precup_survivor_record_count"
            ],
            "one_higgs_proton_safe_intersection_record_count": summary[
                "one_higgs_proton_safe_intersection_record_count"
            ],
            "boundary_improvement_record_count": summary[
                "boundary_improvement_record_count"
            ],
            "best_frontier": closest["frontier_index"],
            "best_source_models": closest["source_models"],
            "one_higgs_pair_triplet_free_embeddings": summary[
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "proton_safe_embeddings": summary["total_proton_safe_embeddings"],
            "one_higgs_proton_safe_embeddings": summary[
                "total_one_higgs_proton_safe_embeddings"
            ],
            "cup_product_eligible_triplet_target_count": summary[
                "total_cup_product_eligible_triplet_target_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "one_higgs_proton_safety_disjoint",
                {
                    "requires_one_higgs_proton_safe": True,
                    "one_higgs_pair_triplet_free_count": summary[
                        "total_one_higgs_pair_triplet_free_embeddings"
                    ],
                    "proton_safe_embedding_count": summary[
                        "total_proton_safe_embeddings"
                    ],
                    "one_higgs_proton_safe_count": summary[
                        "total_one_higgs_proton_safe_embeddings"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy6836_model136_intersection_forcing_search.json",
            "experiments/latent_atlas/reports/cicy6836_model136_intersection_forcing_search_verification.json",
            "experiments/latent_atlas/reports/cicy6836_model186_frontier691_followup_search.json",
            "experiments/latent_atlas/reports/cicy6836_model186_frontier691_followup_search_verification.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement_verification.json",
            "reports/cicy6836_family_precup_promotion_gate.json",
            "reports/cicy6836_family_precup_promotion_gate_verification.json",
        ],
        representative_examples=[closest] + report["boundary_improvement_records"][:2],
        nearest_escape={
            "minimal_change": (
                "find a CICY6836 q1 branch whose one-Higgs/triplet-free embeddings "
                "also have zero dangerous operators, or improve beyond the "
                "already-followed frontier-691 floor"
            ),
            "next_generator": (
                "with existing-boundary targets exhausted, pivot to presentation "
                "bridge engines or exact product machinery rather than repeatedly "
                "rediscovering frontier 691"
            ),
        },
    )


def cicy6715_model215_computed_anchor_missing_higgs_cup_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("cicy6715_model215_intersection_forcing_search.json"))
    summary = report["summary"]
    source = report["source_boundary_metrics"]
    model215 = source["model215"]
    model336 = source["model336"]
    return syndrome(
        syndrome_id="cicy6715_model215_computed_anchor_missing_one_higgs_and_cup_radius2",
        title="CICY6715 computed proton-safe anchors miss both one-Higgs and triplet-cup gates",
        geometry="CICY6715/model 215 and 336 option 1",
        scope_class="grammar-local",
        claim_scope=(
            "CICY6715 option-1 local pair-delta radius-2 grammar around the "
            "component-computed proton-safe anchors 215 and 336. This closes "
            "those computed queue targets only; the model-766 unresolved "
            "character envelope remains a separate representative-resolution pivot."
        ),
        stage="one_higgs_and_triplet_cup_gate",
        minimal_obstruction_core={
            "focus_model": report["parameters"]["focus_model"],
            "source_models": report["parameters"]["source_models"],
            "radius": report["parameters"]["radius"],
            "frontier_size": summary["frontier_size"],
            "q1_candidate_count": summary["q1_candidate_count"],
            "screened_candidate_count": summary["screened_candidate_count"],
            "stage_counts": summary["stage_counts"],
            "promotion_timeout_count": summary["promotion_timeout_count"],
            "promotion_error_count": summary["promotion_error_count"],
            "component_unresolved_record_count": summary[
                "component_unresolved_record_count"
            ],
            "total_embeddings_screened": summary["total_embeddings_screened"],
            "total_one_higgs_pair_triplet_free_embeddings": summary[
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "total_one_higgs_proton_safe_embeddings": summary[
                "total_one_higgs_proton_safe_embeddings"
            ],
            "total_pre_cup_survivor_count": summary["total_pre_cup_survivor_count"],
            "total_cup_product_eligible_triplet_target_count": summary[
                "total_cup_product_eligible_triplet_target_count"
            ],
            "aggregate_obstruction_counts": summary["aggregate_obstruction_counts"],
            "aggregate_mass_support_class_counts": summary[
                "aggregate_mass_support_class_counts"
            ],
            "model215_wall_metrics": model215["wall_metrics"],
            "model336_wall_metrics": model336["wall_metrics"],
            "unresolved_envelope_used_as_seed": report["parameters"][
                "unresolved_envelope_used_as_seed"
            ],
            "unresolved_envelope_remains_live": report["interpretation"][
                "unresolved_envelope_remains_live"
            ],
        },
        cheap_prefilter="computed_anchor_missing_one_higgs_and_cup",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy6715_model215_intersection_forcing_search.json",
            "frontier_size": summary["frontier_size"],
            "q1_candidate_count": summary["q1_candidate_count"],
            "screened_candidate_count": summary["screened_candidate_count"],
            "promotion_timeout_count": summary["promotion_timeout_count"],
            "promotion_error_count": summary["promotion_error_count"],
            "component_unresolved_record_count": summary[
                "component_unresolved_record_count"
            ],
            "one_higgs_record_count": summary["one_higgs_record_count"],
            "one_higgs_proton_safe_intersection_record_count": summary[
                "one_higgs_proton_safe_intersection_record_count"
            ],
            "one_higgs_precup_survivor_record_count": summary[
                "one_higgs_precup_survivor_record_count"
            ],
            "cup_target_record_count": summary["cup_target_record_count"],
            "total_embeddings_screened": summary["total_embeddings_screened"],
            "total_one_higgs_pair_triplet_free_embeddings": summary[
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "total_pre_cup_survivor_count": summary["total_pre_cup_survivor_count"],
            "total_cup_product_eligible_triplet_target_count": summary[
                "total_cup_product_eligible_triplet_target_count"
            ],
            "unresolved_envelope_used_as_seed": report["parameters"][
                "unresolved_envelope_used_as_seed"
            ],
            "unresolved_envelope_remains_live": report["interpretation"][
                "unresolved_envelope_remains_live"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "computed_anchor_missing_one_higgs_and_cup",
                {
                    "requires_one_higgs_or_cup": True,
                    "component_characters_computed": model215[
                        "component_characters_computed"
                    ],
                    "all_embeddings_proton_safe": model215["wall_metrics"][
                        "all_embeddings_proton_safe"
                    ],
                    "one_higgs_pair_triplet_free_count": model215["wall_metrics"][
                        "one_higgs_pair_triplet_free_count"
                    ],
                    "pre_cup_survivor_count": model215["wall_metrics"][
                        "pre_cup_survivor_count"
                    ],
                    "cup_product_eligible_triplet_target_count": model215[
                        "wall_metrics"
                    ]["cup_product_eligible_triplet_target_count"],
                },
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy6715_model215_intersection_forcing_search.json",
            "experiments/latent_atlas/reports/cicy6715_model215_intersection_forcing_search_verification.json",
            "reports/cicy6715_6927_same_hodge_lateral_wall_metric_pass.json",
            "reports/cicy6715_6927_same_hodge_lateral_wall_metric_pass_verification.json",
            "reports/cicy6715_component_unresolved_envelope.json",
            "reports/cicy6715_component_unresolved_envelope_verification.json",
        ],
        representative_examples=report["closest_records"][:3],
        nearest_escape={
            "minimal_change": (
                "find a computed CICY6715 q1 branch with one-Higgs/triplet-free "
                "structure or a triplet-cup target while preserving proton safety; "
                "alternatively resolve the model-766 representative ambiguity"
            ),
            "next_generator": (
                "advance the cross-geometry queue to the next open target, or run "
                "a representative-resolution pass on the CICY6715 model-766 envelope "
                "if prioritizing that live ambiguity"
            ),
        },
    )


def cicy6715_model766_branch99_higher_map_syndrome() -> dict[str, Any]:
    report = load_json(
        latent_artifact("cicy6715_model766_branch99_representative_resolution.json")
    )
    scan = report["finite_order_scan"]
    target = report["higher_map_target"]
    default = report["pycicy_default_higher_map_audit"]["as_returned"]
    required = target["required_rank_split_to_realize_branch99"]
    return syndrome(
        syndrome_id="cicy6715_model766_branch99_higher_map_order_no_realization",
        title="CICY6715 model-766 branch99 shadow fails finite equivariant higher-map order scan",
        geometry="CICY6715/model 766 option 1 branch 99",
        scope_class="candidate-specific",
        claim_scope=(
            "CICY6715 model-766 option-1 branch99 representative-resolution "
            "target under the current pyCICY higher-map equation-order "
            "conventions. This is not a theorem over all possible equivariant "
            "higher-map constructions."
        ),
        stage="representative_equivariant_higher_map_realization",
        minimal_obstruction_core={
            "unresolved_pair": report["parameters"]["unresolved_pair"],
            "unresolved_line_bundle": report["parameters"][
                "unresolved_line_bundle"
            ],
            "source_entry": target["source_entry"],
            "target_entry": target["target_entry"],
            "source_e2_multiplicities": target["source_e2_multiplicities"],
            "target_e2_multiplicities": target["target_e2_multiplicities"],
            "h1_requested_multiplicities": report["branch_shadow_request"][
                "h1_requested_multiplicities"
            ],
            "h2_requested_multiplicities": report["branch_shadow_request"][
                "h2_requested_multiplicities"
            ],
            "required_rank_split": required,
            "pycicy_raw_rank": default["raw_rank"],
            "pycicy_raw_equivariance_residual": default[
                "raw_equivariance_residual"
            ],
            "averaged_irrep_rank_split": default["averaged_irrep_rank_split"],
            "averaged_rank": default["averaged_rank"],
            "permutation_count_tested": scan["permutation_count_tested"],
            "complete_permutation_scan": scan["complete_permutation_scan"],
            "first_certifying_order": scan["first_certifying_order"],
        },
        cheap_prefilter="higher_map_order_no_realization",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy6715_model766_branch99_representative_resolution.json",
            "clean_one_higgs_precup_shadow_count": report["branch_shadow_request"][
                "clean_one_higgs_precup_count"
            ],
            "permutation_count_tested": scan["permutation_count_tested"],
            "complete_permutation_scan": scan["complete_permutation_scan"],
            "branch_representative_certified": report["classification"][
                "branch99_representative_certified"
            ],
            "required_rank_total": sum(required.values()),
            "pycicy_raw_rank": default["raw_rank"],
            "averaged_rank": default["averaged_rank"],
            "prefilter_sample_passes": evaluate_prefilter(
                "higher_map_order_no_realization",
                {
                    "requires_representative_resolution": True,
                    "complete_permutation_scan": scan["complete_permutation_scan"],
                    "permutation_count_tested": scan["permutation_count_tested"],
                    "branch_representative_certified": report["classification"][
                        "branch99_representative_certified"
                    ],
                    "required_rank_total": sum(required.values()),
                    "pycicy_raw_rank": default["raw_rank"],
                    "averaged_rank": default["averaged_rank"],
                },
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy6715_model766_branch99_representative_resolution.json",
            "experiments/latent_atlas/reports/cicy6715_model766_branch99_representative_resolution_verification.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement_verification.json",
            "reports/cicy6715_component_unresolved_envelope.json",
            "reports/cicy6715_component_unresolved_envelope_verification.json",
        ],
        representative_examples=[
            report["branch_shadow_request"]["example"],
            scan["best_nearest_order"],
        ],
        nearest_escape={
            "minimal_change": (
                "construct an explicitly equivariant higher-map convention whose "
                "rank-7 image has irrep split 1/2/2/2, or find another branch "
                "whose representative split is resolved without this collision"
            ),
            "next_generator": (
                "advance the verified queue to the CICY6784 frontier-48 full "
                "chain-contraction fallback or to presentation-bridge targets"
            ),
        },
    )


def cicy6788_wall_breaker_one_higgs_proton_unsafe_syndrome() -> dict[str, Any]:
    report = load_json(artifact("cicy6788_obstruction_targeted_wall_breaker_search.json"))
    one_higgs_examples = [
        item
        for item in report["closest_records"]
        if item["wall_metrics"]["one_higgs_pair_triplet_free_count"] > 0
    ]
    proton_safe_examples = [
        item
        for item in report["closest_records"]
        if item["wall_metrics"]["all_embeddings_proton_safe"]
    ]
    example = one_higgs_examples[0]
    return syndrome(
        syndrome_id="cicy6788_wall_breaker_one_higgs_proton_unsafe",
        title="CICY6788 targeted wall-breaker keeps one-Higgs slices proton-unsafe",
        geometry="CICY6788/model 227 and 620 option 0",
        scope_class="grammar-local",
        claim_scope=(
            "CICY6788 option-0 active-column three-column and paired-rectangle "
            "wall-breaker grammar seeded from the verified radius-2 q1 boundary "
            "records for models 227 and 620. This is not a global CICY6788 no-go."
        ),
        stage="one_higgs_proton_safety_wall_breaker_gate",
        minimal_obstruction_core={
            "seed_count": report["summary"]["seed_count"],
            "frontier_size": report["summary"]["frontier_size"],
            "q1_candidate_count": report["summary"]["q1_candidate_count"],
            "screened_candidate_count": report["summary"]["screened_candidate_count"],
            "promoted_metric_improvement_count": report["summary"][
                "promoted_metric_improvement_count"
            ],
            "q1_candidate_counts_by_source": report["summary"][
                "q1_candidate_counts_by_source"
            ],
            "total_one_higgs_pair_triplet_free_embeddings": report["summary"][
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "total_one_higgs_proton_safe_embeddings": report["summary"][
                "total_one_higgs_proton_safe_embeddings"
            ],
            "total_pre_cup_survivor_count": report["summary"][
                "total_pre_cup_survivor_count"
            ],
            "total_cup_product_eligible_triplet_target_count": report["summary"][
                "total_cup_product_eligible_triplet_target_count"
            ],
            "source_wall_tradeoff": {
                "model227_one_higgs_min_danger": 2,
                "model620_all_embeddings_proton_safe_but_no_one_higgs": True,
            },
        },
        cheap_prefilter="one_higgs_proton_unsafe",
        replay_counts={
            "source": "reports/cicy6788_obstruction_targeted_wall_breaker_search.json",
            "frontier_size": report["summary"]["frontier_size"],
            "q1_candidate_count": report["summary"]["q1_candidate_count"],
            "screened_candidate_count": report["summary"]["screened_candidate_count"],
            "promoted_metric_improvement_count": report["summary"][
                "promoted_metric_improvement_count"
            ],
            "total_one_higgs_pair_triplet_free_embeddings": report["summary"][
                "total_one_higgs_pair_triplet_free_embeddings"
            ],
            "total_one_higgs_proton_safe_embeddings": report["summary"][
                "total_one_higgs_proton_safe_embeddings"
            ],
            "total_pre_cup_survivor_count": report["summary"][
                "total_pre_cup_survivor_count"
            ],
            "total_cup_product_eligible_triplet_target_count": report["summary"][
                "total_cup_product_eligible_triplet_target_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "one_higgs_proton_unsafe",
                {
                    "requires_one_higgs_proton_safe": True,
                    "one_higgs_pair_triplet_free_count": example["wall_metrics"][
                        "one_higgs_pair_triplet_free_count"
                    ],
                    "one_higgs_proton_safe_count": example["wall_metrics"][
                        "one_higgs_proton_safe_count"
                    ],
                    "min_dangerous_operator_count_among_one_higgs": example[
                        "wall_metrics"
                    ]["min_dangerous_operator_count_among_one_higgs"],
                },
            ),
        },
        evidence_artifacts=[
            "reports/cicy6788_obstruction_targeted_wall_breaker_search.json",
            "reports/cicy6788_obstruction_targeted_wall_breaker_search_verification.json",
            "reports/cicy6788_intersection_forcing_local_search_r2.json",
            "reports/cicy6788_intersection_forcing_local_search_r2_verification.json",
            "experiments/latent_atlas/reports/overlap_first_seed_queue.json",
            "experiments/latent_atlas/reports/overlap_first_seed_queue_verification.json",
        ],
        representative_examples=(one_higgs_examples[:2] + proton_safe_examples[:1]),
        nearest_escape={
            "minimal_change": (
                "find a CICY6788 option-0 q1 branch with positive one-Higgs "
                "count and zero dangerous operators in the same Wilson slice, "
                "then recover a triplet-cup/pre-cup target"
            ),
            "next_generator": (
                "avoid replaying this active-column wall-breaker grammar; use "
                "exact same-embedding overlap as an early gate on a broader "
                "geometry or presentation scan"
            ),
        },
    )


def cicy6784_cubic_yukawa_absent_syndrome() -> dict[str, Any]:
    report = load_json(artifact("cicy6784_model31_operator_yukawa_frontier.json"))
    summaries = report["operator_summaries"]
    up = summaries["up_type_10_10_5"]
    down = summaries["down_lepton_10_5bar_5bar"]
    proton = summaries["proton_components_10_5bar_5bar"]
    mass = summaries["higgs_mass_5bar_5_singlet"]
    neutral_down = [
        row
        for row in report["operator_tables"]["down_lepton_10_5bar_5bar"]
        if row["neutral_under_S_U1_5"]
    ]
    return syndrome(
        syndrome_id="cicy6784_strict_precup_cubic_yukawa_absent",
        title="Strict pre-cup survivor, but no renormalizable cubic Yukawa channel",
        geometry="CICY6784/model 31 option 2",
        scope_class="candidate-specific",
        claim_scope=(
            "Best strict survivor cicy6784_model31_option2_wilson_004 at the "
            "renormalizable cubic operator layer. This does not exclude "
            "higher-degree singlet-dressed Yukawa operators."
        ),
        stage="cubic_operator_yukawa_gate",
        minimal_obstruction_core={
            "selected_embedding": report["selected_embedding"]["label"],
            "one_higgs_precup_status": report["selected_embedding"]["classification"][
                "status"
            ],
            "up_type_cubic_allowed_count": up["allowed_count"],
            "down_lepton_cubic_allowed_count": down["allowed_count"],
            "proton_decay_allowed_count": proton["allowed_count"],
            "higgs_bilinear_degree_one_hits": mass[
                "degree_one_charge_neutral_count"
            ],
            "up_type_charge_neutral_count": up["charge_neutral_count"],
            "down_lepton_charge_neutral_count": down["charge_neutral_count"],
            "neutral_down_lepton_operator": neutral_down[0]["operator"]
            if neutral_down
            else None,
            "neutral_down_lepton_forbidden_reason": neutral_down[0][
                "down_lepton_forbidden_reason"
            ]
            if neutral_down
            else None,
        },
        cheap_prefilter="cubic_yukawa_absent",
        replay_counts={
            "source": "reports/cicy6784_model31_operator_yukawa_frontier.json",
            "up_type_operator_count": up["operator_count"],
            "up_type_cubic_allowed_count": up["allowed_count"],
            "down_lepton_operator_count": down["operator_count"],
            "down_lepton_cubic_allowed_count": down["allowed_count"],
            "proton_decay_allowed_count": proton["allowed_count"],
            "higgs_bilinear_degree_one_hits": mass[
                "degree_one_charge_neutral_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "cubic_yukawa_absent",
                {
                    "requires_renormalizable_cubic_yukawa": True,
                    "up_type_cubic_allowed_count": up["allowed_count"],
                    "down_lepton_cubic_allowed_count": down["allowed_count"],
                    "proton_decay_allowed_count": proton["allowed_count"],
                    "higher_degree_yukawa_escape_allowed": True,
                },
            ),
        },
        evidence_artifacts=[
            "reports/cicy6784_model31_lead_dossier.json",
            "reports/cicy6784_model31_lead_dossier_verification.json",
            "reports/cicy6784_model31_operator_yukawa_frontier.json",
            "reports/cicy6784_model31_operator_yukawa_frontier_verification.json",
        ],
        representative_examples=[
            report["selected_embedding"],
            {
                "up_type_summary": up,
                "down_lepton_summary": down,
                "neutral_down_lepton_candidates": neutral_down,
            },
        ],
        nearest_escape={
            "minimal_change": (
                "allow finite-degree singlet monoids to dress 10*10*5 or "
                "10*5bar*5bar operators while preserving proton safety and "
                "Higgs doublet protection"
            ),
            "next_generator": report["next_pivot"]["recommended_goal"],
            "stop_rule": report["next_pivot"]["stop_rule"],
        },
    )


def cicy6784_higher_degree_yukawa_charge_mismatch_syndrome() -> dict[str, Any]:
    report = load_json(artifact("cicy6784_model31_higher_degree_yukawa_search.json"))
    summary = report["summary"]
    up = summary["up_type"]
    down = summary["down_lepton"]
    up_boundary = report["nearest_charge_boundaries"]["up_type_10_10_5"][0]
    down_boundary = report["nearest_charge_boundaries"]["down_lepton_10_5bar_5bar"][0]
    return syndrome(
        syndrome_id="cicy6784_higher_degree_le3_yukawa_charge_mismatch",
        title="Degree<=3 singlet-dressed Yukawa monoids never reach charge neutrality",
        geometry="CICY6784/model 31 option 2",
        scope_class="candidate-specific",
        claim_scope=(
            "Best strict survivor cicy6784_model31_option2_wilson_004 with "
            "representative-compatible singlet monoids of degree <= 3. This "
            "does not exclude degree > 3 monoids, altered charge structure, "
            "other Wilson embeddings, or other geometries."
        ),
        stage="bounded_singlet_dressed_yukawa_charge_gate",
        minimal_obstruction_core={
            "selected_embedding": report["selected_embedding"]["label"],
            "max_singlet_monoid_degree": summary["max_singlet_monoid_degree"],
            "singlet_label_count": summary["singlet_label_count"],
            "monoid_count": summary["monoid_count"],
            "up_type_operator_monoid_count": up["operator_monoid_count"],
            "down_lepton_operator_monoid_count": down["operator_monoid_count"],
            "up_type_charge_neutral_count": up["charge_neutral_count"],
            "down_lepton_charge_neutral_count": down["charge_neutral_count"],
            "safe_yukawa_operator_monoid_count": summary[
                "safe_yukawa_operator_monoid_count"
            ],
            "nearest_up_type_charge_defect": summary[
                "nearest_up_type_charge_defect"
            ],
            "nearest_down_lepton_charge_defect": summary[
                "nearest_down_lepton_charge_defect"
            ],
        },
        cheap_prefilter="higher_degree_yukawa_charge_mismatch",
        replay_counts={
            "source": "reports/cicy6784_model31_higher_degree_yukawa_search.json",
            "monoid_degree_counts": summary["monoid_degree_counts"],
            "up_type_operator_monoid_count": up["operator_monoid_count"],
            "down_lepton_operator_monoid_count": down["operator_monoid_count"],
            "up_type_charge_neutral_count": up["charge_neutral_count"],
            "down_lepton_charge_neutral_count": down["charge_neutral_count"],
            "safe_yukawa_operator_monoid_count": summary[
                "safe_yukawa_operator_monoid_count"
            ],
            "nearest_up_type_charge_defect": summary[
                "nearest_up_type_charge_defect"
            ],
            "nearest_down_lepton_charge_defect": summary[
                "nearest_down_lepton_charge_defect"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "higher_degree_yukawa_charge_mismatch",
                {
                    "requires_higher_degree_yukawa": True,
                    "max_singlet_monoid_degree": summary[
                        "max_singlet_monoid_degree"
                    ],
                    "degree_bound": 3,
                    "up_type_charge_neutral_count": up["charge_neutral_count"],
                    "down_lepton_charge_neutral_count": down[
                        "charge_neutral_count"
                    ],
                    "safe_yukawa_operator_monoid_count": summary[
                        "safe_yukawa_operator_monoid_count"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "reports/cicy6784_model31_higher_degree_yukawa_search.json",
            "reports/cicy6784_model31_higher_degree_yukawa_search_verification.json",
            "reports/cicy6784_model31_operator_yukawa_frontier.json",
            "reports/cicy6784_model31_operator_yukawa_frontier_verification.json",
        ],
        representative_examples=[
            report["selected_embedding"],
            {
                "nearest_up_type_charge_boundary": up_boundary,
                "nearest_down_lepton_charge_boundary": down_boundary,
            },
        ],
        nearest_escape={
            "minimal_change": (
                "lower the down/lepton trace-neutral L1 defect from 2 to 0 "
                "or the up-type defect from 4 to 0 while preserving the strict "
                "one-Higgs/proton-safe pre-cup gates"
            ),
            "escape_hatches": [
                "extend singlet monoids beyond degree 3",
                "alter the singlet charge span through a local bundle move",
                "switch Wilson embedding or geometry while preserving exact overlap",
            ],
            "next_generator": (
                "charge-defect-guided exact-overlap search seeded by the nearest "
                "CICY6784 higher-degree Yukawa boundaries"
            ),
        },
    )


def cicy6784_charge_defect_no_improvement_syndrome() -> dict[str, Any]:
    report = load_json(artifact("cicy6784_charge_defect_guided_yukawa_escape_search.json"))
    summary = report["summary"]
    nearest = report["nearest_records"][0]
    higher = nearest["higher_degree_yukawa"]
    return syndrome(
        syndrome_id="cicy6784_radius1_charge_defect_no_improvement",
        title="Charge-defect-guided local moves do not lower the Yukawa charge boundary",
        geometry="CICY6784/model 31 option 2",
        scope_class="candidate-specific",
        claim_scope=(
            "Radius-1 pair-delta plus rectangle local grammar around the verified "
            "CICY6784/model31 option-2 strict seed, with degree <= 3 singlet "
            "monoids. This does not exclude larger radius, altered move grammar, "
            "degree > 3 monoids, different Wilson embeddings, or other geometries."
        ),
        stage="charge_defect_guided_local_escape_gate",
        minimal_obstruction_core={
            "pair_delta_radius": report["parameters"]["pair_delta_radius"],
            "include_rectangles": report["parameters"]["include_rectangles"],
            "frontier_size": summary["frontier_size"],
            "stage_counts": summary["stage_counts"],
            "q1_candidate_count": summary["q1_candidate_count"],
            "screened_candidate_count": summary["screened_candidate_count"],
            "promotion_timeout_count": summary["promotion_timeout_count"],
            "strict_pre_cup_record_count": summary["strict_pre_cup_record_count"],
            "safe_yukawa_record_count": summary["safe_yukawa_record_count"],
            "charge_defect_improved_record_count": summary[
                "charge_defect_improved_record_count"
            ],
            "best_nearest_up_type_charge_defect": summary[
                "best_nearest_up_type_charge_defect"
            ],
            "best_nearest_down_lepton_charge_defect": summary[
                "best_nearest_down_lepton_charge_defect"
            ],
        },
        cheap_prefilter="charge_defect_guided_no_improvement",
        replay_counts={
            "source": "reports/cicy6784_charge_defect_guided_yukawa_escape_search.json",
            "frontier_size": summary["frontier_size"],
            "stage_counts": summary["stage_counts"],
            "q1_candidate_count": summary["q1_candidate_count"],
            "screened_candidate_count": summary["screened_candidate_count"],
            "promotion_timeout_count": summary["promotion_timeout_count"],
            "strict_pre_cup_record_count": summary["strict_pre_cup_record_count"],
            "safe_yukawa_record_count": summary["safe_yukawa_record_count"],
            "charge_defect_improved_record_count": summary[
                "charge_defect_improved_record_count"
            ],
            "nearest_up_type_charge_defect": higher["nearest_up_type_charge_defect"],
            "nearest_down_lepton_charge_defect": higher[
                "nearest_down_lepton_charge_defect"
            ],
            "higher_degree_prefilter_hits": higher["prefilter_hits"],
            "prefilter_sample_passes": evaluate_prefilter(
                "charge_defect_guided_no_improvement",
                {
                    "requires_charge_defect_escape": True,
                    "frontier_size": summary["frontier_size"],
                    "q1_candidate_count": summary["q1_candidate_count"],
                    "promotion_timeout_count": summary["promotion_timeout_count"],
                    "safe_yukawa_record_count": summary["safe_yukawa_record_count"],
                    "charge_defect_improved_record_count": summary[
                        "charge_defect_improved_record_count"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "reports/cicy6784_charge_defect_guided_yukawa_escape_search.json",
            "reports/cicy6784_charge_defect_guided_yukawa_escape_search_verification.json",
            "reports/cicy6784_model31_higher_degree_yukawa_search.json",
            "reports/cicy6784_model31_higher_degree_yukawa_search_verification.json",
        ],
        representative_examples=[
            {
                "nearest_promoted_record": nearest,
                "bounded_search_interpretation": report["interpretation"],
            }
        ],
        nearest_escape={
            "minimal_change": (
                "find a q=1 branch that lowers the down/lepton defect from 2 "
                "to 0 or the up-type defect from 4 to 0 while preserving the "
                "strict one-Higgs/proton-safe pre-cup gates"
            ),
            "closed_boundary": (
                "within radius-1 pair-delta plus rectangle moves, every q1 "
                "candidate is the original seed, so no local downhill defect "
                "move is available in this grammar"
            ),
            "next_pivots": [
                "increase radius with an early charge-defect target",
                "use multi-column or singlet-charge-span-aware moves",
                "extend monoids beyond degree 3",
                "pivot to another exact-overlap seed or geometry",
            ],
        },
    )


def cicy6784_upstream_transferred_m3_boundary_syndrome() -> dict[str, Any]:
    report = load_json(artifact("cicy6784_upstream_complement_map_audit.json"))
    direct = report["direct_E1_triple_product_audit"]
    origin = direct["origin_product_diagnostic"]
    transferred = report["transferred_m3_requirements"]
    classification = report["classification"]
    return syndrome(
        syndrome_id="cicy6784_upstream_direct_e1_requires_transferred_m3",
        title="Effective complement route has final top pairing, but upstream direct E1 product vanishes",
        geometry="CICY6784/model 31 option 2",
        scope_class="candidate-specific",
        claim_scope=(
            "Frontier-48 degree-4 down/lepton effective-complement route with "
            "anchor 5bar_04. This is not an MSSM no-go: it records that the "
            "plain E1 route is blocked and that coefficient rank now requires "
            "a transferred m3/homotopy primitive or a different direct-product "
            "factorization."
        ),
        stage="effective_complement_exact_engine_gate",
        minimal_obstruction_core={
            "target_channel": report["target_pairing"]["channel_id"],
            "target_anchor": report["target_pairing"]["anchor_leg_id"],
            "top_pairing_rank": report["target_pairing"]["top_pairing_rank"],
            "top_pairing_equivariant": report["target_pairing"][
                "top_pairing_equivariant"
            ],
            "upstream_operator": "10_4*5bar_12*S_34",
            "line_bundle_sum": direct["line_bundle_sum"],
            "target_line_bundle": direct["target_line_bundle"],
            "source_entries": direct["source_entries"],
            "target_entry": direct["target_entry"],
            "source_koszul_degree_sum": direct["source_koszul_degree_sum"],
            "target_koszul_degree": direct["target_entry"][0],
            "direct_origin_wedge_survivor_count": origin[
                "direct_origin_wedge_survivor_count"
            ],
            "origin_failure_reasons": sorted(
                {piece["failure_reason"] for piece in origin["pieces"]}
            ),
            "ten_kernel_dimension": report["ten_kernel_audit"][
                "kernel_dimension"
            ],
            "missing_primitive": transferred["missing_primitive"],
        },
        cheap_prefilter="upstream_direct_e1_requires_transferred_m3",
        replay_counts={
            "source": "reports/cicy6784_upstream_complement_map_audit.json",
            "target_top_pairing_rank": report["target_pairing"][
                "top_pairing_rank"
            ],
            "direct_origin_piece_count": origin["piece_count"],
            "direct_origin_wedge_survivor_count": origin[
                "direct_origin_wedge_survivor_count"
            ],
            "ten_kernel_dimension": report["ten_kernel_audit"][
                "kernel_dimension"
            ],
            "transferred_m3_output_degree": transferred["output_degree"],
            "coefficient_rank_status": classification["coefficient_rank_status"],
            "prefilter_sample_passes": evaluate_prefilter(
                "upstream_direct_e1_requires_transferred_m3",
                {
                    "requires_effective_complement_map": True,
                    "direct_E1_triple_product_status": classification[
                        "direct_upstream_E1_triple_product_status"
                    ],
                    "direct_origin_wedge_survivor_count": origin[
                        "direct_origin_wedge_survivor_count"
                    ],
                    "source_koszul_degree_sum": direct[
                        "source_koszul_degree_sum"
                    ],
                    "target_koszul_degree": direct["target_entry"][0],
                    "transferred_m3_complement_map_status": classification[
                        "transferred_m3_complement_map_status"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "reports/cicy6784_upstream_complement_map_audit.json",
            "reports/cicy6784_upstream_complement_map_audit_verification.json",
            "reports/cicy6784_direct_top_pairing_probe.json",
            "reports/cicy6784_direct_top_pairing_probe_verification.json",
        ],
        representative_examples=[
            {
                "target_pairing": report["target_pairing"],
                "direct_E1_triple_product_audit": direct,
                "ten_kernel_audit": report["ten_kernel_audit"],
            }
        ],
        nearest_escape={
            "minimal_change": (
                "compute a transferred m3 matrix into the 4-dimensional H2 "
                "complement, or find a factorization whose upstream product "
                "has a direct E1 survivor into the complement"
            ),
            "next_engine_requirement": report["next_pivot"]["status"],
            "first_target": report["next_pivot"]["first_target"],
            "stop_rule": report["next_pivot"]["stop_rule"],
        },
    )


def cicy6784_transferred_m3_no_direct_tree_syndrome() -> dict[str, Any]:
    report = load_json(artifact("cicy6784_transferred_m3_route_inventory.json"))
    summary = report["summary"]
    classification = report["classification"]
    compact_routes = [
        {
            "tree": route["tree"],
            "intermediate_line_bundle": route["intermediate_line_bundle"],
            "intermediate_cohomology": route["intermediate_cohomology"],
            "binary_product_status_counts": route[
                "binary_product_status_counts"
            ],
            "homotopy_eligible_direct_product_count": route[
                "homotopy_eligible_direct_product_count"
            ],
            "final_direct_survivor_count": route[
                "final_direct_survivor_count"
            ],
            "route_status": route["route_status"],
        }
        for route in report["route_records"]
    ]
    return syndrome(
        syndrome_id="cicy6784_transferred_m3_no_direct_tree_survivor",
        title="Transferred-m3 route has no homotopy-eligible direct tree term",
        geometry="CICY6784/model 31 option 2",
        scope_class="candidate-specific",
        claim_scope=(
            "Frontier-48 degree-4 down/lepton effective-complement route under "
            "the standard direct-tree inventory. This does not prove the full "
            "transferred m3 coefficient is zero; it says a cheap direct-tree "
            "wrapper around the existing E1 product data is unavailable."
        ),
        stage="transferred_m3_direct_tree_inventory_gate",
        minimal_obstruction_core={
            "target_line_bundle": report["target_complement"]["line_bundle"],
            "target_cohomology": report["target_complement"]["cohomology"],
            "route_count": summary["route_count"],
            "route_status_counts": summary["route_status_counts"],
            "homotopy_eligible_direct_product_total": summary[
                "homotopy_eligible_direct_product_total"
            ],
            "final_direct_tree_survivor_total": summary[
                "final_direct_tree_survivor_total"
            ],
            "route_obstructions": compact_routes,
        },
        cheap_prefilter="transferred_m3_direct_tree_no_survivor",
        replay_counts={
            "source": "reports/cicy6784_transferred_m3_route_inventory.json",
            "route_count": summary["route_count"],
            "direct_binary_target_piece_total": summary[
                "direct_binary_target_piece_total"
            ],
            "homotopy_eligible_direct_product_total": summary[
                "homotopy_eligible_direct_product_total"
            ],
            "final_direct_tree_survivor_total": summary[
                "final_direct_tree_survivor_total"
            ],
            "route_status_counts": summary["route_status_counts"],
            "coefficient_rank_status": classification["coefficient_rank_status"],
            "prefilter_sample_passes": evaluate_prefilter(
                "transferred_m3_direct_tree_no_survivor",
                {
                    "requires_transferred_m3": True,
                    "route_count": summary["route_count"],
                    "homotopy_eligible_direct_product_total": summary[
                        "homotopy_eligible_direct_product_total"
                    ],
                    "final_direct_tree_survivor_total": summary[
                        "final_direct_tree_survivor_total"
                    ],
                    "standard_m3_direct_tree_inventory_status": classification[
                        "standard_m3_direct_tree_inventory_status"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "reports/cicy6784_transferred_m3_route_inventory.json",
            "reports/cicy6784_transferred_m3_route_inventory_verification.json",
            "reports/cicy6784_upstream_complement_map_audit.json",
            "reports/cicy6784_upstream_complement_map_audit_verification.json",
        ],
        representative_examples=[
            {
                "candidate_identity": report["candidate_identity"],
                "compact_routes": compact_routes,
            }
        ],
        nearest_escape={
            "minimal_change": (
                "find an effective-complement route with at least one "
                "homotopy-eligible binary direct product, or implement the "
                "full chain-contraction/homotopy-transfer convention"
            ),
            "next_engine_requirement": report["next_pivot"]["status"],
            "first_engine_target": report["next_pivot"]["first_engine_target"],
            "search_escape": report["next_pivot"]["search_escape"],
            "stop_rule": report["next_pivot"]["stop_rule"],
        },
    )


def cicy6784_preferred_routes_no_homotopy_seed_syndrome() -> dict[str, Any]:
    report = load_json(artifact("cicy6784_effective_complement_route_ranker.json"))
    summary = report["summary"]
    classification = report["classification"]
    top = report["ranked_factorizations"][0]
    compact_ranked = [
        {
            "channel_id": record["channel_id"],
            "anchor_leg_id": record["anchor_leg_id"],
            "complement_leg_ids": record["complement_leg_ids"],
            "direct_top_pairing_rank": record["direct_top_pairing_rank"],
            "direct_binary_target_piece_total": record[
                "direct_binary_target_piece_total"
            ],
            "direct_binary_product_rank_total": record[
                "direct_binary_product_rank_total"
            ],
            "homotopy_eligible_direct_product_total": record[
                "homotopy_eligible_direct_product_total"
            ],
            "priority_class": record["priority_class"],
            "rank_key": record["rank_key"],
        }
        for record in report["ranked_factorizations"]
    ]
    return syndrome(
        syndrome_id="cicy6784_preferred_effective_routes_no_homotopy_seed",
        title="Preferred effective-complement routes lack homotopy-eligible binary seeds",
        geometry="CICY6784/model 31 option 2",
        scope_class="candidate-specific",
        claim_scope=(
            "All six preferred matter-anchored effective-complement "
            "factorizations in the CICY6784 frontier-48 lead. This does not "
            "exclude full chain contraction, non-preferred factorizations, "
            "changed generators, or other geometries."
        ),
        stage="effective_complement_route_ranking_gate",
        minimal_obstruction_core={
            "factorization_count": summary["factorization_count"],
            "priority_class_counts": summary["priority_class_counts"],
            "homotopy_eligible_factorization_count": summary[
                "homotopy_eligible_factorization_count"
            ],
            "direct_binary_target_factorization_count": summary[
                "direct_binary_target_factorization_count"
            ],
            "max_homotopy_eligible_direct_products": summary[
                "max_homotopy_eligible_direct_products"
            ],
            "max_direct_binary_target_pieces": summary[
                "max_direct_binary_target_pieces"
            ],
            "best_near_boundary": compact_ranked[0],
        },
        cheap_prefilter="preferred_effective_routes_no_homotopy_seed",
        replay_counts={
            "source": "reports/cicy6784_effective_complement_route_ranker.json",
            "factorization_count": summary["factorization_count"],
            "priority_class_counts": summary["priority_class_counts"],
            "homotopy_eligible_factorization_count": summary[
                "homotopy_eligible_factorization_count"
            ],
            "direct_binary_target_factorization_count": summary[
                "direct_binary_target_factorization_count"
            ],
            "max_homotopy_eligible_direct_products": summary[
                "max_homotopy_eligible_direct_products"
            ],
            "max_direct_binary_target_pieces": summary[
                "max_direct_binary_target_pieces"
            ],
            "route_ranker_status": classification["route_ranker_status"],
            "prefilter_sample_passes": evaluate_prefilter(
                "preferred_effective_routes_no_homotopy_seed",
                {
                    "requires_effective_complement_route": True,
                    "factorization_count": summary["factorization_count"],
                    "homotopy_eligible_factorization_count": summary[
                        "homotopy_eligible_factorization_count"
                    ],
                    "max_homotopy_eligible_direct_products": summary[
                        "max_homotopy_eligible_direct_products"
                    ],
                    "route_ranker_status": classification[
                        "route_ranker_status"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "reports/cicy6784_effective_complement_route_ranker.json",
            "reports/cicy6784_effective_complement_route_ranker_verification.json",
            "reports/cicy6784_transferred_m3_route_inventory.json",
            "reports/cicy6784_transferred_m3_route_inventory_verification.json",
        ],
        representative_examples=[
            {
                "top_ranked_factorization": top,
                "compact_ranked_factorizations": compact_ranked,
            }
        ],
        nearest_escape={
            "minimal_change": (
                "increase homotopy_eligible_direct_product_total above zero "
                "for at least one effective-complement route"
            ),
            "next_generator_feature": report["next_pivot"][
                "recommended_generator_feature"
            ],
            "next_pivot": report["next_pivot"]["status"],
            "stop_rule": report["next_pivot"]["stop_rule"],
        },
    )


def cicy6784_single_anchor_no_homotopy_seed_syndrome() -> dict[str, Any]:
    report = load_json(artifact("cicy6784_single_anchor_homotopy_seed_queue.json"))
    summary = report["summary"]
    classification = report["classification"]
    compact_ranked = [
        {
            "channel_id": record["channel_id"],
            "anchor_leg_id": record["anchor_leg_id"],
            "anchor_source": record["anchor_source"],
            "selection_valid_matter_anchor": record[
                "selection_valid_matter_anchor"
            ],
            "direct_top_pairing_rank": record["direct_top_pairing_rank"],
            "direct_binary_target_piece_total": record[
                "direct_binary_target_piece_total"
            ],
            "homotopy_eligible_direct_product_total": record[
                "homotopy_eligible_direct_product_total"
            ],
            "route_status": record["route_status"],
            "frontier_rank_key": record["frontier_rank_key"],
        }
        for record in report["ranked_routes"]
    ]
    return syndrome(
        syndrome_id="cicy6784_single_anchor_effective_routes_no_homotopy_seed",
        title="Single-anchor effective-complement queue has no promotable homotopy seed",
        geometry="CICY6784/model 31 option 2",
        scope_class="candidate-specific",
        claim_scope=(
            "All eleven single-anchor effective-complement factorizations in "
            "the CICY6784 frontier-48 lead. This extends the preferred-route "
            "no-go but does not exclude multi-stage complement partitions, "
            "nearby deformations, other exact-overlap geometries, or full "
            "chain contraction."
        ),
        stage="single_anchor_effective_route_queue_gate",
        minimal_obstruction_core={
            "single_anchor_route_count": summary["single_anchor_route_count"],
            "selection_valid_matter_anchor_count": summary[
                "selection_valid_matter_anchor_count"
            ],
            "shadow_route_count": summary["shadow_route_count"],
            "route_status_counts": summary["route_status_counts"],
            "channel_status_counts": summary["channel_status_counts"],
            "homotopy_positive_route_count": summary[
                "homotopy_positive_route_count"
            ],
            "promotable_homotopy_seed_count": summary[
                "promotable_homotopy_seed_count"
            ],
            "max_homotopy_eligible_direct_products": summary[
                "max_homotopy_eligible_direct_products"
            ],
            "max_valid_homotopy_eligible_direct_products": summary[
                "max_valid_homotopy_eligible_direct_products"
            ],
            "best_valid_route": summary["best_valid_route"],
            "best_shadow_boundary": next(
                record
                for record in compact_ranked
                if not record["selection_valid_matter_anchor"]
            ),
        },
        cheap_prefilter="single_anchor_effective_routes_no_homotopy_seed",
        replay_counts={
            "source": "reports/cicy6784_single_anchor_homotopy_seed_queue.json",
            "single_anchor_route_count": summary["single_anchor_route_count"],
            "selection_valid_matter_anchor_count": summary[
                "selection_valid_matter_anchor_count"
            ],
            "shadow_route_count": summary["shadow_route_count"],
            "route_status_counts": summary["route_status_counts"],
            "homotopy_positive_route_count": summary[
                "homotopy_positive_route_count"
            ],
            "promotable_homotopy_seed_count": summary[
                "promotable_homotopy_seed_count"
            ],
            "max_homotopy_eligible_direct_products": summary[
                "max_homotopy_eligible_direct_products"
            ],
            "single_anchor_route_queue_status": classification[
                "single_anchor_route_queue_status"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "single_anchor_effective_routes_no_homotopy_seed",
                {
                    "requires_single_anchor_effective_route": True,
                    "single_anchor_route_count": summary[
                        "single_anchor_route_count"
                    ],
                    "selection_valid_matter_anchor_count": summary[
                        "selection_valid_matter_anchor_count"
                    ],
                    "promotable_homotopy_seed_count": summary[
                        "promotable_homotopy_seed_count"
                    ],
                    "max_homotopy_eligible_direct_products": summary[
                        "max_homotopy_eligible_direct_products"
                    ],
                    "single_anchor_route_queue_status": classification[
                        "single_anchor_route_queue_status"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "reports/cicy6784_single_anchor_homotopy_seed_queue.json",
            "reports/cicy6784_single_anchor_homotopy_seed_queue_verification.json",
            "reports/cicy6784_effective_complement_route_ranker.json",
            "reports/cicy6784_effective_complement_route_ranker_verification.json",
        ],
        representative_examples=[
            {
                "best_valid_route": summary["best_valid_route"],
                "compact_ranked_routes": compact_ranked,
            }
        ],
        nearest_escape={
            "minimal_change": (
                "find at least one valid effective-complement route with "
                "positive homotopy_eligible_direct_product_total"
            ),
            "next_generator_feature": report["next_pivot"][
                "recommended_generator_feature"
            ],
            "next_pivot": report["next_pivot"]["status"],
            "escape_hatches": report["next_pivot"][
                "route_grammar_escape_hatches"
            ],
            "stop_rule": report["next_pivot"]["stop_rule"],
        },
    )


def cicy6784_multistage_first_pair_no_homotopy_seed_syndrome() -> dict[str, Any]:
    report = load_json(artifact("cicy6784_multistage_homotopy_seed_closure.json"))
    summary = report["summary"]
    classification = report["classification"]
    valid = summary["valid_first_pair_slots"]
    all_slots = summary["all_first_pair_slots"]
    best = summary["best_valid_first_pair_boundary"]
    return syndrome(
        syndrome_id="cicy6784_multistage_first_pair_no_homotopy_seed",
        title="Cheap multi-stage direct-tree routes are blocked at the first H1-H1 pair",
        geometry="CICY6784/model 31 option 2",
        scope_class="candidate-specific",
        claim_scope=(
            "The cheap direct-tree multi-stage complement grammar for the "
            "CICY6784 frontier-48 lead. Every route in this grammar has an "
            "initial H1-H1 binary product; this does not compute or exclude "
            "full transferred higher products from an explicit chain "
            "contraction."
        ),
        stage="multi_stage_direct_tree_first_pair_gate",
        minimal_obstruction_core={
            "single_anchor_route_count": summary["single_anchor_route_count"],
            "selection_valid_matter_anchor_count": summary[
                "selection_valid_matter_anchor_count"
            ],
            "route_count_by_complement_input_count": summary[
                "route_count_by_complement_input_count"
            ],
            "all_first_pair_slot_count": all_slots["first_pair_slot_count"],
            "valid_first_pair_slot_count": valid["first_pair_slot_count"],
            "valid_direct_target_first_pair_slot_count": valid[
                "direct_target_first_pair_slot_count"
            ],
            "valid_homotopy_eligible_first_pair_slot_count": valid[
                "homotopy_eligible_first_pair_slot_count"
            ],
            "valid_product_piece_status_counts": valid[
                "product_piece_status_counts"
            ],
            "best_valid_first_pair_boundary": best,
        },
        cheap_prefilter="multistage_first_pair_no_homotopy_seed",
        replay_counts={
            "source": "reports/cicy6784_multistage_homotopy_seed_closure.json",
            "all_first_pair_slot_count": all_slots["first_pair_slot_count"],
            "valid_first_pair_slot_count": valid["first_pair_slot_count"],
            "valid_direct_target_first_pair_slot_count": valid[
                "direct_target_first_pair_slot_count"
            ],
            "valid_homotopy_eligible_first_pair_slot_count": valid[
                "homotopy_eligible_first_pair_slot_count"
            ],
            "multi_stage_direct_tree_status": classification[
                "multi_stage_direct_tree_status"
            ],
            "coefficient_rank_status": classification["coefficient_rank_status"],
            "prefilter_sample_passes": evaluate_prefilter(
                "multistage_first_pair_no_homotopy_seed",
                {
                    "requires_multistage_direct_tree_route": True,
                    "valid_first_pair_slot_count": valid["first_pair_slot_count"],
                    "valid_homotopy_eligible_first_pair_slot_count": valid[
                        "homotopy_eligible_first_pair_slot_count"
                    ],
                    "valid_direct_target_first_pair_slot_count": valid[
                        "direct_target_first_pair_slot_count"
                    ],
                    "multi_stage_direct_tree_status": classification[
                        "multi_stage_direct_tree_status"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "reports/cicy6784_multistage_homotopy_seed_closure.json",
            "reports/cicy6784_multistage_homotopy_seed_closure_verification.json",
            "reports/cicy6784_single_anchor_homotopy_seed_queue.json",
            "reports/cicy6784_single_anchor_homotopy_seed_queue_verification.json",
        ],
        representative_examples=[
            {
                "best_valid_first_pair_boundary": best,
                "valid_first_pair_slots": valid,
                "claim_boundary": report["interpretation"]["claim_boundary"],
            }
        ],
        nearest_escape={
            "minimal_change": (
                "find a valid first H1-H1 pair with positive "
                "homotopy_eligible_direct_product_count"
            ),
            "next_pivot": report["next_pivot"]["status"],
            "generator_feature": report["next_pivot"]["generator_feature"],
            "recommended_next_pass": report["next_pivot"][
                "recommended_next_pass"
            ],
            "stop_rule": report["next_pivot"]["stop_rule"],
        },
    )


def cicy6784_chain_contraction_fallback_syndrome() -> dict[str, Any]:
    report = load_json(artifact("cicy6784_frontier48_chain_contraction_fallback.json"))
    standard = report["standard_m3_zero_certificate"]
    capability = report["pycicy_capability_probe"]
    classification = report["classification"]
    return syndrome(
        syndrome_id="cicy6784_frontier48_chain_contraction_fallback_closed_current_engine",
        title="Frontier-48 exact-engine fallback closes: standard m3 zero, no chain API",
        geometry="CICY6784/model 31 option 2 frontier 48",
        scope_class="candidate-specific",
        claim_scope=(
            "CICY6784 frontier-48 exact-engine fallback under the current "
            "pyCICY/local symbolic verifier. This is not a theorem over every "
            "possible hand-built A-infinity/Yoneda convention; adding a real "
            "product-plus-chain-contraction engine is an explicit escape hatch."
        ),
        stage="exact_engine_chain_contraction_fallback_gate",
        minimal_obstruction_core={
            "queue_target": report["queue_target"]["target_id"],
            "target_complement": report["target_complement"],
            "standard_m3_tree_count": standard["standard_m3_tree_count"],
            "product_piece_count": standard["product_piece_count"],
            "product_status_counts": standard["product_status_counts"],
            "direct_binary_target_piece_total": standard[
                "direct_binary_target_piece_total"
            ],
            "homotopy_eligible_direct_product_total": standard[
                "homotopy_eligible_direct_product_total"
            ],
            "final_direct_tree_survivor_total": standard[
                "final_direct_tree_survivor_total"
            ],
            "standard_m3_matrix_rank": standard["standard_m3_matrix_rank"],
            "has_exposed_product_plus_chain_contraction_api": capability[
                "has_exposed_product_plus_chain_contraction_api"
            ],
            "map_substrate_methods_available": capability[
                "map_substrate_methods_available"
            ],
        },
        cheap_prefilter="chain_contraction_fallback_closed_current_engine",
        replay_counts={
            "source": "reports/cicy6784_frontier48_chain_contraction_fallback.json",
            "standard_m3_tree_count": standard["standard_m3_tree_count"],
            "product_piece_count": standard["product_piece_count"],
            "direct_binary_target_piece_total": standard[
                "direct_binary_target_piece_total"
            ],
            "homotopy_eligible_direct_product_total": standard[
                "homotopy_eligible_direct_product_total"
            ],
            "standard_m3_matrix_rank": standard["standard_m3_matrix_rank"],
            "has_exposed_product_plus_chain_contraction_api": capability[
                "has_exposed_product_plus_chain_contraction_api"
            ],
            "queue_target_closed_under_current_engine": classification[
                "queue_target_closed_under_current_engine"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "chain_contraction_fallback_closed_current_engine",
                {
                    "requires_chain_contraction_fallback": True,
                    "fallback_status": report["status"],
                    "standard_m3_tree_count": standard["standard_m3_tree_count"],
                    "standard_m3_matrix_rank": standard["standard_m3_matrix_rank"],
                    "direct_binary_target_piece_total": standard[
                        "direct_binary_target_piece_total"
                    ],
                    "homotopy_eligible_direct_product_total": standard[
                        "homotopy_eligible_direct_product_total"
                    ],
                    "has_exposed_product_plus_chain_contraction_api": capability[
                        "has_exposed_product_plus_chain_contraction_api"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "reports/cicy6784_frontier48_chain_contraction_fallback.json",
            "reports/cicy6784_frontier48_chain_contraction_fallback_verification.json",
            "reports/cicy6784_transferred_m3_route_inventory.json",
            "reports/cicy6784_transferred_m3_route_inventory_verification.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement_verification.json",
        ],
        representative_examples=[
            {
                "term_records": standard["term_records"],
                "pycicy_capability_probe": capability,
            }
        ],
        nearest_escape={
            "minimal_change": (
                "add a genuine product-plus-chain-contraction implementation "
                "or move to a geometry/presentation whose first-pair route is "
                "positive before exact coefficient evaluation"
            ),
            "next_pivot": report["next_pivot"]["status"],
            "recommended_next_pass": report["next_pivot"][
                "recommended_next_pass"
            ],
            "stop_rule": report["next_pivot"]["stop_rule"],
        },
    )


def cicy4185_split_action_lift_missing_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("cicy4185_bridge_lift_audit.json"))
    pool = report["same_hodge_favourable_pool"]
    split = report["selected_split_7910"]
    raw = report["cicy4185"]["raw_free_action_summary"]
    inherited = report["inherited_bundle_pilot"]
    topology_counts = inherited["topology_gate_counts"]
    sample = {
        "requires_split_action_lift": True,
        "parent_free_action_count": raw["free_option_count"],
        "direct_one_step_split_hit_count": pool["direct_one_step_split_hit_count"],
        "selected_split_symmetry_status": split["metadata"]["symmetry_status"],
        "selected_split_free_symmetry_option_count": split["metadata"][
            "free_symmetry_option_count"
        ],
        "same_hodge_favourable_known_free_count": len(
            pool["favourable_known_free_nums"]
        ),
        "inherited_slope_feasible_count": topology_counts.get(
            "slope_feasible_count", 0
        ),
        "bridge_status": report["status"],
    }
    return syndrome(
        syndrome_id="cicy4185_7910_split_action_lift_missing_current_data",
        title="Unique favourable split witness, but no local split-action lift data",
        geometry="CICY4185 via favourable split 7910",
        scope_class="presentation-local",
        claim_scope=(
            "Current cicylist.m and local verifier data for the CICY4185 same-Hodge "
            "presentation bridge. This is not a theorem that no split action lift "
            "exists; adding an explicit action-transfer engine is an escape hatch."
        ),
        stage="presentation_bridge_split_action_lift_gate",
        minimal_obstruction_core={
            "parent_cicy": 4185,
            "selected_split": 7910,
            "same_hodge_pool_count": pool["pool_count"],
            "direct_one_step_split_hit_count": pool[
                "direct_one_step_split_hit_count"
            ],
            "split_row_index": split["split_hit"]["split_row_index"],
            "split_columns": split["split_hit"]["split_columns"],
            "parent_free_z2_option_count": raw["free_option_count"],
            "all_parent_free_options_row_trivial": raw[
                "all_free_options_row_trivial"
            ],
            "selected_split_symmetry_status": split["metadata"][
                "symmetry_status"
            ],
            "selected_split_free_symmetry_option_count": split["metadata"][
                "free_symmetry_option_count"
            ],
            "same_hodge_favourable_known_free_nums": pool[
                "favourable_known_free_nums"
            ],
            "inherited_bundle_tested_record_count": inherited[
                "tested_record_count"
            ],
            "inherited_topology_gate_counts": topology_counts,
        },
        cheap_prefilter="split_action_lift_missing_current_data",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy4185_bridge_lift_audit.json",
            **sample,
            "same_hodge_pool_count": pool["pool_count"],
            "favourable_unknown_nums": pool["favourable_unknown_nums"],
            "inherited_c1_zero_count": topology_counts["c1_zero_count"],
            "inherited_index_pair_minus6_count": topology_counts[
                "index_pair_minus6_count"
            ],
            "inherited_anomaly_nonnegative_count": topology_counts[
                "anomaly_nonnegative_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "split_action_lift_missing_current_data", sample
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy4185_bridge_lift_audit.json",
            "experiments/latent_atlas/reports/cicy4185_bridge_lift_audit_verification.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement_verification.json",
            "reports/no_go_atlas_guided_lateral_scout.json",
            "reports/nonfavourable_ambient_restricted_scout.json",
        ],
        representative_examples=[
            {
                "selected_split_hit": split["split_hit"],
                "raw_free_action_summary": raw,
                "first_inherited_bundle_row": inherited["rows"][0],
            }
        ],
        nearest_escape={
            "minimal_change": (
                "construct an explicit action-transfer map from a selected "
                "CICY4185 free Z2 action to the CICY7910 split coordinates and "
                "equations"
            ),
            "recommended_next_pass": report["next_pivot"]["recommended_next_pass"],
            "engine_escape_hatch": report["next_pivot"]["engine_escape_hatch"],
            "stop_rule": report["next_pivot"]["stop_rule"],
        },
    )


def cicy6187_split_action_lift_missing_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("cicy6187_bridge_lift_audit.json"))
    pool = report["same_hodge_favourable_pool"]
    split = report["selected_split_7899"]
    raw = report["cicy6187"]["raw_free_action_summary"]
    breadcrumb = report["ambient_bundle_breadcrumb"]
    sample = {
        "requires_split_action_lift": True,
        "parent_free_action_count": raw["free_option_count"],
        "direct_one_step_split_hit_count": pool["direct_one_step_split_hit_count"],
        "selected_split_symmetry_status": split["metadata"]["symmetry_status"],
        "selected_split_free_symmetry_option_count": split["metadata"][
            "free_symmetry_option_count"
        ],
        "same_hodge_favourable_known_free_count": len(
            pool["favourable_known_free_nums"]
        ),
        "inherited_slope_feasible_count": 0,
        "bridge_status": report["status"],
    }
    return syndrome(
        syndrome_id="cicy6187_7899_split_action_lift_missing_current_data",
        title="Unique favourable split witness, but no local split-action lift data",
        geometry="CICY6187 via favourable split 7899",
        scope_class="presentation-local",
        claim_scope=(
            "Current cicylist.m and local verifier data for the CICY6187 same-Hodge "
            "presentation bridge. This is not a theorem that no split action lift "
            "exists; adding an explicit action-transfer engine is an escape hatch."
        ),
        stage="presentation_bridge_split_action_lift_gate",
        minimal_obstruction_core={
            "parent_cicy": 6187,
            "selected_split": 7899,
            "same_hodge_pool_count": pool["pool_count"],
            "direct_one_step_split_hit_count": pool[
                "direct_one_step_split_hit_count"
            ],
            "split_row_index": split["split_hit"]["split_row_index"],
            "split_columns": split["split_hit"]["split_columns"],
            "parent_free_z2_option_count": raw["free_option_count"],
            "all_parent_free_options_row_trivial": raw[
                "all_free_options_row_trivial"
            ],
            "selected_split_symmetry_status": split["metadata"][
                "symmetry_status"
            ],
            "selected_split_free_symmetry_option_count": split["metadata"][
                "free_symmetry_option_count"
            ],
            "same_hodge_favourable_known_free_nums": pool[
                "favourable_known_free_nums"
            ],
            "ambient_restricted_bundle_breadcrumb_available": breadcrumb[
                "ambient_restricted_bundle_breadcrumb_available"
            ],
            "ambient_breadcrumb_target_report_count": breadcrumb[
                "cicy6187_target_report_count"
            ],
        },
        cheap_prefilter="split_action_lift_missing_current_data",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy6187_bridge_lift_audit.json",
            **sample,
            "same_hodge_pool_count": pool["pool_count"],
            "favourable_unknown_nums": pool["favourable_unknown_nums"],
            "ambient_breadcrumb_target_report_count": breadcrumb[
                "cicy6187_target_report_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "split_action_lift_missing_current_data", sample
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy6187_bridge_lift_audit.json",
            "experiments/latent_atlas/reports/cicy6187_bridge_lift_audit_verification.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement_verification.json",
            "reports/no_go_atlas_guided_lateral_scout.json",
            "reports/nonfavourable_ambient_restricted_scout.json",
        ],
        representative_examples=[
            {
                "selected_split_hit": split["split_hit"],
                "raw_free_action_summary": raw,
                "ambient_bundle_breadcrumb": breadcrumb,
            }
        ],
        nearest_escape={
            "minimal_change": (
                "construct an explicit action-transfer map from a selected "
                "CICY6187 free Z2 action to the CICY7899 split coordinates and "
                "equations"
            ),
            "recommended_next_pass": report["next_pivot"]["recommended_next_pass"],
            "engine_escape_hatch": report["next_pivot"]["engine_escape_hatch"],
            "stop_rule": report["next_pivot"]["stop_rule"],
        },
    )


def cicy6201_split_action_lift_missing_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("cicy6201_bridge_lift_audit.json"))
    pool = report["same_hodge_favourable_pool"]
    split = report["selected_split_7900"]
    raw = report["cicy6201"]["raw_free_action_summary"]
    breadcrumb = report["ambient_bundle_breadcrumb"]
    sample = {
        "requires_split_action_lift": True,
        "parent_free_action_count": raw["free_option_count"],
        "direct_one_step_split_hit_count": pool["direct_one_step_split_hit_count"],
        "selected_split_symmetry_status": split["metadata"]["symmetry_status"],
        "selected_split_free_symmetry_option_count": split["metadata"][
            "free_symmetry_option_count"
        ],
        "same_hodge_favourable_known_free_count": len(
            pool["favourable_known_free_nums"]
        ),
        "inherited_slope_feasible_count": 0,
        "bridge_status": report["status"],
    }
    return syndrome(
        syndrome_id="cicy6201_7900_split_action_lift_missing_current_data",
        title="Unique favourable split witness, but no local split-action lift data",
        geometry="CICY6201 via favourable split 7900",
        scope_class="presentation-local",
        claim_scope=(
            "Current cicylist.m and local verifier data for the CICY6201 same-Hodge "
            "presentation bridge. This is not a theorem that no split action lift "
            "exists; adding an explicit action-transfer engine is an escape hatch."
        ),
        stage="presentation_bridge_split_action_lift_gate",
        minimal_obstruction_core={
            "parent_cicy": 6201,
            "selected_split": 7900,
            "same_hodge_pool_count": pool["pool_count"],
            "direct_one_step_split_hit_count": pool[
                "direct_one_step_split_hit_count"
            ],
            "split_row_index": split["split_hit"]["split_row_index"],
            "split_columns": split["split_hit"]["split_columns"],
            "parent_free_z2_option_count": raw["free_option_count"],
            "all_parent_free_options_row_trivial": raw[
                "all_free_options_row_trivial"
            ],
            "selected_split_symmetry_status": split["metadata"][
                "symmetry_status"
            ],
            "selected_split_free_symmetry_option_count": split["metadata"][
                "free_symmetry_option_count"
            ],
            "same_hodge_favourable_known_free_nums": pool[
                "favourable_known_free_nums"
            ],
            "ambient_restricted_bundle_breadcrumb_available": breadcrumb[
                "ambient_restricted_bundle_breadcrumb_available"
            ],
            "ambient_breadcrumb_target_report_count": breadcrumb[
                "cicy6201_target_report_count"
            ],
        },
        cheap_prefilter="split_action_lift_missing_current_data",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy6201_bridge_lift_audit.json",
            **sample,
            "same_hodge_pool_count": pool["pool_count"],
            "favourable_unknown_nums": pool["favourable_unknown_nums"],
            "ambient_breadcrumb_target_report_count": breadcrumb[
                "cicy6201_target_report_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "split_action_lift_missing_current_data", sample
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy6201_bridge_lift_audit.json",
            "experiments/latent_atlas/reports/cicy6201_bridge_lift_audit_verification.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement_verification.json",
            "reports/no_go_atlas_guided_lateral_scout.json",
            "reports/nonfavourable_ambient_restricted_scout.json",
        ],
        representative_examples=[
            {
                "selected_split_hit": split["split_hit"],
                "raw_free_action_summary": raw,
                "ambient_bundle_breadcrumb": breadcrumb,
            }
        ],
        nearest_escape={
            "minimal_change": (
                "construct an explicit action-transfer map from a selected "
                "CICY6201 free Z2 action to the CICY7900 split coordinates and "
                "equations"
            ),
            "recommended_next_pass": report["next_pivot"]["recommended_next_pass"],
            "engine_escape_hatch": report["next_pivot"]["engine_escape_hatch"],
            "stop_rule": report["next_pivot"]["stop_rule"],
        },
    )


def cicy6281_split_action_lift_missing_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("cicy6281_bridge_lift_audit.json"))
    pool = report["same_hodge_favourable_pool"]
    split = report["selected_split_7904"]
    raw = report["cicy6281"]["raw_free_action_summary"]
    breadcrumb = report["ambient_bundle_breadcrumb"]
    sample = {
        "requires_split_action_lift": True,
        "parent_free_action_count": raw["free_option_count"],
        "direct_one_step_split_hit_count": pool["direct_one_step_split_hit_count"],
        "selected_split_symmetry_status": split["metadata"]["symmetry_status"],
        "selected_split_free_symmetry_option_count": split["metadata"][
            "free_symmetry_option_count"
        ],
        "same_hodge_favourable_known_free_count": len(
            pool["favourable_known_free_nums"]
        ),
        "inherited_slope_feasible_count": 0,
        "bridge_status": report["status"],
    }
    return syndrome(
        syndrome_id="cicy6281_7904_split_action_lift_missing_current_data",
        title="Unique favourable split witness, but no local split-action lift data",
        geometry="CICY6281 via favourable split 7904",
        scope_class="presentation-local",
        claim_scope=(
            "Current cicylist.m and local verifier data for the CICY6281 same-Hodge "
            "presentation bridge. This is not a theorem that no split action lift "
            "exists; adding an explicit action-transfer engine is an escape hatch."
        ),
        stage="presentation_bridge_split_action_lift_gate",
        minimal_obstruction_core={
            "parent_cicy": 6281,
            "selected_split": 7904,
            "same_hodge_pool_count": pool["pool_count"],
            "direct_one_step_split_hit_count": pool[
                "direct_one_step_split_hit_count"
            ],
            "split_row_index": split["split_hit"]["split_row_index"],
            "split_columns": split["split_hit"]["split_columns"],
            "parent_free_z2_option_count": raw["free_option_count"],
            "all_parent_free_options_row_trivial": raw[
                "all_free_options_row_trivial"
            ],
            "selected_split_symmetry_status": split["metadata"][
                "symmetry_status"
            ],
            "selected_split_free_symmetry_option_count": split["metadata"][
                "free_symmetry_option_count"
            ],
            "same_hodge_favourable_known_free_nums": pool[
                "favourable_known_free_nums"
            ],
            "ambient_restricted_bundle_breadcrumb_available": breadcrumb[
                "ambient_restricted_bundle_breadcrumb_available"
            ],
            "ambient_breadcrumb_target_report_count": breadcrumb[
                "cicy6281_target_report_count"
            ],
        },
        cheap_prefilter="split_action_lift_missing_current_data",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy6281_bridge_lift_audit.json",
            **sample,
            "same_hodge_pool_count": pool["pool_count"],
            "favourable_unknown_nums": pool["favourable_unknown_nums"],
            "ambient_breadcrumb_target_report_count": breadcrumb[
                "cicy6281_target_report_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "split_action_lift_missing_current_data", sample
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy6281_bridge_lift_audit.json",
            "experiments/latent_atlas/reports/cicy6281_bridge_lift_audit_verification.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement_verification.json",
            "reports/no_go_atlas_guided_lateral_scout.json",
            "reports/nonfavourable_ambient_restricted_scout.json",
        ],
        representative_examples=[
            {
                "selected_split_hit": split["split_hit"],
                "raw_free_action_summary": raw,
                "ambient_bundle_breadcrumb": breadcrumb,
            }
        ],
        nearest_escape={
            "minimal_change": (
                "construct an explicit action-transfer map from a selected "
                "CICY6281 free Z2 action to the CICY7904 split coordinates and "
                "equations"
            ),
            "recommended_next_pass": report["next_pivot"]["recommended_next_pass"],
            "engine_escape_hatch": report["next_pivot"]["engine_escape_hatch"],
            "stop_rule": report["next_pivot"]["stop_rule"],
        },
    )


def cicy4078_split_action_lift_missing_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("cicy4078_bridge_lift_audit.json"))
    pool = report["same_hodge_favourable_pool"]
    split = report["selected_split_7908"]
    raw = report["cicy4078"]["raw_free_action_summary"]
    inherited = report["inherited_bundle_pilot"]
    topology_counts = inherited["topology_gate_counts"]
    sample = {
        "requires_split_action_lift": True,
        "parent_free_action_count": raw["free_option_count"],
        "direct_one_step_split_hit_count": pool["direct_one_step_split_hit_count"],
        "selected_split_symmetry_status": split["metadata"]["symmetry_status"],
        "selected_split_free_symmetry_option_count": split["metadata"][
            "free_symmetry_option_count"
        ],
        "same_hodge_favourable_known_free_count": len(
            pool["favourable_known_free_nums"]
        ),
        "inherited_slope_feasible_count": topology_counts.get(
            "slope_feasible_count", 0
        ),
        "bridge_status": report["status"],
    }
    return syndrome(
        syndrome_id="cicy4078_7908_split_action_lift_missing_current_data",
        title="Unique favourable split witness, but no local split-action lift data",
        geometry="CICY4078 via favourable split 7908",
        scope_class="presentation-local",
        claim_scope=(
            "Current cicylist.m and local verifier data for the CICY4078 same-Hodge "
            "presentation bridge. This is not a theorem that no split action lift "
            "exists; adding an explicit action-transfer engine is an escape hatch."
        ),
        stage="presentation_bridge_split_action_lift_gate",
        minimal_obstruction_core={
            "parent_cicy": 4078,
            "selected_split": 7908,
            "same_hodge_pool_count": pool["pool_count"],
            "direct_one_step_split_hit_count": pool[
                "direct_one_step_split_hit_count"
            ],
            "split_row_index": split["split_hit"]["split_row_index"],
            "split_columns": split["split_hit"]["split_columns"],
            "parent_free_z2_option_count": raw["free_option_count"],
            "all_parent_free_options_row_trivial": raw[
                "all_free_options_row_trivial"
            ],
            "selected_split_symmetry_status": split["metadata"][
                "symmetry_status"
            ],
            "selected_split_free_symmetry_option_count": split["metadata"][
                "free_symmetry_option_count"
            ],
            "same_hodge_favourable_known_free_nums": pool[
                "favourable_known_free_nums"
            ],
            "inherited_bundle_tested_record_count": inherited[
                "tested_record_count"
            ],
            "inherited_topology_gate_counts": topology_counts,
        },
        cheap_prefilter="split_action_lift_missing_current_data",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy4078_bridge_lift_audit.json",
            **sample,
            "same_hodge_pool_count": pool["pool_count"],
            "favourable_unknown_nums": pool["favourable_unknown_nums"],
            "inherited_c1_zero_count": topology_counts["c1_zero_count"],
            "inherited_index_pair_minus6_count": topology_counts[
                "index_pair_minus6_count"
            ],
            "inherited_anomaly_nonnegative_count": topology_counts[
                "anomaly_nonnegative_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "split_action_lift_missing_current_data", sample
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy4078_bridge_lift_audit.json",
            "experiments/latent_atlas/reports/cicy4078_bridge_lift_audit_verification.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement_verification.json",
            "reports/no_go_atlas_guided_lateral_scout.json",
            "reports/nonfavourable_ambient_restricted_scout.json",
        ],
        representative_examples=[
            {
                "selected_split_hit": split["split_hit"],
                "raw_free_action_summary": raw,
                "first_inherited_bundle_row": inherited["rows"][0],
            }
        ],
        nearest_escape={
            "minimal_change": (
                "construct an explicit action-transfer map from a selected "
                "CICY4078 free Z2 action to the CICY7908 split coordinates and "
                "equations"
            ),
            "recommended_next_pass": report["next_pivot"]["recommended_next_pass"],
            "engine_escape_hatch": report["next_pivot"]["engine_escape_hatch"],
            "stop_rule": report["next_pivot"]["stop_rule"],
        },
    )


def cicy5141_split_action_lift_missing_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("cicy5141_bridge_lift_audit.json"))
    pool = report["same_hodge_favourable_pool"]
    split = report["selected_split_7912"]
    raw = report["cicy5141"]["raw_free_action_summary"]
    breadcrumb = report["ambient_bundle_breadcrumb"]
    sample = {
        "requires_split_action_lift": True,
        "parent_free_action_count": raw["free_option_count"],
        "direct_one_step_split_hit_count": pool["direct_one_step_split_hit_count"],
        "selected_split_symmetry_status": split["metadata"]["symmetry_status"],
        "selected_split_free_symmetry_option_count": split["metadata"][
            "free_symmetry_option_count"
        ],
        "same_hodge_favourable_known_free_count": len(
            pool["favourable_known_free_nums"]
        ),
        "inherited_slope_feasible_count": 0,
        "bridge_status": report["status"],
    }
    return syndrome(
        syndrome_id="cicy5141_7912_split_action_lift_missing_current_data",
        title="Unique favourable split witness, but no local split-action lift data",
        geometry="CICY5141 via favourable split 7912",
        scope_class="presentation-local",
        claim_scope=(
            "Current cicylist.m and local verifier data for the CICY5141 same-Hodge "
            "presentation bridge. This is not a theorem that no split action lift "
            "exists; adding an explicit action-transfer engine is an escape hatch."
        ),
        stage="presentation_bridge_split_action_lift_gate",
        minimal_obstruction_core={
            "parent_cicy": 5141,
            "selected_split": 7912,
            "same_hodge_pool_count": pool["pool_count"],
            "direct_one_step_split_hit_count": pool[
                "direct_one_step_split_hit_count"
            ],
            "split_row_index": split["split_hit"]["split_row_index"],
            "split_columns": split["split_hit"]["split_columns"],
            "parent_free_z2_option_count": raw["free_option_count"],
            "all_parent_free_options_row_trivial": raw[
                "all_free_options_row_trivial"
            ],
            "selected_split_symmetry_status": split["metadata"][
                "symmetry_status"
            ],
            "selected_split_free_symmetry_option_count": split["metadata"][
                "free_symmetry_option_count"
            ],
            "same_hodge_favourable_known_free_nums": pool[
                "favourable_known_free_nums"
            ],
            "ambient_restricted_bundle_breadcrumb_available": breadcrumb[
                "ambient_restricted_bundle_breadcrumb_available"
            ],
            "ambient_breadcrumb_target_report_count": breadcrumb[
                "cicy5141_target_report_count"
            ],
        },
        cheap_prefilter="split_action_lift_missing_current_data",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy5141_bridge_lift_audit.json",
            **sample,
            "same_hodge_pool_count": pool["pool_count"],
            "favourable_unknown_nums": pool["favourable_unknown_nums"],
            "ambient_breadcrumb_target_report_count": breadcrumb[
                "cicy5141_target_report_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "split_action_lift_missing_current_data", sample
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy5141_bridge_lift_audit.json",
            "experiments/latent_atlas/reports/cicy5141_bridge_lift_audit_verification.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement.json",
            "experiments/latent_atlas/reports/cross_geometry_queue_advancement_verification.json",
            "reports/no_go_atlas_guided_lateral_scout.json",
            "reports/nonfavourable_ambient_restricted_scout.json",
        ],
        representative_examples=[
            {
                "selected_split_hit": split["split_hit"],
                "raw_free_action_summary": raw,
                "ambient_bundle_breadcrumb": breadcrumb,
            }
        ],
        nearest_escape={
            "minimal_change": (
                "construct an explicit action-transfer map from a selected "
                "CICY5141 free Z2 action to the CICY7912 split coordinates and "
                "equations"
            ),
            "recommended_next_pass": report["next_pivot"]["recommended_next_pass"],
            "engine_escape_hatch": report["next_pivot"]["engine_escape_hatch"],
            "stop_rule": report["next_pivot"]["stop_rule"],
        },
    )


def cicy6784_radius4_local_deformation_no_first_pair_seed_syndrome() -> dict[str, Any]:
    report = load_json(artifact("cicy6784_radius4_first_pair_seed_scout.json"))
    summary = report["summary"]
    classification = report["classification"]
    top = summary["top_ranked_record"]
    return syndrome(
        syndrome_id="cicy6784_radius4_local_deformation_no_first_pair_seed",
        title="Radius-4 local q=1 deformation scout finds no positive first-pair homotopy seed",
        geometry="CICY6784/model 31 option 2",
        scope_class="grammar-local",
        claim_scope=(
            "The finite pair-delta radius-4 plus rectangle local deformation "
            "grammar around the CICY6784 frontier-48 degree-4 Yukawa lead. "
            "This does not rule out broader radii, different move grammars, "
            "other geometries, or full chain-contraction/homotopy-transfer "
            "maps."
        ),
        stage="local_deformation_first_pair_seed_gate",
        minimal_obstruction_core={
            "seed_frontier_index": report["seed_candidate"]["frontier_index"],
            "frontier_size": summary["frontier_size"],
            "stage_counts": summary["stage_counts"],
            "q1_candidate_count": summary["q1_candidate_count"],
            "promoted_q1_count": summary["promoted_q1_count"],
            "safe_up_down_yukawa_record_count": summary[
                "safe_up_down_yukawa_record_count"
            ],
            "positive_first_pair_seed_record_count": summary[
                "positive_first_pair_seed_record_count"
            ],
            "max_valid_homotopy_eligible_first_pair_slot_count": summary[
                "max_valid_homotopy_eligible_first_pair_slot_count"
            ],
            "max_valid_direct_target_first_pair_slot_count": summary[
                "max_valid_direct_target_first_pair_slot_count"
            ],
            "top_ranked_record": top,
        },
        cheap_prefilter="local_deformation_first_pair_no_homotopy_seed",
        replay_counts={
            "source": "reports/cicy6784_radius4_first_pair_seed_scout.json",
            "frontier_size": summary["frontier_size"],
            "stage_counts": summary["stage_counts"],
            "q1_candidate_count": summary["q1_candidate_count"],
            "promoted_q1_count": summary["promoted_q1_count"],
            "promotion_timeout_count": summary["promotion_timeout_count"],
            "safe_up_down_yukawa_record_count": summary[
                "safe_up_down_yukawa_record_count"
            ],
            "positive_first_pair_seed_record_count": summary[
                "positive_first_pair_seed_record_count"
            ],
            "max_valid_homotopy_eligible_first_pair_slot_count": summary[
                "max_valid_homotopy_eligible_first_pair_slot_count"
            ],
            "max_valid_direct_target_first_pair_slot_count": summary[
                "max_valid_direct_target_first_pair_slot_count"
            ],
            "deformation_scout_status": classification[
                "deformation_scout_status"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "local_deformation_first_pair_no_homotopy_seed",
                {
                    "requires_local_deformation_first_pair_seed": True,
                    "frontier_size": summary["frontier_size"],
                    "q1_candidate_count": summary["q1_candidate_count"],
                    "safe_up_down_yukawa_record_count": summary[
                        "safe_up_down_yukawa_record_count"
                    ],
                    "positive_first_pair_seed_record_count": summary[
                        "positive_first_pair_seed_record_count"
                    ],
                    "max_valid_homotopy_eligible_first_pair_slot_count": summary[
                        "max_valid_homotopy_eligible_first_pair_slot_count"
                    ],
                    "deformation_scout_status": classification[
                        "deformation_scout_status"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "reports/cicy6784_radius4_first_pair_seed_scout.json",
            "reports/cicy6784_radius4_first_pair_seed_scout_verification.json",
            "reports/cicy6784_multistage_homotopy_seed_closure.json",
            "reports/cicy6784_multistage_homotopy_seed_closure_verification.json",
        ],
        representative_examples=[
            {
                "top_ranked_record": top,
                "ranked_promoted_records": report["ranked_promoted_records"],
                "learned_boundary": report["interpretation"]["learned_boundary"],
            }
        ],
        nearest_escape={
            "minimal_change": (
                "find a q=1 local deformation with safe up/down Yukawa "
                "selection and positive valid_homotopy_eligible_first_pair_slot_count"
            ),
            "current_stop_rule": report["interpretation"]["stop_rule"],
            "recommended_pivot": (
                "search cross-geometry or broader generators that rank by "
                "positive first-pair homotopy eligibility before promotion, "
                "or implement full chain contraction for the current lead"
            ),
        },
    )


def verified_overlap_first_pair_seed_absent_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("verified_overlap_first_pair_seed_scout.json"))
    summary = report["summary"]
    classification = report["classification"]
    top = summary["top_ranked_record"]
    return syndrome(
        syndrome_id="verified_overlap_first_pair_seed_absent",
        title="Verified overlap queue has no positive first-pair homotopy seed",
        geometry="Verified order-4 overlap queue and CICY6784 radius-4 extension",
        scope_class="grammar-local",
        claim_scope=(
            "The current verified overlap/retrieval queue, the three "
            "reconstruction-authoritative exact-overlap promotions, and the "
            "verified CICY6784 radius-4 local deformation extension. This is "
            "not a no-go for broader order-4 geometries or full chain "
            "contraction."
        ),
        stage="verified_overlap_first_pair_seed_gate",
        minimal_obstruction_core={
            "retrieval_relevant_row_count": summary["retrieval_relevant_row_count"],
            "retrieval_only_without_first_pair_reconstruction_count": summary[
                "retrieval_only_without_first_pair_reconstruction_count"
            ],
            "exact_overlap_promoted_row_count": summary[
                "exact_overlap_promoted_row_count"
            ],
            "radius4_local_promoted_row_count": summary[
                "radius4_local_promoted_row_count"
            ],
            "scored_record_count": summary["scored_record_count"],
            "first_pair_seed_status_counts": summary[
                "first_pair_seed_status_counts"
            ],
            "strict_exact_overlap_seed_count": summary[
                "strict_exact_overlap_seed_count"
            ],
            "safe_up_type_only_record_count": summary[
                "safe_up_type_only_record_count"
            ],
            "safe_up_down_yukawa_record_count": summary[
                "safe_up_down_yukawa_record_count"
            ],
            "positive_first_pair_seed_record_count": summary[
                "positive_first_pair_seed_record_count"
            ],
            "max_valid_homotopy_eligible_first_pair_slot_count": summary[
                "max_valid_homotopy_eligible_first_pair_slot_count"
            ],
            "max_valid_direct_target_first_pair_slot_count": summary[
                "max_valid_direct_target_first_pair_slot_count"
            ],
            "top_ranked_record": top,
        },
        cheap_prefilter="verified_overlap_first_pair_seed_absent",
        replay_counts={
            "source": "experiments/latent_atlas/reports/verified_overlap_first_pair_seed_scout.json",
            "retrieval_relevant_row_count": summary["retrieval_relevant_row_count"],
            "scored_record_count": summary["scored_record_count"],
            "safe_up_type_only_record_count": summary[
                "safe_up_type_only_record_count"
            ],
            "safe_up_down_yukawa_record_count": summary[
                "safe_up_down_yukawa_record_count"
            ],
            "positive_first_pair_seed_record_count": summary[
                "positive_first_pair_seed_record_count"
            ],
            "max_valid_homotopy_eligible_first_pair_slot_count": summary[
                "max_valid_homotopy_eligible_first_pair_slot_count"
            ],
            "first_pair_seed_scout_status": classification[
                "first_pair_seed_scout_status"
            ],
            "coefficient_rank_status": classification["coefficient_rank_status"],
            "prefilter_sample_passes": evaluate_prefilter(
                "verified_overlap_first_pair_seed_absent",
                {
                    "requires_verified_overlap_first_pair_seed": True,
                    "scored_record_count": summary["scored_record_count"],
                    "safe_up_down_yukawa_record_count": summary[
                        "safe_up_down_yukawa_record_count"
                    ],
                    "positive_first_pair_seed_record_count": summary[
                        "positive_first_pair_seed_record_count"
                    ],
                    "max_valid_homotopy_eligible_first_pair_slot_count": summary[
                        "max_valid_homotopy_eligible_first_pair_slot_count"
                    ],
                    "first_pair_seed_scout_status": classification[
                        "first_pair_seed_scout_status"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/verified_overlap_first_pair_seed_scout.json",
            "experiments/latent_atlas/reports/verified_overlap_first_pair_seed_scout_verification.json",
            "experiments/latent_atlas/reports/overlap_first_seed_queue.json",
            "experiments/latent_atlas/reports/unaudited_order4_exact_overlap_scout.json",
            "reports/cicy6784_radius4_first_pair_seed_scout.json",
            "reports/cicy6784_radius4_first_pair_seed_scout_verification.json",
        ],
        representative_examples=[
            {
                "top_ranked_record": top,
                "ranked_scored_records": report["ranked_scored_records"],
                "learned_boundary": report["interpretation"]["learned_boundary"],
            }
        ],
        nearest_escape={
            "minimal_change": (
                "find at least one reconstruction-authoritative row with "
                "safe up/down Yukawa support and positive first-pair homotopy "
                "eligibility"
            ),
            "recommended_pivot": report["interpretation"]["recommended_pivot"],
            "stop_rule": report["interpretation"]["stop_rule"],
        },
    )


def first_pair_positive_generator_no_seed_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("first_pair_positive_generator_expansion.json"))
    summary = report["summary"]
    classification = report["classification"]
    top = summary["top_ranked_record"]
    return syndrome(
        syndrome_id="first_pair_positive_generator_no_seed_radius4",
        title="Radius-4 first-pair-positive generator expansion finds no seed",
        geometry="CICY6784/model 7, 14, 31 option 2 plus radius-4 frontier boundary",
        scope_class="grammar-local",
        claim_scope=(
            "The finite CICY6784 option-2 radius-4 pair-delta plus rectangle "
            "multi-seed expansion from the verified overlap frontier. This is "
            "not a no-go for other CICY6784 move grammars, other geometries, "
            "or full chain contraction."
        ),
        stage="first_pair_positive_generator_gate",
        minimal_obstruction_core={
            "seed_count": summary["seed_count"],
            "seed_ids": summary["seed_ids"],
            "frontier_size": summary["frontier_size"],
            "stage_counts": summary["stage_counts"],
            "q1_candidate_count": summary["q1_candidate_count"],
            "promoted_q1_count": summary["promoted_q1_count"],
            "promotion_timeout_count": summary["promotion_timeout_count"],
            "first_pair_seed_status_counts": summary[
                "first_pair_seed_status_counts"
            ],
            "safe_up_type_only_record_count": summary[
                "safe_up_type_only_record_count"
            ],
            "safe_up_down_yukawa_record_count": summary[
                "safe_up_down_yukawa_record_count"
            ],
            "positive_first_pair_seed_record_count": summary[
                "positive_first_pair_seed_record_count"
            ],
            "max_valid_homotopy_eligible_first_pair_slot_count": summary[
                "max_valid_homotopy_eligible_first_pair_slot_count"
            ],
            "max_valid_direct_target_first_pair_slot_count": summary[
                "max_valid_direct_target_first_pair_slot_count"
            ],
            "top_ranked_record": top,
        },
        cheap_prefilter="first_pair_positive_generator_no_seed",
        replay_counts={
            "source": "experiments/latent_atlas/reports/first_pair_positive_generator_expansion.json",
            "seed_count": summary["seed_count"],
            "frontier_size": summary["frontier_size"],
            "q1_candidate_count": summary["q1_candidate_count"],
            "promoted_q1_count": summary["promoted_q1_count"],
            "safe_up_type_only_record_count": summary[
                "safe_up_type_only_record_count"
            ],
            "safe_up_down_yukawa_record_count": summary[
                "safe_up_down_yukawa_record_count"
            ],
            "positive_first_pair_seed_record_count": summary[
                "positive_first_pair_seed_record_count"
            ],
            "max_valid_homotopy_eligible_first_pair_slot_count": summary[
                "max_valid_homotopy_eligible_first_pair_slot_count"
            ],
            "generator_expansion_status": classification[
                "generator_expansion_status"
            ],
            "coefficient_rank_status": classification["coefficient_rank_status"],
            "prefilter_sample_passes": evaluate_prefilter(
                "first_pair_positive_generator_no_seed",
                {
                    "requires_first_pair_positive_generator_seed": True,
                    "frontier_size": summary["frontier_size"],
                    "q1_candidate_count": summary["q1_candidate_count"],
                    "safe_up_down_yukawa_record_count": summary[
                        "safe_up_down_yukawa_record_count"
                    ],
                    "positive_first_pair_seed_record_count": summary[
                        "positive_first_pair_seed_record_count"
                    ],
                    "max_valid_homotopy_eligible_first_pair_slot_count": summary[
                        "max_valid_homotopy_eligible_first_pair_slot_count"
                    ],
                    "generator_expansion_status": classification[
                        "generator_expansion_status"
                    ],
                },
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/first_pair_positive_generator_expansion.json",
            "experiments/latent_atlas/reports/first_pair_positive_generator_expansion_verification.json",
            "experiments/latent_atlas/reports/verified_overlap_first_pair_seed_scout.json",
            "experiments/latent_atlas/reports/verified_overlap_first_pair_seed_scout_verification.json",
            "reports/cicy6784_radius4_first_pair_seed_scout.json",
            "reports/cicy6784_radius4_first_pair_seed_scout_verification.json",
        ],
        representative_examples=[
            {
                "top_ranked_record": top,
                "ranked_promoted_records": report["ranked_promoted_records"],
                "learned_boundary": report["interpretation"]["learned_boundary"],
            }
        ],
        nearest_escape={
            "minimal_change": (
                "find a q1 promotion in this or a broader generator with safe "
                "up/down Yukawa support and positive first-pair homotopy "
                "eligibility"
            ),
            "recommended_pivot": report["interpretation"]["recommended_pivot"],
            "stop_rule": report["interpretation"]["stop_rule"],
        },
    )


def cicy5248_split_action_lift_missing_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("cicy5248_bridge_action_transfer_audit.json"))
    pool = report["same_hodge_favourable_pool"]
    split = report["selected_split_witness"]
    raw = report["raw_free_action_summary"]
    breadcrumb = report["ambient_breadcrumb_summary"]
    sample = {
        "requires_split_action_lift": True,
        "parent_free_action_count": raw["free_option_count"],
        "direct_one_step_split_hit_count": pool["direct_one_step_split_hit_count"],
        "selected_split_symmetry_status": split["symmetry_status"],
        "selected_split_free_symmetry_option_count": split[
            "free_symmetry_option_count"
        ],
        "same_hodge_favourable_known_free_count": len(
            pool["favourable_known_free_nums"]
        ),
        "inherited_slope_feasible_count": 0,
        "bridge_status": report["status"],
    }
    return syndrome(
        syndrome_id="cicy5248_7913_split_action_lift_missing_current_data",
        title="Unique favourable split witness, but no local split-action lift data",
        geometry="CICY5248 via favourable split 7913",
        scope_class="presentation-local",
        claim_scope=(
            "Current cicylist.m and local verifier data for the CICY5248 same-Hodge "
            "presentation bridge. This is not a theorem that no split action lift "
            "exists; adding an explicit action-transfer engine is an escape hatch."
        ),
        stage="presentation_bridge_split_action_lift_gate",
        minimal_obstruction_core={
            "parent_cicy": 5248,
            "selected_split": 7913,
            "same_hodge_pool_count": pool["pool_count"],
            "direct_one_step_split_hit_count": pool[
                "direct_one_step_split_hit_count"
            ],
            "split_row_index": split["split_hit"]["split_row_index"],
            "split_columns": split["split_hit"]["split_columns"],
            "parent_free_z2_option_count": raw["free_option_count"],
            "all_parent_free_options_row_trivial": raw[
                "all_free_options_row_trivial"
            ],
            "selected_split_symmetry_status": split["symmetry_status"],
            "selected_split_free_symmetry_option_count": split[
                "free_symmetry_option_count"
            ],
            "same_hodge_favourable_known_free_nums": pool[
                "favourable_known_free_nums"
            ],
            "ambient_restricted_bundle_breadcrumb_available": breadcrumb[
                "ambient_restricted_bundle_breadcrumb_available"
            ],
            "ambient_breadcrumb_target_report_count": breadcrumb[
                "cicy5248_target_report_count"
            ],
        },
        cheap_prefilter="split_action_lift_missing_current_data",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy5248_bridge_action_transfer_audit.json",
            **sample,
            "same_hodge_pool_count": pool["pool_count"],
            "favourable_unknown_nums": pool["favourable_unknown_nums"],
            "ambient_breadcrumb_target_report_count": breadcrumb[
                "cicy5248_target_report_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "split_action_lift_missing_current_data", sample
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy5248_bridge_action_transfer_audit.json",
            "experiments/latent_atlas/reports/cicy5248_bridge_action_transfer_audit_verification.json",
            "experiments/latent_atlas/reports/atlas_gap_queue_post_cicy5248_bridge_advancement.json",
            "experiments/latent_atlas/reports/atlas_gap_queue_post_cicy5248_bridge_advancement_verification.json",
            "experiments/latent_atlas/reports/atlas_guided_raw_scout_outside_verified_corpus.json",
            "reports/no_go_atlas_guided_lateral_scout.json",
            "reports/nonfavourable_ambient_restricted_scout.json",
        ],
        representative_examples=[
            {
                "selected_split_hit": split["split_hit"],
                "raw_free_action_summary": raw,
                "ambient_bundle_breadcrumb": breadcrumb,
            }
        ],
        nearest_escape={
            "minimal_change": (
                "construct an explicit action-transfer map from a selected "
                "CICY5248 free Z2 action to the CICY7913 split coordinates and "
                "equations"
            ),
            "recommended_next_pass": report["next_step"][
                "recommended_next_target_id"
            ],
            "engine_escape_hatch": report["next_step"]["return_condition"],
            "stop_rule": (
                "Do not promote CICY5248 until a documented transfer realizes the "
                "parent free action on the CICY7913 split data."
            ),
        },
    )


def cicy5406_split_action_lift_missing_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("cicy5406_bridge_action_transfer_audit.json"))
    pool = report["same_hodge_favourable_pool"]
    split = report["selected_split_witness"]
    raw = report["raw_free_action_summary"]
    breadcrumb = report["ambient_breadcrumb_summary"]
    sample = {
        "requires_split_action_lift": True,
        "parent_free_action_count": raw["free_option_count"],
        "direct_one_step_split_hit_count": pool["direct_one_step_split_hit_count"],
        "selected_split_symmetry_status": split["symmetry_status"],
        "selected_split_free_symmetry_option_count": split[
            "free_symmetry_option_count"
        ],
        "same_hodge_favourable_known_free_count": len(
            pool["favourable_known_free_nums"]
        ),
        "inherited_slope_feasible_count": 0,
        "bridge_status": report["status"],
    }
    return syndrome(
        syndrome_id="cicy5406_7918_split_action_lift_missing_current_data",
        title="Unique favourable split witness, but no local split-action lift data",
        geometry="CICY5406 via favourable split 7918",
        scope_class="presentation-local",
        claim_scope=(
            "Current cicylist.m and local verifier data for the CICY5406 same-Hodge "
            "presentation bridge. This is not a theorem that no split action lift "
            "exists; adding an explicit action-transfer engine is an escape hatch."
        ),
        stage="presentation_bridge_split_action_lift_gate",
        minimal_obstruction_core={
            "parent_cicy": 5406,
            "selected_split": 7918,
            "same_hodge_pool_count": pool["pool_count"],
            "direct_one_step_split_hit_count": pool[
                "direct_one_step_split_hit_count"
            ],
            "split_row_index": split["split_hit"]["split_row_index"],
            "split_columns": split["split_hit"]["split_columns"],
            "parent_free_z2_option_count": raw["free_option_count"],
            "all_parent_free_options_row_trivial": raw[
                "all_free_options_row_trivial"
            ],
            "selected_split_symmetry_status": split["symmetry_status"],
            "selected_split_free_symmetry_option_count": split[
                "free_symmetry_option_count"
            ],
            "same_hodge_favourable_known_free_nums": pool[
                "favourable_known_free_nums"
            ],
            "ambient_restricted_bundle_breadcrumb_available": breadcrumb[
                "ambient_restricted_bundle_breadcrumb_available"
            ],
            "ambient_breadcrumb_target_report_count": breadcrumb[
                "cicy5406_target_report_count"
            ],
        },
        cheap_prefilter="split_action_lift_missing_current_data",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy5406_bridge_action_transfer_audit.json",
            **sample,
            "same_hodge_pool_count": pool["pool_count"],
            "favourable_unknown_nums": pool["favourable_unknown_nums"],
            "ambient_breadcrumb_target_report_count": breadcrumb[
                "cicy5406_target_report_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "split_action_lift_missing_current_data", sample
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy5406_bridge_action_transfer_audit.json",
            "experiments/latent_atlas/reports/cicy5406_bridge_action_transfer_audit_verification.json",
            "experiments/latent_atlas/reports/atlas_gap_queue_post_cicy5406_bridge_advancement.json",
            "experiments/latent_atlas/reports/atlas_gap_queue_post_cicy5406_bridge_advancement_verification.json",
            "experiments/latent_atlas/reports/atlas_guided_raw_scout_outside_verified_corpus.json",
            "reports/no_go_atlas_guided_lateral_scout.json",
            "reports/nonfavourable_ambient_restricted_scout.json",
        ],
        representative_examples=[
            {
                "selected_split_hit": split["split_hit"],
                "raw_free_action_summary": raw,
                "ambient_bundle_breadcrumb": breadcrumb,
            }
        ],
        nearest_escape={
            "minimal_change": (
                "construct an explicit action-transfer map from a selected "
                "CICY5406 free Z2 action to the CICY7918 split coordinates and "
                "equations"
            ),
            "recommended_next_pass": report["next_step"][
                "recommended_next_target_id"
            ],
            "engine_escape_hatch": report["next_step"]["return_condition"],
            "stop_rule": (
                "Do not promote CICY5406 until a documented transfer realizes the "
                "parent free action on the CICY7918 split data."
            ),
        },
    )


def cicy5449_no_direct_split_witness_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("cicy5449_bridge_action_transfer_audit.json"))
    pool = report["same_hodge_favourable_pool"]
    search = report["direct_split_search"]
    raw = report["raw_free_action_summary"]
    breadcrumb = report["ambient_breadcrumb_summary"]
    sample = {
        "requires_concrete_split_witness": True,
        "parent_free_action_count": raw["free_option_count"],
        "same_hodge_pool_count": pool["pool_count"],
        "same_hodge_favourable_unknown_count": len(
            pool["favourable_unknown_nums"]
        ),
        "same_hodge_favourable_known_free_count": len(
            pool["favourable_known_free_nums"]
        ),
        "direct_one_step_split_hit_count": search[
            "direct_one_step_split_hit_count"
        ],
        "bridge_status": report["status"],
    }
    return syndrome(
        syndrome_id="cicy5449_no_direct_split_witness_current_data",
        title="Same-Hodge favourable pool exists, but no direct split witness",
        geometry="CICY5449 no direct favourable split witness",
        scope_class="presentation-local",
        claim_scope=(
            "Current cicylist.m and local verifier data for the CICY5449 same-Hodge "
            "presentation bridge under ordinary one-step split-row contractions. "
            "This is not a theorem that no favourable presentation or multi-step "
            "split route exists."
        ),
        stage="presentation_bridge_witness_selection_gate",
        minimal_obstruction_core={
            "parent_cicy": 5449,
            "same_hodge_pool_count": pool["pool_count"],
            "same_hodge_favourable_unknown_nums": pool[
                "favourable_unknown_nums"
            ],
            "same_hodge_favourable_known_free_nums": pool[
                "favourable_known_free_nums"
            ],
            "direct_one_step_split_hit_count": search[
                "direct_one_step_split_hit_count"
            ],
            "parent_free_z2_option_count": raw["free_option_count"],
            "all_parent_free_options_row_trivial": raw[
                "all_free_options_row_trivial"
            ],
            "ambient_restricted_bundle_breadcrumb_available": breadcrumb[
                "ambient_restricted_bundle_breadcrumb_available"
            ],
            "ambient_breadcrumb_target_report_count": breadcrumb[
                "cicy5449_target_report_count"
            ],
        },
        cheap_prefilter="direct_split_witness_missing_current_data",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy5449_bridge_action_transfer_audit.json",
            **sample,
            "ambient_breadcrumb_target_report_count": breadcrumb[
                "cicy5449_target_report_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "direct_split_witness_missing_current_data", sample
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy5449_bridge_action_transfer_audit.json",
            "experiments/latent_atlas/reports/cicy5449_bridge_action_transfer_audit_verification.json",
            "experiments/latent_atlas/reports/atlas_gap_queue_post_cicy5449_bridge_advancement.json",
            "experiments/latent_atlas/reports/atlas_gap_queue_post_cicy5449_bridge_advancement_verification.json",
            "experiments/latent_atlas/reports/atlas_guided_raw_scout_outside_verified_corpus.json",
            "reports/no_go_atlas_guided_lateral_scout.json",
            "reports/nonfavourable_ambient_restricted_scout.json",
        ],
        representative_examples=[
            {
                "direct_split_search": search,
                "raw_free_action_summary": raw,
                "ambient_bundle_breadcrumb": breadcrumb,
            }
        ],
        nearest_escape={
            "minimal_change": (
                "find a concrete favourable presentation witness for CICY5449 by "
                "broadening beyond ordinary one-step P2 split contractions"
            ),
            "recommended_next_pass": report["next_step"][
                "recommended_next_target_id"
            ],
            "engine_escape_hatch": report["next_step"]["return_condition"],
            "stop_rule": (
                "Do not promote CICY5449 until a concrete favourable witness or "
                "presentation isomorphism is documented."
            ),
        },
    )


def cicy7810_no_direct_split_witness_syndrome() -> dict[str, Any]:
    report = load_json(latent_artifact("cicy7810_bridge_action_transfer_audit.json"))
    pool = report["same_hodge_favourable_pool"]
    search = report["direct_split_search"]
    raw = report["raw_free_action_summary"]
    breadcrumb = report["ambient_breadcrumb_summary"]
    sample = {
        "requires_concrete_split_witness": True,
        "parent_free_action_count": raw["free_option_count"],
        "same_hodge_pool_count": pool["pool_count"],
        "same_hodge_favourable_unknown_count": len(
            pool["favourable_unknown_nums"]
        ),
        "same_hodge_favourable_known_free_count": len(
            pool["favourable_known_free_nums"]
        ),
        "direct_one_step_split_hit_count": search[
            "direct_one_step_split_hit_count"
        ],
        "bridge_status": report["status"],
    }
    return syndrome(
        syndrome_id="cicy7810_no_direct_split_witness_current_data",
        title="Z3 same-Hodge favourable pool exists, but no direct split witness",
        geometry="CICY7810 no direct favourable split witness",
        scope_class="presentation-local",
        claim_scope=(
            "Current cicylist.m and local verifier data for the CICY7810 same-Hodge "
            "presentation bridge under ordinary one-step split-row contractions. "
            "This is not a theorem that no favourable presentation or multi-step "
            "split route exists."
        ),
        stage="presentation_bridge_witness_selection_gate",
        minimal_obstruction_core={
            "parent_cicy": 7810,
            "same_hodge_pool_count": pool["pool_count"],
            "same_hodge_favourable_unknown_nums": pool[
                "favourable_unknown_nums"
            ],
            "same_hodge_favourable_known_free_nums": pool[
                "favourable_known_free_nums"
            ],
            "direct_one_step_split_hit_count": search[
                "direct_one_step_split_hit_count"
            ],
            "parent_free_z3_option_count": raw["free_option_count"],
            "all_parent_free_options_row_trivial": raw[
                "all_free_options_row_trivial"
            ],
            "ambient_restricted_bundle_breadcrumb_available": breadcrumb[
                "ambient_restricted_bundle_breadcrumb_available"
            ],
            "ambient_breadcrumb_target_report_count": breadcrumb[
                "cicy7810_target_report_count"
            ],
        },
        cheap_prefilter="direct_split_witness_missing_current_data",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy7810_bridge_action_transfer_audit.json",
            **sample,
            "ambient_breadcrumb_target_report_count": breadcrumb[
                "cicy7810_target_report_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "direct_split_witness_missing_current_data", sample
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy7810_bridge_action_transfer_audit.json",
            "experiments/latent_atlas/reports/cicy7810_bridge_action_transfer_audit_verification.json",
            "experiments/latent_atlas/reports/atlas_gap_queue_post_cicy7810_bridge_advancement.json",
            "experiments/latent_atlas/reports/atlas_gap_queue_post_cicy7810_bridge_advancement_verification.json",
            "experiments/latent_atlas/reports/atlas_guided_raw_scout_outside_verified_corpus.json",
            "reports/no_go_atlas_guided_lateral_scout.json",
            "reports/nonfavourable_ambient_restricted_scout.json",
        ],
        representative_examples=[
            {
                "direct_split_search": search,
                "raw_free_action_summary": raw,
                "ambient_bundle_breadcrumb": breadcrumb,
            }
        ],
        nearest_escape={
            "minimal_change": (
                "find a concrete favourable presentation witness for CICY7810 by "
                "broadening beyond ordinary one-step split-row contractions"
            ),
            "recommended_next_pass": report["next_step"][
                "recommended_next_target_id"
            ],
            "engine_escape_hatch": report["next_step"]["return_condition"],
            "stop_rule": (
                "Do not promote CICY7810 until a concrete favourable witness or "
                "presentation isomorphism is documented."
            ),
        },
    )


def cicy5302_gutall_benchmark_pool_engine_gap_syndrome() -> dict[str, Any]:
    report = load_json(
        latent_artifact("cicy5302_gutall_benchmark_pool_engine_audit.json")
    )
    algebraic = report["algebraic_pool_summary"]
    raw = report["raw_free_action_summary"]
    lift = report["ambient_lift_readiness"]["by_symmetry_order"]
    engine = report["promotion_engine_inventory"]
    sample = {
        "requires_geometry_specific_promotion_engine": True,
        "model_count": algebraic["model_count"],
        "algebraic_benchmark_failure_count": algebraic["failure_count"],
        "raw_free_action_count": raw["free_option_count"],
        "generic_ambient_line_bundle_lift_readiness_engine_available": engine[
            "generic_ambient_line_bundle_lift_readiness_engine_available"
        ],
        "geometry_specific_wilson_component_engine_available": engine[
            "geometry_specific_wilson_component_engine_available"
        ],
        "geometry_specific_representative_mass_engine_available": engine[
            "geometry_specific_representative_mass_engine_available"
        ],
        "generic_representative_promotion_engine_available": engine[
            "generic_representative_promotion_engine_available"
        ],
        "engine_gap_status": report["status"],
    }
    return syndrome(
        syndrome_id="cicy5302_gutall_benchmark_pool_engine_gap_current_data",
        title="Large clean GUTall benchmark pool, but no current CICY5302 promotion engine",
        geometry="CICY5302 GUTall benchmark pool",
        scope_class="grammar-local",
        claim_scope=(
            "Current repository promotion grammar for CICY5302. This records that "
            "the algebraic/index/anomaly and raw-action layers are verified, but "
            "the current code has no CICY5302 Wilson-component plus equivariant "
            "representative mass-channel engine. It is not a physical no-go for "
            "CICY5302."
        ),
        stage="geometry_specific_equivariant_representative_and_component_mass_engine_gate",
        minimal_obstruction_core={
            "cicy": 5302,
            "h11": report["parent_geometry"]["h11"],
            "h21": report["parent_geometry"]["h21"],
            "eta": report["parent_geometry"]["eta"],
            "model_count": algebraic["model_count"],
            "model_counts_by_symmetry_order": algebraic[
                "model_counts_by_symmetry_order"
            ],
            "algebraic_benchmark_failure_count": algebraic["failure_count"],
            "raw_free_action_count": raw["free_option_count"],
            "raw_free_order_counts": raw["free_order_counts"],
            "raw_free_group_structure_counts": raw["free_group_structure_counts"],
            "all_free_options_row_trivial": raw["all_free_options_row_trivial"],
            "ambient_lift_readiness_by_symmetry_order": lift,
            "geometry_specific_wilson_component_engine_available": engine[
                "geometry_specific_wilson_component_engine_available"
            ],
            "geometry_specific_representative_mass_engine_available": engine[
                "geometry_specific_representative_mass_engine_available"
            ],
            "generic_representative_promotion_engine_available": engine[
                "generic_representative_promotion_engine_available"
            ],
            "matched_current_engine_artifacts": engine[
                "matched_current_engine_artifacts"
            ],
        },
        cheap_prefilter="geometry_specific_engine_missing_current_data",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy5302_gutall_benchmark_pool_engine_audit.json",
            **sample,
            "order2_ambient_lift_ready_count": lift["2"][
                "any_direct_sum_equivariant_lift_count"
            ],
            "order4_ambient_lift_ready_count": lift["4"][
                "any_direct_sum_equivariant_lift_count"
            ],
            "order4_ambient_lift_obstructed_count": lift["4"][
                "no_direct_sum_equivariant_lift_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "geometry_specific_engine_missing_current_data", sample
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy5302_gutall_benchmark_pool_engine_audit.json",
            "experiments/latent_atlas/reports/cicy5302_gutall_benchmark_pool_engine_audit_verification.json",
            "experiments/latent_atlas/reports/atlas_gap_queue_post_cicy7810_bridge_advancement.json",
            "experiments/latent_atlas/reports/atlas_gap_queue_post_cicy7810_bridge_advancement_verification.json",
            "experiments/latent_atlas/reports/atlas_guided_raw_scout_outside_verified_corpus.json",
            "reports/no_go_atlas_guided_lateral_scout.json",
        ],
        representative_examples=[
            {
                "algebraic_pool_summary": algebraic,
                "raw_free_action_summary": raw,
                "ambient_lift_readiness": lift,
                "promotion_engine_inventory": engine,
            }
        ],
        nearest_escape={
            "minimal_change": (
                "implement a CICY5302 Wilson-component and equivariant Koszul "
                "representative mass-channel engine"
            ),
            "recommended_next_pass": report["next_step"][
                "recommended_next_target_id"
            ],
            "engine_escape_hatch": report["next_step"]["return_condition"],
            "stop_rule": report["next_step"]["stop_rule"],
        },
    )


def cicy5256_gutall_benchmark_pool_engine_gap_syndrome() -> dict[str, Any]:
    report = load_json(
        latent_artifact("cicy5256_gutall_benchmark_pool_engine_audit.json")
    )
    algebraic = report["algebraic_pool_summary"]
    raw = report["raw_free_action_summary"]
    lift = report["ambient_lift_readiness"]["by_symmetry_order"]
    engine = report["promotion_engine_inventory"]
    sample = report["prefilter_sample"]
    return syndrome(
        syndrome_id="cicy5256_gutall_benchmark_pool_engine_gap_current_data",
        title="Clean GUTall benchmark pool, but no current CICY5256 promotion engine",
        geometry="CICY5256 GUTall benchmark pool",
        scope_class="grammar-local",
        claim_scope=(
            "Current repository promotion grammar for CICY5256. This records that "
            "the algebraic/index/anomaly, raw-action, and ambient lift-readiness "
            "layers are verified, but the current code has no CICY5256 Wilson-"
            "component plus equivariant representative mass-channel engine. It is "
            "not a physical no-go for CICY5256."
        ),
        stage="geometry_specific_equivariant_representative_and_component_mass_engine_gate",
        minimal_obstruction_core={
            "cicy": 5256,
            "h11": report["parent_geometry"]["h11"],
            "h21": report["parent_geometry"]["h21"],
            "eta": report["parent_geometry"]["eta"],
            "model_count": algebraic["model_count"],
            "model_counts_by_symmetry_order": algebraic[
                "model_counts_by_symmetry_order"
            ],
            "algebraic_benchmark_failure_count": algebraic["failure_count"],
            "raw_free_action_count": raw["free_option_count"],
            "raw_free_order_counts": raw["free_order_counts"],
            "raw_free_group_structure_counts": raw["free_group_structure_counts"],
            "all_free_options_row_trivial": raw["all_free_options_row_trivial"],
            "ambient_lift_readiness_by_symmetry_order": lift,
            "geometry_specific_wilson_component_engine_available": engine[
                "geometry_specific_wilson_component_engine_available"
            ],
            "geometry_specific_representative_mass_engine_available": engine[
                "geometry_specific_representative_mass_engine_available"
            ],
            "generic_representative_promotion_engine_available": engine[
                "generic_representative_promotion_engine_available"
            ],
            "matched_current_engine_artifacts": engine[
                "matched_current_engine_artifacts"
            ],
        },
        cheap_prefilter="geometry_specific_engine_missing_current_data",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy5256_gutall_benchmark_pool_engine_audit.json",
            **sample,
            "order2_ambient_lift_ready_count": lift["2"][
                "any_direct_sum_equivariant_lift_count"
            ],
            "order4_ambient_lift_ready_count": lift["4"][
                "any_direct_sum_equivariant_lift_count"
            ],
            "order4_ambient_lift_obstructed_count": lift["4"][
                "no_direct_sum_equivariant_lift_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "geometry_specific_engine_missing_current_data", sample
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy5256_gutall_benchmark_pool_engine_audit.json",
            "experiments/latent_atlas/reports/cicy5256_gutall_benchmark_pool_engine_audit_verification.json",
            "experiments/latent_atlas/reports/atlas_gap_queue_post_cicy5425_benchmark_advancement.json",
            "experiments/latent_atlas/reports/atlas_gap_queue_post_cicy5425_benchmark_advancement_verification.json",
            "experiments/latent_atlas/reports/atlas_guided_raw_scout_outside_verified_corpus.json",
            "reports/no_go_atlas_guided_lateral_scout.json",
        ],
        representative_examples=[
            {
                "algebraic_pool_summary": algebraic,
                "raw_free_action_summary": raw,
                "ambient_lift_readiness": lift,
                "promotion_engine_inventory": engine,
            }
        ],
        nearest_escape={
            "minimal_change": (
                "implement a CICY5256 Wilson-component and equivariant Koszul "
                "representative mass-channel engine"
            ),
            "recommended_next_pass": report["next_step"][
                "recommended_next_target_id"
            ],
            "engine_escape_hatch": report["next_step"]["return_condition"],
            "stop_rule": report["next_step"]["stop_rule"],
        },
    )


def cicy5273_gutall_benchmark_pool_raw_action_gap_syndrome() -> dict[str, Any]:
    report = load_json(
        latent_artifact("cicy5273_gutall_benchmark_pool_engine_audit.json")
    )
    algebraic = report["algebraic_pool_summary"]
    raw = report["raw_free_action_summary"]
    lift = report["ambient_lift_readiness"]["by_symmetry_order"]
    sample = report["prefilter_sample"]
    return syndrome(
        syndrome_id="cicy5273_gutall_benchmark_pool_raw_action_gap_current_data",
        title="Clean GUTall benchmark pool, but no local raw free-action option",
        geometry="CICY5273 GUTall benchmark pool",
        scope_class="grammar-local",
        claim_scope=(
            "Current repository data for CICY5273. This records that the "
            "algebraic/index/anomaly GUTall pool is verified, but local cicylist.m "
            "has no free-action option to feed Wilson-component descent. It is not "
            "a physical no-go for CICY5273."
        ),
        stage="raw_free_action_data_gate",
        minimal_obstruction_core={
            "cicy": 5273,
            "h11": report["parent_geometry"]["h11"],
            "h21": report["parent_geometry"]["h21"],
            "eta": report["parent_geometry"]["eta"],
            "model_count": algebraic["model_count"],
            "model_counts_by_symmetry_order": algebraic[
                "model_counts_by_symmetry_order"
            ],
            "algebraic_benchmark_failure_count": algebraic["failure_count"],
            "gutall_symmetry_orders": report["parent_geometry"][
                "symmetry_orders_in_cicy_entry"
            ],
            "raw_symmetry_status": raw["raw_symmetry_status"],
            "raw_symmetry_option_count": raw["raw_symmetry_option_count"],
            "raw_free_action_count": raw["free_option_count"],
            "ambient_lift_readiness_by_symmetry_order": lift,
        },
        cheap_prefilter="raw_free_action_data_missing_current_data",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy5273_gutall_benchmark_pool_engine_audit.json",
            **sample,
            "order2_ambient_lift_ready_count": lift["2"][
                "any_direct_sum_equivariant_lift_count"
            ],
            "order2_ambient_lift_obstructed_count": lift["2"][
                "no_direct_sum_equivariant_lift_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "raw_free_action_data_missing_current_data", sample
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy5273_gutall_benchmark_pool_engine_audit.json",
            "experiments/latent_atlas/reports/cicy5273_gutall_benchmark_pool_engine_audit_verification.json",
            "experiments/latent_atlas/reports/atlas_gap_queue_post_cicy5302_benchmark_advancement.json",
            "experiments/latent_atlas/reports/atlas_gap_queue_post_cicy5302_benchmark_advancement_verification.json",
            "experiments/latent_atlas/reports/atlas_guided_raw_scout_outside_verified_corpus.json",
            "reports/no_go_atlas_guided_lateral_scout.json",
        ],
        representative_examples=[
            {
                "algebraic_pool_summary": algebraic,
                "raw_free_action_summary": raw,
                "ambient_lift_readiness": lift,
            }
        ],
        nearest_escape={
            "minimal_change": (
                "recover explicit raw free-action data for CICY5273 or provide an "
                "external quotient-action certificate compatible with Wilson descent"
            ),
            "recommended_next_pass": report["next_step"][
                "recommended_next_target_id"
            ],
            "engine_escape_hatch": report["next_step"]["return_condition"],
            "stop_rule": report["next_step"]["stop_rule"],
        },
    )


def cicy6738_gutall_benchmark_pool_raw_action_gap_syndrome() -> dict[str, Any]:
    report = load_json(
        latent_artifact("cicy6738_gutall_benchmark_pool_engine_audit.json")
    )
    algebraic = report["algebraic_pool_summary"]
    raw = report["raw_free_action_summary"]
    lift = report["ambient_lift_readiness"]["by_symmetry_order"]
    sample = report["prefilter_sample"]
    return syndrome(
        syndrome_id="cicy6738_gutall_benchmark_pool_raw_action_gap_current_data",
        title="Clean GUTall benchmark pool, but no local raw free-action option",
        geometry="CICY6738 GUTall benchmark pool",
        scope_class="grammar-local",
        claim_scope=(
            "Current repository data for CICY6738. This records that the "
            "algebraic/index/anomaly GUTall pool is verified, but local cicylist.m "
            "has no free-action option to feed Wilson-component descent. It is not "
            "a physical no-go for CICY6738."
        ),
        stage="raw_free_action_data_gate",
        minimal_obstruction_core={
            "cicy": 6738,
            "h11": report["parent_geometry"]["h11"],
            "h21": report["parent_geometry"]["h21"],
            "eta": report["parent_geometry"]["eta"],
            "model_count": algebraic["model_count"],
            "model_counts_by_symmetry_order": algebraic[
                "model_counts_by_symmetry_order"
            ],
            "algebraic_benchmark_failure_count": algebraic["failure_count"],
            "gutall_symmetry_orders": report["parent_geometry"][
                "symmetry_orders_in_cicy_entry"
            ],
            "raw_symmetry_status": raw["raw_symmetry_status"],
            "raw_symmetry_option_count": raw["raw_symmetry_option_count"],
            "raw_free_action_count": raw["free_option_count"],
            "ambient_lift_readiness_by_symmetry_order": lift,
        },
        cheap_prefilter="raw_free_action_data_missing_current_data",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy6738_gutall_benchmark_pool_engine_audit.json",
            **sample,
            "order2_ambient_lift_ready_count": lift["2"][
                "any_direct_sum_equivariant_lift_count"
            ],
            "order2_ambient_lift_obstructed_count": lift["2"][
                "no_direct_sum_equivariant_lift_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "raw_free_action_data_missing_current_data", sample
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy6738_gutall_benchmark_pool_engine_audit.json",
            "experiments/latent_atlas/reports/cicy6738_gutall_benchmark_pool_engine_audit_verification.json",
            "experiments/latent_atlas/reports/atlas_gap_queue_post_cicy5273_benchmark_advancement.json",
            "experiments/latent_atlas/reports/atlas_gap_queue_post_cicy5273_benchmark_advancement_verification.json",
            "experiments/latent_atlas/reports/atlas_guided_raw_scout_outside_verified_corpus.json",
            "reports/no_go_atlas_guided_lateral_scout.json",
        ],
        representative_examples=[
            {
                "algebraic_pool_summary": algebraic,
                "raw_free_action_summary": raw,
                "ambient_lift_readiness": lift,
            }
        ],
        nearest_escape={
            "minimal_change": (
                "recover explicit raw free-action data for CICY6738 or provide an "
                "external quotient-action certificate compatible with Wilson descent"
            ),
            "recommended_next_pass": report["next_step"][
                "recommended_next_target_id"
            ],
            "engine_escape_hatch": report["next_step"]["return_condition"],
            "stop_rule": report["next_step"]["stop_rule"],
        },
    )


def cicy5425_gutall_benchmark_pool_raw_action_gap_syndrome() -> dict[str, Any]:
    report = load_json(
        latent_artifact("cicy5425_gutall_benchmark_pool_engine_audit.json")
    )
    algebraic = report["algebraic_pool_summary"]
    raw = report["raw_free_action_summary"]
    lift = report["ambient_lift_readiness"]["by_symmetry_order"]
    sample = report["prefilter_sample"]
    return syndrome(
        syndrome_id="cicy5425_gutall_benchmark_pool_raw_action_gap_current_data",
        title="Clean GUTall benchmark pool, but no local raw free-action option",
        geometry="CICY5425 GUTall benchmark pool",
        scope_class="grammar-local",
        claim_scope=(
            "Current repository data for CICY5425. This records that the "
            "algebraic/index/anomaly GUTall pool is verified, but local cicylist.m "
            "has no free-action option to feed Wilson-component descent. It is not "
            "a physical no-go for CICY5425."
        ),
        stage="raw_free_action_data_gate",
        minimal_obstruction_core={
            "cicy": 5425,
            "h11": report["parent_geometry"]["h11"],
            "h21": report["parent_geometry"]["h21"],
            "eta": report["parent_geometry"]["eta"],
            "model_count": algebraic["model_count"],
            "model_counts_by_symmetry_order": algebraic[
                "model_counts_by_symmetry_order"
            ],
            "algebraic_benchmark_failure_count": algebraic["failure_count"],
            "gutall_symmetry_orders": report["parent_geometry"][
                "symmetry_orders_in_cicy_entry"
            ],
            "raw_symmetry_status": raw["raw_symmetry_status"],
            "raw_symmetry_option_count": raw["raw_symmetry_option_count"],
            "raw_free_action_count": raw["free_option_count"],
            "ambient_lift_readiness_by_symmetry_order": lift,
        },
        cheap_prefilter="raw_free_action_data_missing_current_data",
        replay_counts={
            "source": "experiments/latent_atlas/reports/cicy5425_gutall_benchmark_pool_engine_audit.json",
            **sample,
            "order2_ambient_lift_ready_count": lift["2"][
                "any_direct_sum_equivariant_lift_count"
            ],
            "order2_ambient_lift_obstructed_count": lift["2"][
                "no_direct_sum_equivariant_lift_count"
            ],
            "prefilter_sample_passes": evaluate_prefilter(
                "raw_free_action_data_missing_current_data", sample
            ),
        },
        evidence_artifacts=[
            "experiments/latent_atlas/reports/cicy5425_gutall_benchmark_pool_engine_audit.json",
            "experiments/latent_atlas/reports/cicy5425_gutall_benchmark_pool_engine_audit_verification.json",
            "experiments/latent_atlas/reports/atlas_gap_queue_post_cicy6738_benchmark_advancement.json",
            "experiments/latent_atlas/reports/atlas_gap_queue_post_cicy6738_benchmark_advancement_verification.json",
            "experiments/latent_atlas/reports/atlas_guided_raw_scout_outside_verified_corpus.json",
            "reports/no_go_atlas_guided_lateral_scout.json",
        ],
        representative_examples=[
            {
                "algebraic_pool_summary": algebraic,
                "raw_free_action_summary": raw,
                "ambient_lift_readiness": lift,
            }
        ],
        nearest_escape={
            "minimal_change": (
                "recover explicit raw free-action data for CICY5425 or provide an "
                "external quotient-action certificate compatible with Wilson descent"
            ),
            "recommended_next_pass": report["next_step"][
                "recommended_next_target_id"
            ],
            "engine_escape_hatch": report["next_step"]["return_condition"],
            "stop_rule": report["next_step"]["stop_rule"],
        },
    )


def build_report() -> dict[str, Any]:
    verification_paths = verified_artifacts()
    syndromes = [
        outside_regime_syndrome(),
        cicy5259_vectorlike_syndrome(),
        cicy7484_vectorlike_syndrome(),
        degree_zero_top_cup_syndrome(),
        representative_mismatch_syndrome(),
        degree_one_intersection_syndrome(),
        higher_degree_downstream_syndrome(),
        branch50_standard_m4_syndrome(),
        cicy6927_model874_s42_basin_syndrome(),
        cicy6927_non_s42_cup_missing_one_higgs_syndrome(),
        cicy6927_model252_s42_boundary_only_syndrome(),
        cicy6927_model254_s42_boundary_only_syndrome(),
        cicy6927_model369_s42_boundary_only_syndrome(),
        cicy6927_model52_s42_boundary_only_syndrome(),
        cicy6836_one_higgs_proton_disjoint_syndrome(),
        cicy6836_model87_intersection_forcing_syndrome(),
        cicy6836_model186_frontier691_followup_syndrome(),
        cicy6836_model136_existing_boundary_floor_syndrome(),
        cicy6715_model215_computed_anchor_missing_higgs_cup_syndrome(),
        cicy6715_model766_branch99_higher_map_syndrome(),
        cicy6788_wall_breaker_one_higgs_proton_unsafe_syndrome(),
        cicy6784_cubic_yukawa_absent_syndrome(),
        cicy6784_higher_degree_yukawa_charge_mismatch_syndrome(),
        cicy6784_charge_defect_no_improvement_syndrome(),
        cicy6784_upstream_transferred_m3_boundary_syndrome(),
        cicy6784_transferred_m3_no_direct_tree_syndrome(),
        cicy6784_preferred_routes_no_homotopy_seed_syndrome(),
        cicy6784_single_anchor_no_homotopy_seed_syndrome(),
        cicy6784_multistage_first_pair_no_homotopy_seed_syndrome(),
        cicy6784_chain_contraction_fallback_syndrome(),
        cicy4185_split_action_lift_missing_syndrome(),
        cicy6187_split_action_lift_missing_syndrome(),
        cicy6201_split_action_lift_missing_syndrome(),
        cicy6281_split_action_lift_missing_syndrome(),
        cicy4078_split_action_lift_missing_syndrome(),
        cicy5141_split_action_lift_missing_syndrome(),
        cicy5248_split_action_lift_missing_syndrome(),
        cicy5406_split_action_lift_missing_syndrome(),
        cicy5449_no_direct_split_witness_syndrome(),
        cicy7810_no_direct_split_witness_syndrome(),
        cicy5302_gutall_benchmark_pool_engine_gap_syndrome(),
        cicy5273_gutall_benchmark_pool_raw_action_gap_syndrome(),
        cicy6738_gutall_benchmark_pool_raw_action_gap_syndrome(),
        cicy5425_gutall_benchmark_pool_raw_action_gap_syndrome(),
        cicy5256_gutall_benchmark_pool_engine_gap_syndrome(),
        cicy6784_radius4_local_deformation_no_first_pair_seed_syndrome(),
        verified_overlap_first_pair_seed_absent_syndrome(),
        first_pair_positive_generator_no_seed_syndrome(),
    ]
    scope_counts = dict(sorted(Counter(item["scope_class"] for item in syndromes).items()))
    prefilter_ids = sorted(
        {item["cheap_prefilter"]["prefilter_id"] for item in syndromes}
    )
    syndrome_ids = {item["syndrome_id"] for item in syndromes}
    branch50 = next(
        item
        for item in syndromes
        if item["syndrome_id"] == "branch50_standard_m4_four_h1_not_cy3_top_cup"
    )
    gates = {
        "source_verifications_pass": gate(
            all_verifications_pass(verification_paths),
            json.dumps({key: str(path) for key, path in verification_paths.items()}, sort_keys=True),
            "all imported source verifications pass",
        ),
        "covers_requested_artifact_families": gate(
            {
                "CICY2544",
                "CICY7484",
                "CICY5259 via favourable split 7914",
                "CICY6927/model 874 option 4",
                "CICY6927/model 252 option 4",
                "CICY6927/model 254 option 4",
                "CICY6927/model 369 option 4",
                "CICY6927/model 52 option 4",
                "CICY6836/model 95 and 139 option 23",
                "CICY6836/model 87 option 23",
                "CICY6836/model 186 option 23 plus frontier 691",
                "CICY6836/model 136 option 23 plus frontier 691",
                "CICY6715/model 215 and 336 option 1",
                "CICY6788/model 227 and 620 option 0",
                "CICY6784/model 31 option 2",
                "CICY4185 via favourable split 7910",
                "CICY6187 via favourable split 7899",
                "CICY6201 via favourable split 7900",
                "CICY6281 via favourable split 7904",
                "CICY4078 via favourable split 7908",
                "CICY5141 via favourable split 7912",
                "CICY5248 via favourable split 7913",
                "CICY5406 via favourable split 7918",
                "CICY5449 no direct favourable split witness",
                "CICY7810 no direct favourable split witness",
                "CICY5302 GUTall benchmark pool",
                "CICY5273 GUTall benchmark pool",
                "CICY6738 GUTall benchmark pool",
                "CICY5425 GUTall benchmark pool",
                "CICY5256 GUTall benchmark pool",
            }.issubset(
                {item["geometry"] for item in syndromes}
            ),
            "syndrome geometries",
            "atlas covers 2544, 7484, 5259/7914, 6927/model-874/model-252/model-254/model-369/model-52, 6836/model-136, 6836, 6715, 6788, 6784, presentation-bridge artifacts, CICY5302, CICY5273, CICY6738, CICY5425, and CICY5256",
        ),
        "every_syndrome_has_scoped_prefilter_and_replay": gate(
            all(
                item["scope_class"]
                in {
                    "candidate-specific",
                    "grammar-local",
                    "presentation-local",
                    "geometry-local",
                    "global-looking",
                }
                and item["cheap_prefilter"]["prefilter_id"] in describe_prefilters()
                and item["replay_counts"]
                and item["evidence_artifacts"]
                for item in syndromes
            ),
            "syndrome records",
            "each no-go syndrome has scope class, executable prefilter, replay counts, and evidence",
        ),
        "prefilter_self_tests_pass": gate(
            all(
                item["replay_counts"].get("prefilter_sample_passes") is True
                for item in syndromes
            ),
            "prefilter sample records",
            "each atlas prefilter fires on its representative obstruction sample",
        ),
        "branch50_negative_control_is_present": gate(
            "branch50_standard_m4_four_h1_not_cy3_top_cup" in syndrome_ids
            and branch50["minimal_obstruction_core"]["candidate_label"]
            == "radius6_broad_adjacency_filtered_10_branch_50"
            and branch50["minimal_obstruction_core"]["operator"] == "5bar_02*5_34"
            and branch50["minimal_obstruction_core"]["monomial"] == ["e3-e2", "e4-e0"]
            and branch50["minimal_obstruction_core"]["output_degree"] == 2
            and branch50["minimal_obstruction_core"]["standard_m4_to_H3_rank"] == 0,
            "branch-50 m4 degree-law syndrome",
            "Branch 50 is preserved as a negative control, not a survivor certificate",
        ),
        "no_active_survivor_after_degree_audit": gate(
            branch50["representative_examples"][0]["verdict"][
                "branch50_killed_for_standard_cochain_m4_mass"
            ]
            and not branch50["representative_examples"][0]["verdict"][
                "mssm_candidate_verified"
            ],
            "branch-50 m4 degree-law verdict",
            "the previous pending survivor is retired by the standard m4 degree-law audit",
        ),
    }
    return {
        "title": "No-Go Atlas v0",
        "status": "no_go_atlas_v0_built",
        "scope": (
            "Existing verified 5259/7914 radius-9, 7484, and 2544 artifacts; "
            "scoped obstruction rules, not global landscape theorems except where marked global-looking."
        ),
        "source_verifications": {
            key: {"path": str(path), "all_gates_pass": load_json(path).get("all_gates_pass")}
            for key, path in verification_paths.items()
        },
        "prefilter_registry": describe_prefilters(),
        "summary": {
            "syndrome_count": len(syndromes),
            "scope_class_counts": scope_counts,
            "prefilter_ids": prefilter_ids,
            "survivor_count": 0,
            "requested_geometries_covered": [
                "5259/7914",
                "7484",
                "2544",
                "6927/model874",
                "6927/model252",
                "6927/model254",
                "6927/model369",
                "6927/model52",
                "6836",
                "6836/model136",
                "6715",
                "6788",
                "6784/model31",
                "4185/7910",
                "6187/7899",
                "6201/7900",
                "6281/7904",
                "4078/7908",
                "5141/7912",
                "5248/7913",
                "5406/7918",
                "5449/no-direct-split",
                "7810/no-direct-split",
                "5302/gutall-benchmark-pool",
                "5273/gutall-benchmark-pool",
                "6738/gutall-benchmark-pool",
                "5425/gutall-benchmark-pool",
                "5256/gutall-benchmark-pool",
            ],
        },
        "syndromes": syndromes,
        "survivor_certificates": [],
        "atlas_policy": {
            "promotion_rule": (
                "Future candidates should not be promoted past a gate if a cheap "
                "atlas prefilter fires inside the prefilter's stated claim scope."
            ),
            "scope_warning": (
                "A grammar-local no-go only prunes that generator/search grammar. "
                "It must not be cited as a manifold-level impossibility theorem."
            ),
            "survivor_rule": (
                "A survivor certificate must include certified survival gates, a "
                "pending next gate, and nearest no-go boundaries. Branches that "
                "fail a later algebraic gate must be moved to negative controls."
            ),
        },
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# No-Go Atlas v0",
        "",
        f"Status: `{report['status']}`",
        f"Scope: {report['scope']}",
        "",
        "## Summary",
        "",
        f"- syndrome_count: `{report['summary']['syndrome_count']}`",
        f"- scope_class_counts: `{report['summary']['scope_class_counts']}`",
        f"- prefilter_ids: `{report['summary']['prefilter_ids']}`",
        f"- survivor_count: `{report['summary']['survivor_count']}`",
        "",
        "## Syndromes",
        "",
    ]
    for item in report["syndromes"]:
        lines.extend(
            [
                f"### {item['syndrome_id']}",
                "",
                f"- title: {item['title']}",
                f"- geometry: `{item['geometry']}`",
                f"- scope_class: `{item['scope_class']}`",
                f"- stage: `{item['stage']}`",
                f"- cheap_prefilter: `{item['cheap_prefilter']['prefilter_id']}`",
                f"- replay_counts: `{item['replay_counts']}`",
                f"- nearest_escape_or_boundary: `{item['nearest_escape_or_boundary']}`",
                "",
            ]
        )
    if report["survivor_certificates"]:
        lines.extend(["## Survivor Certificates", ""])
        for survivor in report["survivor_certificates"]:
            lines.extend(
                [
                    f"- survivor_id: `{survivor['survivor_id']}`",
                    f"- candidate: `{survivor['candidate_label']}`",
                    f"- status: `{survivor['status']}`",
                    "",
                ]
            )
    else:
        lines.extend(
            [
                "## No Active Survivor Certificates",
                "",
                "Branch 50 is now recorded as `branch50_standard_m4_four_h1_not_cy3_top_cup`, a candidate-specific negative control.",
                "",
            ]
        )
    lines.extend(["", "## Gates", ""])
    for key, item in report["gates"].items():
        lines.append(f"- {key}: `{item['pass']}` - {item['note']}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "no_go_atlas_v0.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "no_go_atlas_v0.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, md_out)
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    print(f"wrote {json_out}")
    print(f"wrote {md_out}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
