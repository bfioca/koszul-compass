#!/usr/bin/env python3
"""Exact monoid audit for radius-6 DT-targeted mass-unresolved q=1 branches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

from build_phenomenology_guided_q1_radius5_unresolved_mass_monoid_audit import (  # noqa: E402
    audit_record,
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def build_report(
    branch_json: Path,
    scout_json: Path,
    branch_verification_json: Path,
) -> dict[str, Any]:
    branch = load_json(branch_json)
    scout = load_json(scout_json)
    branch_verification = load_json(branch_verification_json)
    branch_records = [
        (branch_json, record)
        for record in branch["desired_q1_branch_candidate_records"]
        if record["classification"]["status"] == "no_certified_triplet_mass_operator_found"
    ]
    scout_records = [
        (scout_json, record)
        for record in scout["filtered_candidate_records"]
        if record["classification"]["status"] == "no_certified_triplet_mass_operator_found"
    ]
    records = [*scout_records, *branch_records]
    audited = [
        audit_record(record, source_path=source_path, weight=1)
        for source_path, record in records
    ]
    upgraded = [
        item for item in audited if item["all_mass_entries_monoid_obstructed"]
    ]
    open_records = [
        item for item in audited if not item["all_mass_entries_monoid_obstructed"]
    ]
    gates = {
        "imports_verified_radius6_branch_analysis": gate(
            branch_verification["all_gates_pass"]
            and branch["summary"]["viable_branches"] == 0,
            str(branch_verification_json),
            "audit starts from the verified radius6 DT branch analysis",
        ),
        "all_mass_unresolved_records_collected": gate(
            len(branch_records)
            == branch["summary"]["statuses"].get(
                "no_certified_triplet_mass_operator_found", 0
            ),
            str(branch_json),
            "all radius6 no-certified-triplet-mass branch records are audited",
        ),
        "audited_records_have_mass_tables": gate(
            all(item["mass_entries"] for item in audited),
            str(branch_json),
            "every audited radius6 record has mass operator entries",
        ),
    }
    return {
        "scope": "exact certified-singlet monoid audit for radius6 DT-targeted mass-unresolved q1 branches",
        "status": (
            "radius6_dt_mass_unresolved_all_upgraded_to_monoid_obstructions"
            if not open_records
            else "radius6_dt_mass_unresolved_has_open_exact_monoid_solutions"
        ),
        "summary": {
            "audited_records": len(audited),
            "direct_scout_records": len(scout_records),
            "branch_records": len(branch_records),
            "upgraded_monoid_obstructions": len(upgraded),
            "open_exact_monoid_solutions": len(open_records),
            "records_with_exact_monoid_solution": sum(
                1 for item in audited if item["has_exact_monoid_solution"]
            ),
            "records_all_mass_entries_obstructed": sum(
                1 for item in audited if item["all_mass_entries_monoid_obstructed"]
            ),
        },
        "audited_records": audited,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-6 DT Mass Monoid Audit",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Open Records", ""])
    open_records = [
        item
        for item in report["audited_records"]
        if not item["all_mass_entries_monoid_obstructed"]
    ]
    if not open_records:
        lines.append("- none")
    else:
        for item in open_records:
            lines.append(f"- `{item['label']}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--branch-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_branch_analysis.json"),
    )
    parser.add_argument(
        "--branch-verification-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_branch_analysis_verification.json"),
    )
    parser.add_argument(
        "--scout-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_targeted_scout.json"),
    )
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_mass_monoid_audit.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_mass_monoid_audit.md"),
    )
    args = parser.parse_args()
    report = build_report(
        Path(args.branch_json),
        Path(args.scout_json),
        Path(args.branch_verification_json),
    )
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
