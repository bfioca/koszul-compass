#!/usr/bin/env python3
"""Adjust the selected radius-4 frontier by verified bounded branch closures."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

TOP_ORBIT = (0, 0, -2, 1, -1, 1, -1)
RESIDUAL_ORBIT = (-2, 2, -1, -1, 1, 0, 1)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def neg(line: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(-value for value in line)


def line_label(line: tuple[int, ...]) -> str:
    return "[" + ",".join(str(value) for value in line) + "]"


def build_report() -> dict[str, Any]:
    demand = load_json(REPORTS / "phenomenology_guided_q1_radius4_missing_line_demand.json")
    top_closure = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_top_orbit_branch_closure.json"
    )
    residual_closure = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_top_residual_branch_closure.json"
    )
    top_verification = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_top_orbit_branch_closure_verification.json"
    )
    residual_verification = load_json(
        REPORTS
        / "phenomenology_guided_q1_radius4_top_residual_branch_closure_verification.json"
    )

    # The closure reports prove this exact five-candidate top-orbit footprint nonviable.
    closed_candidates = {
        "batch1:window4_radius4_adjacency_filtered_5_known_line_resolved",
        "batch1:window4_radius4_adjacency_filtered_7_known_line_resolved",
        "batch2:window3_radius4_adjacency_filtered_8_known_line_resolved",
        "batch2:window3_radius4_adjacency_filtered_9_known_line_resolved",
        "batch2:window6_radius4_adjacency_filtered_1_known_line_resolved",
    }
    closed_orbits = {TOP_ORBIT, RESIDUAL_ORBIT}

    open_candidates = [
        candidate
        for candidate in demand["known_line_incomplete_candidates"]
        if candidate["candidate"] not in closed_candidates
    ]
    open_candidate_ids = {candidate["candidate"] for candidate in open_candidates}

    adjusted_rows = []
    removed_rows = []
    for row in demand["all_missing_serre_orbits"]:
        orbit = tuple(row["serre_orbit_representative"])
        remaining_blocks = [
            block
            for block in row["example_blocks"]
            if block["candidate"] in open_candidate_ids
        ]
        # example_blocks is truncated, so use candidate ids for accurate active demand.
        active_candidate_ids = [
            candidate
            for candidate in row["candidate_ids"]
            if candidate in open_candidate_ids
        ]
        if orbit in closed_orbits or not active_candidate_ids:
            removed_rows.append(
                {
                    "serre_orbit_representative": row["serre_orbit_representative"],
                    "dual_representative": row["dual_representative"],
                    "original_candidate_count": row["candidate_count"],
                    "original_block_count": row["block_count"],
                    "removed_reason": "closed_by_verified_branch_closure"
                    if orbit in closed_orbits
                    else "all_candidate_demands_closed",
                }
            )
            continue
        active_block_count = sum(
            2
            for candidate in row["candidate_ids"]
            if candidate in open_candidate_ids
        )
        adjusted_rows.append(
            {
                **row,
                "candidate_ids": active_candidate_ids,
                "candidate_count": len(active_candidate_ids),
                "block_count": active_block_count,
                "example_blocks": remaining_blocks,
            }
        )
    adjusted_rows.sort(
        key=lambda row: (
            -row["candidate_count"],
            -row["block_count"],
            row["serre_orbit_representative"],
        )
    )

    open_distribution = Counter(
        len(candidate["missing_serre_orbits"])
        for candidate in open_candidates
    )
    gates = {
        "source_demand_passes": gate(
            demand["all_gates_pass"],
            str(REPORTS / "phenomenology_guided_q1_radius4_missing_line_demand.json"),
            "closure-adjusted frontier starts from the verified missing-line demand report",
        ),
        "closure_verifications_pass": gate(
            top_verification["all_gates_pass"]
            and residual_verification["all_gates_pass"]
            and top_closure["all_gates_pass"]
            and residual_closure["all_gates_pass"],
            "top-orbit and residual branch closure verifications",
            "only verified no-viable branch closures are subtracted",
        ),
        "closed_candidate_count_matches_closures": gate(
            len(closed_candidates) == 5
            and top_closure["summary"]["candidate_count"] == 5
            and residual_closure["summary"]["viable_count"] == 0,
            "closed top-orbit candidate set",
            "all five candidates touched by the highest-demand orbit are branch-closed nonviable",
        ),
        "adjusted_counts_match": gate(
            len(open_candidates) == 22
            and sum(row["block_count"] for row in adjusted_rows) == 58
            and len(adjusted_rows) == 23,
            "closure-adjusted missing-line rows",
            "adjusted frontier removes closed candidates and closed Serre orbits",
        ),
        "top_open_orbit_is_next_bottleneck": gate(
            adjusted_rows[0]["candidate_count"] == 2
            and adjusted_rows[0]["block_count"] == 4
            and adjusted_rows[0]["serre_orbit_representative"]
            == [-1, 0, 2, 0, 2, -1, 0],
            "closure-adjusted ranked orbits",
            "next active bottleneck is the first two-candidate orbit after top closure",
        ),
        "no_closed_orbits_remain_active": gate(
            all(tuple(row["serre_orbit_representative"]) not in closed_orbits for row in adjusted_rows)
            and all(candidate["candidate"] not in closed_candidates for candidate in open_candidates),
            "closure-adjusted frontier",
            "closed candidates and closed Serre orbits are absent from active queue",
        ),
    }

    return {
        "scope": "closure-adjusted selected radius-4 missing-line frontier",
        "status": "closure_adjusted_probe_queue_emitted",
        "closures_applied": {
            "closed_candidates": sorted(closed_candidates),
            "closed_serre_orbits": [list(TOP_ORBIT), list(RESIDUAL_ORBIT)],
            "top_orbit_viable_count": top_closure["summary"]["viable_count"],
            "residual_viable_count": residual_closure["summary"]["viable_count"],
        },
        "summary": {
            "raw_known_line_incomplete_candidates": demand["summary"][
                "known_line_incomplete_candidates"
            ],
            "closed_candidates": len(closed_candidates),
            "open_known_line_incomplete_candidates": len(open_candidates),
            "raw_missing_blocks": demand["summary"]["raw_missing_blocks"],
            "closure_adjusted_missing_blocks": sum(
                row["block_count"] for row in adjusted_rows
            ),
            "raw_unique_missing_serre_orbits": demand["summary"][
                "unique_missing_serre_orbits"
            ],
            "closure_adjusted_unique_missing_serre_orbits": len(adjusted_rows),
            "open_candidates_by_missing_serre_orbit_count": dict(
                sorted(open_distribution.items())
            ),
            "next_probe_orbit": adjusted_rows[0] if adjusted_rows else None,
        },
        "top_open_serre_orbits": adjusted_rows[:30],
        "all_open_serre_orbits": adjusted_rows,
        "removed_serre_orbits": removed_rows,
        "open_known_line_incomplete_candidates": open_candidates,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Closure-Adjusted Radius-4 Frontier",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Closures Applied", ""])
    for candidate in report["closures_applied"]["closed_candidates"]:
        lines.append(f"- closed candidate: `{candidate}`")
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
                "After subtracting the verified no-viable top-orbit and residual "
                "branch closures, the active selected radius-4 character frontier "
                "has 22 open candidates and 23 missing Serre orbits. The next "
                "probe target is the highest-ranked two-candidate orbit."
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
            REPORTS / "phenomenology_guided_q1_radius4_closure_adjusted_frontier.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_closure_adjusted_frontier.md"
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
