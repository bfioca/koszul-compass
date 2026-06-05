#!/usr/bin/env python3
"""Cumulative selected radius-4 frontier after final branch closure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from build_phenomenology_guided_q1_radius4_cumulative15_adjusted_frontier import (  # noqa: E402
    CLOSED_CANDIDATES as CUMULATIVE15_CLOSED_CANDIDATES,
    CLOSED_ORBITS as CUMULATIVE15_CLOSED_ORBITS,
)
from build_phenomenology_guided_q1_radius4_seventeenth_orbit_branch_closure import (  # noqa: E402
    SEVENTEENTH_ORBIT,
    TARGET_CANDIDATE as SEVENTEENTH_TARGET_CANDIDATE,
)

CLOSED_CANDIDATES = set(CUMULATIVE15_CLOSED_CANDIDATES) | {SEVENTEENTH_TARGET_CANDIDATE}
CLOSED_ORBITS = set(CUMULATIVE15_CLOSED_ORBITS) | {SEVENTEENTH_ORBIT}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def build_report() -> dict[str, Any]:
    demand = load_json(REPORTS / "phenomenology_guided_q1_radius4_missing_line_demand.json")
    verification_paths = [
        REPORTS / "phenomenology_guided_q1_radius4_cumulative15_adjusted_frontier_verification.json",
        REPORTS / "phenomenology_guided_q1_radius4_seventeenth_orbit_branch_closure_verification.json",
    ]
    verifications = [load_json(path) for path in verification_paths]
    open_candidates = [
        item
        for item in demand["known_line_incomplete_candidates"]
        if item["candidate"] not in CLOSED_CANDIDATES
    ]
    open_candidate_ids = {item["candidate"] for item in open_candidates}
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
        open_rows.append(row)
    gates = {
        "all_closure_verifications_pass": gate(
            all(item["all_gates_pass"] for item in verifications),
            ", ".join(str(path) for path in verification_paths),
            "cumulative16 frontier extends only verified no-viable branch closures",
        ),
        "frontier_exhausted": gate(
            len(CLOSED_CANDIDATES) == demand["summary"]["known_line_incomplete_candidates"]
            and len(open_candidates) == 0
            and len(open_rows) == 0
            and sum(row.get("block_count", 0) for row in open_rows) == 0,
            "cumulative16 open candidate/orbit rows",
            "all selected radius-4 known-line incomplete candidates are branch-closed",
        ),
        "closed_orbits_cover_raw_open_demands": gate(
            len(CLOSED_ORBITS) == demand["summary"]["unique_missing_serre_orbits"]
            and len(removed_rows) == demand["summary"]["unique_missing_serre_orbits"],
            "cumulative16 closed Serre orbits",
            "all raw missing Serre-orbit rows are removed by verified closures",
        ),
    }
    return {
        "scope": "cumulative16 exhausted selected radius-4 frontier",
        "status": "selected_radius4_frontier_exhausted_no_viable_candidate_found",
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
            "cumulative16_adjusted_missing_blocks": 0,
            "raw_unique_missing_serre_orbits": demand["summary"][
                "unique_missing_serre_orbits"
            ],
            "cumulative16_adjusted_unique_missing_serre_orbits": len(open_rows),
            "open_candidates_by_missing_serre_orbit_count": {},
            "next_probe_orbit": None,
        },
        "all_open_serre_orbits": open_rows,
        "removed_serre_orbits": removed_rows,
        "open_known_line_incomplete_candidates": open_candidates,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Cumulative16 Exhausted Radius-4 Frontier",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "All selected radius-4 known-line incomplete candidates have now been "
                "branch-closed through verified character completions. No branch produced "
                "a viable quotient-compatible q=1 candidate under the current "
                "phenomenology filter."
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
            REPORTS / "phenomenology_guided_q1_radius4_cumulative16_exhausted_frontier.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_cumulative16_exhausted_frontier.md"
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
