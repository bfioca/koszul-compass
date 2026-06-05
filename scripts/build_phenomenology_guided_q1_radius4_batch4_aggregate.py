#!/usr/bin/env python3
"""Aggregate the selected radius-4 batch-4 scout sweep."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

WINDOWS = [
    (f"window{i}", REPORTS / f"phenomenology_guided_q1_radius4_adjacency_scout_batch4_window{i}.json", REPORTS / f"phenomenology_guided_q1_radius4_adjacency_scout_batch4_window{i}_verification.json")
    for i in range(1, 7)
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
    all_verifications_pass = True
    for label, report_path, verification_path in WINDOWS:
        report = load_json(report_path)
        verification = load_json(verification_path)
        all_verifications_pass = all_verifications_pass and verification["all_gates_pass"]
        if adjacency_counters is None:
            adjacency_counters = report["adjacency_counters"]
            frontier_size = report["adjacency_counters"]["within_charge_bound"]
        screening = report["screening_counters"]
        intervals.append([screening["frontier_start"], screening["frontier_start"] + screening["frontier_records_screened"]])
        for key, value in screening.items():
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
    gates = {
        "window_verifications_pass": gate(
            all_verifications_pass,
            ", ".join(str(item[2]) for item in WINDOWS),
            "all batch-4 scout window verifications pass",
        ),
        "windows_cover_batch_frontier": gate(
            intervals == [[0, 1600], [1600, 3200], [3200, 4800], [4800, 6400], [6400, 8000], [8000, 8269]],
            "batch-4 intervals",
            "windows cover the full selected batch-4 frontier contiguously",
        ),
        "aggregate_counts_match": gate(
            totals["frontier_records_screened"] == 8269
            and totals["raw_q1_spectrum_survivors"] == 48
            and totals["raw_q1_certification_attempts"] == 48
            and totals["character_certified_q1_survivors"] == 9,
            "batch-4 window counters",
            "window counters aggregate to expected batch-4 totals",
        ),
        "no_viable_candidate_found": gate(
            categories == {"phenomenologically obstructed": 9, "unresolved": 39}
            and statuses
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 4,
                "missing_character_or_charge_level_data": 39,
                "negative_control_doublet_triplet_obstruction": 5,
            },
            "batch-4 scout classifications",
            "no viable candidate appears in the full batch-4 scout sweep",
        ),
    }
    return {
        "scope": "aggregate of selected radius-4 adjacency q=1 scout batch 4",
        "status": "no_viable_candidate_found_in_radius4_batch4_scout_frontier",
        "source_batch": {"source_start": 48, "source_limit": 16, "actual_source_records": 15},
        "adjacency_counters": adjacency_counters,
        "coverage": {
            "frontier_size": frontier_size,
            "covered_records": totals["frontier_records_screened"],
            "remaining_records": max(0, frontier_size - totals["frontier_records_screened"]),
            "intervals": intervals,
        },
        "aggregate_totals": dict(sorted(totals.items())),
        "categories": dict(sorted(categories.items())),
        "statuses": dict(sorted(statuses.items())),
        "viable_count": 0,
        "window_summaries": summaries,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Selected Radius-4 Batch 4 Scout Aggregate",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- source batch: `{report['source_batch']}`",
        f"- coverage: `{report['coverage']}`",
        f"- aggregate totals: `{report['aggregate_totals']}`",
        f"- categories: `{report['categories']}`",
        f"- statuses: `{report['statuses']}`",
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
    parser.add_argument("--json-out", default=str(REPORTS / "phenomenology_guided_q1_radius4_batch4_aggregate.json"))
    parser.add_argument("--md-out", default=str(REPORTS / "phenomenology_guided_q1_radius4_batch4_aggregate.md"))
    args = parser.parse_args()
    report = build_report()
    Path(args.json_out).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, Path(args.md_out))
    print(f"status={report['status']}")
    print(f"coverage={report['coverage']}")
    print(f"categories={report['categories']}")
    print(f"statuses={report['statuses']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
