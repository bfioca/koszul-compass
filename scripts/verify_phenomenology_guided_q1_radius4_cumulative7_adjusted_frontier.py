#!/usr/bin/env python3
"""Verify the cumulative7 closure-adjusted selected radius-4 frontier."""

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


def verify() -> dict[str, Any]:
    path = REPORTS / "phenomenology_guided_q1_radius4_cumulative7_adjusted_frontier.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_cumulative7_adjusted_frontier.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    summary = report["summary"]
    next_orbit = summary["next_probe_orbit"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side cumulative7 frontier gates passed",
        ),
        "cumulative7_counts_match": gate(
            summary["closed_candidates"] == 18
            and summary["open_known_line_incomplete_candidates"] == 9
            and summary["cumulative7_adjusted_missing_blocks"] == 32
            and summary["cumulative7_adjusted_unique_missing_serre_orbits"] == 16,
            str(path),
            "cumulative7 adjusted counts match verified branch-closure subtraction",
        ),
        "open_distribution_match": gate(
            summary["open_candidates_by_missing_serre_orbit_count"]
            == {"1": 6, "2": 2, "6": 1},
            str(path),
            "open candidate missing-orbit distribution matches cumulative7 frontier",
        ),
        "next_probe_orbit_match": gate(
            next_orbit["serre_orbit_representative"] == [-2, 0, -3, 0, 1, 1, 0]
            and next_orbit["dual_representative"] == [2, 0, 3, 0, -1, -1, 0]
            and next_orbit["candidate_count"] == 1
            and next_orbit["block_count"] == 2
            and next_orbit["cohomology_counts"]
            == {"[0, 0, 4, 0]": 1, "[0, 4, 0, 0]": 1},
            str(path),
            "next cumulative7 probe orbit is the highest-ranked remaining single-candidate demand",
        ),
        "all_open_rows_are_single_candidate": gate(
            all(row["candidate_count"] == 1 and row["block_count"] == 2 for row in report["all_open_serre_orbits"]),
            str(path),
            "all remaining active Serre-orbit demands are single-candidate rows",
        ),
        "closed_items_absent": gate(
            all(
                item["candidate"] not in report["closures_applied"]["closed_candidates"]
                for item in report["open_known_line_incomplete_candidates"]
            )
            and all(
                row["serre_orbit_representative"]
                not in report["closures_applied"]["closed_serre_orbits"]
                for row in report["all_open_serre_orbits"]
            ),
            str(path),
            "closed candidates and closed Serre orbits are absent from cumulative7 open frontier",
        ),
        "markdown_exposes_frontier": gate(
            "open_known_line_incomplete_candidates: `9`" in md_text
            and "cumulative7_adjusted_missing_blocks: `32`" in md_text
            and "[-2, 0, -3, 0, 1, 1, 0]" in md_text,
            str(md_path),
            "markdown exposes cumulative7 adjusted counts and next orbit",
        ),
    }
    return {
        "scope": "verification for cumulative7 closure-adjusted selected radius-4 frontier",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_cumulative7_adjusted_frontier_verification.json"
        ),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
