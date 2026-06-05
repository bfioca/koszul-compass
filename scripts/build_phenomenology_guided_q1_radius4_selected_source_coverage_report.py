#!/usr/bin/env python3
"""Top-level coverage report for selected radius-4 source batches 1-4."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

BATCHES = [
    ("batch1", REPORTS / "phenomenology_guided_q1_radius4_adjacency_aggregate.json"),
    ("batch2", REPORTS / "phenomenology_guided_q1_radius4_batch2_aggregate.json"),
    ("batch3", REPORTS / "phenomenology_guided_q1_radius4_batch3_aggregate.json"),
    ("batch4", REPORTS / "phenomenology_guided_q1_radius4_batch4_aggregate.json"),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def categories(report: dict[str, Any]) -> dict[str, int]:
    return report.get("final_categories") or report.get("aggregate_categories") or report["categories"]


def statuses(report: dict[str, Any]) -> dict[str, int]:
    return report.get("final_statuses") or report.get("aggregate_statuses") or report["statuses"]


def batch4_closed_counts(
    scout_report: dict[str, Any],
    known_line_report: dict[str, Any],
    mass_audit_report: dict[str, Any],
) -> tuple[dict[str, int], dict[str, int]]:
    """Replace batch4 scout character gaps with known-line and exact-monoid closure."""
    gap_count = known_line_report["summary"]["attempted_character_gap_records"]
    upgraded = mass_audit_report["summary"]["upgraded_obstructions"]

    closed_categories: Counter[str] = Counter(categories(scout_report))
    closed_categories["unresolved"] -= gap_count
    closed_categories.update(known_line_report["summary"]["categories"])
    closed_categories["unresolved"] -= upgraded
    closed_categories["phenomenologically obstructed"] += upgraded

    closed_statuses: Counter[str] = Counter(statuses(scout_report))
    closed_statuses["missing_character_or_charge_level_data"] -= gap_count
    closed_statuses.update(known_line_report["summary"]["statuses"])
    closed_statuses["no_certified_triplet_mass_operator_found"] -= upgraded
    closed_statuses["no_triplet_mass_in_certified_singlet_monoid"] += upgraded

    return (
        dict(sorted((key, value) for key, value in closed_categories.items() if value)),
        dict(sorted((key, value) for key, value in closed_statuses.items() if value)),
    )


def build_report() -> dict[str, Any]:
    batch4_known_line = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_batch4_known_line_resolved.json"
    )
    batch4_mass_audit = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_batch4_known_line_mass_monoid_audit.json"
    )
    batch_rows = []
    totals: Counter[str] = Counter()
    total_frontier = 0
    total_covered = 0
    total_remaining = 0
    aggregate_categories: Counter[str] = Counter()
    aggregate_statuses: Counter[str] = Counter()
    for label, path in BATCHES:
        report = load_json(path)
        row_categories = categories(report)
        row_statuses = statuses(report)
        closure_note = "aggregate scout categories/statuses"
        if label == "batch4":
            row_categories, row_statuses = batch4_closed_counts(
                report, batch4_known_line, batch4_mass_audit
            )
            closure_note = "known-line closure plus exact singlet-monoid audit"
        total_frontier += report["coverage"]["frontier_size"]
        total_covered += report["coverage"]["covered_records"]
        total_remaining += report["coverage"]["remaining_records"]
        totals.update(report["aggregate_totals"])
        aggregate_categories.update(row_categories)
        aggregate_statuses.update(row_statuses)
        batch_rows.append(
            {
                "batch": label,
                "report": str(path),
                "source_batch": report.get("source_batch", {"source_start": 0, "source_limit": 16})
                if label != "batch1"
                else {"source_start": 0, "source_limit": 16},
                "coverage": report["coverage"],
                "raw_q1_spectrum_survivors": report["aggregate_totals"][
                    "raw_q1_spectrum_survivors"
                ],
                "character_certified_q1_survivors": report["aggregate_totals"][
                    "character_certified_q1_survivors"
                ],
                "categories": row_categories,
                "statuses": row_statuses,
                "closure_note": closure_note,
                "viable_count": report.get("viable_count", 0),
            }
        )

    post_exhaustion = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_post_exhaustion_obstruction_report.json"
    )
    batch3_verification = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_batch3_aggregate_verification.json"
    )
    batch4_verification = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_batch4_aggregate_verification.json"
    )
    batch4_known_line_verification = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_batch4_known_line_resolved_verification.json"
    )
    batch4_mass_audit_verification = load_json(
        REPORTS
        / "phenomenology_guided_q1_radius4_batch4_known_line_mass_monoid_audit_verification.json"
    )
    gates = {
        "all_batch_frontiers_covered": gate(
            total_frontier == total_covered == 34500 and total_remaining == 0,
            ", ".join(str(path) for _, path in BATCHES),
            "all four selected radius-4 source batches are covered at scout level",
        ),
        "source_records_exhaust_selected_radius3_obstructions": gate(
            [row["source_batch"].get("source_start") for row in batch_rows] == [0, 16, 32, 48]
            and batch_rows[-1]["source_batch"].get("actual_source_records") == 15,
            "batch source ranges",
            "batches cover the 63 strict radius-3 obstructed source records",
        ),
        "no_viable_candidate_found": gate(
            sum(row["viable_count"] for row in batch_rows) == 0,
            "batch classification summaries",
            "no selected radius-4 batch reports a viable candidate",
        ),
        "closure_reports_verified": gate(
            post_exhaustion["all_gates_pass"]
            and batch3_verification["all_gates_pass"]
            and batch4_verification["all_gates_pass"],
            "post-exhaustion, batch3, and batch4 verifications",
            "available closure/checkpoint reports are verified",
        ),
        "batch4_known_line_and_mass_closure_verified": gate(
            batch4_known_line_verification["all_gates_pass"]
            and batch4_mass_audit_verification["all_gates_pass"],
            "batch4 known-line and exact mass-monoid verifications",
            "batch4 character-gap closure and mass-bound upgrade are verified",
        ),
        "final_checkpoint_counts_match": gate(
            dict(sorted(aggregate_categories.items()))
            == {"phenomenologically obstructed": 111, "unresolved": 89}
            and dict(sorted(aggregate_statuses.items()))
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 31,
                "known_line_resolution_still_incomplete": 44,
                "missing_character_or_charge_level_data": 45,
                "negative_control_doublet_triplet_obstruction": 66,
                "no_triplet_mass_in_certified_singlet_monoid": 11,
                "rejected_spectrum_signature_not_q1_three_family": 3,
            },
            "selected-source final/checkpoint category and status totals",
            "batch4 closure is reflected in the selected-source ledger",
        ),
    }
    return {
        "scope": "coverage ledger for selected radius-4 expansion of strict radius-3 obstructed q=1 sources",
        "status": "selected_radius4_source_batches_covered_no_viable_candidate_found",
        "summary": {
            "source_records_expanded": 63,
            "frontier_records": total_frontier,
            "covered_records": total_covered,
            "remaining_records": total_remaining,
            "raw_q1_spectrum_survivors": totals["raw_q1_spectrum_survivors"],
            "character_certified_q1_survivors_at_scout_time": totals[
                "character_certified_q1_survivors"
            ],
            "viable_count": 0,
            "final_or_checkpoint_categories": dict(sorted(aggregate_categories.items())),
            "final_or_checkpoint_statuses": dict(sorted(aggregate_statuses.items())),
        },
        "batch_rows": batch_rows,
        "closure_scope_note": (
            "Batches 1-3 have additional known-line and/or exact-monoid closure "
            "artifacts. Batch4 now has known-line resolution plus exact monoid "
            "closure for the one mass-bound row, leaving 31 known-line-incomplete "
            "rows for future branch closure. Batches 1-2 are retained at their "
            "existing final/checkpoint convention."
        ),
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Selected Radius-4 Source Coverage",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Batch Rows", ""])
    for row in report["batch_rows"]:
        lines.append(
            f"- `{row['batch']}`: coverage `{row['coverage']}`; "
            f"raw q1 `{row['raw_q1_spectrum_survivors']}`; "
            f"categories `{row['categories']}`; statuses `{row['statuses']}`"
        )
    lines.extend(["", "## Scope Note", "", report["closure_scope_note"], ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_selected_source_coverage_report.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_selected_source_coverage_report.md"
        ),
    )
    args = parser.parse_args()
    report = build_report()
    Path(args.json_out).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, Path(args.md_out))
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
