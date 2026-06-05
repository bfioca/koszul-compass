#!/usr/bin/env python3
"""Verify the representative-level cup-product audit for the q=1 lead."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

EXPECTED_LABEL = "radius6_broad_adjacency_filtered_4_branch_18"
EXPECTED_OPERATOR = "5bar_02*5_24*S_40"
EXPECTED_STATUS = "obstructed_by_representative_character_mismatch_before_cup_product"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def verify(report_json: Path, report_md: Path) -> dict[str, Any]:
    report = load_json(report_json)
    md_text = report_md.read_text(encoding="utf-8")
    l02 = report["l02_representative_cokernel_audit"]
    product = report["product_shape_audit"]
    verdict = report["verdict"]
    line_audits = report["line_audits"]
    source = l02["source_entry"]["basis_sign_representation"]
    target = l02["target_entry"]["basis_sign_representation"]
    branch = l02["branch_completion_character"]
    computed = l02["computed_cokernel_character_from_representative_map"]
    required = l02["required_image_ranks_for_branch_character"]
    gates = {
        "builder_gates_pass": gate(
            report.get("all_gates_pass")
            and all(item.get("pass") for item in report.get("gates", {}).values()),
            str(report_json),
            "builder-side representative audit gates passed",
        ),
        "expected_scope_and_status": gate(
            report["candidate_label"] == EXPECTED_LABEL
            and report["operator"] == EXPECTED_OPERATOR
            and report["status"] == EXPECTED_STATUS,
            str(report_json),
            "audit targets the corrected lead and reports the representative mismatch status",
        ),
        "single_source_legs_are_available": gate(
            report["single_source_leg_checks"]["L24_dual_single_source_matches_mass_probe"]
            and report["single_source_leg_checks"]["L40_single_source_matches_mass_probe"]
            and len(line_audits["L24_dual"]["entries"]) == 1
            and len(line_audits["L40_singlet"]["entries"]) == 1,
            str(report_json),
            "L24 dual and L40 representatives are reconstructed as single E1 entries",
        ),
        "l02_is_two_entry_cokernel": gate(
            l02["no_other_e1_entries_for_l02"]
            and source["multiplicities"] == {"+": 2, "-": 2}
            and target["multiplicities"] == {"+": 3, "-": 3}
            and l02["source_totals_match_branch_sources"],
            str(report_json),
            "L02 has exactly the E1 source/target reps used by the branch source totals",
        ),
        "computed_l02_cokernel_is_regular": gate(
            l02["equivariant_first_page_rank_split"]["rank_plus"] == 2
            and l02["equivariant_first_page_rank_split"]["rank_minus"] == 2
            and l02["equivariant_first_page_rank_split"]["cross_eigen_nonzero_entries"] == 0
            and computed["multiplicities"] == {"+": 1, "-": 1},
            str(report_json),
            "explicit equivariant first-page map gives a +1/-1 cokernel",
        ),
        "branch_character_is_infeasible": gate(
            branch["multiplicities"] == {"+": 2, "-": 0}
            and required == {"+": 1, "-": 3}
            and required["-"] > source["multiplicities"]["-"]
            and not l02["branch_character_feasible_from_e1_bounds"]
            and not l02["branch_character_matches_computed_cokernel"],
            str(report_json),
            "branch-completion character would require impossible minus-image rank",
        ),
        "product_needs_chain_map": gate(
            product["naive_tensor_product_position"]["origin_union"] == [1, 2]
            and product["naive_tensor_product_position"]["j"] == 5
            and product["top_h3_ox_representative_position"]["origins"]
            == [[0, 1, 2, 3, 4, 5, 6]]
            and product["top_h3_ox_representative_position"]["j"] == 10
            and not product["direct_e1_product_lands_on_top_representative"],
            str(report_json),
            "naive E1 product does not directly land on the top H3(O_X) representative",
        ),
        "heuristics_kept_separate": gate(
            not report["heuristic_nonvanishing_tests"]["performed"],
            str(report_json),
            "unsafe heuristic nonvanishing tests are not presented as certification",
        ),
        "dangerous_regression_preserved": gate(
            report["dangerous_operator_regression"]["count"] == 10
            and report["dangerous_operator_regression"]["all_forbidden"],
            str(report_json),
            "dangerous operator regression is carried through from the mass-rank probe",
        ),
        "markdown_exposes_obstruction": gate(
            "Status: `obstructed_by_representative_character_mismatch_before_cup_product`"
            in md_text
            and "computed representative cokernel" in md_text
            and "branch feasible from E1 bounds: `False`" in md_text
            and "mass-rank verified: `False`" in md_text,
            str(report_md),
            "markdown exposes the representative mismatch and avoids a mass-rank claim",
        ),
    }
    return {
        "scope": "verification for lead q=1 representative cup-product audit",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_lead_cup_product_representative_audit.json"
        ),
    )
    parser.add_argument(
        "--report-md",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_lead_cup_product_representative_audit.md"
        ),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_lead_cup_product_representative_audit_verification.json"
        ),
    )
    args = parser.parse_args()
    result = verify(report_json=Path(args.report_json), report_md=Path(args.report_md))
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
