#!/usr/bin/env python3
"""Verify the radius-9 representative-gated generation replay rollup."""

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
    controls = report["regression_controls"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"]
            and all(item["pass"] for item in report["gates"].values()),
            str(report_json),
            "builder-side representative generation replay gates passed",
        ),
        "expected_status": gate(
            report["status"]
            == "radius9_representative_generation_replay_zero_promotion_ready_candidates"
            and report["scope"].startswith("replay the materialized radius-9"),
            str(report_json),
            "report is the generation-time representative gate replay",
        ),
        "materialized_frontier_replayed": gate(
            summary["windows_closed"] == 45
            and summary["materialized_q1_records_generated"] == 4065
            and summary["materialized_q1_weight_generated"] == 549038,
            str(report_json),
            "all materialized radius-9 q=1 source records are replayed",
        ),
        "selection_stage_counts_match_refined_frontier": gate(
            summary["selection_rule_candidate_rows"] == 14
            and summary["selection_rule_candidate_weight"] == 1962
            and summary["selection_rule_status_weight"]
            == {
                "character_refined_doublet_mass_obstruction": 33072,
                "no_character_refined_triplet_mass_operator_found": 510611,
                "passes_refined_charge_character_dt_and_proton_filter": 1962,
                "selective_dt_but_proton_unprotected": 3393,
            },
            str(report_json),
            "selection-rule replay reproduces the corrected character-refined frontier",
        ),
        "representative_stage_prunes_all_shadow_survivors": gate(
            summary["representative_grammar_pruned_rows"] == 14
            and summary["representative_grammar_pruned_weight"] == 1962
            and summary["representative_grammar_unresolved_rows"] == 0
            and summary["representative_compatible_rows"] == 0
            and summary["cup_product_eligible_rows"] == 0
            and summary["representative_status_weight"]
            == {
                "not_evaluated_selection_rule_not_viable": 547076,
                "representative_obstructed": 1962,
            },
            str(report_json),
            "representative grammar gate blocks all current shadow survivors before promotion",
        ),
        "branch18_regression": gate(
            controls["branch18"]["candidate_label"]
            == "radius6_broad_adjacency_filtered_4_branch_18"
            and controls["branch18"]["operator"] == "5bar_02*5_24"
            and controls["branch18"]["obstruction_summary"]["branch_actual"][
                "multiplicities"
            ]
            == {"+": 2, "-": 0}
            and controls["branch18"]["obstruction_summary"]["computed_actual"][
                "multiplicities"
            ]
            == {"+": 1, "-": 1},
            str(report_json),
            "branch 18 shadow collision remains a generation-time prune",
        ),
        "five12_e2_regression": gate(
            len(controls["five12"]) == 2
            and all(
                item["operator"] == "5bar_12*5_12"
                and item["obstruction_summary"]["first_obstructing_role"]
                == "5_12:cup_H1_wedge2_V_dual"
                and item["obstruction_summary"]["branch_actual"]["multiplicities"]
                == {"+": 0, "-": 2}
                and item["obstruction_summary"]["computed_actual"]["multiplicities"]
                == {"+": 1, "-": 1}
                for item in controls["five12"]
            ),
            str(report_json),
            "5_12 cup-dual E2 mismatch remains a generation-time prune",
        ),
        "five23_kernel_regression": gate(
            controls["five23"]["operator"] == "5bar_23*5_23"
            and controls["five23"]["obstruction_summary"]["first_obstructing_role"]
            == "5bar_23:physical_H1_wedge2_V"
            and controls["five23"]["obstruction_summary"]["branch_actual"][
                "multiplicities"
            ]
            == {"+": 2, "-": 0}
            and controls["five23"]["obstruction_summary"]["computed_actual"][
                "multiplicities"
            ]
            == {"+": 2, "-": 1},
            str(report_json),
            "5bar_23 kernel mismatch remains a generation-time prune",
        ),
        "markdown_reports_generation_boundary": gate(
            "representative_grammar_pruned_weight: `1962`" in md_text
            and "representative_compatible_weight: `0`" in md_text
            and "cup_product_eligible_weight: `0`" in md_text,
            str(report_md),
            "markdown exposes zero promotion-ready candidate boundary",
        ),
    }
    return {
        "scope": "verification for radius-9 representative-gated generation replay",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_generation_replay_rollup.json"
        ),
    )
    parser.add_argument(
        "--report-md",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_generation_replay_rollup.md"
        ),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_generation_replay_rollup_verification.json"
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
