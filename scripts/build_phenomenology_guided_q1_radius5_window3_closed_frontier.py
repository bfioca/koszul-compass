#!/usr/bin/env python3
"""Summarize a radius-5 window after bounded and large-branch closure."""

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


def build_report(
    *,
    scout_json: Path,
    branch_json: Path,
    large_jsons: list[Path],
    title: str,
    status: str,
    scope: str,
    expected_raw_q1: int | None,
    expected_unresolved: int | None,
) -> dict[str, Any]:
    scout = load_json(scout_json)
    branch = load_json(branch_json)
    large_reports = [load_json(path) for path in large_jsons]
    adjusted_statuses = Counter(branch["summary"]["statuses"])
    for large in large_reports:
        adjusted_statuses.update(
            {
                large["summary"]["q1_representative_status"]: large["summary"][
                    "desired_q1_branches"
                ],
                "rejected_spectrum_signature_not_q1_three_family": large["summary"][
                    "not_desired_q1_branches"
                ],
            }
        )
    gates = {
        "imports_radius5_scout": gate(
            scout["all_gates_pass"]
            and (
                expected_raw_q1 is None
                or scout["summary"]["raw_q1_spectrum_survivors"] == expected_raw_q1
            )
            and scout["summary"]["viable_count"] == 0,
            str(scout_json),
            "window closure starts from the verified radius5 scout",
        ),
        "imports_bounded_branch_closure": gate(
            branch["all_gates_pass"]
            and (
                expected_unresolved is None
                or branch["summary"]["unresolved_records"] == expected_unresolved
            )
            and branch["summary"]["records_skipped"] >= 1
            and branch["summary"]["viable_branches"] == 0,
            str(branch_json),
            "bounded branch closure handles non-large missing-character records",
        ),
        "imports_large_branch_closure": gate(
            bool(large_reports)
            and all(
                large["all_gates_pass"]
                and large["summary"]["viable_q1_branches"] == 0
                for large in large_reports
            ),
            ", ".join(str(path) for path in large_jsons),
            "large skipped records are closed by aggregate support-invariant q1 representatives",
        ),
        "no_viable_candidate": gate(
            branch["summary"]["viable_branches"] == 0
            and all(large["summary"]["viable_q1_branches"] == 0 for large in large_reports),
            "radius5 window3 branch closures",
            "no bounded or large branch q1 completion is viable",
        ),
    }
    return {
        "scope": scope,
        "status": status,
        "summary": {
            "frontier_records_screened": scout["screening_counters"][
                "frontier_records_screened"
            ],
            "frontier_records_after_window": scout["screening_counters"][
                "frontier_records_after_window"
            ],
            "raw_q1_spectrum_survivors": scout["summary"][
                "raw_q1_spectrum_survivors"
            ],
            "missing_character_records": scout["summary"]["statuses"][
                "missing_character_or_charge_level_data"
            ],
            "bounded_records_evaluated": branch["summary"]["records_evaluated"],
            "large_records_closed": branch["summary"]["records_skipped"],
            "bounded_branch_completions_evaluated": branch["summary"][
                "branches_evaluated"
            ],
            "large_branch_completions_counted": sum(
                large["summary"]["total_branches"] for large in large_reports
            ),
            "desired_q1_branch_completions": branch["summary"]["desired_q1_branches"]
            + sum(large["summary"]["desired_q1_branches"] for large in large_reports),
            "viable_count": 0,
            "adjusted_statuses": dict(sorted(adjusted_statuses.items())),
        },
        "interpretation": (
            "This radius5 window is closed: non-large missing-character records are closed by "
            "bounded branch enumeration, and the large branch is closed at aggregate "
            "support-invariant level. No q=1 completion passes the charge-level filter."
        ),
        "title": title,
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
    lines.extend(["", "## Interpretation", "", report["interpretation"], ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scout-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_adjacency_scout_window3.json"),
    )
    parser.add_argument(
        "--branch-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_branch_analysis_window3.json"),
    )
    parser.add_argument(
        "--large-json",
        action="append",
        default=None,
    )
    parser.add_argument("--title", default="Radius-5 Window 3 Closed Frontier")
    parser.add_argument("--status", default="radius5_window3_branch_closed_no_viable_candidate")
    parser.add_argument("--scope", default="radius5 window3 closed frontier")
    parser.add_argument("--expected-raw-q1", type=int, default=None)
    parser.add_argument("--expected-unresolved", type=int, default=None)
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_window3_closed_frontier.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_window3_closed_frontier.md"),
    )
    args = parser.parse_args()
    report = build_report(
        scout_json=Path(args.scout_json),
        branch_json=Path(args.branch_json),
        large_jsons=[
            Path(item)
            for item in (
                args.large_json
                or [str(REPORTS / "phenomenology_guided_q1_radius5_window3_large_branch_closure.json")]
            )
        ],
        title=args.title,
        status=args.status,
        scope=args.scope,
        expected_raw_q1=args.expected_raw_q1,
        expected_unresolved=args.expected_unresolved,
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
