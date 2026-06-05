#!/usr/bin/env python3
"""Aggregate bounded radius-3 adjacency scout windows."""

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
        "phenomenology_guided_q1_radius3_adjacency_scout.json",
        "phenomenology_guided_q1_radius3_adjacency_scout_verification.json",
    ),
    (
        "window2",
        "phenomenology_guided_q1_radius3_adjacency_scout_window2.json",
        "phenomenology_guided_q1_radius3_adjacency_scout_window2_verification.json",
    ),
    (
        "window3",
        "phenomenology_guided_q1_radius3_adjacency_scout_window3.json",
        "phenomenology_guided_q1_radius3_adjacency_scout_window3_verification.json",
    ),
    (
        "window4",
        "phenomenology_guided_q1_radius3_adjacency_scout_window4.json",
        "phenomenology_guided_q1_radius3_adjacency_scout_window4_verification.json",
    ),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def build_report() -> dict[str, Any]:
    summaries = []
    totals: Counter[str] = Counter()
    categories: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    intervals = []
    verified = []
    frontier_size = None
    adjacency_counters = None

    for label, report_name, verification_name in WINDOWS:
        report_path = REPORTS / report_name
        verification_path = REPORTS / verification_name
        report = load_json(report_path)
        verification = load_json(verification_path)
        screening = report["screening_counters"]
        summary = report["summary"]
        start = screening["frontier_start"]
        screened = screening["frontier_records_screened"]
        interval = [start, start + screened]
        intervals.append(interval)
        verified.append(verification["all_gates_pass"])
        if frontier_size is None:
            frontier_size = report["adjacency_counters"]["within_charge_bound"]
        if adjacency_counters is None:
            adjacency_counters = report["adjacency_counters"]

        for key in [
            "frontier_records_screened",
            "c1_survivors",
            "index_survivors",
            "anomaly_survivors",
            "slope_survivors",
            "spectrum_survivors",
            "raw_q1_spectrum_survivors",
            "raw_q1_certification_attempts",
            "character_certified_q1_survivors",
            "cohomology_exceptions",
            "topology_exceptions",
        ]:
            totals[key] += screening[key]
        totals["viable_count"] += summary["viable_count"]
        categories.update(summary["categories"])
        statuses.update(summary["statuses"])
        summaries.append(
            {
                "label": label,
                "report": str(report_path),
                "verification": str(verification_path),
                "verification_passed": verification["all_gates_pass"],
                "interval": interval,
                "screening_counters": screening,
                "summary": summary,
            }
        )

    intervals = sorted(intervals)
    covered = sum(end - start for start, end in intervals)
    gates = {
        "window_verifications_pass": gate(
            all(verified),
            ", ".join(str(REPORTS / item[2]) for item in WINDOWS),
            "all imported radius-3 scout window verifications pass",
        ),
        "windows_are_contiguous": gate(
            intervals == [[0, 4000], [4000, 8000], [8000, 12000], [12000, 15595]],
            ", ".join(str(REPORTS / item[1]) for item in WINDOWS),
            "radius-3 adjacency windows cover the full bounded frontier contiguously",
        ),
        "aggregate_counts_match": gate(
            dict(sorted(totals.items()))
            == {
                "anomaly_survivors": 2634,
                "c1_survivors": 15595,
                "character_certified_q1_survivors": 32,
                "cohomology_exceptions": 1,
                "frontier_records_screened": 15595,
                "index_survivors": 2951,
                "raw_q1_certification_attempts": 64,
                "raw_q1_spectrum_survivors": 64,
                "slope_survivors": 1257,
                "spectrum_survivors": 711,
                "topology_exceptions": 0,
                "viable_count": 0,
            },
            ", ".join(str(REPORTS / item[1]) for item in WINDOWS),
            "first two window counters aggregate to the expected sweep totals",
        ),
        "no_viable_candidate_found": gate(
            totals["viable_count"] == 0
            and categories == {"phenomenologically obstructed": 30, "unresolved": 34},
            "radius-3 adjacency filtered records",
            "no viable candidate was found in the full bounded radius-3 adjacency frontier",
        ),
    }

    return {
        "scope": "aggregate of bounded radius-3 adjacency q=1 scout windows",
        "status": "no_viable_candidate_found_in_full_radius3_adjacency_frontier",
        "adjacency_counters": adjacency_counters,
        "coverage": {
            "frontier_size": frontier_size,
            "intervals": intervals,
            "covered_records": covered,
            "remaining_records": frontier_size - covered if frontier_size is not None else None,
        },
        "aggregate_totals": dict(sorted(totals.items())),
        "aggregate_categories": dict(sorted(categories.items())),
        "aggregate_statuses": dict(sorted(statuses.items())),
        "window_summaries": summaries,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-3 Adjacency Scout Aggregate",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Coverage",
        "",
        f"- intervals: `{report['coverage']['intervals']}`",
        f"- covered records: `{report['coverage']['covered_records']}`",
        f"- remaining records: `{report['coverage']['remaining_records']}`",
        f"- adjacency counters: `{report['adjacency_counters']}`",
        "",
        "## Aggregate Counts",
        "",
        f"- totals: `{report['aggregate_totals']}`",
        f"- categories: `{report['aggregate_categories']}`",
        f"- statuses: `{report['aggregate_statuses']}`",
        "",
        "## Window Summary",
        "",
    ]
    for item in report["window_summaries"]:
        lines.append(
            "- "
            f"`{item['label']}` interval `{item['interval']}`: "
            f"raw q=1 `{item['screening_counters']['raw_q1_spectrum_survivors']}`, "
            f"character-certified `{item['screening_counters']['character_certified_q1_survivors']}`, "
            f"viable `{item['summary']['viable_count']}`, "
            f"statuses `{item['summary']['statuses']}`"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_adjacency_aggregate.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_adjacency_aggregate.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"coverage={report['coverage']}")
    print(f"totals={report['aggregate_totals']}")
    print(f"categories={report['aggregate_categories']}")
    print(f"statuses={report['aggregate_statuses']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
