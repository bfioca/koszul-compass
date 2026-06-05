#!/usr/bin/env python3
"""Aggregate selected radius-4 adjacency scout batch 2 windows."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

WINDOWS = [
    ("window1", "phenomenology_guided_q1_radius4_adjacency_scout_batch2_window1.json", "phenomenology_guided_q1_radius4_adjacency_scout_batch2_window1_verification.json"),
    ("window2", "phenomenology_guided_q1_radius4_adjacency_scout_batch2_window2.json", "phenomenology_guided_q1_radius4_adjacency_scout_batch2_window2_verification.json"),
    ("window3", "phenomenology_guided_q1_radius4_adjacency_scout_batch2_window3.json", "phenomenology_guided_q1_radius4_adjacency_scout_batch2_window3_verification.json"),
    ("window4", "phenomenology_guided_q1_radius4_adjacency_scout_batch2_window4.json", "phenomenology_guided_q1_radius4_adjacency_scout_batch2_window4_verification.json"),
    ("window5", "phenomenology_guided_q1_radius4_adjacency_scout_batch2_window5.json", "phenomenology_guided_q1_radius4_adjacency_scout_batch2_window5_verification.json"),
    ("window6", "phenomenology_guided_q1_radius4_adjacency_scout_batch2_window6.json", "phenomenology_guided_q1_radius4_adjacency_scout_batch2_window6_verification.json"),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def build_report() -> dict[str, Any]:
    totals: Counter[str] = Counter()
    categories: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    intervals = []
    summaries = []
    adjacency_counters = None
    frontier_size = None
    verifications_pass = True
    for label, report_name, verification_name in WINDOWS:
        report_path = REPORTS / report_name
        verification_path = REPORTS / verification_name
        report = load_json(report_path)
        verification = load_json(verification_path)
        verifications_pass = verifications_pass and verification["all_gates_pass"]
        if adjacency_counters is None:
            adjacency_counters = report["adjacency_counters"]
            frontier_size = report["adjacency_counters"]["within_charge_bound"]
        s = report["screening_counters"]
        intervals.append([s["frontier_start"], s["frontier_start"] + s["frontier_records_screened"]])
        for key, value in s.items():
            if isinstance(value, int) and key not in {
                "frontier_start",
                "frontier_records_before_window",
                "frontier_records_after_window",
                "frontier_records_unscreened",
            }:
                totals[key] += value
        categories.update(report["summary"]["categories"])
        statuses.update(report["summary"]["statuses"])
        summaries.append(
            {
                "label": label,
                "report": str(report_path),
                "verification": str(verification_path),
                "interval": intervals[-1],
                "summary": report["summary"],
            }
        )
    intervals = sorted(intervals)
    coverage_ok = (
        intervals[0][0] == 0
        and all(left[1] == right[0] for left, right in zip(intervals, intervals[1:]))
        and intervals[-1][1] == frontier_size
    )
    gates = {
        "window_verifications_pass": gate(
            verifications_pass,
            ", ".join(str(REPORTS / item[2]) for item in WINDOWS),
            "all batch-2 scout window verifications pass",
        ),
        "windows_cover_batch_frontier": gate(
            coverage_ok and frontier_size == 8743,
            "batch-2 radius-4 intervals",
            "windows cover the second selected source batch contiguously",
        ),
        "aggregate_counts_match": gate(
            totals["frontier_records_screened"] == 8743
            and totals["raw_q1_spectrum_survivors"] == 42
            and totals["character_certified_q1_survivors"] == 18,
            "batch-2 radius-4 counters",
            "window counters aggregate to expected batch-2 totals",
        ),
        "no_viable_candidate_found": gate(
            sum(item["summary"]["viable_count"] for item in summaries) == 0,
            "batch-2 radius-4 classifications",
            "no viable candidate appears in the second selected source batch",
        ),
    }
    return {
        "scope": "aggregate of selected radius-4 adjacency q=1 scout batch 2",
        "status": "no_viable_candidate_found_in_radius4_batch2_frontier",
        "source_batch": {"source_start": 16, "source_limit": 16},
        "adjacency_counters": adjacency_counters,
        "coverage": {
            "frontier_size": frontier_size,
            "covered_records": totals["frontier_records_screened"],
            "remaining_records": max(0, frontier_size - totals["frontier_records_screened"]),
            "intervals": intervals,
        },
        "aggregate_totals": dict(sorted(totals.items())),
        "aggregate_categories": dict(sorted(categories.items())),
        "aggregate_statuses": dict(sorted(statuses.items())),
        "viable_count": 0,
        "window_summaries": summaries,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Selected Radius-4 Batch 2 Aggregate",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
        f"- source batch: `{report['source_batch']}`",
        f"- coverage: `{report['coverage']}`",
        f"- aggregate totals: `{report['aggregate_totals']}`",
        f"- categories: `{report['aggregate_categories']}`",
        f"- statuses: `{report['aggregate_statuses']}`",
        f"- viable count: `{report['viable_count']}`",
        "",
        "## Windows",
        "",
    ]
    for item in report["window_summaries"]:
        lines.append(f"- `{item['label']}` interval `{item['interval']}`: `{item['summary']}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", default=str(REPORTS / "phenomenology_guided_q1_radius4_batch2_aggregate.json"))
    parser.add_argument("--md-out", default=str(REPORTS / "phenomenology_guided_q1_radius4_batch2_aggregate.md"))
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"coverage={report['coverage']}")
    print(f"aggregate_totals={report['aggregate_totals']}")
    print(f"categories={report['aggregate_categories']}")
    print(f"statuses={report['aggregate_statuses']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
