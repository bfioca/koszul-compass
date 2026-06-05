#!/usr/bin/env python3
"""Selection-preserving representative-feasible branch-character scout."""

from __future__ import annotations

import argparse
import copy
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from string_theory.cicy import (  # noqa: E402
    bundle_c1,
    bundle_c2,
    bundle_index,
    triple_intersections,
    wedge2_index,
)
from string_theory.slope import find_slope_zero, intersection_tensor  # noqa: E402
from build_cicy5259_quotient_wilson_line_report import sector_record  # noqa: E402
from build_cicy5259_lead_phenomenology_dossier import charged_matter_inventory  # noqa: E402
from build_phenomenology_filter_report import (  # noqa: E402
    certified_h1_singlets,
    classify_from_tables,
    enumerate_singlet_monomials,
    find_mass_operator_table,
    find_proton_decay_table,
    is_desired_q1_signature,
)
from build_phenomenology_guided_q1_radius2_enhanced_backlog import (  # noqa: E402
    SECTOR_LABELS,
    SECTOR_TARGET_KEYS,
    apply_monoid_obstruction_override,
    prediction_from_characters,
)
from build_phenomenology_guided_q1_radius9_character_refined_dt_report import (  # noqa: E402
    full_candidate_record,
    proton_allowed_count,
    refined_classification,
    refined_mass_table,
    source_records,
)
from build_phenomenology_guided_q1_radius9_escape_grammar_scout import (  # noqa: E402
    mine_feasible_patterns,
    rep_key,
)
from phenomenology_guided_q1_representative_grammar_gate import (  # noqa: E402
    RepresentativeGrammarGate,
    apply_representative_grammar_boundary,
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def matrix_key(matrix: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in matrix)


def compact_slope(slope: Any) -> dict[str, Any]:
    data = slope.as_dict()
    return {
        "feasible": data["feasible"],
        "max_normalized_slope": data["max_normalized_slope"],
        "max_abs_slope": data["max_abs_slope"],
        "iterations": data["iterations"],
        "restarts": data["restarts"],
        "seed": data["seed"],
        "kahler_point": data["kahler_point"],
    }


def certify_matrix_gates(
    *,
    matrix: list[list[int]],
    intersections: dict[tuple[int, int, int], int],
    c2_tx: list[int],
    tensor: Any,
    seed: int,
) -> dict[str, Any]:
    c1 = bundle_c1(matrix)
    index_v = bundle_index(matrix, intersections, c2_tx)
    index_wedge2_v = wedge2_index(matrix, intersections, c2_tx)
    c2_v = bundle_c2(matrix, intersections)
    anomaly = [tx - v for tx, v in zip(c2_tx, c2_v)]
    slope = find_slope_zero(
        matrix,
        tensor,
        tolerance=1e-7,
        restarts=4,
        max_iterations=2500,
        seed=seed,
    )
    slope_data = compact_slope(slope)
    passes = (
        c1 == [0] * len(matrix)
        and index_v == -6
        and index_wedge2_v == -6
        and all(value >= 0 for value in anomaly)
        and slope_data["feasible"]
        and slope_data["max_normalized_slope"] <= 1e-7
    )
    return {
        "passes": passes,
        "c1": c1,
        "index_v": index_v,
        "index_wedge2_v": index_wedge2_v,
        "c2_v": c2_v,
        "anomaly": anomaly,
        "slope_search": slope_data,
        "note": (
            "matrix-level gates are recomputed for the fixed branch-scout matrix; "
            "branch replacements do not alter charges or topology"
        ),
    }


def parse_role(role: str) -> dict[str, Any]:
    label, detail = role.split(":", 1)
    suffix = label.split("_", 1)[1]
    pair = [int(suffix[0]), int(suffix[1])]
    if label.startswith("5bar_"):
        return {
            "sector": "wedge2_V",
            "pair": pair,
            "cohomology_key": "H1",
            "detail": detail,
        }
    if detail == "physical_H2_wedge2_V":
        return {
            "sector": "wedge2_V",
            "pair": pair,
            "cohomology_key": "H2",
            "detail": detail,
        }
    if detail == "cup_H1_wedge2_V_dual":
        return {
            "sector": "wedge2_V_dual",
            "pair": pair,
            "cohomology_key": "H1",
            "detail": detail,
        }
    raise ValueError(f"unsupported branch replacement role: {role}")


def refresh_sector_records(characters: dict[str, Any]) -> dict[str, Any]:
    refreshed = {}
    for sector_key, target_keys in SECTOR_TARGET_KEYS.items():
        sector = characters[sector_key]
        refreshed[sector_key] = sector_record(
            label=SECTOR_LABELS[sector_key],
            line_certificates=sector["line_certificates"],
            cohomology_degree_keys=target_keys,
        )
    return refreshed


def replace_role_actual(
    *,
    characters: dict[str, Any],
    role: str,
    replacement: dict[str, Any],
) -> dict[str, Any]:
    parsed = parse_role(role)
    sector = characters[parsed["sector"]]
    for cert in sector["line_certificates"]:
        if cert.get("summand_pair") != parsed["pair"]:
            continue
        actual = copy.deepcopy(cert.get("actual") or {})
        actual[parsed["cohomology_key"]] = copy.deepcopy(replacement)
        cert["actual"] = actual
        cert["actual_character_computed"] = True
        cert["method"] = "selection_preserving_representative_feasible_branch_replacement"
        return {
            "role": role,
            "sector": parsed["sector"],
            "summand_pair": parsed["pair"],
            "cohomology_key": parsed["cohomology_key"],
            "representative_feasible": replacement,
        }
    raise KeyError(f"could not find certificate for role {role}")


def rebuild_filtered_record_from_characters(
    *,
    original: dict[str, Any],
    characters: dict[str, Any],
    source: dict[str, Any],
    variant_label: str,
    variant: dict[str, Any],
) -> dict[str, Any]:
    refreshed = refresh_sector_records(characters)
    prediction = prediction_from_characters(refreshed)
    desired = is_desired_q1_signature(prediction)
    target_for_inventory = {"characters": refreshed}
    inventory = charged_matter_inventory(target_for_inventory)
    singlets = original["singlet_moduli_inventory"]
    monomials = enumerate_singlet_monomials(
        certified_h1_singlets(singlets["all_nonzero_ext1_line_sectors"]),
        max_degree=2,
    )
    mass_table = find_mass_operator_table(
        inventory=inventory,
        singlet_monomials=monomials,
    )
    proton_table = find_proton_decay_table(inventory)
    classification = classify_from_tables(
        desired_signature=desired,
        character_certified=True,
        mass_table=mass_table,
        proton_table=proton_table,
    )
    filtered = {
        "label": variant_label,
        "source": {
            "kind": "selection_preserving_branch_character_scout",
            **source,
        },
        "cicy_route": original.get("cicy_route", "5259/7914"),
        "matrix": original["matrix"],
        "spectrum_certificate": {
            "cohomology": original["spectrum_certificate"]["cohomology"],
            "vectorlike_prediction": prediction,
            "desired_q1_three_family_signature": desired,
        },
        "character_certificate": {
            "character_certified": True,
            "characters": refreshed,
        },
        "charged_matter_inventory": inventory,
        "singlet_moduli_inventory": singlets,
        "mass_operator_table": mass_table,
        "proton_decay_operator_table": proton_table,
        "classification": classification,
        "branch_replacement_variant": variant,
        "matrix_invariant_source": {
            "candidate_label": original["label"],
            "source": source,
            "note": "matrix unchanged from verified generation-pruned refined survivor",
        },
    }
    apply_monoid_obstruction_override(filtered)
    return filtered


def full_candidate_for_gate(
    *,
    source: dict[str, Any],
    weight: int,
    record: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    mass_table = refined_mass_table(record)
    classification = refined_classification(record, mass_table)
    return (
        full_candidate_record(
            source=source,
            weight=weight,
            record=record,
            mass_table=mass_table,
            classification=classification,
        ),
        mass_table,
        classification,
    )


def mine_seed_records_with_audits(
    *, windows: int, grammar_gate: RepresentativeGrammarGate
) -> list[dict[str, Any]]:
    seeds = []
    for source, weight, original in source_records(windows):
        candidate, mass_table, selection = full_candidate_for_gate(
            source=source,
            weight=weight,
            record=original,
        )
        if selection["category"] != "viable":
            continue
        audit = grammar_gate.audit_candidate(candidate=candidate, mass_table=mass_table)
        if audit["status"] != "representative_obstructed":
            continue
        obstructed_targets = []
        for target in audit["target_audits"]:
            if target["status"] != "representative_obstructed":
                continue
            obstructed_legs = [
                leg
                for leg in target["matter_and_cup_leg_audits"]
                if leg["status"] == "representative_obstructed"
                and leg.get("computed_actual") is not None
                and leg.get("branch_actual") != leg.get("computed_actual")
            ]
            obstructed_targets.append(
                {
                    "operator": target["operator"],
                    "status": target["status"],
                    "matter_and_cup_leg_audits": target["matter_and_cup_leg_audits"],
                    "obstructed_legs": obstructed_legs,
                    "obstruction_summary": target["obstruction_summary"],
                }
            )
        seeds.append(
            {
                "candidate_label": original["label"],
                "source": source,
                "weight": weight,
                "record": copy.deepcopy(original),
                "selection_rule_stage": selection,
                "representative_audit": audit,
                "obstructed_targets": obstructed_targets,
                "matrix": original["matrix"],
            }
        )
    return seeds


def seed_records_for_pattern_mining(seeds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for seed in seeds:
        targets = []
        for target in seed["obstructed_targets"]:
            summary = target["obstruction_summary"]
            if not summary:
                continue
            targets.append(
                {
                    "candidate_label": seed["candidate_label"],
                    "source": seed["source"],
                    "weight": seed["weight"],
                    "operator": target["operator"],
                    "obstructing_role": summary["first_obstructing_role"],
                    "branch_requested": summary["branch_actual"],
                    "representative_feasible": summary["computed_actual"],
                    "required_image_ranks_for_branch": summary.get(
                        "required_image_ranks_for_branch"
                    ),
                    "reason": summary["reason"],
                }
            )
        rows.append(
            {
                "candidate_label": seed["candidate_label"],
                "source": seed["source"],
                "weight": seed["weight"],
                "matrix": seed["matrix"],
                "selection_rule_stage": seed["selection_rule_stage"],
                "representative_grammar_stage": {
                    "status": seed["representative_audit"]["status"]
                },
                "obstructed_targets": targets,
            }
        )
    return rows


def replacement_variants_for_seed(seed: dict[str, Any]) -> list[dict[str, Any]]:
    variants = []
    seen = set()
    for target in seed["obstructed_targets"]:
        legs = target["obstructed_legs"]
        if not legs:
            continue
        first = legs[0]
        candidate_variants = [
            {
                "mode": "first_obstructed_leg_feasible",
                "operator": target["operator"],
                "replacements": [
                    {
                        "role": first["role"],
                        "branch_requested": first["branch_actual"],
                        "representative_feasible": first["computed_actual"],
                        "reason": first["reason"],
                    }
                ],
            },
            {
                "mode": "all_obstructed_legs_feasible",
                "operator": target["operator"],
                "replacements": [
                    {
                        "role": leg["role"],
                        "branch_requested": leg["branch_actual"],
                        "representative_feasible": leg["computed_actual"],
                        "reason": leg["reason"],
                    }
                    for leg in legs
                ],
            },
        ]
        for variant in candidate_variants:
            key = json.dumps(variant, sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            variants.append(variant)
    return variants


def evaluate_variant(
    *,
    seed: dict[str, Any],
    variant: dict[str, Any],
    variant_index: int,
    grammar_gate: RepresentativeGrammarGate,
    matrix_cert_cache: dict[tuple[tuple[int, ...], ...], dict[str, Any]],
    intersections: dict[tuple[int, int, int], int],
    c2_tx: list[int],
    tensor: Any,
) -> dict[str, Any]:
    characters = copy.deepcopy(seed["record"]["character_certificate"]["characters"])
    applied = []
    for replacement in variant["replacements"]:
        applied.append(
            replace_role_actual(
                characters=characters,
                role=replacement["role"],
                replacement=replacement["representative_feasible"],
            )
        )
    enriched_variant = {
        **variant,
        "applied_replacements": applied,
        "seed_label": seed["candidate_label"],
        "seed_source": seed["source"],
    }
    synthetic = rebuild_filtered_record_from_characters(
        original=seed["record"],
        characters=characters,
        source=seed["source"],
        variant_label=(
            f"{seed['candidate_label']}_selection_preserving_branch_{variant_index}"
        ),
        variant=enriched_variant,
    )
    key = matrix_key(synthetic["matrix"])
    if key not in matrix_cert_cache:
        matrix_cert_cache[key] = certify_matrix_gates(
            matrix=synthetic["matrix"],
            intersections=intersections,
            c2_tx=c2_tx,
            tensor=tensor,
            seed=870000 + len(matrix_cert_cache),
        )
    matrix_certification = matrix_cert_cache[key]
    desired = synthetic["spectrum_certificate"]["desired_q1_three_family_signature"]
    synthetic_mass_table = refined_mass_table(synthetic)
    refined = refined_classification(synthetic, synthetic_mass_table)
    synthetic["character_refined_classification"] = refined
    synthetic["character_refined_mass_support_classes"] = dict(
        sorted(
            Counter(
                item["character_refined_support_class"] for item in synthetic_mass_table
            ).items()
        )
    )
    if desired and matrix_certification["passes"] and refined["category"] == "viable":
        boundary = apply_representative_grammar_boundary(
            filtered_record=synthetic,
            grammar_gate=grammar_gate,
            source={
                "kind": "selection_preserving_branch_character_scout",
                "seed_label": seed["candidate_label"],
                "seed_source": seed["source"],
                "mode": variant["mode"],
                "operator": variant["operator"],
            },
            weight=seed["weight"],
        )
        representative = boundary["representative_grammar_stage"]
    else:
        status = (
            "not_evaluated_q1_not_preserved"
            if not desired
            else "not_evaluated_matrix_certification_failed"
            if not matrix_certification["passes"]
            else "not_evaluated_selection_rule_not_viable"
        )
        representative = {
            "status": status,
            "promoted_to_lead_candidate": False,
            "cup_product_planning_allowed": False,
            "target_status_counts": {},
        }
        synthetic["representative_grammar_gate"] = {
            "selection_rule_stage": refined,
            "representative_grammar_stage": representative,
            "triplet_mass_targets": [],
        }

    if not desired:
        failure = "q1_signature_lost"
    elif not matrix_certification["passes"]:
        failure = "matrix_certification_failed"
    elif refined["category"] != "viable":
        failure = f"selection_preservation_failed:{refined['status']}"
    elif representative["status"] != "representative_compatible":
        failure = f"representative_gate_failed:{representative['status']}"
    else:
        failure = "representative_compatible"
    return {
        "variant_label": synthetic["label"],
        "seed_label": seed["candidate_label"],
        "seed_source": seed["source"],
        "seed_weight": seed["weight"],
        "operator": variant["operator"],
        "mode": variant["mode"],
        "replacement_count": len(variant["replacements"]),
        "replacements": variant["replacements"],
        "q1_preserved": desired,
        "refined_selection_status": refined["status"],
        "refined_selection_category": refined["category"],
        "proton_allowed_count": proton_allowed_count(synthetic),
        "matrix_certification": matrix_certification,
        "representative_status": representative["status"],
        "promoted_to_lead_candidate": representative["promoted_to_lead_candidate"],
        "cup_product_planning_allowed": representative["cup_product_planning_allowed"],
        "failure_class": failure,
        "vectorlike_prediction": synthetic["spectrum_certificate"][
            "vectorlike_prediction"
        ],
        "charged_matter_counts": {
            key: len(value)
            for key, value in synthetic["charged_matter_inventory"].items()
        },
        "mass_support_classes": synthetic["character_refined_mass_support_classes"],
        "representative_targets": synthetic["representative_grammar_gate"][
            "triplet_mass_targets"
        ],
    }


def build_report(
    *,
    windows: int,
    replay_json: Path,
    replay_verification_json: Path,
    escape_json: Path,
    escape_verification_json: Path,
) -> dict[str, Any]:
    replay = load_json(replay_json)
    replay_verification = load_json(replay_verification_json)
    escape = load_json(escape_json)
    escape_verification = load_json(escape_verification_json)
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    c2_tx = split["full_picard_presentation_7914"]["c2_tx"]
    intersections = triple_intersections(conf)
    tensor = intersection_tensor(intersections, 7)
    grammar_gate = RepresentativeGrammarGate()
    matrix_cert_cache: dict[tuple[tuple[int, ...], ...], dict[str, Any]] = {}
    seeds = mine_seed_records_with_audits(windows=windows, grammar_gate=grammar_gate)
    mined = mine_feasible_patterns(
        seeds=seed_records_for_pattern_mining(seeds),
        escape_report=escape,
    )
    variants = []
    for seed in seeds:
        for variant_index, variant in enumerate(replacement_variants_for_seed(seed)):
            variants.append(
                evaluate_variant(
                    seed=seed,
                    variant=variant,
                    variant_index=variant_index,
                    grammar_gate=grammar_gate,
                    matrix_cert_cache=matrix_cert_cache,
                    intersections=intersections,
                    c2_tx=c2_tx,
                    tensor=tensor,
                )
            )
    by_pattern: dict[str, Counter[str]] = defaultdict(Counter)
    for item in variants:
        by_pattern[f"{item['operator']}|{item['mode']}"][item["failure_class"]] += (
            item["seed_weight"]
        )
    compatible = [
        item
        for item in variants
        if item["q1_preserved"]
        and item["matrix_certification"]["passes"]
        and item["refined_selection_category"] == "viable"
        and item["representative_status"] == "representative_compatible"
        and item["promoted_to_lead_candidate"]
    ]
    cup_product = [
        item
        for item in variants
        if item["q1_preserved"]
        and item["matrix_certification"]["passes"]
        and item["refined_selection_category"] == "viable"
        and item["cup_product_planning_allowed"]
    ]
    failure_rows = Counter(item["failure_class"] for item in variants)
    failure_weight = Counter()
    representative_status_rows = Counter(
        item["representative_status"] for item in variants
    )
    for item in variants:
        failure_weight[item["failure_class"]] += item["seed_weight"]
    compatible_patterns = [
        {
            "pattern": pattern,
            "failure_weight": dict(sorted(counts.items())),
            "selection_preserving_weight": sum(
                weight
                for key, weight in counts.items()
                if key.startswith("representative_gate_failed")
                or key == "representative_compatible"
            ),
            "compatible_weight": counts["representative_compatible"],
        }
        for pattern, counts in sorted(by_pattern.items())
    ]
    summary = {
        "windows_closed": windows,
        "seed_rows": len(seeds),
        "seed_weight": sum(seed["weight"] for seed in seeds),
        "observed_triplet_only_operator_shape_count": len(
            mined["observed_triplet_only_operator_shapes"]
        ),
        "feasible_pattern_count": len(
            [
                item
                for item in mined["feasible_patterns"]
                if item["status"] == "representative_feasible_replacement"
            ]
        ),
        "branch_replacement_variant_count": len(variants),
        "matrix_certified_variant_count": sum(
            item["matrix_certification"]["passes"] for item in variants
        ),
        "q1_preserving_variant_count": sum(item["q1_preserved"] for item in variants),
        "q1_and_matrix_certified_variant_count": sum(
            item["q1_preserved"] and item["matrix_certification"]["passes"]
            for item in variants
        ),
        "selection_preserving_variant_count": sum(
            item["q1_preserved"]
            and item["matrix_certification"]["passes"]
            and item["refined_selection_category"] == "viable"
            for item in variants
        ),
        "representative_compatible_count": len(compatible),
        "representative_unresolved_count": sum(
            item["representative_status"] == "representative_unresolved"
            for item in variants
        ),
        "cup_product_eligible_count": len(cup_product),
        "failure_class_rows": dict(sorted(failure_rows.items())),
        "failure_class_weight": dict(sorted(failure_weight.items())),
        "representative_status_rows": dict(sorted(representative_status_rows.items())),
    }
    selection_gated_promotions = all(
        item["q1_preserved"]
        and item["matrix_certification"]["passes"]
        and item["refined_selection_category"] == "viable"
        and item["proton_allowed_count"] == 0
        and item["representative_status"] == "representative_compatible"
        for item in compatible
    ) and all(
        item["q1_preserved"]
        and item["matrix_certification"]["passes"]
        and item["refined_selection_category"] == "viable"
        and item["proton_allowed_count"] == 0
        for item in cup_product
    )
    unaudited_variants_are_blocked = all(
        item["representative_status"] == "not_evaluated_q1_not_preserved"
        and not item["promoted_to_lead_candidate"]
        and not item["cup_product_planning_allowed"]
        for item in variants
        if not item["q1_preserved"]
    ) and all(
        item["representative_status"] == "not_evaluated_matrix_certification_failed"
        and not item["promoted_to_lead_candidate"]
        and not item["cup_product_planning_allowed"]
        for item in variants
        if item["q1_preserved"] and not item["matrix_certification"]["passes"]
    ) and all(
        item["representative_status"] == "not_evaluated_selection_rule_not_viable"
        and not item["promoted_to_lead_candidate"]
        and not item["cup_product_planning_allowed"]
        for item in variants
        if item["q1_preserved"]
        and item["matrix_certification"]["passes"]
        and item["refined_selection_category"] != "viable"
    )
    gates = {
        "imports_verified_generation_replay": gate(
            replay["all_gates_pass"]
            and replay_verification["all_gates_pass"]
            and replay["summary"]["representative_grammar_pruned_rows"] == 14,
            f"{replay_json} + {replay_verification_json}",
            "branch scout starts from the verified representative-gated generation replay",
        ),
        "imports_verified_feasible_patterns": gate(
            escape["all_gates_pass"]
            and escape_verification["all_gates_pass"]
            and len(escape["escape_scan"]["triplet_only_operator_rows"]) == 16,
            f"{escape_json} + {escape_verification_json}",
            "branch scout imports the verified observed operator inventory",
        ),
        "mines_requested_seed_and_pattern_sets": gate(
            summary["seed_rows"] == 14
            and summary["seed_weight"] == 1962
            and summary["observed_triplet_only_operator_shape_count"] == 16
            and summary["feasible_pattern_count"] >= 37,
            "seed and feasible-pattern mining",
            "the scout covers the requested 14 pruned survivors and 16 observed operator shapes",
        ),
        "enumerates_branch_character_replacements": gate(
            summary["branch_replacement_variant_count"] >= summary["seed_rows"]
            and all(item["replacement_count"] >= 1 for item in variants),
            "branch replacement variants",
            "the scout enumerates representative-feasible branch-character replacements",
        ),
        "selection_preservation_is_tested": gate(
            summary["q1_preserving_variant_count"] > 0
            and summary["q1_and_matrix_certified_variant_count"]
            == summary["q1_preserving_variant_count"]
            and summary["selection_preserving_variant_count"]
            <= summary["q1_preserving_variant_count"]
            and "q1_signature_lost" in summary["failure_class_rows"],
            "variant selection outcomes",
            "the scout distinguishes q1 loss from matrix-certified selection-preserving variants",
        ),
        "matrix_gates_are_recomputed": gate(
            summary["q1_and_matrix_certified_variant_count"]
            == summary["q1_preserving_variant_count"]
            and all(
                item["matrix_certification"]["index_v"] == -6
                and item["matrix_certification"]["index_wedge2_v"] == -6
                and all(value >= 0 for value in item["matrix_certification"]["anomaly"])
                for item in variants
            )
            and all(
                item["matrix_certification"]["passes"]
                for item in variants
                if item["q1_preserved"]
            ),
            "variant matrix certificates",
            "index, anomaly, and slope gates are recomputed before representative promotion",
        ),
        "representative_audit_is_selection_gated": gate(
            selection_gated_promotions and unaudited_variants_are_blocked,
            "representative/cup-product outcomes",
            "promotion is only allowed after q=1, refined selection, and proton gates",
        ),
        "outcome_is_resolved": gate(
            summary["representative_compatible_count"] == len(compatible)
            and summary["cup_product_eligible_count"] == len(cup_product)
            and (
                summary["representative_compatible_count"] > 0
                or summary["cup_product_eligible_count"] == 0
            ),
            "resolved branch-replacement outcomes",
            "the scout either emits selection-gated survivors or proves zero promotion-ready replacements",
        ),
    }
    active_obstruction = (
        "most representative-feasible branch replacements destroy q=1; the surviving "
        "selection-preserving replacements are representative-compatible scout targets"
        if compatible
        else "representative-feasible replacements either destroy q=1 or fail the refined "
        "DT/singlet/proton selection gates before representative promotion"
    )
    current_result = (
        "selection-preserving branch replacement finds representative-compatible, "
        "cup-product-eligible branch-character scout targets pending full realization checks"
        if compatible
        else "selection-preserving branch replacement finds no representative-compatible "
        "or cup-product-eligible candidate"
    )
    return {
        "title": "Radius-9 Selection-Preserving Representative-Feasible Branch Scout",
        "status": (
            "selection_preserving_branch_scout_found_representative_compatible_candidate"
            if compatible
            else "selection_preserving_branch_scout_no_promotion_ready_candidate"
        ),
        "scope": (
            "replace obstructed branch-character requests by mined representative-feasible "
            "characters while requiring q=1, refined DT/singlet/proton selection, "
            "and representative compatibility before promotion"
        ),
        "source_artifacts": {
            "generation_replay_json": str(replay_json),
            "generation_replay_verification_json": str(replay_verification_json),
            "obstruction_escape_json": str(escape_json),
            "obstruction_escape_verification_json": str(escape_verification_json),
        },
        "summary": summary,
        "feasible_character_mining": mined,
        "branch_replacement_variants": variants,
        "pattern_compatibility": compatible_patterns,
        "representative_compatible_variants": compatible,
        "cup_product_eligible_variants": cup_product,
        "interpretation": {
            "active_obstruction": active_obstruction,
            "current_result": current_result,
            "caveat": (
                "compatible rows are synthetic branch-character replacements over fixed "
                "matrices; they are not yet new full matrix/cup-product certificates"
            ),
        },
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        f"# {report['title']}",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Pattern Compatibility", ""])
    for item in report["pattern_compatibility"]:
        lines.append(
            f"- `{item['pattern']}`: failures `{item['failure_weight']}`, "
            f"selection-preserving weight `{item['selection_preserving_weight']}`, "
            f"compatible weight `{item['compatible_weight']}`"
        )
    lines.extend(["", "## Compatible Branch-Scout Rows", ""])
    if report["representative_compatible_variants"]:
        for item in report["representative_compatible_variants"]:
            replacement_roles = ", ".join(
                replacement["role"] for replacement in item["replacements"]
            )
            prediction = item["vectorlike_prediction"]
            slope = item["matrix_certification"]["slope_search"]
            source = item["seed_source"]
            lines.append(
                f"- `{item['variant_label']}`: seed `{item['seed_label']}`, "
                f"window `{source.get('window')}`, operator `{item['operator']}`, "
                f"replacement `{replacement_roles}`, net families "
                f"`{prediction.get('net_families')}`, vectorlike pairs "
                f"`T={prediction.get('colored_triplet_vectorlike_pairs')}, "
                f"D={prediction.get('electroweak_doublet_vectorlike_pairs')}`, "
                f"max normalized slope `{slope['max_normalized_slope']}`"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Interpretation", ""])
    for key, value in report["interpretation"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Gates", ""])
    for key, item in report["gates"].items():
        lines.append(f"- {key}: `{item['pass']}` - {item['note']}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", type=int, default=45)
    parser.add_argument(
        "--replay-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_generation_replay_rollup.json"
        ),
    )
    parser.add_argument(
        "--replay-verification-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_generation_replay_rollup_verification.json"
        ),
    )
    parser.add_argument(
        "--escape-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_obstruction_escape_report.json"
        ),
    )
    parser.add_argument(
        "--escape-verification-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_obstruction_escape_report_verification.json"
        ),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_selection_preserving_branch_scout.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_selection_preserving_branch_scout.md"
        ),
    )
    args = parser.parse_args()
    report = build_report(
        windows=args.windows,
        replay_json=Path(args.replay_json),
        replay_verification_json=Path(args.replay_verification_json),
        escape_json=Path(args.escape_json),
        escape_verification_json=Path(args.escape_verification_json),
    )
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_markdown(report, md_out)
    print(f"status={report['status']}")
    print(f"summary={json.dumps(report['summary'], sort_keys=True)}")
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
