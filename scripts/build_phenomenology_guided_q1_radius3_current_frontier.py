#!/usr/bin/env python3
"""Summarize the current radius-3 adjacency frontier after unresolved audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def build_report() -> dict[str, Any]:
    aggregate = load_json(REPORTS / "phenomenology_guided_q1_radius3_adjacency_aggregate.json")
    audit = load_json(REPORTS / "phenomenology_guided_q1_radius3_unresolved_audit.json")
    rank_path = REPORTS / "phenomenology_guided_q1_radius3_high_priority_rank_resolved.json"
    rank_resolved = load_json(rank_path) if rank_path.exists() else None
    medium_path = REPORTS / "phenomenology_guided_q1_radius3_medium_three_family_rank_resolved.json"
    medium_resolved = load_json(medium_path) if medium_path.exists() else None
    medium_small_path = REPORTS / "phenomenology_guided_q1_radius3_medium_small_rank_resolved.json"
    medium_small_resolved = (
        load_json(medium_small_path) if medium_small_path.exists() else None
    )
    sign_conflict_path = REPORTS / "phenomenology_guided_q1_radius3_sign_conflict_probe.json"
    sign_conflict = load_json(sign_conflict_path) if sign_conflict_path.exists() else None
    low_repeated_path = REPORTS / "phenomenology_guided_q1_radius3_low_repeated_rank_resolved.json"
    low_repeated_resolved = (
        load_json(low_repeated_path) if low_repeated_path.exists() else None
    )
    low_remaining_path = REPORTS / "phenomenology_guided_q1_radius3_low_remaining_rank_resolved.json"
    low_remaining_resolved = (
        load_json(low_remaining_path) if low_remaining_path.exists() else None
    )

    audited_obstructed = audit["summary"]["recommended_categories"].get(
        "phenomenologically obstructed", 0
    )
    audited_unresolved = audit["summary"]["recommended_categories"].get("unresolved", 0)
    rank_new_obstructed = (
        rank_resolved["summary"]["categories"].get("phenomenologically obstructed", 0)
        if rank_resolved is not None
        else 0
    )
    rank_remaining_unresolved = (
        rank_resolved["summary"]["categories"].get("unresolved", 0)
        if rank_resolved is not None
        else 0
    )
    rank_attempted = (
        rank_resolved["summary"]["high_priority_records"]
        if rank_resolved is not None
        else 0
    )
    medium_new_obstructed = (
        medium_resolved["summary"]["categories"].get("phenomenologically obstructed", 0)
        if medium_resolved is not None
        else 0
    )
    medium_remaining_unresolved = (
        medium_resolved["summary"]["categories"].get("unresolved", 0)
        if medium_resolved is not None
        else 0
    )
    medium_attempted = (
        medium_resolved["summary"]["records"] if medium_resolved is not None else 0
    )
    medium_small_new_obstructed = (
        medium_small_resolved["summary"]["categories"].get("phenomenologically obstructed", 0)
        if medium_small_resolved is not None
        else 0
    )
    medium_small_remaining_unresolved = (
        medium_small_resolved["summary"]["categories"].get("unresolved", 0)
        if medium_small_resolved is not None
        else 0
    )
    medium_small_attempted = (
        medium_small_resolved["summary"]["records"]
        if medium_small_resolved is not None
        else 0
    )
    low_repeated_new_obstructed = (
        low_repeated_resolved["summary"]["categories"].get("phenomenologically obstructed", 0)
        if low_repeated_resolved is not None
        else 0
    )
    low_repeated_remaining_unresolved = (
        low_repeated_resolved["summary"]["categories"].get("unresolved", 0)
        if low_repeated_resolved is not None
        else 0
    )
    low_repeated_attempted = (
        low_repeated_resolved["summary"]["records"]
        if low_repeated_resolved is not None
        else 0
    )
    low_remaining_new_obstructed = (
        low_remaining_resolved["summary"]["categories"].get("phenomenologically obstructed", 0)
        if low_remaining_resolved is not None
        else 0
    )
    low_remaining_remaining_unresolved = (
        low_remaining_resolved["summary"]["categories"].get("unresolved", 0)
        if low_remaining_resolved is not None
        else 0
    )
    low_remaining_attempted = (
        low_remaining_resolved["summary"]["records"]
        if low_remaining_resolved is not None
        else 0
    )
    current_obstructed = (
        aggregate["aggregate_categories"]["phenomenologically obstructed"]
        + audited_obstructed
        + rank_new_obstructed
        + medium_new_obstructed
        + medium_small_new_obstructed
        + low_repeated_new_obstructed
        + low_remaining_new_obstructed
    )
    current_unresolved = (
        audited_unresolved
        - rank_attempted
        - medium_attempted
        - medium_small_attempted
        - low_repeated_attempted
        - low_remaining_attempted
        + rank_remaining_unresolved
        + medium_remaining_unresolved
        + medium_small_remaining_unresolved
        + low_repeated_remaining_unresolved
        + low_remaining_remaining_unresolved
    )

    high_priority = [
        record
        for record in audit["records"]
        if record["audit"].get("priority_bucket")
        == "high_priority_q1_or_adjacent_small_map"
    ]

    gates = {
        "imports_full_radius3_aggregate": gate(
            aggregate["coverage"]["covered_records"] == 15595
            and aggregate["coverage"]["remaining_records"] == 0
            and aggregate["aggregate_totals"]["raw_q1_spectrum_survivors"] == 64,
            str(REPORTS / "phenomenology_guided_q1_radius3_adjacency_aggregate.json"),
            "current frontier starts from the full bounded radius-3 adjacency sweep",
        ),
        "imports_unresolved_audit": gate(
            audit["all_gates_pass"]
            and audit["summary"]["recommended_categories"]
            == {"phenomenologically obstructed": 2, "unresolved": 32},
            str(REPORTS / "phenomenology_guided_q1_radius3_unresolved_audit.json"),
            "current frontier imports the audit-strengthened unresolved classifications",
        ),
        "counts_are_accounted": gate(
            current_obstructed == 63
            and current_unresolved == 1
            and current_obstructed + current_unresolved
            == aggregate["aggregate_totals"]["raw_q1_spectrum_survivors"],
            "current radius-3 frontier count accounting",
            "all 64 raw q=1 survivors are either obstructed or unresolved after audit",
        ),
        "no_viable_candidate_found": gate(
            aggregate["aggregate_totals"]["viable_count"] == 0,
            str(REPORTS / "phenomenology_guided_q1_radius3_adjacency_aggregate.json"),
            "no viable candidate appears in the full bounded radius-3 adjacency sweep",
        ),
        "high_priority_backlog_identified": gate(
            len(high_priority) == 4
            and all(
                record["audit"]["missing_character_block_count"] <= 2
                for record in high_priority
            ),
            str(REPORTS / "phenomenology_guided_q1_radius3_unresolved_audit.json"),
            "four high-priority trace-feasible q=1-or-adjacent small-map records remain",
        ),
        "rank_resolution_imported": gate(
            rank_resolved is not None
            and rank_resolved["all_gates_pass"]
            and rank_resolved["summary"]["character_certified_records"] == 3
            and rank_resolved["summary"]["categories"]
            == {"phenomenologically obstructed": 3, "unresolved": 1},
            str(rank_path),
            "current frontier imports the known-rank resolution pass over high-priority records",
        ),
        "medium_three_family_resolution_imported": gate(
            medium_resolved is not None
            and medium_resolved["all_gates_pass"]
            and medium_resolved["summary"]["categories"]
            == {"phenomenologically obstructed": 1},
            str(medium_path),
            "current frontier imports the medium-three-family character resolution",
        ),
        "sign_conflict_blocker_recorded": gate(
            sign_conflict is not None
            and sign_conflict["all_gates_pass"]
            and sign_conflict["status"]
            == "character_certificate_blocked_by_sign_constraint_conflict",
            str(sign_conflict_path),
            "the remaining high-priority unresolved record has a recorded sign-conflict blocker",
        ),
        "medium_small_resolution_imported": gate(
            medium_small_resolved is not None
            and medium_small_resolved["all_gates_pass"]
            and medium_small_resolved["summary"]["categories"]
            == {"phenomenologically obstructed": 6},
            str(medium_small_path),
            "current frontier imports the medium-small character resolutions",
        ),
        "low_repeated_resolution_imported": gate(
            low_repeated_resolved is not None
            and low_repeated_resolved["all_gates_pass"]
            and low_repeated_resolved["summary"]["categories"]
            == {"phenomenologically obstructed": 6},
            str(low_repeated_path),
            "current frontier imports the low-priority repeated-pattern resolutions",
        ),
        "low_remaining_resolution_imported": gate(
            low_remaining_resolved is not None
            and low_remaining_resolved["all_gates_pass"]
            and low_remaining_resolved["summary"]["categories"]
            == {"phenomenologically obstructed": 15},
            str(low_remaining_path),
            "current frontier imports the remaining low-priority resolutions",
        ),
    }

    return {
        "scope": "current radius-3 adjacency q=1 frontier after unresolved audit",
        "status": "no_viable_candidate_found_radius3_frontier_partly_unresolved",
        "summary": {
            "raw_q1_spectrum_survivors": aggregate["aggregate_totals"][
                "raw_q1_spectrum_survivors"
            ],
            "character_certified_q1_survivors": aggregate["aggregate_totals"][
                "character_certified_q1_survivors"
            ],
            "current_obstructed_count": current_obstructed,
            "current_unresolved_count": current_unresolved,
            "viable_count": 0,
            "audit_strengthened_obstructions": audited_obstructed,
            "rank_resolution_obstructions": rank_new_obstructed,
            "medium_three_family_resolution_obstructions": medium_new_obstructed,
            "medium_small_resolution_obstructions": medium_small_new_obstructed,
            "low_repeated_resolution_obstructions": low_repeated_new_obstructed,
            "low_remaining_resolution_obstructions": low_remaining_new_obstructed,
            "high_priority_unresolved_records": rank_remaining_unresolved,
            "sign_conflict_unresolved_records": 1 if sign_conflict is not None else 0,
            "missing_character_block_count": audit["summary"][
                "missing_character_block_count"
            ],
            "unique_missing_block_patterns": audit["summary"][
                "unique_missing_block_patterns"
            ],
        },
        "high_priority_unresolved_frontier": [
            {
                "window": record["window"],
                "label": record["label"],
                "source_radius2_record": record["source_radius2_record"],
                "vectorlike_prediction": record["vectorlike_prediction"],
                "missing_character_block_count": record["audit"][
                    "missing_character_block_count"
                ],
                "missing_character_blocks": record["audit"][
                    "missing_character_blocks"
                ],
                "trace_feasibility": record["audit"][
                    "desired_q1_trace_feasibility"
                ],
            }
            for record in high_priority
            if rank_resolved is None
            or not any(
                filtered["source_window"] == record["window"]
                and filtered["source_filtered_label"] == record["label"]
                and filtered["classification"]["category"] != "unresolved"
                for filtered in rank_resolved["filtered_candidate_records"]
            )
        ],
        "interpretation": (
            "The full bounded radius-3 adjacency frontier has been swept. No viable "
            "candidate survives the current charge-level filter. The audit upgrades "
            "two no-triplet-mass records to obstruction, and the known-rank pass "
            "certifies three high-priority desired-q1 records as additional "
            "negative-control obstructions. One high-priority sign-conflict character "
            "case remains. The medium-priority three-family near-miss is also "
            "character-certified and rejected because the resolved spectrum is not q=1. "
            "The six medium-priority small-map records are now character-certified "
            "and obstructed as well. Six low-priority repeated-pattern records are "
            "character-certified and rejected as non-q1. The remaining low-priority "
            "records are now character-certified and obstructed; only the high-priority "
            "sign-conflict character case remains unresolved."
        ),
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-3 Current Q1 Frontier",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## High-Priority Unresolved Frontier", ""])
    for record in report["high_priority_unresolved_frontier"]:
        lines.append(
            "- "
            f"`{record['window']}/{record['label']}` from `{record['source_radius2_record']}`: "
            f"prediction `{record['vectorlike_prediction']}`, "
            f"missing blocks `{record['missing_character_block_count']}`"
        )
    lines.extend(["", "## Interpretation", "", report["interpretation"], ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_current_frontier.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_current_frontier.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
