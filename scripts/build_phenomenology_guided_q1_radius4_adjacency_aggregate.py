#!/usr/bin/env python3
"""Aggregate bounded radius-4 adjacency scout windows."""

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
        "phenomenology_guided_q1_radius4_adjacency_scout.json",
        "phenomenology_guided_q1_radius4_adjacency_scout_verification.json",
    ),
    (
        "window2",
        "phenomenology_guided_q1_radius4_adjacency_scout_window2.json",
        "phenomenology_guided_q1_radius4_adjacency_scout_window2_verification.json",
    ),
    (
        "window3",
        "phenomenology_guided_q1_radius4_adjacency_scout_window3.json",
        "phenomenology_guided_q1_radius4_adjacency_scout_window3_verification.json",
    ),
    (
        "window4",
        "phenomenology_guided_q1_radius4_adjacency_scout_window4.json",
        "phenomenology_guided_q1_radius4_adjacency_scout_window4_verification.json",
    ),
    (
        "window5",
        "phenomenology_guided_q1_radius4_adjacency_scout_window5.json",
        "phenomenology_guided_q1_radius4_adjacency_scout_window5_verification.json",
    ),
    (
        "window6",
        "phenomenology_guided_q1_radius4_adjacency_scout_window6.json",
        "phenomenology_guided_q1_radius4_adjacency_scout_window6_verification.json",
    ),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def build_report() -> dict[str, Any]:
    window_summaries = []
    intervals = []
    categories: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    totals: Counter[str] = Counter()
    all_records: list[dict[str, Any]] = []
    adjacency_counters = None
    frontier_size = None

    for label, report_name, verification_name in WINDOWS:
        report_path = REPORTS / report_name
        verification_path = REPORTS / verification_name
        report = load_json(report_path)
        verification = load_json(verification_path)
        start = report["screening_counters"]["frontier_start"]
        screened = report["screening_counters"]["frontier_records_screened"]
        intervals.append([start, start + screened])
        if adjacency_counters is None:
            adjacency_counters = report["adjacency_counters"]
            frontier_size = report["adjacency_counters"]["within_charge_bound"]
        for key, value in report["screening_counters"].items():
            if isinstance(value, int) and key not in {
                "frontier_start",
                "frontier_records_before_window",
                "frontier_records_after_window",
                "frontier_records_unscreened",
            }:
                totals[key] += value
        categories.update(report["summary"]["categories"])
        statuses.update(report["summary"]["statuses"])
        all_records.extend(report["filtered_candidate_records"])
        window_summaries.append(
            {
                "label": label,
                "report": str(report_path),
                "verification": str(verification_path),
                "interval": [start, start + screened],
                "screening_counters": report["screening_counters"],
                "summary": report["summary"],
                "verification_passed": verification["all_gates_pass"],
            }
        )

    intervals_sorted = sorted(intervals)
    coverage_ok = (
        intervals_sorted
        and intervals_sorted[0][0] == 0
        and all(
            left[1] == right[0]
            for left, right in zip(intervals_sorted, intervals_sorted[1:])
        )
        and intervals_sorted[-1][1] == frontier_size
    )
    viable_count = sum(
        1
        for record in all_records
        if record["classification"]["category"] == "viable"
    )
    unresolved_records = [
        {
            "window": next(
                item["label"]
                for item in window_summaries
                if item["interval"][0]
                <= record.get("_aggregate_window_start", item["interval"][0])
                < item["interval"][1]
            )
            if False
            else None,
            "label": record["label"],
            "source": record.get("radius4_source_raw_candidate_key"),
            "status": record["classification"]["status"],
            "vectorlike_prediction": record["spectrum_certificate"][
                "vectorlike_prediction"
            ],
        }
        for record in all_records
        if record["classification"]["category"] == "unresolved"
    ]

    gates = {
        "window_verifications_pass": gate(
            all(item["verification_passed"] for item in window_summaries),
            ", ".join(str(REPORTS / item[2]) for item in WINDOWS),
            "all imported radius-4 scout window verifications pass",
        ),
        "windows_are_contiguous": gate(
            coverage_ok,
            "radius-4 selected frontier intervals",
            "windows cover the selected bounded frontier contiguously",
        ),
        "aggregate_counts_match": gate(
            totals["frontier_records_screened"] == frontier_size == 8733
            and totals["raw_q1_spectrum_survivors"] == len(all_records) == 49
            and totals["raw_q1_certification_attempts"] == len(all_records)
            and totals["character_certified_q1_survivors"] == 28,
            "radius-4 selected frontier filtered records",
            "window counters aggregate to the selected radius-4 sweep totals",
        ),
        "no_viable_candidate_found": gate(
            viable_count == 0,
            "radius-4 selected frontier filtered records",
            "no viable candidate was found in the selected bounded radius-4 frontier",
        ),
    }
    return {
        "scope": "aggregate of selected bounded radius-4 adjacency q=1 scout windows",
        "status": "no_viable_candidate_found_in_selected_radius4_adjacency_frontier",
        "adjacency_counters": adjacency_counters,
        "coverage": {
            "frontier_size": frontier_size,
            "covered_records": totals["frontier_records_screened"],
            "remaining_records": max(0, frontier_size - totals["frontier_records_screened"]),
            "intervals": intervals_sorted,
        },
        "aggregate_totals": dict(sorted(totals.items())),
        "aggregate_categories": dict(sorted(categories.items())),
        "aggregate_statuses": dict(sorted(statuses.items())),
        "viable_count": viable_count,
        "unresolved_records": unresolved_records,
        "window_summaries": window_summaries,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Selected Radius-4 Adjacency Aggregate",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Coverage",
        "",
        f"- coverage: `{report['coverage']}`",
        f"- adjacency counters: `{report['adjacency_counters']}`",
        "",
        "## Totals",
        "",
        f"- aggregate totals: `{report['aggregate_totals']}`",
        f"- categories: `{report['aggregate_categories']}`",
        f"- statuses: `{report['aggregate_statuses']}`",
        f"- viable count: `{report['viable_count']}`",
        "",
        "## Windows",
        "",
    ]
    for item in report["window_summaries"]:
        lines.append(
            f"- `{item['label']}` interval `{item['interval']}`: "
            f"`{item['summary']}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The selected radius-4 frontier expands the first 16 prioritized "
                "strict radius-3 q=1 obstruction records by one primitive move. "
                "It is closed for this selected source set and contains no viable "
                "candidate under the 5259-derived charge-level filter."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_adjacency_aggregate.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_adjacency_aggregate.md"),
    )
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
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
