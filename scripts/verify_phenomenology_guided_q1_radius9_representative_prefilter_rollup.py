#!/usr/bin/env python3
"""Verify the radius-9 representative-prefiltered promotion rollup."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def obstruction_role_counts(report: dict[str, Any]) -> Counter[str]:
    return Counter(
        record["representative_stage"]["first_failure"]["first_obstructing_role"]
        for record in report["promotion_records"]
        if record["representative_stage"].get("first_failure")
        and "first_obstructing_role" in record["representative_stage"]["first_failure"]
    )


def verify(report_json: Path, report_md: Path, windows: int) -> dict[str, Any]:
    report = load_json(report_json)
    md_text = report_md.read_text(encoding="utf-8")
    summary = report["summary"]
    controls = report["regression_controls"]
    records = report["promotion_records"]
    role_counts = obstruction_role_counts(report)
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"]
            and all(item["pass"] for item in report["gates"].values()),
            str(report_json),
            "builder-side representative prefilter gates passed",
        ),
        "expected_scope_and_status": gate(
            report["status"]
            == f"radius9_representative_prefilter_windows1_{windows}_no_representative_compatible_candidate"
            and report["scope"].startswith("apply representative-equivariant realizability")
            and report["classification_hierarchy"]["character_shadow_viable"].startswith(
                "passes component-character"
            ),
            str(report_json),
            "rollup uses representative realizability as the promotion gate",
        ),
        "summary_counts_close_frontier": gate(
            summary["windows_closed"] == windows
            and summary["adjusted_desired_q1_candidates"] == 549038
            and summary["character_shadow_viable_weight"] == 1962
            and summary["character_shadow_viable_rows"] == 14
            and summary["representative_prefilter_status_weight"]
            == {"representative_obstructed": 1962}
            and summary["representative_prefilter_status_rows"]
            == {"representative_obstructed": 14}
            and summary["representative_compatible_weight"] == 0
            and summary["representative_unresolved_weight"] == 0
            and summary["cup_product_eligible_weight"] == 0
            and summary["cup_product_eligible_rows"] == 0,
            str(report_json),
            "all character-shadow viable weight is resolved as representative-obstructed",
        ),
        "promotion_records_are_gated": gate(
            len(records) == 14
            and sum(record["weight"] for record in records) == 1962
            and all(
                record["selection_rule_stage"]["status"] == "character_shadow_viable"
                and record["representative_stage"]["status"] == "representative_obstructed"
                and not record["representative_stage"]["cup_product_eligible"]
                for record in records
            ),
            str(report_json),
            "every shadow survivor is blocked before lead dossier or cup-product promotion",
        ),
        "promotion_policy_blocks_downstream_work": gate(
            not report["promotion_policy"]["lead_dossier_allowed"]
            and not report["promotion_policy"]["cup_product_planning_allowed"]
            and "blocked for this frontier" in report["promotion_policy"]["reason"],
            str(report_json),
            "lead dossier and cup-product planning are disabled without representative compatibility",
        ),
        "obstruction_roles_match_rerank": gate(
            role_counts == {
                "5_12:cup_H1_wedge2_V_dual": 2,
                "5bar_02:physical_H1_wedge2_V": 9,
                "5bar_04:physical_H1_wedge2_V": 2,
                "5bar_23:physical_H1_wedge2_V": 1,
            },
            str(report_json),
            "promotion rollup preserves representative obstruction class counts",
        ),
        "branch18_regression": gate(
            controls["branch18"]["obstruction_summary"]["branch_actual"]["multiplicities"]
            == {"+": 2, "-": 0}
            and controls["branch18"]["obstruction_summary"]["computed_actual"][
                "multiplicities"
            ]
            == {"+": 1, "-": 1},
            str(report_json),
            "branch 18 impossible character request remains covered",
        ),
        "five12_regression": gate(
            len(controls["five12"]) == 2
            and all(
                target["obstruction_summary"]["branch_actual"]["multiplicities"]
                == {"+": 0, "-": 2}
                and target["obstruction_summary"]["computed_actual"]["multiplicities"]
                == {"+": 1, "-": 1}
                for target in controls["five12"]
            ),
            str(report_json),
            "former fivebar_12 unresolved cases remain E2 cup-dual obstructions",
        ),
        "five23_regression": gate(
            controls["five23"]["obstruction_summary"]["branch_actual"]["multiplicities"]
            == {"+": 2, "-": 0}
            and controls["five23"]["obstruction_summary"]["computed_actual"][
                "multiplicities"
            ]
            == {"+": 2, "-": 1},
            str(report_json),
            "former fivebar_23 map failure remains an explicit kernel mismatch",
        ),
        "markdown_reports_no_promotion": gate(
            "lead dossier allowed: `False`" in md_text
            and "cup-product planning allowed: `False`" in md_text
            and "representative_prefilter_status_weight: `{'representative_obstructed': 1962}`"
            in md_text,
            str(report_md),
            "markdown exposes representative closure and no-promotion policy",
        ),
    }
    return {
        "scope": "verification for radius-9 representative-prefiltered promotion rollup",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", type=int, default=45)
    parser.add_argument(
        "--report-json",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_representative_prefilter_rollup.json"
        ),
    )
    parser.add_argument(
        "--report-md",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_representative_prefilter_rollup.md"
        ),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_prefilter_rollup_verification.json"
        ),
    )
    args = parser.parse_args()
    result = verify(
        report_json=Path(args.report_json),
        report_md=Path(args.report_md),
        windows=args.windows,
    )
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
