#!/usr/bin/env python3
"""Aggregate the full selected radius-4 batch-3 sweep."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

WINDOWS = [
    ("window1", REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch3_window1.json", REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch3_window1_verification.json"),
    ("window2", REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch3_window2.json", REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch3_window2_verification.json"),
    ("window3", REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch3_window3.json", REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch3_window3_verification.json"),
    ("window4", REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch3_window4.json", REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch3_window4_verification.json"),
    ("window5", REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch3_window5.json", REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch3_window5_verification.json"),
    ("window6", REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch3_window6.json", REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch3_window6_verification.json"),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def build_report() -> dict[str, Any]:
    totals: Counter[str] = Counter()
    initial_categories: Counter[str] = Counter()
    initial_statuses: Counter[str] = Counter()
    intervals = []
    summaries = []
    frontier_size = None
    adjacency_counters = None
    all_window_verifications_pass = True
    for label, report_path, verification_path in WINDOWS:
        report = load_json(report_path)
        verification = load_json(verification_path)
        all_window_verifications_pass = all_window_verifications_pass and verification["all_gates_pass"]
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
        initial_categories.update(report["summary"]["categories"])
        initial_statuses.update(report["summary"]["statuses"])
        summaries.append(
            {
                "label": label,
                "report": str(report_path),
                "verification": str(verification_path),
                "interval": intervals[-1],
                "summary": report["summary"],
            }
        )

    known = load_json(REPORTS / "phenomenology_guided_q1_radius4_batch3_known_line_resolved.json")
    known_verification = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_batch3_known_line_resolved_verification.json"
    )
    window4_mass = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_batch3_window4_mass_monoid_audit.json"
    )
    window4_mass_verification = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_batch3_window4_mass_monoid_audit_verification.json"
    )
    known_mass = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_batch3_known_line_mass_monoid_audit.json"
    )

    final_categories = Counter(initial_categories)
    final_statuses = Counter(initial_statuses)
    final_categories.subtract({"unresolved": known["summary"]["attempted_unresolved_records"]})
    final_statuses.subtract({"missing_character_or_charge_level_data": known["summary"]["attempted_unresolved_records"]})
    final_categories.update(known["summary"]["categories"])
    final_statuses.update(known["summary"]["statuses"])
    for mass_report in [window4_mass, known_mass]:
        upgraded = mass_report["summary"]["upgraded_obstructions"]
        final_statuses.subtract({"no_certified_triplet_mass_operator_found": upgraded})
        final_statuses.update({"no_triplet_mass_in_certified_singlet_monoid": upgraded})
        # Category remains unresolved -> obstructed for upgraded mass rows.
        final_categories.subtract({"unresolved": upgraded})
        final_categories.update({"phenomenologically obstructed": upgraded})

    intervals = sorted(intervals)
    gates = {
        "window_verifications_pass": gate(
            all_window_verifications_pass,
            ", ".join(str(item[2]) for item in WINDOWS),
            "all batch-3 scout window verifications pass",
        ),
        "windows_cover_batch_frontier": gate(
            intervals == [[0, 1600], [1600, 3200], [3200, 4800], [4800, 6400], [6400, 8000], [8000, 8755]],
            "batch-3 intervals",
            "windows cover the full selected batch-3 frontier contiguously",
        ),
        "known_line_and_mass_audits_pass": gate(
            known["all_gates_pass"]
            and known_verification["all_gates_pass"]
            and window4_mass["all_gates_pass"]
            and window4_mass_verification["all_gates_pass"]
            and known_mass["all_gates_pass"],
            "batch-3 known-line and mass audit reports",
            "post-scout closure reports passed their gates",
        ),
        "aggregate_counts_match": gate(
            totals["frontier_records_screened"] == 8755
            and totals["raw_q1_spectrum_survivors"] == 61
            and totals["raw_q1_certification_attempts"] == 61
            and totals["character_certified_q1_survivors"] == 41,
            "batch-3 window counters",
            "window counters aggregate to expected batch-3 totals",
        ),
        "final_classifications_match": gate(
            dict(+final_categories) == {"phenomenologically obstructed": 48, "unresolved": 13}
            and dict(+final_statuses)
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 14,
                "known_line_resolution_still_incomplete": 13,
                "negative_control_doublet_triplet_obstruction": 24,
                "no_triplet_mass_in_certified_singlet_monoid": 9,
                "rejected_spectrum_signature_not_q1_three_family": 1,
            },
            "batch-3 final classification accounting",
            "known-line and exact monoid closures are reflected in final counts",
        ),
    }
    return {
        "scope": "aggregate of selected radius-4 adjacency q=1 scout batch 3",
        "status": "no_viable_candidate_found_in_radius4_batch3_frontier",
        "source_batch": {"source_start": 32, "source_limit": 16},
        "adjacency_counters": adjacency_counters,
        "coverage": {
            "frontier_size": frontier_size,
            "covered_records": totals["frontier_records_screened"],
            "remaining_records": max(0, frontier_size - totals["frontier_records_screened"]),
            "intervals": intervals,
        },
        "aggregate_totals": dict(sorted(totals.items())),
        "initial_categories": dict(+initial_categories),
        "initial_statuses": dict(+initial_statuses),
        "post_closure": {
            "known_line_summary": known["summary"],
            "window4_mass_audit_summary": window4_mass["summary"],
            "known_line_mass_audit_summary": known_mass["summary"],
        },
        "final_categories": dict(+final_categories),
        "final_statuses": dict(+final_statuses),
        "viable_count": 0,
        "window_summaries": summaries,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Selected Radius-4 Batch 3 Aggregate",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- source batch: `{report['source_batch']}`",
        f"- coverage: `{report['coverage']}`",
        f"- aggregate totals: `{report['aggregate_totals']}`",
        f"- initial categories: `{report['initial_categories']}`",
        f"- final categories: `{report['final_categories']}`",
        f"- final statuses: `{report['final_statuses']}`",
        f"- viable count: `{report['viable_count']}`",
        "",
        "## Post Closure",
        "",
    ]
    for key, value in report["post_closure"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", default=str(REPORTS / "phenomenology_guided_q1_radius4_batch3_aggregate.json"))
    parser.add_argument("--md-out", default=str(REPORTS / "phenomenology_guided_q1_radius4_batch3_aggregate.md"))
    args = parser.parse_args()
    report = build_report()
    Path(args.json_out).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, Path(args.md_out))
    print(f"status={report['status']}")
    print(f"coverage={report['coverage']}")
    print(f"final_categories={report['final_categories']}")
    print(f"final_statuses={report['final_statuses']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
