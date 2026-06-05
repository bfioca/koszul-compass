#!/usr/bin/env python3
"""Verify the selected radius-4 missing line-character demand report."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_missing_line_demand.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_missing_line_demand.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    summary = report["summary"]
    demand_rows = report["all_missing_serre_orbits"]
    candidates = report["known_line_incomplete_candidates"]

    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side missing-line demand gates passed",
        ),
        "summary_counts_match_frontier": gate(
            summary["candidate_records"] == 45
            and summary["known_line_incomplete_candidates"] == 27
            and summary["mass_level_unresolved_candidates"] == 1
            and summary["raw_missing_blocks"] == 70
            and summary["unique_missing_serre_orbits"] == 25,
            str(path),
            "summary counts match the combined known-line frontier",
        ),
        "candidate_unlock_distribution_match": gate(
            summary["candidates_by_missing_serre_orbit_count"]
            == {"1": 23, "2": 3, "6": 1},
            str(path),
            "candidate missing-orbit distribution matches expected low-cost unlock frontier",
        ),
        "top_orbit_is_highest_demand": gate(
            demand_rows[0]["serre_orbit_representative"]
            == [0, 0, -2, 1, -1, 1, -1]
            and demand_rows[0]["candidate_count"] == 5
            and demand_rows[0]["block_count"] == 10,
            str(path),
            "top Serre orbit is the largest current missing-character demand",
        ),
        "demand_rows_are_ranked": gate(
            all(
                (
                    demand_rows[index]["candidate_count"],
                    demand_rows[index]["block_count"],
                )
                >= (
                    demand_rows[index + 1]["candidate_count"],
                    demand_rows[index + 1]["block_count"],
                )
                for index in range(len(demand_rows) - 1)
            ),
            str(path),
            "demand rows are monotonically ranked by candidate and block count",
        ),
        "candidate_rows_are_ranked": gate(
            all(
                candidates[index]["missing_serre_orbit_count"]
                <= candidates[index + 1]["missing_serre_orbit_count"]
                for index in range(len(candidates) - 1)
            ),
            str(path),
            "candidate unlock rows are ranked by missing Serre-orbit count",
        ),
        "mass_level_unresolved_exposed": gate(
            len(report["mass_level_unresolved_candidates"]) == 1
            and report["mass_level_unresolved_candidates"][0]["classification"]["status"]
            == "no_certified_triplet_mass_operator_found",
            str(path),
            "mass-level unresolved candidate is separated from character probe queue",
        ),
        "markdown_exposes_queue": gate(
            "unique_missing_serre_orbits: `25`" in md_text
            and "[0, 0, -2, 1, -1, 1, -1]" in md_text
            and "no_certified_triplet_mass_operator_found" in md_text,
            str(md_path),
            "markdown exposes the ranked queue and mass-level unresolved record",
        ),
    }
    return {
        "scope": "verification for selected radius-4 missing line-character demand",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_missing_line_demand_verification.json"
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
