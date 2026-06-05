#!/usr/bin/env python3
"""Summarize selected radius-4 frontier after bounded branch analysis."""

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
    current = load_json(REPORTS / "phenomenology_guided_q1_radius4_current_frontier.json")
    branches = load_json(REPORTS / "phenomenology_guided_q1_radius4_unresolved_branch_analysis.json")
    large = load_json(REPORTS / "phenomenology_guided_q1_radius4_large_branch_closure.json")
    branch_exhausted_records = [
        record for record in branches["record_branch_reports"] if not record["skipped"]
    ]
    skipped = branches["skipped_records"]
    gates = {
        "imports_current_frontier": gate(
            current["all_gates_pass"]
            and current["summary"]["current_obstructed_count"] == 35
            and current["summary"]["current_unresolved_count"] == 14,
            str(REPORTS / "phenomenology_guided_q1_radius4_current_frontier.json"),
            "branch-enhanced frontier starts from verified current selected radius-4 frontier",
        ),
        "imports_branch_analysis": gate(
            branches["all_gates_pass"]
            and branches["summary"]["records_evaluated"] == 13
            and branches["summary"]["records_skipped"] == 1
            and branches["summary"]["viable_branches"] == 0,
            str(REPORTS / "phenomenology_guided_q1_radius4_unresolved_branch_analysis.json"),
            "branch-enhanced frontier imports bounded branch analysis with no viable branch",
        ),
        "imports_large_branch_closure": gate(
            large["all_gates_pass"]
            and large["status"] == "large_branch_all_q1_completions_obstructed"
            and large["summary"]["viable_q1_branches"] == 0,
            str(REPORTS / "phenomenology_guided_q1_radius4_large_branch_closure.json"),
            "the sole skipped large branch is closed at aggregate q=1 support level",
        ),
        "accounting_matches": gate(
            current["summary"]["current_obstructed_count"]
            + len(branch_exhausted_records)
            + len(skipped)
            == current["summary"]["raw_q1_spectrum_survivors"]
            == 49,
            "selected radius-4 branch-enhanced accounting",
            "all selected radius-4 raw q=1 survivors are strict-obstructed, branch-exhausted, or skipped-unresolved",
        ),
    }
    return {
        "scope": "branch-enhanced selected radius-4 q=1 frontier",
        "status": "no_viable_candidate_found_selected_radius4_frontier_branch_closed",
        "summary": {
            "raw_q1_spectrum_survivors": 49,
            "strict_obstructed_count": current["summary"]["current_obstructed_count"],
            "branch_exhausted_nonviable_records": len(branch_exhausted_records),
            "large_branch_closed_records": 1,
            "large_branch_desired_q1_branches": large["summary"][
                "desired_q1_branches"
            ],
            "effective_viable_count": 0,
            "branches_evaluated": branches["summary"]["branches_evaluated"],
            "desired_q1_branches": branches["summary"]["desired_q1_branches"],
            "viable_branches": branches["summary"]["viable_branches"],
            "branch_statuses": branches["summary"]["statuses"],
        },
        "branch_exhausted_records": [
            {
                "label": record["label"],
                "branches_evaluated": record["branches_evaluated"],
                "desired_q1_branches": record["desired_q1_branches"],
                "statuses": record["statuses"],
            }
            for record in branch_exhausted_records
        ],
        "large_branch_closure": {
            "source": skipped,
            "closure_summary": large["summary"],
            "representative_classification": large["q1_representative_candidate"][
                "classification"
            ],
        },
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Branch-Enhanced Selected Radius-4 Frontier",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Branch-Exhausted Records", ""])
    for record in report["branch_exhausted_records"]:
        lines.append(
            f"- `{record['label']}`: branches `{record['branches_evaluated']}`, "
            f"desired-q1 `{record['desired_q1_branches']}`, statuses `{record['statuses']}`"
        )
    lines.extend(["", "## Large Branch Closure", ""])
    lines.append(f"- closure: `{report['large_branch_closure']['closure_summary']}`")
    lines.append(
        "- representative classification: "
        f"`{report['large_branch_closure']['representative_classification']}`"
    )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The selected radius-4 frontier has no viable candidate under strict "
                "certification, bounded dimension-compatible branch completion, or "
                "aggregate closure of the large branch. No selected radius-4 q=1 "
                "survivor passes the 5259-derived charge-level filter."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_branch_enhanced_frontier.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_branch_enhanced_frontier.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
