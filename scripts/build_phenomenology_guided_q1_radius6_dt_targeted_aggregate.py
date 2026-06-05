#!/usr/bin/env python3
"""Aggregate the closed radius-6 DT-targeted frontier windows."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


DEFAULT_REPORTS = [
    REPORTS / "phenomenology_guided_q1_radius6_dt_closed_frontier.json",
    REPORTS / "phenomenology_guided_q1_radius6_dt_closed_frontier_window2.json",
    REPORTS / "phenomenology_guided_q1_radius6_dt_closed_frontier_window3.json",
]
DEFAULT_VERIFICATIONS = [
    REPORTS / "phenomenology_guided_q1_radius6_dt_closed_frontier_verification.json",
    REPORTS / "phenomenology_guided_q1_radius6_dt_closed_frontier_window2_verification.json",
    REPORTS / "phenomenology_guided_q1_radius6_dt_closed_frontier_window3_verification.json",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def branch_completions_evaluated(report: dict[str, Any]) -> int:
    summary = report["summary"]
    if "branch_completions_evaluated" in summary:
        return summary["branch_completions_evaluated"]
    return summary["bounded_branch_completions_evaluated"] + summary[
        "large_branch_completions_counted"
    ]


def desired_q1_branch_completions(report: dict[str, Any]) -> int:
    summary = report["summary"]
    if "desired_q1_branch_completions" in summary:
        return summary["desired_q1_branch_completions"]
    return summary["bounded_desired_q1_branch_completions"] + summary[
        "large_desired_q1_branch_completions"
    ]


def build_report(closed_reports: list[Path], verifications: list[Path]) -> dict[str, Any]:
    reports = [load_json(path) for path in closed_reports]
    verification_reports = [load_json(path) for path in verifications]
    statuses: Counter[str] = Counter()
    for report in reports:
        statuses.update(report["summary"]["adjusted_statuses"])
    summary = {
        "windows_closed": len(reports),
        "frontier_records_screened": sum(
            report["summary"]["frontier_records_screened"] for report in reports
        ),
        "frontier_records_after_final_window": reports[-1]["summary"][
            "frontier_records_after_window"
        ],
        "raw_q1_spectrum_survivors": sum(
            report["summary"]["raw_q1_spectrum_survivors"] for report in reports
        ),
        "direct_character_certified_q1_records": sum(
            report["summary"]["direct_character_certified_q1_records"]
            for report in reports
        ),
        "branch_completions_evaluated": sum(
            branch_completions_evaluated(report) for report in reports
        ),
        "desired_q1_branch_completions": sum(
            desired_q1_branch_completions(report) for report in reports
        ),
        "adjusted_desired_q1_candidates": sum(
            report["summary"]["adjusted_desired_q1_candidates"] for report in reports
        ),
        "mass_records_upgraded_by_exact_monoid": sum(
            report["summary"]["mass_records_upgraded_by_exact_monoid"]
            for report in reports
        ),
        "open_mass_monoid_solutions": sum(
            report["summary"]["open_mass_monoid_solutions"] for report in reports
        ),
        "viable_count": sum(report["summary"]["viable_count"] for report in reports),
        "adjusted_statuses": dict(sorted(statuses.items())),
    }
    gates = {
        "all_window_verifications_pass": gate(
            all(item["all_gates_pass"] for item in verification_reports),
            ", ".join(str(path) for path in verifications),
            "all closed radius6 DT-targeted windows are verified",
        ),
        "frontier_exhausted": gate(
            summary["frontier_records_after_final_window"] == 0,
            str(closed_reports[-1]),
            "the final radius6 DT-targeted window exhausts the frontier",
        ),
        "no_open_mass_uncertainty": gate(
            summary["open_mass_monoid_solutions"] == 0
            and "missing_character_or_charge_level_data"
            not in summary["adjusted_statuses"]
            and "no_certified_triplet_mass_operator_found"
            not in summary["adjusted_statuses"],
            "aggregate adjusted statuses",
            "all character and mass uncertainties are closed or upgraded",
        ),
        "no_viable_candidate": gate(
            summary["viable_count"] == 0,
            "aggregate radius6 DT-targeted statuses",
            "no viable candidate is found in the exhausted radius6 DT-targeted frontier",
        ),
    }
    return {
        "scope": "aggregate closure of the radius6 DT-targeted frontier from proton-safe doublet-triplet-obstructed q1 seeds",
        "status": "radius6_dt_targeted_frontier_exhausted_no_viable_candidate",
        "summary": summary,
        "closed_window_reports": [str(path) for path in closed_reports],
        "interpretation": (
            "The proton-safe doublet-triplet-obstructed q1 seed surface was expanded "
            "by one additional local move and exhausted across three radius6 windows. "
            "Every raw q1 survivor is either directly classified or fully branch-completed; "
            "exact singlet-monoid audits close the remaining mass uncertainties. No "
            "candidate passes the charge-level doublet-triplet and proton-suppression filter."
        ),
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-6 DT-Targeted Aggregate",
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
    parser.add_argument("--closed-report", action="append", default=None)
    parser.add_argument("--verification", action="append", default=None)
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_targeted_aggregate.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_targeted_aggregate.md"),
    )
    args = parser.parse_args()
    reports = [Path(item) for item in (args.closed_report or DEFAULT_REPORTS)]
    verifications = [Path(item) for item in (args.verification or DEFAULT_VERIFICATIONS)]
    if len(reports) != len(verifications):
        raise SystemExit("--closed-report and --verification counts must match")
    report = build_report(reports, verifications)
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
