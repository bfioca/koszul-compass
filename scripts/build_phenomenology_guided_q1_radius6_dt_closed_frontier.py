#!/usr/bin/env python3
"""Closed frontier summary for the radius-6 DT-targeted search window."""

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


def adjusted_statuses(scout: dict[str, Any], branch: dict[str, Any], audit: dict[str, Any]) -> dict[str, int]:
    statuses: Counter[str] = Counter()
    for record in scout["filtered_candidate_records"]:
        status = record["classification"]["status"]
        if status == "missing_character_or_charge_level_data":
            continue
        if status == "no_certified_triplet_mass_operator_found":
            status = "no_triplet_mass_in_certified_singlet_monoid"
        statuses[status] += 1
    for status, count in branch["summary"]["statuses"].items():
        if status == "no_certified_triplet_mass_operator_found":
            status = "no_triplet_mass_in_certified_singlet_monoid"
        statuses[status] += count
    if audit["summary"]["open_exact_monoid_solutions"] != 0:
        statuses["open_exact_monoid_solution_after_audit"] += audit["summary"][
            "open_exact_monoid_solutions"
        ]
    return dict(sorted(statuses.items()))


def build_report(
    *,
    scout_json: Path,
    scout_verification_json: Path,
    branch_json: Path,
    branch_verification_json: Path,
    audit_json: Path,
    audit_verification_json: Path,
    title: str,
    status: str,
) -> dict[str, Any]:
    scout = load_json(scout_json)
    scout_v = load_json(scout_verification_json)
    branch = load_json(branch_json)
    branch_v = load_json(branch_verification_json)
    audit = load_json(audit_json)
    audit_v = load_json(audit_verification_json)
    search_parameters = scout.get("search_parameters", {})
    source_radius = search_parameters.get("source_radius", 5)
    target_radius = search_parameters.get("target_radius", source_radius + 1)
    statuses = adjusted_statuses(scout, branch, audit)
    direct_non_missing = sum(
        1
        for record in scout["filtered_candidate_records"]
        if record["classification"]["status"] != "missing_character_or_charge_level_data"
    )
    direct_viable = sum(
        1
        for record in scout["filtered_candidate_records"]
        if record["classification"]["category"] == "viable"
    )
    summary = {
        "frontier_records_screened": scout["screening_counters"][
            "frontier_records_screened"
        ],
        "frontier_records_after_window": scout["screening_counters"][
            "frontier_records_after_window"
        ],
        "raw_q1_spectrum_survivors": scout["summary"]["raw_q1_spectrum_survivors"],
        "direct_character_certified_q1_records": direct_non_missing,
        "branch_completions_evaluated": branch["summary"]["branches_evaluated"],
        "desired_q1_branch_completions": branch["summary"]["desired_q1_branches"],
        "adjusted_desired_q1_candidates": direct_non_missing
        + branch["summary"]["desired_q1_branches"],
        "mass_records_upgraded_by_exact_monoid": audit["summary"][
            "upgraded_monoid_obstructions"
        ],
        "open_mass_monoid_solutions": audit["summary"]["open_exact_monoid_solutions"],
        "viable_count": direct_viable + branch["summary"]["viable_branches"],
        "adjusted_statuses": statuses,
    }
    gates = {
        "imports_verified_components": gate(
            scout_v["all_gates_pass"]
            and branch_v["all_gates_pass"]
            and audit_v["all_gates_pass"],
            f"radius{target_radius} scout, branch, and mass-audit verification artifacts",
            "closed frontier imports verified component reports",
        ),
        "branch_frontier_closed": gate(
            branch["summary"]["records_skipped"] == 0
            and branch["summary"]["records_evaluated"]
            == branch["summary"]["unresolved_records"],
            str(branch_json),
            f"all missing-character radius{target_radius} records are fully branch-evaluated",
        ),
        "mass_uncertainty_closed": gate(
            summary["open_mass_monoid_solutions"] == 0
            and "no_certified_triplet_mass_operator_found" not in statuses,
            str(audit_json),
            "all no-certified-triplet-mass records are upgraded by exact monoid audit",
        ),
        "no_viable_candidate": gate(
            summary["viable_count"] == 0,
            f"adjusted radius{target_radius} DT-targeted classifications",
            f"no direct or branch-completed radius{target_radius} q1 candidate passes the charge-level filter",
        ),
    }
    return {
        "scope": (
            f"closed radius{target_radius} DT-targeted frontier from verified "
            f"radius{source_radius} q1 seeds"
        ),
        "status": status,
        "title": title,
        "summary": summary,
        "component_reports": {
            "scout": str(scout_json),
            "branch_analysis": str(branch_json),
            "mass_monoid_audit": str(audit_json),
        },
        "interpretation": (
            f"The targeted radius{target_radius} window starts from verified "
            f"radius{source_radius} q1 near-misses. "
            "All missing-character records are fully branch-enumerated, every desired-q1 "
            "branch emits spectrum, character, mass, and proton tables, and exact "
            "certified-singlet monoid feasibility closes the remaining mass-bound "
            "uncertainties. No viable charge-level candidate is found."
        ),
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        f"# {report.get('title', 'Radius-6 DT-Targeted Closed Frontier')}",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Interpretation", "", report["interpretation"], ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scout-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_targeted_scout.json"),
    )
    parser.add_argument(
        "--scout-verification-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_targeted_scout_verification.json"),
    )
    parser.add_argument(
        "--branch-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_branch_analysis.json"),
    )
    parser.add_argument(
        "--branch-verification-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_branch_analysis_verification.json"),
    )
    parser.add_argument(
        "--audit-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_mass_monoid_audit.json"),
    )
    parser.add_argument(
        "--audit-verification-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_mass_monoid_audit_verification.json"),
    )
    parser.add_argument(
        "--title",
        default="Radius-6 DT-Targeted Closed Frontier",
    )
    parser.add_argument(
        "--status",
        default="radius6_dt_targeted_closed_no_viable_candidate",
    )
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_closed_frontier.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_closed_frontier.md"),
    )
    args = parser.parse_args()
    report = build_report(
        scout_json=Path(args.scout_json),
        scout_verification_json=Path(args.scout_verification_json),
        branch_json=Path(args.branch_json),
        branch_verification_json=Path(args.branch_verification_json),
        audit_json=Path(args.audit_json),
        audit_verification_json=Path(args.audit_verification_json),
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
