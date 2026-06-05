#!/usr/bin/env python3
"""Verify the closure-adjusted selected radius-4 frontier report."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_closure_adjusted_frontier.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_closure_adjusted_frontier.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    summary = report["summary"]
    next_orbit = summary["next_probe_orbit"]

    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side closure-adjusted frontier gates passed",
        ),
        "closure_counts_match": gate(
            summary["raw_known_line_incomplete_candidates"] == 27
            and summary["closed_candidates"] == 5
            and summary["open_known_line_incomplete_candidates"] == 22,
            str(path),
            "verified branch closures remove five formerly open character-incomplete candidates",
        ),
        "adjusted_missing_demand_counts_match": gate(
            summary["raw_missing_blocks"] == 70
            and summary["closure_adjusted_missing_blocks"] == 58
            and summary["raw_unique_missing_serre_orbits"] == 25
            and summary["closure_adjusted_unique_missing_serre_orbits"] == 23,
            str(path),
            "adjusted missing-line demand counts match closure subtraction",
        ),
        "open_candidate_distribution_match": gate(
            summary["open_candidates_by_missing_serre_orbit_count"]
            == {"1": 19, "2": 2, "6": 1},
            str(path),
            "open candidate missing-orbit distribution is preserved exactly",
        ),
        "next_probe_orbit_match": gate(
            next_orbit["serre_orbit_representative"] == [-1, 0, 2, 0, 2, -1, 0]
            and next_orbit["dual_representative"] == [1, 0, -2, 0, -2, 1, 0]
            and next_orbit["candidate_count"] == 2
            and next_orbit["block_count"] == 4
            and next_orbit["cohomology_counts"] == {"[0, 2, 2, 0]": 4},
            str(path),
            "next active probe orbit is the highest-ranked adjusted frontier demand",
        ),
        "closed_items_absent": gate(
            all(
                candidate
                not in {
                    "batch1:window4_radius4_adjacency_filtered_5_known_line_resolved",
                    "batch1:window4_radius4_adjacency_filtered_7_known_line_resolved",
                    "batch2:window3_radius4_adjacency_filtered_8_known_line_resolved",
                    "batch2:window3_radius4_adjacency_filtered_9_known_line_resolved",
                    "batch2:window6_radius4_adjacency_filtered_1_known_line_resolved",
                }
                for item in report["open_known_line_incomplete_candidates"]
                for candidate in [item["candidate"]]
            )
            and all(
                row["serre_orbit_representative"]
                not in ([0, 0, -2, 1, -1, 1, -1], [-2, 2, -1, -1, 1, 0, 1])
                for row in report["all_open_serre_orbits"]
            ),
            str(path),
            "closed top-orbit footprint is absent from the active adjusted frontier",
        ),
        "markdown_exposes_adjusted_frontier": gate(
            "open_known_line_incomplete_candidates: `22`" in md_text
            and "closure_adjusted_missing_blocks: `58`" in md_text
            and "[-1, 0, 2, 0, 2, -1, 0]" in md_text,
            str(md_path),
            "markdown exposes adjusted counts and next active probe orbit",
        ),
    }
    return {
        "scope": "verification for closure-adjusted selected radius-4 frontier",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_closure_adjusted_frontier_verification.json"
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
