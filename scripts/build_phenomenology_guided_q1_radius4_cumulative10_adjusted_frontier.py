#!/usr/bin/env python3
"""Cumulative selected radius-4 frontier after eleventh cluster closure."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from build_phenomenology_guided_q1_radius4_cumulative9_adjusted_frontier import (  # noqa: E402
    CLOSED_CANDIDATES as CUMULATIVE9_CLOSED_CANDIDATES,
    CLOSED_ORBITS as CUMULATIVE9_CLOSED_ORBITS,
)
from build_phenomenology_guided_q1_radius4_eleventh_cluster_branch_closure import (  # noqa: E402
    CLUSTER_ORBITS,
    TARGET_CANDIDATE as ELEVENTH_CLUSTER_TARGET_CANDIDATE,
)

CLOSED_CANDIDATES = set(CUMULATIVE9_CLOSED_CANDIDATES) | {
    ELEVENTH_CLUSTER_TARGET_CANDIDATE
}
CLOSED_ORBITS = set(CUMULATIVE9_CLOSED_ORBITS) | set(CLUSTER_ORBITS)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def build_report() -> dict[str, Any]:
    demand = load_json(REPORTS / "phenomenology_guided_q1_radius4_missing_line_demand.json")
    verification_paths = [
        REPORTS / "phenomenology_guided_q1_radius4_cumulative9_adjusted_frontier_verification.json",
        REPORTS
        / "phenomenology_guided_q1_radius4_eleventh_cluster_branch_closure_verification.json",
    ]
    verifications = [load_json(path) for path in verification_paths]
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
            all(item["all_gates_pass"] for item in verifications),
            ", ".join(str(path) for path in verification_paths),
            "cumulative10 frontier extends only verified no-viable branch closures",
        ),
        "cumulative_counts_match": gate(
            len(open_candidates) == 6
            and sum(row["block_count"] for row in open_rows) == 14
            and len(open_rows) == 7,
            "cumulative10 open candidate/orbit rows",
            "twenty-one branch-closed candidates and eighteen Serre orbits are removed",
        ),
        "open_distribution_match": gate(
            dict(sorted(open_distribution.items())) == {1: 5, 2: 1},
            "cumulative10 open candidates",
            "open candidate missing-orbit distribution matches cumulative10 subtraction",
        ),
        "next_open_orbit_match": gate(
            bool(open_rows)
            and open_rows[0]["candidate_count"] == 1
            and open_rows[0]["block_count"] == 2,
            "cumulative10 open Serre orbit ranking",
            "all remaining active Serre orbits are single-candidate demands",
        ),
        "closed_items_absent": gate(
            all(item["candidate"] not in CLOSED_CANDIDATES for item in open_candidates)
            and all(tuple(row["serre_orbit_representative"]) not in CLOSED_ORBITS for row in open_rows),
            "cumulative10 open frontier",
            "closed candidates and Serre orbits are absent",
        ),
    }
    return {
        "scope": "cumulative10 closure-adjusted selected radius-4 frontier",
        "status": "cumulative10_closure_adjusted_probe_queue_emitted",
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
            "cumulative10_adjusted_missing_blocks": sum(row["block_count"] for row in open_rows),
            "raw_unique_missing_serre_orbits": demand["summary"][
                "unique_missing_serre_orbits"
            ],
            "cumulative10_adjusted_unique_missing_serre_orbits": len(open_rows),
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
        "# Cumulative10 Closure-Adjusted Radius-4 Frontier",
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
                "After applying the verified eleventh six-orbit cluster closure, "
                "all remaining active Serre-orbit demands remain single-candidate rows. "
                "The selected radius-4 frontier is reduced to six character-incomplete "
                "candidates."
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
            REPORTS / "phenomenology_guided_q1_radius4_cumulative10_adjusted_frontier.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_cumulative10_adjusted_frontier.md"
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
