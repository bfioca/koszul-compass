#!/usr/bin/env python3
"""Closed frontier summary for a radius-6 targeted window with large closures."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def remap_status(status: str) -> str:
    if status == "no_certified_triplet_mass_operator_found":
        return "no_triplet_mass_in_certified_singlet_monoid"
    return status


def build_report(
    *,
    scout_json: Path,
    scout_verification_json: Path,
    branch_json: Path,
    large_closure_jsons: list[Path],
    large_closure_verification_jsons: list[Path],
    audit_json: Path,
    title: str,
    status: str,
) -> dict[str, Any]:
    scout = load_json(scout_json)
    scout_v = load_json(scout_verification_json)
    branch = load_json(branch_json)
    large_closures = [load_json(path) for path in large_closure_jsons]
    large_vs = [load_json(path) for path in large_closure_verification_jsons]
    audit = load_json(audit_json)
    statuses: Counter[str] = Counter()
    direct_non_missing = 0
    direct_viable = 0
    for record in scout["filtered_candidate_records"]:
        item_status = record["classification"]["status"]
        if item_status == "missing_character_or_charge_level_data":
            continue
        direct_non_missing += 1
        direct_viable += int(record["classification"]["category"] == "viable")
        statuses[remap_status(item_status)] += 1
    for item_status, count in branch["summary"]["statuses"].items():
        statuses[remap_status(item_status)] += count
    for closure in large_closures:
        summary = closure["summary"]
        rep = closure["q1_representative_candidate"]
        statuses[rep["classification"]["status"]] += summary["desired_q1_branches"]
        statuses["rejected_spectrum_signature_not_q1_three_family"] += summary[
            "not_desired_q1_branches"
        ]
    summary = {
        "frontier_records_screened": scout["screening_counters"][
            "frontier_records_screened"
        ],
        "frontier_records_after_window": scout["screening_counters"][
            "frontier_records_after_window"
        ],
        "raw_q1_spectrum_survivors": scout["summary"]["raw_q1_spectrum_survivors"],
        "direct_character_certified_q1_records": direct_non_missing,
        "bounded_branch_completions_evaluated": branch["summary"][
            "branches_evaluated"
        ],
        "bounded_desired_q1_branch_completions": branch["summary"][
            "desired_q1_branches"
        ],
        "large_branch_completions_counted": sum(
            item["summary"]["total_branches"] for item in large_closures
        ),
        "large_desired_q1_branch_completions": sum(
            item["summary"]["desired_q1_branches"] for item in large_closures
        ),
        "adjusted_desired_q1_candidates": direct_non_missing
        + branch["summary"]["desired_q1_branches"]
        + sum(item["summary"]["desired_q1_branches"] for item in large_closures),
        "mass_records_upgraded_by_exact_monoid": audit["summary"][
            "upgraded_monoid_obstructions"
        ],
        "open_mass_monoid_solutions": audit["summary"]["open_exact_monoid_solutions"],
        "viable_count": direct_viable
        + branch["summary"]["viable_branches"]
        + sum(item["summary"]["viable_q1_branches"] for item in large_closures),
        "adjusted_statuses": dict(sorted(statuses.items())),
    }
    gates = {
        "verified_components_imported": gate(
            scout_v["all_gates_pass"] and all(item["all_gates_pass"] for item in large_vs),
            "component verification artifacts",
            "scout and large branch closure verifications passed",
        ),
        "all_large_branches_closed": gate(
            branch["summary"]["records_skipped"] == len(large_closures)
            and all(item["summary"]["viable_q1_branches"] == 0 for item in large_closures),
            str(branch_json),
            "all skipped branch records are covered by verified large closures",
        ),
        "no_open_uncertainty": gate(
            summary["open_mass_monoid_solutions"] == 0
            and "missing_character_or_charge_level_data" not in summary["adjusted_statuses"]
            and "no_certified_triplet_mass_operator_found" not in summary["adjusted_statuses"],
            str(audit_json),
            "character and mass uncertainties are closed or upgraded",
        ),
        "no_viable_candidate": gate(
            summary["viable_count"] == 0,
            "adjusted classifications",
            "no direct, bounded-branch, or large-branch q1 candidate is viable",
        ),
    }
    return {
        "scope": "closed radius6 targeted frontier with bounded and large branch closures",
        "status": status,
        "title": title,
        "summary": summary,
        "component_reports": {
            "scout": str(scout_json),
            "branch_analysis": str(branch_json),
            "large_closures": [str(path) for path in large_closure_jsons],
            "mass_monoid_audit": str(audit_json),
        },
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        f"# {report['title']}",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scout-json", required=True)
    parser.add_argument("--scout-verification-json", required=True)
    parser.add_argument("--branch-json", required=True)
    parser.add_argument("--large-closure-json", action="append", required=True)
    parser.add_argument("--large-closure-verification-json", action="append", required=True)
    parser.add_argument("--audit-json", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--md-out", required=True)
    args = parser.parse_args()
    report = build_report(
        scout_json=Path(args.scout_json),
        scout_verification_json=Path(args.scout_verification_json),
        branch_json=Path(args.branch_json),
        large_closure_jsons=[Path(item) for item in args.large_closure_json],
        large_closure_verification_jsons=[
            Path(item) for item in args.large_closure_verification_json
        ],
        audit_json=Path(args.audit_json),
        title=args.title,
        status=args.status,
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
