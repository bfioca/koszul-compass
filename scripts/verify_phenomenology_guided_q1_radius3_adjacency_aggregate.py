#!/usr/bin/env python3
"""Verify the radius-3 adjacency scout aggregate."""

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
    path = REPORTS / "phenomenology_guided_q1_radius3_adjacency_aggregate.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius3_adjacency_aggregate.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder aggregate gates all passed",
        ),
        "coverage_is_full_frontier": gate(
            report["coverage"]["intervals"]
            == [[0, 4000], [4000, 8000], [8000, 12000], [12000, 15595]]
            and report["coverage"]["covered_records"] == 15595
            and report["coverage"]["remaining_records"] == 0,
            str(path),
            "aggregate covers the full bounded radius-3 adjacency frontier",
        ),
        "totals_match_windows": gate(
            report["aggregate_totals"]["raw_q1_spectrum_survivors"] == 64
            and report["aggregate_totals"]["character_certified_q1_survivors"] == 32
            and report["aggregate_totals"]["viable_count"] == 0
            and report["aggregate_totals"]["cohomology_exceptions"] == 1,
            str(path),
            "aggregate totals match the imported window reports",
        ),
        "classification_distribution": gate(
            report["aggregate_categories"]
            == {"phenomenologically obstructed": 30, "unresolved": 34}
            and report["aggregate_statuses"]
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 10,
                "missing_character_or_charge_level_data": 32,
                "negative_control_doublet_triplet_obstruction": 20,
                "no_certified_triplet_mass_operator_found": 2,
            },
            str(path),
            "all certified radius-3 adjacency q=1 records in the aggregate are obstructed",
        ),
        "markdown_exposes_aggregate": gate(
            "Status: `no_viable_candidate_found_in_full_radius3_adjacency_frontier`"
            in md_text
            and "covered records: `15595`" in md_text
            and "remaining records: `0`" in md_text,
            str(md_path),
            "markdown exposes aggregate coverage and status",
        ),
    }
    return {
        "scope": "verification for radius-3 adjacency scout aggregate",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_adjacency_aggregate_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
