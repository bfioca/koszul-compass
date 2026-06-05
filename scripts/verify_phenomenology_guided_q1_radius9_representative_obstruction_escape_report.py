#!/usr/bin/env python3
"""Verify the radius-9 representative obstruction and escape report."""

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
    scan = report["escape_scan"]
    anatomy = report["obstruction_anatomy"]
    anatomy_by_role = {item["obstruction_role"]: item for item in anatomy}
    unresolved = scan["representative_unresolved_targets"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"]
            and all(item["pass"] for item in report["gates"].values()),
            str(report_json),
            "builder-side obstruction escape gates passed",
        ),
        "expected_status": gate(
            report["status"]
            == "no_representative_compatible_escape_target_in_bounded_materialized_scan"
            and report["interpretation"]["active_bottleneck"]
            == "representative-realizability, not cup-product rank",
            str(report_json),
            "report classifies the current bottleneck as representative-realizability",
        ),
        "closed_frontier_anatomy": gate(
            set(anatomy_by_role)
            == {
                "5_12:cup_H1_wedge2_V_dual",
                "5bar_02:physical_H1_wedge2_V",
                "5bar_04:physical_H1_wedge2_V",
                "5bar_23:physical_H1_wedge2_V",
            }
            and sum(item["represented_weight"] for item in anatomy) == 1962
            and anatomy_by_role["5bar_02:physical_H1_wedge2_V"]["branch_actual"][
                "multiplicities"
            ]
            == {"+": 2, "-": 0}
            and anatomy_by_role["5bar_02:physical_H1_wedge2_V"]["computed_actual"][
                "multiplicities"
            ]
            == {"+": 1, "-": 1}
            and anatomy_by_role["5_12:cup_H1_wedge2_V_dual"]["computed_actual"][
                "multiplicities"
            ]
            == {"+": 1, "-": 1},
            str(report_json),
            "closed character-shadow viable frontier is explained by four obstruction classes",
        ),
        "bounded_scan_counts": gate(
            scan["bounds"]["windows"] == 45
            and scan["bounds"]["max_unique_operators"] == 24
            and scan["bounds"]["max_audits"] == 24
            and scan["scanned"]["materialized_records"] == 4065
            and scan["scanned"]["represented_weight"] == 549038
            and scan["scanned"]["records_with_triplet_only_shadow_operator"] == 1530
            and scan["selected_escape_operator_count"] == 12
            and scan["audited_escape_target_count"] == 12,
            str(report_json),
            "escape scan is bounded and traverses the materialized radius-9 records",
        ),
        "operator_inventory_is_stable": gate(
            scan["triplet_only_operator_rows"]["5bar_12*5_12"] == 609
            and scan["triplet_only_operator_rows"]["5bar_01*5_12"] == 324
            and scan["triplet_only_operator_rows"]["5bar_34*5_34"] == 98
            and len(scan["triplet_only_operator_rows"]) == 16,
            str(report_json),
            "triplet-only shadow operator inventory is stable",
        ),
        "no_compatible_escape_target": gate(
            len(scan["representative_compatible_targets"]) == 0
            and len(scan["representative_obstructed_targets"]) == 11
            and len(scan["representative_unresolved_targets"]) == 1,
            str(report_json),
            "bounded escape scan found no representative-compatible target",
        ),
        "unresolved_escape_target_is_not_viable": gate(
            len(unresolved) == 1
            and unresolved[0]["operator"] == "5bar_34*5_34"
            and unresolved[0]["classification"]["status"]
            == "character_refined_doublet_mass_obstruction"
            and unresolved[0]["proton_allowed_count"] == 1
            and unresolved[0]["unresolved_summary"]["first_unresolved_role"]
            == "5bar_34:physical_H1_wedge2_V",
            str(report_json),
            "single unresolved escape target is already blocked by non-representative gates",
        ),
        "markdown_reports_boundary": gate(
            "representative-compatible targets: `0`" in md_text
            and "representative-unresolved targets: `1`" in md_text
            and "blind radius expansion is low-value" in md_text,
            str(report_md),
            "markdown exposes no-compatible result and unresolved boundary",
        ),
    }
    return {
        "scope": "verification for radius-9 representative obstruction and escape report",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_obstruction_escape_report.json"
        ),
    )
    parser.add_argument(
        "--report-md",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_obstruction_escape_report.md"
        ),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_obstruction_escape_report_verification.json"
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
