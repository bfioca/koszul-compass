#!/usr/bin/env python3
"""Cumulative selected radius-4 frontier after verified branch closures."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

CLOSED_CANDIDATES = {
    "batch1:window4_radius4_adjacency_filtered_5_known_line_resolved",
    "batch1:window4_radius4_adjacency_filtered_7_known_line_resolved",
    "batch2:window3_radius4_adjacency_filtered_8_known_line_resolved",
    "batch2:window3_radius4_adjacency_filtered_9_known_line_resolved",
    "batch2:window6_radius4_adjacency_filtered_1_known_line_resolved",
    "batch1:window2_radius4_adjacency_filtered_5_known_line_resolved",
    "batch2:window5_radius4_adjacency_filtered_5_known_line_resolved",
}
CLOSED_ORBITS = {
    (0, 0, -2, 1, -1, 1, -1),
    (-2, 2, -1, -1, 1, 0, 1),
    (-1, 0, 2, 0, 2, -1, 0),
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def build_report() -> dict[str, Any]:
    demand = load_json(REPORTS / "phenomenology_guided_q1_radius4_missing_line_demand.json")
    top_v = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_top_orbit_branch_closure_verification.json"
    )
    residual_v = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_top_residual_branch_closure_verification.json"
    )
    next_v = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_next_orbit_branch_closure_verification.json"
    )

    open_candidates = [
        item
        for item in demand["known_line_incomplete_candidates"]
        if item["candidate"] not in CLOSED_CANDIDATES
    ]
    open_candidate_ids = {item["candidate"] for item in open_candidates}
    open_distribution = Counter(len(item["missing_serre_orbits"]) for item in open_candidates)

    open_rows = []
    removed_rows = []
    for row in demand["all_missing_serre_orbits"]:
        orbit = tuple(row["serre_orbit_representative"])
        active_candidate_ids = [
            candidate for candidate in row["candidate_ids"] if candidate in open_candidate_ids
        ]
        if orbit in CLOSED_ORBITS or not active_candidate_ids:
            removed_rows.append(
                {
                    "serre_orbit_representative": row["serre_orbit_representative"],
                    "dual_representative": row["dual_representative"],
                    "original_candidate_count": row["candidate_count"],
                    "original_block_count": row["block_count"],
                    "removed_reason": "closed_by_verified_branch_closure"
                    if orbit in CLOSED_ORBITS
                    else "all_candidate_demands_closed",
                }
            )
            continue
        open_rows.append(
            {
                **row,
                "candidate_ids": active_candidate_ids,
                "candidate_count": len(active_candidate_ids),
                "block_count": 2 * len(active_candidate_ids),
                "example_blocks": [
                    block
                    for block in row["example_blocks"]
                    if block["candidate"] in open_candidate_ids
                ],
            }
        )
    open_rows.sort(
        key=lambda row: (
            -row["candidate_count"],
            -row["block_count"],
            row["serre_orbit_representative"],
        )
    )
    gates = {
        "all_closure_verifications_pass": gate(
            top_v["all_gates_pass"] and residual_v["all_gates_pass"] and next_v["all_gates_pass"],
            "branch closure verification reports",
            "cumulative frontier subtracts only verified no-viable closures",
        ),
        "cumulative_counts_match": gate(
            len(open_candidates) == 20
            and sum(row["block_count"] for row in open_rows) == 54
            and len(open_rows) == 22,
            "cumulative open candidate/orbit rows",
            "seven branch-closed candidates and three Serre orbits are removed",
        ),
        "open_distribution_match": gate(
            dict(sorted(open_distribution.items())) == {1: 17, 2: 2, 6: 1},
            "cumulative open candidates",
            "open candidate missing-orbit distribution matches cumulative subtraction",
        ),
        "next_open_orbit_match": gate(
            open_rows[0]["serre_orbit_representative"] == [-1, 0, 2, 1, 1, -1, 0]
            and open_rows[0]["candidate_count"] == 2
            and open_rows[0]["block_count"] == 4,
            "cumulative open Serre orbit ranking",
            "next cumulative bottleneck is the highest-ranked remaining two-candidate orbit",
        ),
        "closed_items_absent": gate(
            all(item["candidate"] not in CLOSED_CANDIDATES for item in open_candidates)
            and all(tuple(row["serre_orbit_representative"]) not in CLOSED_ORBITS for row in open_rows),
            "cumulative open frontier",
            "closed candidates and Serre orbits are absent",
        ),
    }
    return {
        "scope": "cumulative closure-adjusted selected radius-4 frontier",
        "status": "cumulative_closure_adjusted_probe_queue_emitted",
        "closures_applied": {
            "closed_candidates": sorted(CLOSED_CANDIDATES),
            "closed_serre_orbits": [list(item) for item in sorted(CLOSED_ORBITS)],
        },
        "summary": {
            "raw_known_line_incomplete_candidates": demand["summary"][
                "known_line_incomplete_candidates"
            ],
            "closed_candidates": len(CLOSED_CANDIDATES),
            "open_known_line_incomplete_candidates": len(open_candidates),
            "raw_missing_blocks": demand["summary"]["raw_missing_blocks"],
            "cumulative_adjusted_missing_blocks": sum(row["block_count"] for row in open_rows),
            "raw_unique_missing_serre_orbits": demand["summary"][
                "unique_missing_serre_orbits"
            ],
            "cumulative_adjusted_unique_missing_serre_orbits": len(open_rows),
            "open_candidates_by_missing_serre_orbit_count": dict(
                sorted(open_distribution.items())
            ),
            "next_probe_orbit": open_rows[0] if open_rows else None,
        },
        "top_open_serre_orbits": open_rows[:30],
        "all_open_serre_orbits": open_rows,
        "removed_serre_orbits": removed_rows,
        "open_known_line_incomplete_candidates": open_candidates,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Cumulative Closure-Adjusted Radius-4 Frontier",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Next Open Serre Orbits", ""])
    for row in report["top_open_serre_orbits"][:15]:
        lines.append(
            "- "
            f"`{row['serre_orbit_representative']}` / "
            f"`{row['dual_representative']}`: "
            f"candidates `{row['candidate_count']}`, blocks `{row['block_count']}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "After the verified top-orbit, residual, and adjusted next-orbit "
                "branch closures, the selected radius-4 active character frontier "
                "has 20 open candidates. The next active bottleneck is the leading "
                "two-candidate Serre orbit listed above."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_cumulative_adjusted_frontier.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_cumulative_adjusted_frontier.md"
        ),
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
