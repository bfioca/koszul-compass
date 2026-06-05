#!/usr/bin/env python3
"""Verify the radius-9 representative-feasible escape grammar scout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def verify(report_json: Path, report_md: Path) -> dict[str, Any]:
    report = load_json(report_json)
    md_text = report_md.read_text(encoding="utf-8")
    summary = report["summary"]
    scout = report["local_move_escape_scout"]
    mining = report["feasible_character_mining"]
    bounds = scout["bounds"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"]
            and all(item["pass"] for item in report["gates"].values()),
            str(report_json),
            "builder-side escape grammar scout gates passed",
        ),
        "expected_status": gate(
            report["status"]
            == "escape_grammar_bounded_local_move_no_promotion_ready_candidate"
            and report["scope"].startswith("mine representative-feasible"),
            str(report_json),
            "report is the representative-feasible escape grammar scout",
        ),
        "seed_and_operator_shape_mining_complete": gate(
            summary["generation_pruned_seed_rows"] == 14
            and summary["generation_pruned_seed_weight"] == 1962
            and summary["observed_triplet_only_operator_shape_count"] == 16
            and summary["feasible_pattern_count"] == 37
            and summary["unresolved_pattern_count"] == 3
            and len(mining["target_column_pairs"]) == 10,
            str(report_json),
            "scout mines the requested pruned survivors, observed operator shapes, and feasible patterns",
        ),
        "local_move_bounds_are_explicit": gate(
            bounds["local_move_radius"] == 1
            and bounds["max_generated_matrices"] == 240
            and bounds["max_certifications"] == 8
            and bounds["max_abs_charge_bound"] == 4
            and bounds["targeted_primitive_count"] == 560
            and bounds["unique_seed_count"] == 6,
            str(report_json),
            "local move escape grammar uses explicit bounded search parameters",
        ),
        "generated_candidate_accounting": gate(
            summary["generated_candidate_count"] == 240
            and summary["raw_q1_candidate_count"] == 2
            and summary["certified_candidate_count"] == 2
            and summary["filtered_candidate_count"] == 2
            and summary["screening_rejected_before_certification_count"] == 238
            and summary["certified_rejected_before_representative_audit_count"] == 2
            and summary["total_rejected_before_representative_audit_count"] == 240,
            str(report_json),
            "generated, screened, certified, and pre-representative rejection counts are consistent",
        ),
        "preservation_gates_reject_before_representative_audit": gate(
            summary["desired_q1_after_character_candidate_count"] == 0
            and summary["selection_viable_count"] == 0
            and summary["character_refined_statuses"]
            == {"no_character_refined_triplet_mass_operator_found": 2}
            and summary["representative_statuses"]
            == {"not_evaluated_selection_rule_not_viable": 2}
            and all(
                record["representative_grammar_gate"]["representative_grammar_stage"][
                    "status"
                ]
                == "not_evaluated_selection_rule_not_viable"
                for record in scout["filtered_records"]
            ),
            str(report_json),
            "certified local moves fail q1/selection gates before representative compatibility is evaluated",
        ),
        "screening_rejections_are_stable": gate(
            scout["screening_rejections"]
            == {
                "anomaly": 2,
                "duplicate_up_to_summand_permutation": 1,
                "index": 181,
                "not_raw_q1": 10,
                "slope": 37,
                "spectrum_or_quality": 8,
            },
            str(report_json),
            "pre-certification screening rejection frontier is stable",
        ),
        "no_escape_survivor": gate(
            summary["representative_compatible_count"] == 0
            and summary["representative_unresolved_count"] == 0
            and summary["cup_product_eligible_count"] == 0
            and scout["representative_compatible_records"] == []
            and scout["cup_product_eligible_records"] == [],
            str(report_json),
            "bounded feasible-character escape grammar finds no promotion-ready candidate",
        ),
        "markdown_reports_escape_boundary": gate(
            "generated_candidate_count: `240`" in md_text
            and "total_rejected_before_representative_audit_count: `240`" in md_text
            and "representative_compatible_count: `0`" in md_text
            and "cup_product_eligible_count: `0`" in md_text,
            str(report_md),
            "markdown exposes generated candidates and zero-promotion boundary",
        ),
    }
    return {
        "scope": "verification for radius-9 representative-feasible escape grammar scout",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_escape_grammar_scout.json"
        ),
    )
    parser.add_argument(
        "--report-md",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_escape_grammar_scout.md"
        ),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_escape_grammar_scout_verification.json"
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
