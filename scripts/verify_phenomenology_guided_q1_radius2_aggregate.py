#!/usr/bin/env python3
"""Verify the aggregate radius-2 q=1 phenomenology report."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

WINDOW_REPORTS = [
    REPORTS / "phenomenology_guided_q1_radius2_pilot.json",
    REPORTS / "phenomenology_guided_q1_radius2_pilot_window2.json",
    REPORTS / "phenomenology_guided_q1_radius2_pilot_window3.json",
    REPORTS / "phenomenology_guided_q1_radius2_pilot_window4.json",
]
WINDOW_VERIFICATIONS = [
    REPORTS / "phenomenology_guided_q1_radius2_pilot_verification.json",
    REPORTS / "phenomenology_guided_q1_radius2_pilot_window2_verification.json",
    REPORTS / "phenomenology_guided_q1_radius2_pilot_window3_verification.json",
    REPORTS / "phenomenology_guided_q1_radius2_pilot_window4_verification.json",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def recompute_from_windows() -> dict[str, Any]:
    totals: Counter[str] = Counter()
    categories: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    intervals = []
    topology = None
    frontier_size = None

    for path in WINDOW_REPORTS:
        report = load_json(path)
        pilot = report["pilot_counters"]
        summary = report["summary"]
        start = pilot.get("anomaly_start", 0)
        screened = pilot["anomaly_records_screened"]
        intervals.append([start, start + screened])
        if frontier_size is None:
            frontier_size = pilot["anomaly_frontier_size"]
        if topology is None:
            topology = {
                "unique_candidates": report["topology_counters"]["unique_candidates"],
                "anomaly_survivors": report["topology_counters"]["anomaly_survivors"],
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
        totals["filtered_candidate_records"] += len(
            report.get("filtered_candidate_records", [])
        )
        categories.update(summary["categories"])
        statuses.update(summary["statuses"])

    return {
        "frontier_size": frontier_size,
        "intervals": sorted(intervals),
        "topology_denominator": topology,
        "totals": dict(sorted(totals.items())),
        "categories": dict(sorted(categories.items())),
        "statuses": dict(sorted(statuses.items())),
    }


def verify() -> dict[str, Any]:
    path = REPORTS / "phenomenology_guided_q1_radius2_aggregate.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_aggregate.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    recomputed = recompute_from_windows()
    verifications = [load_json(path) for path in WINDOW_VERIFICATIONS]

    expected_totals = {
        "anomaly_records_screened": 8459,
        "character_certified_q1_survivors": 19,
        "cohomology_exceptions": 3,
        "filtered_candidate_records": 29,
        "raw_q1_certification_attempts": 29,
        "raw_q1_spectrum_survivors": 29,
        "slope_survivors": 2127,
        "spectrum_survivors": 902,
        "viable_count": 0,
    }
    expected_categories = {"phenomenologically obstructed": 18, "unresolved": 11}
    expected_statuses = {
        "dangerous_10_5bar_5bar_operator_allowed": 5,
        "missing_character_or_charge_level_data": 10,
        "negative_control_doublet_triplet_obstruction": 13,
        "no_certified_triplet_mass_operator_found": 1,
    }
    expected_intervals = [[0, 1200], [1200, 3600], [3600, 6000], [6000, 8459]]

    verification_gates = {
        "aggregate_file_gates_pass": gate(
            report["all_gates_pass"] and all(item["pass"] for item in report["gates"].values()),
            str(path),
            "aggregate report builder gates pass",
        ),
        "window_verifications_pass": gate(
            all(item["all_gates_pass"] for item in verifications),
            ", ".join(str(path) for path in WINDOW_VERIFICATIONS),
            "all four window verification reports pass",
        ),
        "coverage_matches_windows": gate(
            recomputed["frontier_size"] == 8459
            and recomputed["intervals"] == expected_intervals
            and report["coverage"]["frontier_size"] == 8459
            and report["coverage"]["intervals"] == expected_intervals
            and report["coverage"]["full_radius2_anomaly_frontier_covered"] is True
            and recomputed["totals"]["anomaly_records_screened"] == 8459,
            ", ".join(str(path) for path in WINDOW_REPORTS),
            "window intervals cover the full current radius-2 anomaly frontier exactly once",
        ),
        "aggregate_counts_match_windows": gate(
            recomputed["topology_denominator"] == report["topology_denominator"]
            and recomputed["totals"] == report["aggregate_totals"] == expected_totals
            and recomputed["categories"]
            == report["aggregate_categories"]
            == expected_categories
            and recomputed["statuses"] == report["aggregate_statuses"] == expected_statuses,
            ", ".join(str(path) for path in WINDOW_REPORTS),
            "aggregate totals and classifications are recomputed from window reports",
        ),
        "certified_records_are_obstructed": gate(
            report["aggregate_totals"]["character_certified_q1_survivors"]
            == report["aggregate_categories"]["phenomenologically obstructed"] + 1
            and report["aggregate_statuses"]["no_certified_triplet_mass_operator_found"]
            == 1
            and report["aggregate_statuses"]["negative_control_doublet_triplet_obstruction"]
            + report["aggregate_statuses"]["dangerous_10_5bar_5bar_operator_allowed"]
            == 18,
            str(path),
            "all classifiable certified q=1 candidates are obstructed; one certified record lacks a triplet mass certificate",
        ),
        "markdown_has_caveat": gate(
            "full radius-2 anomaly-frontier coverage" in md_text
            and "not a global no-go" in md_text
            and "does not prove a strict radius-2 no-go" in md_text
            and "unresolved q=1 records remain" in md_text,
            str(md_path),
            "markdown states both the full current coverage and the unresolved-candidate caveat",
        ),
    }

    return {
        "scope": "verification for aggregate radius-2 q=1 phenomenology report",
        "all_gates_pass": all(item["pass"] for item in verification_gates.values()),
        "gates": verification_gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_aggregate_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
