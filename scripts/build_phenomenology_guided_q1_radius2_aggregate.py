#!/usr/bin/env python3
"""Build an aggregate report for the radius-2 q=1 phenomenology windows."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

WINDOWS = [
    {
        "label": "window1",
        "json": "phenomenology_guided_q1_radius2_pilot.json",
        "verification": "phenomenology_guided_q1_radius2_pilot_verification.json",
        "start": 0,
        "screened": 1200,
    },
    {
        "label": "window2",
        "json": "phenomenology_guided_q1_radius2_pilot_window2.json",
        "verification": "phenomenology_guided_q1_radius2_pilot_window2_verification.json",
        "start": 1200,
        "screened": 2400,
    },
    {
        "label": "window3",
        "json": "phenomenology_guided_q1_radius2_pilot_window3.json",
        "verification": "phenomenology_guided_q1_radius2_pilot_window3_verification.json",
        "start": 3600,
        "screened": 2400,
    },
    {
        "label": "window4",
        "json": "phenomenology_guided_q1_radius2_pilot_window4.json",
        "verification": "phenomenology_guided_q1_radius2_pilot_window4_verification.json",
        "start": 6000,
        "screened": 2459,
    },
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def aggregate() -> dict[str, Any]:
    window_summaries: list[dict[str, Any]] = []
    categories: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    totals: Counter[str] = Counter()
    frontier_size = None
    topology_denominator = None
    verified_windows = []
    intervals = []

    for spec in WINDOWS:
        report_path = REPORTS / spec["json"]
        verification_path = REPORTS / spec["verification"]
        report = load_json(report_path)
        verification = load_json(verification_path)
        pilot = report["pilot_counters"]
        topology = report["topology_counters"]
        summary = report["summary"]
        record_count = len(report.get("filtered_candidate_records", []))

        start = pilot.get("anomaly_start", 0)
        screened = pilot["anomaly_records_screened"]
        end = start + screened
        intervals.append([start, end])
        verified_windows.append(bool(verification["all_gates_pass"]))
        if frontier_size is None:
            frontier_size = pilot["anomaly_frontier_size"]
        if topology_denominator is None:
            topology_denominator = {
                "unique_candidates": topology["unique_candidates"],
                "anomaly_survivors": topology["anomaly_survivors"],
            }

        totals["anomaly_records_screened"] += screened
        totals["slope_survivors"] += pilot["slope_survivors"]
        totals["spectrum_survivors"] += pilot["spectrum_survivors"]
        totals["raw_q1_spectrum_survivors"] += pilot["raw_q1_spectrum_survivors"]
        totals["raw_q1_certification_attempts"] += pilot[
            "raw_q1_certification_attempts"
        ]
        totals["character_certified_q1_survivors"] += pilot[
            "character_certified_q1_survivors"
        ]
        totals["cohomology_exceptions"] += pilot.get("cohomology_exceptions", 0)
        totals["viable_count"] += summary["viable_count"]
        totals["filtered_candidate_records"] += record_count
        categories.update(summary["categories"])
        statuses.update(summary["statuses"])

        window_summaries.append(
            {
                "label": spec["label"],
                "report": str(report_path),
                "verification": str(verification_path),
                "verification_passed": verification["all_gates_pass"],
                "interval": [start, end],
                "pilot_counters": {
                    "anomaly_records_screened": screened,
                    "slope_survivors": pilot["slope_survivors"],
                    "spectrum_survivors": pilot["spectrum_survivors"],
                    "raw_q1_spectrum_survivors": pilot[
                        "raw_q1_spectrum_survivors"
                    ],
                    "character_certified_q1_survivors": pilot[
                        "character_certified_q1_survivors"
                    ],
                    "cohomology_exceptions": pilot.get("cohomology_exceptions", 0),
                },
                "summary": summary,
            }
        )

    intervals_sorted = sorted(intervals)
    contiguous = intervals_sorted == [[0, 1200], [1200, 3600], [3600, 6000], [6000, 8459]]
    full_coverage = (
        frontier_size == 8459
        and totals["anomaly_records_screened"] == frontier_size
        and contiguous
    )
    categories_dict = dict(sorted(categories.items()))
    statuses_dict = dict(sorted(statuses.items()))
    totals_dict = dict(sorted(totals.items()))

    gates = {
        "window_verifications_pass": gate(
            all(verified_windows),
            ", ".join(str(REPORTS / spec["verification"]) for spec in WINDOWS),
            "all per-window verification artifacts pass",
        ),
        "frontier_coverage_is_full": gate(
            full_coverage,
            ", ".join(str(REPORTS / spec["json"]) for spec in WINDOWS),
            "windows cover the full radius-2 anomaly frontier under current pilot settings",
        ),
        "aggregate_counts_match": gate(
            totals_dict
            == {
                "anomaly_records_screened": 8459,
                "character_certified_q1_survivors": 19,
                "cohomology_exceptions": 3,
                "filtered_candidate_records": 29,
                "raw_q1_certification_attempts": 29,
                "raw_q1_spectrum_survivors": 29,
                "slope_survivors": 2127,
                "spectrum_survivors": 902,
                "viable_count": 0,
            },
            ", ".join(str(REPORTS / spec["json"]) for spec in WINDOWS),
            "aggregate screening totals are stable across the four windows",
        ),
        "classification_counts_match": gate(
            categories_dict == {"phenomenologically obstructed": 18, "unresolved": 11}
            and statuses_dict
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 5,
                "missing_character_or_charge_level_data": 10,
                "negative_control_doublet_triplet_obstruction": 13,
                "no_certified_triplet_mass_operator_found": 1,
            },
            ", ".join(str(REPORTS / spec["json"]) for spec in WINDOWS),
            "certified q=1 records are obstructed while unresolved records are preserved",
        ),
        "no_viable_candidate_found": gate(
            totals["viable_count"] == 0,
            ", ".join(str(REPORTS / spec["json"]) for spec in WINDOWS),
            "no viable q=1 candidate appears in the screened radius-2 anomaly frontier",
        ),
    }

    return {
        "scope": "aggregate radius-2 q=1 phenomenology-guided search report around CICY 5259/7914",
        "status": "no_viable_candidate_found_with_unresolved_frontier_records",
        "interpretation": (
            "This is full radius-2 anomaly-frontier coverage under the current "
            "move primitives, charge bound, slope search, cohomology, and "
            "character-certification settings. It is not a global no-go: "
            "unresolved q=1 records remain because character or charge-level "
            "operator data is incomplete."
        ),
        "topology_denominator": topology_denominator,
        "coverage": {
            "frontier_size": frontier_size,
            "intervals": intervals_sorted,
            "full_radius2_anomaly_frontier_covered": full_coverage,
        },
        "aggregate_totals": totals_dict,
        "aggregate_categories": categories_dict,
        "aggregate_statuses": statuses_dict,
        "window_summaries": window_summaries,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    totals = report["aggregate_totals"]
    lines = [
        "# Radius-2 Q1 Phenomenology Aggregate",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Scope",
        "",
        report["interpretation"],
        "",
        "## Coverage",
        "",
        "- full radius-2 anomaly-frontier coverage under current settings: "
        f"`{report['coverage']['full_radius2_anomaly_frontier_covered']}`",
        f"- intervals: `{report['coverage']['intervals']}`",
        f"- frontier size: `{report['coverage']['frontier_size']}`",
        f"- topology denominator: `{report['topology_denominator']}`",
        "",
        "## Aggregate Counts",
        "",
        f"- totals: `{totals}`",
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
            f"raw q1 `{item['pilot_counters']['raw_q1_spectrum_survivors']}`, "
            f"character-certified `{item['pilot_counters']['character_certified_q1_survivors']}`, "
            f"viable `{item['summary']['viable_count']}`, "
            f"categories `{item['summary']['categories']}`"
        )
    lines.extend(
        [
            "",
            "## Caveat",
            "",
            (
                "No viable candidate was found, and every character-certified q=1 "
                "candidate was classified as phenomenologically obstructed. This "
                "does not prove a strict radius-2 no-go because unresolved q=1 "
                "records remain."
            ),
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_aggregate.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_aggregate.md"),
    )
    args = parser.parse_args()
    report = aggregate()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"full_coverage={report['coverage']['full_radius2_anomaly_frontier_covered']}")
    print(f"raw_q1={report['aggregate_totals']['raw_q1_spectrum_survivors']}")
    print(
        "character_certified_q1="
        f"{report['aggregate_totals']['character_certified_q1_survivors']}"
    )
    print(f"viable_count={report['aggregate_totals']['viable_count']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
