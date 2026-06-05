#!/usr/bin/env python3
"""Verify the cumulative16 exhausted selected radius-4 frontier report."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_cumulative16_exhausted_frontier.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_cumulative16_exhausted_frontier.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    summary = report["summary"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side cumulative16 exhausted-frontier gates passed",
        ),
        "frontier_counts_exhausted": gate(
            summary["raw_known_line_incomplete_candidates"] == 27
            and summary["closed_candidates"] == 27
            and summary["open_known_line_incomplete_candidates"] == 0
            and summary["raw_missing_blocks"] == 70
            and summary["cumulative16_adjusted_missing_blocks"] == 0
            and summary["raw_unique_missing_serre_orbits"] == 25
            and summary["cumulative16_adjusted_unique_missing_serre_orbits"] == 0
            and summary["next_probe_orbit"] is None,
            str(path),
            "selected radius-4 frontier has no open candidates, blocks, or Serre orbits",
        ),
        "open_lists_empty": gate(
            report["open_known_line_incomplete_candidates"] == []
            and report["all_open_serre_orbits"] == []
            and summary["open_candidates_by_missing_serre_orbit_count"] == {},
            str(path),
            "all open frontier lists are empty",
        ),
        "closures_cover_demands": gate(
            len(report["closures_applied"]["closed_candidates"]) == 27
            and len(report["closures_applied"]["closed_serre_orbits"]) == 25
            and len(report["removed_serre_orbits"]) == 25,
            str(path),
            "closed candidate and Serre-orbit sets cover the raw missing-line demand",
        ),
        "markdown_exposes_exhaustion": gate(
            "open_known_line_incomplete_candidates: `0`" in md_text
            and "cumulative16_adjusted_missing_blocks: `0`" in md_text
            and "No branch produced" in md_text,
            str(md_path),
            "markdown exposes exhausted frontier and no-viable conclusion",
        ),
    }
    return {
        "scope": "verification for cumulative16 exhausted selected radius-4 frontier",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_cumulative16_exhausted_frontier_verification.json"
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
