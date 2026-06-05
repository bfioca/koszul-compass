#!/usr/bin/env python3
"""Summarize batch-3 frontier after branch analysis and exact mass closure."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def build_report() -> dict[str, Any]:
    known = load_json(REPORTS / "phenomenology_guided_q1_radius4_batch3_known_line_resolved.json")
    branch = load_json(REPORTS / "phenomenology_guided_q1_radius4_batch3_branch_analysis.json")
    mass = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_batch3_branch_mass_monoid_audit.json"
    )
    q1_statuses = Counter(branch["summary"]["statuses"])
    q1_statuses["no_certified_triplet_mass_operator_found"] -= mass["summary"][
        "upgraded_obstructions"
    ]
    q1_statuses["no_triplet_mass_in_certified_singlet_monoid"] += mass["summary"][
        "upgraded_obstructions"
    ]
    q1_statuses = Counter({key: value for key, value in q1_statuses.items() if value})

    gates = {
        "imports_batch3_known_line": gate(
            known["all_gates_pass"]
            and known["summary"]["statuses"].get("known_line_resolution_still_incomplete")
            == 13,
            str(REPORTS / "phenomenology_guided_q1_radius4_batch3_known_line_resolved.json"),
            "batch3 starts with 13 known-line-incomplete q=1 survivor records",
        ),
        "imports_branch_analysis": gate(
            branch["all_gates_pass"]
            and branch["summary"]["unresolved_records"] == 13
            and branch["summary"]["records_skipped"] == 0
            and branch["summary"]["viable_branches"] == 0,
            str(REPORTS / "phenomenology_guided_q1_radius4_batch3_branch_analysis.json"),
            "all batch3 incomplete records were branch-enumerated with no viable branch",
        ),
        "imports_exact_mass_closure": gate(
            mass["all_gates_pass"]
            and mass["summary"]["mass_bound_branches"] == 2
            and mass["summary"]["open_mass_bound_uncertainties"] == 0,
            str(REPORTS / "phenomenology_guided_q1_radius4_batch3_branch_mass_monoid_audit.json"),
            "all mass-bound q=1 branches are exact singlet-monoid obstructions",
        ),
        "adjusted_q1_statuses_have_no_unresolved_mass_bound": gate(
            "no_certified_triplet_mass_operator_found" not in q1_statuses
            and sum(q1_statuses.values()) == branch["summary"]["branches_evaluated"],
            "batch3 adjusted branch status accounting",
            "branch statuses are adjusted by the exact mass-monoid closure",
        ),
    }
    return {
        "scope": "batch3 branch-closed selected radius-4 q=1 frontier",
        "status": "batch3_known_line_incomplete_frontier_branch_closed_no_viable_candidate",
        "summary": {
            "known_line_incomplete_records_closed": 13,
            "branch_records_evaluated": branch["summary"]["records_evaluated"],
            "branch_records_skipped": branch["summary"]["records_skipped"],
            "branches_evaluated": branch["summary"]["branches_evaluated"],
            "desired_q1_branches": branch["summary"]["desired_q1_branches"],
            "viable_branches": branch["summary"]["viable_branches"],
            "mass_bound_branches_upgraded": mass["summary"]["upgraded_obstructions"],
            "open_mass_bound_uncertainties": mass["summary"][
                "open_mass_bound_uncertainties"
            ],
            "adjusted_branch_statuses": dict(sorted(q1_statuses.items())),
        },
        "interpretation": (
            "Every batch3 known-line-incomplete survivor has been closed by bounded "
            "dimension-compatible branch completion. No branch reaches the viable "
            "charge-level filter; the remaining mass-bound q=1 branches are exact "
            "certified singlet-monoid obstructions."
        ),
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Batch-3 Branch-Closed Frontier",
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
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_batch3_branch_closed_frontier.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_batch3_branch_closed_frontier.md"
        ),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
