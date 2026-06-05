#!/usr/bin/env python3
"""Build the No-Go Atlas v0.

The atlas compresses verified failed searches into scoped obstruction
syndromes and executable cheap prefilters.  It also records the current
higher-degree survivor as a proof-carrying pending certificate.
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
        "cicy5259_quotient": artifact("cicy5259_quotient_wilson_line_verification.json"),
        "outside_regime_free_symmetry": artifact(
            "outside_regime_free_symmetry_no_go_verification.json"
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
            "followup_result": "branch radius6_broad_adjacency_filtered_10_branch_50 is frozen in the survivor dossier",
        },
    )


def survivor_certificate() -> dict[str, Any]:
    dossier = load_json(artifact("phenomenology_guided_q1_radius9_higher_degree_candidate_dossier.json"))
    higher = load_json(artifact("phenomenology_guided_q1_radius9_higher_degree_intersection_search.json"))
    examples = higher["minimal_operator_examples"]
    return {
        "survivor_id": "survivor_radius6_broad_adjacency_filtered_10_branch_50",
        "candidate_label": dossier["candidate_identity"]["label"],
        "geometry": dossier["candidate_identity"]["route"],
        "status": dossier["status"],
        "classification": dossier["verdict"]["classification"],
        "source_artifacts": [
            "reports/phenomenology_guided_q1_radius9_higher_degree_candidate_dossier.json",
            "reports/phenomenology_guided_q1_radius9_higher_degree_candidate_dossier_verification.json",
        ],
        "operator_certificate": dossier["operator_certificate"],
        "cohomology_legs": dossier["cohomology_legs"],
        "certified_survival_gates": dossier["verdict"]["certified_facts"],
        "pending_gate": {
            "gate": "higher_order_effective_mass_map_rank",
            "ordinary_cup_status": dossier["higher_order_mass_map_frontier"][
                "ordinary_cup_status"
            ],
            "triplet_rank_condition": dossier["higher_order_mass_map_frontier"][
                "triplet_mass_block"
            ],
            "doublet_rank_condition": dossier["higher_order_mass_map_frontier"][
                "doublet_mass_block"
            ],
            "not_claimed": dossier["verdict"]["not_claimed"],
        },
        "nearest_no_go_boundaries": [
            {
                "boundary_id": "cubic_only_gate",
                "tiny_mutation": "forbid degree-2/3 singlet monoids and require a simple CY3 cubic cup product",
                "resulting_status": "not promoted because simple_cy3_cubic_top_cup_eligible is false",
                "evidence": dossier["higher_order_mass_map_frontier"][
                    "ordinary_cup_reason"
                ],
            },
            {
                "boundary_id": "doublet_support",
                "tiny_mutation": "same higher-monoid grammar but triplet support also hits the doublet component",
                "resulting_status": "higher_monoid_doublet_support_obstruction",
                "example": examples["higher_monoid_doublet_support_obstruction"],
            },
            {
                "boundary_id": "proton_unprotected",
                "tiny_mutation": "keep triplet-only support but allow dangerous 10*5bar*5bar operators",
                "resulting_status": "higher_monoid_triplet_only_but_proton_unprotected",
                "example": examples["higher_monoid_triplet_only_but_proton_unprotected"],
            },
            {
                "boundary_id": "cup_5_unrealizable",
                "tiny_mutation": "keep representative-compatible 5bar and proton safety but fail the cup-dual 5 representative character",
                "resulting_status": "higher_monoid_triplet_only_proton_safe_but_cup_5_unrealizable",
                "example": examples[
                    "higher_monoid_triplet_only_proton_safe_but_cup_5_unrealizable"
                ],
            },
        ],
    }


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
    ]
    survivor = survivor_certificate()
    scope_counts = dict(sorted(Counter(item["scope_class"] for item in syndromes).items()))
    prefilter_ids = sorted(
        {item["cheap_prefilter"]["prefilter_id"] for item in syndromes}
    )
    gates = {
        "source_verifications_pass": gate(
            all_verifications_pass(verification_paths),
            json.dumps({key: str(path) for key, path in verification_paths.items()}, sort_keys=True),
            "all imported source verifications pass",
        ),
        "covers_requested_artifact_families": gate(
            {"CICY2544", "CICY7484", "CICY5259 via favourable split 7914"}.issubset(
                {item["geometry"] for item in syndromes}
                | {survivor["geometry"]}
            ),
            "syndrome geometries + survivor geometry",
            "atlas covers 2544, 7484, and 5259/7914 artifacts",
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
        "survivor_certificate_is_branch50": gate(
            survivor["candidate_label"]
            == "radius6_broad_adjacency_filtered_10_branch_50"
            and survivor["status"] == "higher_order_mass_map_pending_for_frozen_candidate"
            and survivor["operator_certificate"]["operator"] == "5bar_02*5_34"
            and survivor["operator_certificate"]["monomial"] == ["e3-e2", "e4-e0"]
            and survivor["pending_gate"]["gate"]
            == "higher_order_effective_mass_map_rank",
            "survivor certificate",
            "branch-50 higher-degree survivor and pending mass-map gate are included",
        ),
        "nearest_no_go_boundaries_present": gate(
            len(survivor["nearest_no_go_boundaries"]) >= 4
            and {
                "cubic_only_gate",
                "doublet_support",
                "proton_unprotected",
                "cup_5_unrealizable",
            }.issubset(
                {item["boundary_id"] for item in survivor["nearest_no_go_boundaries"]}
            ),
            "survivor nearest boundaries",
            "survivor carries nearest no-go boundary examples",
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
            "survivor_count": 1,
            "requested_geometries_covered": ["5259/7914", "7484", "2544"],
        },
        "syndromes": syndromes,
        "survivor_certificates": [survivor],
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
                "pending next gate, and nearest no-go boundaries."
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
    survivor = report["survivor_certificates"][0]
    lines.extend(
        [
            "## Survivor Certificate",
            "",
            f"- survivor_id: `{survivor['survivor_id']}`",
            f"- candidate: `{survivor['candidate_label']}`",
            f"- status: `{survivor['status']}`",
            f"- operator: `{survivor['operator_certificate']['operator']}`",
            f"- monomial: `{survivor['operator_certificate']['monomial']}`",
            f"- pending_gate: `{survivor['pending_gate']}`",
            "",
            "Nearest no-go boundaries:",
        ]
    )
    for boundary in survivor["nearest_no_go_boundaries"]:
        lines.append(f"- `{boundary['boundary_id']}`: {boundary['tiny_mutation']}")
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
