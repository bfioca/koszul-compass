#!/usr/bin/env python3
"""Summarize a closed radius-5 frontier source slice."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

DEFAULT_WINDOW_REPORTS = [
    REPORTS / "phenomenology_guided_q1_radius5_window1_closed_frontier.json",
    REPORTS / "phenomenology_guided_q1_radius5_window2_closed_frontier.json",
    REPORTS / "phenomenology_guided_q1_radius5_window3_closed_frontier.json",
]
DEFAULT_WINDOW_VERIFICATIONS = [
    REPORTS / "phenomenology_guided_q1_radius5_window1_closed_frontier_verification.json",
    REPORTS / "phenomenology_guided_q1_radius5_window2_closed_frontier_verification.json",
    REPORTS / "phenomenology_guided_q1_radius5_window3_closed_frontier_verification.json",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def branch_count(summary: dict[str, Any]) -> int:
    return int(
        summary.get(
            "bounded_branch_completions_evaluated",
            summary.get("branch_completions_evaluated", 0),
        )
    )


def first_summary_value(
    windows: list[dict[str, Any]], key: str, default: int
) -> int:
    for window in windows:
        if key in window["summary"]:
            return int(window["summary"][key])
    return default


def build_report(
    *,
    window_reports: list[Path],
    window_verifications: list[Path],
    window_label: str,
    title: str,
    status: str,
    scope: str,
) -> dict[str, Any]:
    windows = [load_json(path) for path in window_reports]
    verifications = [load_json(path) for path in window_verifications]
    statuses: Counter[str] = Counter()
    for window in windows:
        statuses.update(window["summary"]["adjusted_statuses"])

    summary = {
        "radius4_sources_available": first_summary_value(
            windows, "radius4_sources_available", 128
        ),
        "radius4_sources_selected": first_summary_value(
            windows, "radius4_sources_selected", 8
        ),
        "frontier_records_screened": sum(
            window["summary"]["frontier_records_screened"] for window in windows
        ),
        "frontier_records_after_final_window": windows[-1]["summary"][
            "frontier_records_after_window"
        ],
        "raw_q1_spectrum_survivors": sum(
            window["summary"]["raw_q1_spectrum_survivors"] for window in windows
        ),
        "character_certified_q1_survivors": sum(
            window["summary"].get("character_certified_q1_survivors", 0)
            for window in windows
        ),
        "bounded_branch_completions_evaluated": sum(
            branch_count(window["summary"]) for window in windows
        ),
        "large_branch_completions_counted": sum(
            window["summary"].get("large_branch_completions_counted", 0)
            for window in windows
        ),
        "desired_q1_branch_completions": sum(
            window["summary"]["desired_q1_branch_completions"] for window in windows
        ),
        "viable_count": sum(window["summary"]["viable_count"] for window in windows),
        "adjusted_statuses": dict(sorted(statuses.items())),
    }
    gates = {
        "all_window_verifications_pass": gate(
            all(item["all_gates_pass"] for item in verifications),
            ", ".join(str(path) for path in window_verifications),
            "all radius5 source-slice window closures are verified",
        ),
        "frontier_exhausted_for_source_slice": gate(
            summary["frontier_records_after_final_window"] == 0,
            ", ".join(str(path) for path in window_reports),
            f"the {window_label} radius5 source slice has no unscreened frontier records",
        ),
        "no_viable_candidate": gate(
            summary["viable_count"] == 0,
            "radius5 source-slice adjusted classifications",
            "no window in this source slice contains a viable candidate",
        ),
    }
    return {
        "scope": scope,
        "status": status,
        "summary": summary,
        "window_reports": [str(path) for path in window_reports],
        "interpretation": (
            f"The {window_label} prioritized radius5 source slice is closed. It produces new q=1 "
            "survivors and many target q=1 branch completions, but all are rejected by "
            "the current 5259-derived charge-level filter."
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
    lines.extend(["", "## Window Reports", ""])
    for item in report["window_reports"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Interpretation", "", report["interpretation"], ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--window-report",
        action="append",
        default=None,
        help="Closed-frontier window JSON. Repeat once per window.",
    )
    parser.add_argument(
        "--window-verification",
        action="append",
        default=None,
        help="Closed-frontier window verification JSON. Repeat once per window.",
    )
    parser.add_argument(
        "--window-label",
        default="first",
    )
    parser.add_argument(
        "--title",
        default="Radius-5 Source Slice Closed Frontier",
    )
    parser.add_argument(
        "--status",
        default="radius5_source_slice_0_8_closed_no_viable_candidate",
    )
    parser.add_argument(
        "--scope",
        default="closed radius5 frontier for first eight prioritized radius4 q1 sources",
    )
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_source_slice_closed_frontier.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_source_slice_closed_frontier.md"),
    )
    args = parser.parse_args()
    window_reports = [Path(item) for item in (args.window_report or DEFAULT_WINDOW_REPORTS)]
    window_verifications = [
        Path(item) for item in (args.window_verification or DEFAULT_WINDOW_VERIFICATIONS)
    ]
    if len(window_reports) != len(window_verifications):
        raise SystemExit("--window-report and --window-verification counts must match")
    report = build_report(
        window_reports=window_reports,
        window_verifications=window_verifications,
        window_label=args.window_label,
        title=args.title,
        status=args.status,
        scope=args.scope,
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
