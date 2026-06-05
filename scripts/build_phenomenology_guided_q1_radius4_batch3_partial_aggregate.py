#!/usr/bin/env python3
"""Aggregate verified batch-3 radius-4 scout windows completed so far."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

WINDOWS = [
    (
        "window1",
        REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch3_window1.json",
        REPORTS
        / "phenomenology_guided_q1_radius4_adjacency_scout_batch3_window1_verification.json",
        REPORTS
        / "phenomenology_guided_q1_radius4_batch3_window1_known_line_resolved.json",
        REPORTS
        / "phenomenology_guided_q1_radius4_batch3_window1_known_line_resolved_verification.json",
    ),
    (
        "window2",
        REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch3_window2.json",
        REPORTS
        / "phenomenology_guided_q1_radius4_adjacency_scout_batch3_window2_verification.json",
        None,
        None,
    ),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def build_report() -> dict[str, Any]:
    totals: Counter[str] = Counter()
    initial_categories: Counter[str] = Counter()
    initial_statuses: Counter[str] = Counter()
    final_categories: Counter[str] = Counter()
    final_statuses: Counter[str] = Counter()
    intervals = []
    summaries = []
    frontier_size = None
    adjacency_counters = None
    all_verifications_pass = True
    for label, report_path, verification_path, known_path, known_verification_path in WINDOWS:
        report = load_json(report_path)
        verification = load_json(verification_path)
        all_verifications_pass = all_verifications_pass and verification["all_gates_pass"]
        if known_path is not None:
            known = load_json(known_path)
            known_verification = load_json(known_verification_path)
            all_verifications_pass = (
                all_verifications_pass and known["all_gates_pass"] and known_verification["all_gates_pass"]
            )
        else:
            known = None
        if adjacency_counters is None:
            adjacency_counters = report["adjacency_counters"]
            frontier_size = report["adjacency_counters"]["within_charge_bound"]
        screening = report["screening_counters"]
        intervals.append(
            [screening["frontier_start"], screening["frontier_start"] + screening["frontier_records_screened"]]
        )
        for key, value in screening.items():
            if isinstance(value, int) and key not in {
                "frontier_start",
                "frontier_records_before_window",
                "frontier_records_after_window",
                "frontier_records_unscreened",
            }:
                totals[key] += value
        initial_categories.update(report["summary"]["categories"])
        initial_statuses.update(report["summary"]["statuses"])
        if known is None:
            final_categories.update(report["summary"]["categories"])
            final_statuses.update(report["summary"]["statuses"])
        else:
            final_categories.update(known["summary"]["categories"])
            final_statuses.update(known["summary"]["statuses"])
            final_categories.update(
                {
                    "phenomenologically obstructed": report["summary"]["categories"].get(
                        "phenomenologically obstructed", 0
                    )
                }
            )
            final_statuses.update(report["summary"]["statuses"])
            final_statuses.subtract({"missing_character_or_charge_level_data": known["summary"]["attempted_unresolved_records"]})
        summaries.append(
            {
                "label": label,
                "report": str(report_path),
                "verification": str(verification_path),
                "known_line_report": str(known_path) if known_path is not None else None,
                "interval": intervals[-1],
                "initial_summary": report["summary"],
                "known_line_summary": known["summary"] if known is not None else None,
            }
        )

    intervals = sorted(intervals)
    covered = sum(right - left for left, right in intervals)
    gates = {
        "window_verifications_pass": gate(
            all_verifications_pass,
            ", ".join(str(item[2]) for item in WINDOWS),
            "all completed batch-3 scout and known-line verifications pass",
        ),
        "windows_are_contiguous_prefix": gate(
            intervals == [[0, 1600], [1600, 3200]],
            "batch-3 completed intervals",
            "completed windows form the first contiguous prefix of the batch-3 frontier",
        ),
        "counts_match_completed_windows": gate(
            totals["frontier_records_screened"] == 3200
            and totals["raw_q1_spectrum_survivors"] == 24
            and totals["raw_q1_certification_attempts"] == 24
            and totals["character_certified_q1_survivors"] == 23,
            "batch-3 completed window counters",
            "completed batch-3 windows preserve scout counts",
        ),
        "known_line_closes_window1_gap": gate(
            dict(+final_categories) == {"phenomenologically obstructed": 24}
            and dict(+final_statuses)
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 11,
                "negative_control_doublet_triplet_obstruction": 13,
            },
            "batch-3 partial final classifications",
            "known-line resolution closes the only completed-window character gap",
        ),
    }
    return {
        "scope": "partial aggregate for completed batch-3 selected radius-4 windows",
        "status": "batch3_partial_no_viable_candidate_found",
        "source_batch": {"source_start": 32, "source_limit": 16},
        "adjacency_counters": adjacency_counters,
        "coverage": {
            "frontier_size": frontier_size,
            "covered_records": covered,
            "remaining_records": max(0, frontier_size - covered),
            "intervals": intervals,
        },
        "aggregate_totals": dict(sorted(totals.items())),
        "initial_categories": dict(+initial_categories),
        "initial_statuses": dict(+initial_statuses),
        "final_categories_after_known_line": dict(+final_categories),
        "final_statuses_after_known_line": dict(+final_statuses),
        "viable_count": 0,
        "window_summaries": summaries,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Selected Radius-4 Batch 3 Partial Aggregate",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- source batch: `{report['source_batch']}`",
        f"- coverage: `{report['coverage']}`",
        f"- aggregate totals: `{report['aggregate_totals']}`",
        f"- initial categories: `{report['initial_categories']}`",
        f"- final categories after known-line: `{report['final_categories_after_known_line']}`",
        f"- final statuses after known-line: `{report['final_statuses_after_known_line']}`",
        f"- viable count: `{report['viable_count']}`",
        "",
        "## Windows",
        "",
    ]
    for item in report["window_summaries"]:
        lines.append(
            f"- `{item['label']}` interval `{item['interval']}`: "
            f"initial `{item['initial_summary']}`; known-line `{item['known_line_summary']}`"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_batch3_partial_aggregate.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_batch3_partial_aggregate.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"coverage={report['coverage']}")
    print(f"final_categories={report['final_categories_after_known_line']}")
    print(f"final_statuses={report['final_statuses_after_known_line']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
