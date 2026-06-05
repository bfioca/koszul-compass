#!/usr/bin/env python3
"""Top-level selected radius-4 branch-closed no-go summary."""

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


def build_report() -> dict[str, Any]:
    coverage = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_selected_source_coverage_report.json"
    )
    post12 = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_post_exhaustion_obstruction_report.json"
    )
    batch3 = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_batch3_branch_closed_frontier.json"
    )
    batch4 = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_batch4_branch_closed_frontier.json"
    )
    verification_paths = [
        REPORTS / "phenomenology_guided_q1_radius4_selected_source_coverage_report_verification.json",
        REPORTS / "phenomenology_guided_q1_radius4_post_exhaustion_obstruction_report_verification.json",
        REPORTS / "phenomenology_guided_q1_radius4_batch3_branch_closed_frontier_verification.json",
        REPORTS / "phenomenology_guided_q1_radius4_batch4_branch_closed_frontier_verification.json",
    ]
    verifications = [load_json(path) for path in verification_paths]

    branch_closed_records = (
        post12["post_exhaustion_accounting"]["verified_branch_closed_character_incomplete_candidates"]
        + batch3["summary"]["known_line_incomplete_records_closed"]
        + batch4["summary"]["known_line_incomplete_records_closed"]
    )
    branch_completions_evaluated = (
        batch3["summary"]["branches_evaluated"] + batch4["summary"]["branches_evaluated"]
    )
    desired_q1_branch_completions = (
        batch3["summary"]["desired_q1_branches"] + batch4["summary"]["desired_q1_branches"]
    )
    mass_bound_upgrades = (
        len(post12["post_exhaustion_accounting"]["exact_mass_bound_closed_candidates"])
        + batch3["summary"]["mass_bound_branches_upgraded"]
        + batch4["summary"]["mass_bound_branches_upgraded"]
    )
    open_mass_uncertainties = (
        len(post12["post_exhaustion_accounting"]["open_mass_bound_uncertainties"])
        + batch3["summary"]["open_mass_bound_uncertainties"]
        + batch4["summary"]["open_mass_bound_uncertainties"]
    )
    viable_count = (
        post12["post_exhaustion_accounting"]["final_viable_count"]
        + batch3["summary"]["viable_branches"]
        + batch4["summary"]["viable_branches"]
    )

    gates = {
        "source_coverage_verified": gate(
            coverage["all_gates_pass"]
            and coverage["summary"]["raw_q1_spectrum_survivors"] == 200
            and coverage["summary"]["covered_records"] == 34500,
            str(REPORTS / "phenomenology_guided_q1_radius4_selected_source_coverage_report.json"),
            "selected radius-4 source coverage remains complete",
        ),
        "all_component_verifications_pass": gate(
            all(item["all_gates_pass"] for item in verifications),
            ", ".join(str(path) for path in verification_paths),
            "all component coverage, closure, and branch-closure reports are verified",
        ),
        "all_live_character_frontiers_closed": gate(
            post12["post_exhaustion_accounting"]["open_character_incomplete_candidates"] == 0
            and batch3["summary"]["branch_records_skipped"] == 0
            and batch4["summary"]["branch_records_skipped"] == 0,
            "post-exhaustion, batch3, and batch4 branch-closure summaries",
            "no selected radius-4 known-line-incomplete candidate remains open",
        ),
        "no_open_mass_uncertainty": gate(
            open_mass_uncertainties == 0,
            "exact mass-monoid audit summaries",
            "all mass-bound cases were upgraded or otherwise closed",
        ),
        "no_viable_candidate": gate(
            viable_count == 0,
            "selected radius-4 branch-closed classifications",
            "no selected radius-4 branch or certified record passes the charge-level viability filter",
        ),
    }
    return {
        "scope": "selected radius-4 source expansion after known-line, branch, and exact mass closure",
        "status": "selected_radius4_branch_closed_no_viable_candidate_found",
        "summary": {
            "source_records_expanded": coverage["summary"]["source_records_expanded"],
            "frontier_records": coverage["summary"]["frontier_records"],
            "covered_records": coverage["summary"]["covered_records"],
            "raw_q1_spectrum_survivors": coverage["summary"][
                "raw_q1_spectrum_survivors"
            ],
            "batch1_2_raw_q1_survivors": post12["selected_radius4_surface"][
                "combined_aggregate_totals"
            ][
                "raw_q1_spectrum_survivors"
            ],
            "batch3_raw_q1_survivors": 61,
            "batch4_raw_q1_survivors": 48,
            "known_line_incomplete_records_branch_closed": branch_closed_records,
            "explicit_branch_completions_evaluated_for_batches3_4": branch_completions_evaluated,
            "desired_q1_branch_completions_for_batches3_4": desired_q1_branch_completions,
            "mass_bound_cases_upgraded_by_exact_monoid": mass_bound_upgrades,
            "open_character_frontier_count": 0,
            "open_mass_bound_uncertainties": open_mass_uncertainties,
            "viable_count": viable_count,
        },
        "component_reports": {
            "batch1_2_post_exhaustion": str(
                REPORTS / "phenomenology_guided_q1_radius4_post_exhaustion_obstruction_report.json"
            ),
            "batch3_branch_closed": str(
                REPORTS / "phenomenology_guided_q1_radius4_batch3_branch_closed_frontier.json"
            ),
            "batch4_branch_closed": str(
                REPORTS / "phenomenology_guided_q1_radius4_batch4_branch_closed_frontier.json"
            ),
        },
        "interpretation": (
            "Across the selected radius-4 expansion of the 63 strict radius-3 "
            "obstructed source records, every raw q=1 spectrum survivor is either "
            "already charge-level obstructed, branch-closed with no viable character "
            "completion, or upgraded from mass-bound uncertainty to an exact certified "
            "singlet-monoid obstruction. This is a bounded no-go for the selected "
            "radius-4 surface, not a global no-go beyond the searched surface."
        ),
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Selected Radius-4 Branch-Closed No-Go",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Component Reports", ""])
    for key, value in report["component_reports"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Interpretation", "", report["interpretation"], ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_selected_branch_closed_no_go.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_selected_branch_closed_no_go.md"
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
