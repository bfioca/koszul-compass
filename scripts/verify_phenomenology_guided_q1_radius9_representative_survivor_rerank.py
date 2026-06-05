#!/usr/bin/env python3
"""Verify the representative-compatible rerank of corrected q=1 survivors."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

NEGATIVE_CONTROL_LABEL = "radius6_broad_adjacency_filtered_4_branch_18"
NEGATIVE_CONTROL_OPERATOR = "5bar_02*5_24"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def triplet_target_count(refined: dict[str, Any]) -> int:
    return sum(
        1
        for candidate in refined["refined_viable_candidate_records"]
        for item in candidate.get("refined_mass_operator_table", [])
        if item.get("character_refined_support_class") == "triplet_only_character_mass"
    )


def obstruction_role_counts(targets: list[dict[str, Any]]) -> Counter[str]:
    return Counter(
        target["obstruction_summary"]["first_obstructing_role"]
        for target in targets
        if target.get("obstruction_summary")
    )


def verify(
    *,
    report_json: Path,
    report_md: Path,
    refined_json: Path,
    refined_verification_json: Path,
) -> dict[str, Any]:
    report = load_json(report_json)
    refined = load_json(refined_json)
    refined_verification = load_json(refined_verification_json)
    md_text = report_md.read_text(encoding="utf-8")
    summary = report["summary"]
    targets = report["ranked_targets"]
    records = report["candidate_records"]
    negative = report["negative_control"]
    negative_obstruction = negative["obstruction_summary"]
    negative_leg = negative["matter_and_cup_leg_audits"][0]
    obstructed_targets = [
        target for target in targets if target["status"] == "representative_obstructed"
    ]
    unresolved_targets = [
        target for target in targets if target["status"] == "representative_unresolved"
    ]
    compatible_targets = [
        target for target in targets if target["status"] == "representative_compatible"
    ]
    role_counts = obstruction_role_counts(targets)
    weighted_obstructed = sum(target["weight"] for target in obstructed_targets)
    weighted_unresolved = sum(target["weight"] for target in unresolved_targets)
    five12_targets = [target for target in targets if target["operator"] == "5bar_12*5_12"]
    five23_target = next(
        target for target in targets if target["operator"] == "5bar_23*5_23"
    )
    gates = {
        "builder_gates_pass": gate(
            report.get("all_gates_pass")
            and all(item.get("pass") for item in report.get("gates", {}).values()),
            str(report_json),
            "builder-side representative rerank gates passed",
        ),
        "expected_scope_and_status": gate(
            report["status"] == "no_representative_compatible_cup_product_target_found"
            and report["scope"] == "corrected refined q=1 viable survivors from windows 1-45"
            and report["shadow_layer_interpretation"]["cup_product_layer"].startswith(
                "not attempted"
            ),
            str(report_json),
            "report is scoped to the corrected q=1 survivor set and stops before cup products",
        ),
        "source_refined_report_verified": gate(
            refined.get("all_gates_pass")
            and refined_verification.get("all_gates_pass")
            and refined["summary"]["refined_viable_candidate_weight"] == 1962
            and summary["refined_report_all_gates_pass"]
            and summary["refined_verification_all_gates_pass"],
            f"{refined_json} + {refined_verification_json}",
            "rerank starts from the verified corrected character-refined survivor report",
        ),
        "all_rows_and_targets_covered": gate(
            len(records) == len(refined["refined_viable_candidate_records"])
            and summary["survivor_rows_audited"] == len(records) == 14
            and summary["survivor_row_weight"]
            == sum(record.get("weight", 1) for record in refined["refined_viable_candidate_records"])
            == 1962
            and len(targets) == summary["triplet_mass_targets_audited"]
            == triplet_target_count(refined)
            == 14,
            str(report_json),
            "every corrected refined survivor row and triplet-only mass target is audited",
        ),
        "status_totals_match_records": gate(
            summary["target_status_counts"] == {
                "representative_obstructed": 14,
            }
            and summary["weighted_target_status_counts"] == {
                "representative_obstructed": 1962,
            }
            and len(obstructed_targets) == summary["representative_obstructed_target_count"] == 14
            and len(unresolved_targets) == summary["representative_unresolved_target_count"] == 0
            and len(compatible_targets) == summary["representative_compatible_target_count"] == 0
            and weighted_obstructed == 1962
            and weighted_unresolved == 0
            and summary["all_targets_resolved_at_representative_layer"]
            and summary["all_targets_representative_obstructed"],
            str(report_json),
            "target status counts and represented weights match explicit target records",
        ),
        "negative_control_shadow_collision": gate(
            negative["candidate_label"] == NEGATIVE_CONTROL_LABEL
            and negative["operator"] == NEGATIVE_CONTROL_OPERATOR
            and negative["status"] == "representative_obstructed"
            and negative_obstruction["first_obstructing_role"]
            == "5bar_02:physical_H1_wedge2_V"
            and negative_obstruction["branch_actual"]["multiplicities"]
            == {"+": 2, "-": 0}
            and negative_obstruction["computed_actual"]["multiplicities"]
            == {"+": 1, "-": 1}
            and negative_obstruction["required_image_ranks_for_branch"]
            == {"+": 1, "-": 3}
            and negative_leg["source_representation"]["multiplicities"] == {"+": 2, "-": 2}
            and negative_leg["target_representation"]["multiplicities"] == {"+": 3, "-": 3}
            and not negative_leg["required_image_ranks_feasible"],
            str(report_json),
            "negative control proves branch character request is not representative-realizable",
        ),
        "obstruction_classes_are_structured": gate(
            role_counts == {
                "5_12:cup_H1_wedge2_V_dual": 2,
                "5bar_02:physical_H1_wedge2_V": 9,
                "5bar_04:physical_H1_wedge2_V": 2,
                "5bar_23:physical_H1_wedge2_V": 1,
            }
            and all(
                target["obstruction_summary"] is not None
                for target in targets
            ),
            str(report_json),
            "hard obstructions are concentrated in four explicit representative mismatch classes",
        ),
        "five12_frontier_resolved_by_e2_cup_dual_obstruction": gate(
            len(five12_targets) == 2
            and all(
                target["obstruction_summary"]["first_obstructing_role"]
                == "5_12:cup_H1_wedge2_V_dual"
                and target["obstruction_summary"]["branch_actual"]["multiplicities"]
                == {"+": 0, "-": 2}
                and target["obstruction_summary"]["computed_actual"]["multiplicities"]
                == {"+": 1, "-": 1}
                and target["obstruction_summary"]["reason"]
                == "dimension-certified equivariant E2 character disagrees with branch actual"
                for target in five12_targets
            )
            and any(
                leg["role"] == "5bar_12:physical_H1_wedge2_V"
                and leg["representative_method"] == "dimension_certified_equivariant_e2"
                and leg["status"] == "representative_compatible"
                for target in five12_targets
                for leg in target["matter_and_cup_leg_audits"]
            )
            and all(
                any(
                    leg["role"] == "5_12:cup_H1_wedge2_V_dual"
                    and leg["e2_resolution"]["status"] == "e2_final_by_dimension"
                    and leg["computed_actual"]["multiplicities"] == {"+": 1, "-": 1}
                    for leg in target["matter_and_cup_leg_audits"]
                )
                for target in five12_targets
            ),
            str(report_json),
            "former fivebar_12 targets are resolved by a dimension-certified E2 mismatch on the cup dual leg",
        ),
        "five23_frontier_resolved_by_fixed_first_page_kernel": gate(
            five23_target["status"] == "representative_obstructed"
            and five23_target["obstruction_summary"]["first_obstructing_role"]
            == "5bar_23:physical_H1_wedge2_V"
            and five23_target["obstruction_summary"]["branch_actual"]["multiplicities"]
            == {"+": 2, "-": 0}
            and five23_target["obstruction_summary"]["computed_actual"]["multiplicities"]
            == {"+": 2, "-": 1}
            and any(
                leg["role"] == "5bar_23:physical_H1_wedge2_V"
                and leg["representative_method"] == "first_page_kernel"
                and leg["map_error"] is None
                and leg["map_split"]["rank_split"]["rank_plus"] == 2
                and leg["map_split"]["rank_split"]["rank_minus"] == 2
                and leg["map_split"]["rank_split"]["cross_eigen_nonzero_entries"] == 0
                for leg in five23_target["matter_and_cup_leg_audits"]
            ),
            str(report_json),
            "former fivebar_23 map-construction failure is resolved to an explicit kernel mismatch",
        ),
        "no_cup_rank_overclaimed": gate(
            summary["first_representative_compatible_target"] is None
            and summary["all_targets_obstructed_or_unresolved"]
            and summary["all_targets_representative_obstructed"]
            and all(not target["eligible_for_exact_cup_product_rank"] for target in targets)
            and all(
                target["cup_product_rank_claim"] == "not_attempted_pre_cup_filter"
                for target in targets
            ),
            str(report_json),
            "no target is promoted to exact cup-product rank verification",
        ),
        "markdown_reports_rerank_boundary": gate(
            "Status: `no_representative_compatible_cup_product_target_found`" in md_text
            and "representative-compatible targets: `0`" in md_text
            and "all targets representative-obstructed: `True`" in md_text
            and "computed actual: `{'dimension': 2, 'nonidentity_trace': 0, 'multiplicities': {'+': 1, '-': 1}, 'regular_multiplicity': 1}`"
            in md_text
            and "No corrected refined survivor row is ready for exact cup-product rank verification"
            in md_text,
            str(report_md),
            "markdown exposes the negative-control evidence and the pre-cup boundary",
        ),
    }
    return {
        "scope": "verification for representative-compatible q=1 survivor rerank",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_representative_survivor_rerank.json"
        ),
    )
    parser.add_argument(
        "--report-md",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_representative_survivor_rerank.md"
        ),
    )
    parser.add_argument(
        "--refined-json",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_character_refined_dt_windows1_45.json"
        ),
    )
    parser.add_argument(
        "--refined-verification-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_character_refined_dt_windows1_45_verification.json"
        ),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_survivor_rerank_verification.json"
        ),
    )
    args = parser.parse_args()
    result = verify(
        report_json=Path(args.report_json),
        report_md=Path(args.report_md),
        refined_json=Path(args.refined_json),
        refined_verification_json=Path(args.refined_verification_json),
    )
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
