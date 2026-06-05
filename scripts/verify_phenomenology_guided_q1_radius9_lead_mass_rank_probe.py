#!/usr/bin/env python3
"""Verify the minimal cup-product mass-rank probe for the frozen q=1 lead."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

EXPECTED_LABEL = "radius6_broad_adjacency_filtered_4_branch_18"
EXPECTED_OPERATOR = "5bar_02*5_24*S_40"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def verify(report_json: Path, report_md: Path) -> dict[str, Any]:
    report = load_json(report_json)
    md_text = report_md.read_text(encoding="utf-8")
    spaces = report["exact_spaces"]
    cup_spaces = spaces["serre_dual_cup_product_spaces"]
    physical_spaces = spaces["component_selection_rule_spaces"]
    blocks = report["component_mass_blocks"]
    capability = report["cup_product_construction_attempt"]["available_machinery"]
    verdict = report["verdict"]
    dangerous = report["dangerous_operator_regression"]
    gates = {
        "builder_gates_pass": gate(
            report.get("all_gates_pass")
            and all(item.get("pass") for item in report.get("gates", {}).values()),
            str(report_json),
            "builder-side mass-rank probe gates passed",
        ),
        "expected_candidate_and_operator": gate(
            report["candidate_label"] == EXPECTED_LABEL
            and spaces["operator"] == EXPECTED_OPERATOR,
            str(report_json),
            "probe freezes the corrected lead and unique corrected mass operator",
        ),
        "physical_five_and_cup_five_are_separated": gate(
            physical_spaces["five_24_physical"]["sector"] == "H2(wedge2 V)"
            and cup_spaces["five_24_cup_leg"]["sector"] == "H1(L_24^*)"
            and cup_spaces["five_24_cup_leg"]["line_bundle"]
            == [0, -2, 0, 0, 1, 0, 0]
            and physical_spaces["five_24_physical"]["line_bundle"]
            == [0, 2, 0, 0, -1, 0, 0],
            str(report_json),
            "physical Wilson-line character source and Serre-dual cup-product leg are distinct",
        ),
        "line_sum_and_target_are_correct": gate(
            cup_spaces["line_bundle_sum_is_trivial"]
            and cup_spaces["line_bundle_sum"] == [0, 0, 0, 0, 0, 0, 0]
            and cup_spaces["target"]["cohomology"] == [1, 0, 0, 1],
            str(report_json),
            "cup product lands in H3(O_X)",
        ),
        "cohomology_recomputations_match": gate(
            cup_spaces["fivebar_02_cup_leg"]["cohomology"] == [0, 2, 0, 0]
            and cup_spaces["five_24_cup_leg"]["cohomology"] == [0, 2, 0, 0]
            and cup_spaces["singlet_S_40_cup_leg"]["cohomology"] == [0, 4, 0, 0],
            str(report_json),
            "source cohomology groups are the expected H1 spaces",
        ),
        "component_blocks_match_selection_rule": gate(
            blocks["triplet_block"]["matrix_shape_after_singlet_vevs"] == [2, 1]
            and blocks["doublet_block"]["matrix_shape_after_singlet_vevs"] == [0, 1]
            and blocks["doublet_block"]["rank"] == 0
            and blocks["triplet_block"]["rank"] is None,
            str(report_json),
            "triplet block is 2-by-1 and doublet block is forced zero",
        ),
        "rank_boundary_not_overclaimed": gate(
            verdict["status"] == "unresolved_due_missing_cup_product_machinery"
            and verdict["mass_rank_verified"] is False
            and verdict["doublet_block_verdict"] == "rank_0_verified_by_component_dimension"
            and verdict["triplet_block_verdict"] == "rank_1_not_computed",
            str(report_json),
            "verdict keeps the candidate selection-rule viable but mass-rank unresolved",
        ),
        "cup_api_absent": gate(
            not capability["has_exposed_trilinear_cup_product_api"]
            and capability["single_map_is_equation_multiplication_hook"]
            and not report["cup_product_construction_attempt"]["cup_product_map_constructed"],
            str(report_json),
            "local pyCICY audit exposes Koszul maps but not a trilinear cup-product API",
        ),
        "dangerous_operator_regression": gate(
            dangerous["count"] == 10
            and dangerous["all_forbidden"]
            and all(
                not item["neutral_under_S_U1_5"] and item["forbidden_by_current_selection_rules"]
                for item in dangerous["operators"]
            ),
            str(report_json),
            "dangerous 10*5bar*5bar operators remain forbidden",
        ),
        "markdown_reports_boundary": gate(
            "Status: `unresolved_due_missing_cup_product_machinery`" in md_text
            and "`H1(wedge2 V*)`" in md_text
            and "triplet block: `rank_1_not_computed`" in md_text
            and "doublet block: `rank_0_verified_by_component_dimension`" in md_text,
            str(report_md),
            "markdown exposes the cup-leg distinction and unresolved rank verdict",
        ),
    }
    return {
        "scope": "verification for lead q=1 minimal cup-product mass-rank probe",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius9_lead_mass_rank_probe.json"),
    )
    parser.add_argument(
        "--report-md",
        default=str(REPORTS / "phenomenology_guided_q1_radius9_lead_mass_rank_probe.md"),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_lead_mass_rank_probe_verification.json"
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
