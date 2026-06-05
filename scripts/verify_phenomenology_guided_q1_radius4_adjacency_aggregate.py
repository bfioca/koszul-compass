#!/usr/bin/env python3
"""Verify the selected radius-4 adjacency aggregate."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_adjacency_aggregate.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_adjacency_aggregate.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    intervals = report["coverage"]["intervals"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side aggregate gates passed",
        ),
        "coverage_is_contiguous_and_complete": gate(
            intervals == [[0, 1600], [1600, 3200], [3200, 4800], [4800, 6400], [6400, 8000], [8000, 8733]]
            and report["coverage"]["covered_records"] == 8733
            and report["coverage"]["remaining_records"] == 0,
            str(path),
            "six windows cover the selected radius-4 frontier contiguously",
        ),
        "aggregate_counts_match_expected_selected_sweep": gate(
            report["aggregate_totals"]["frontier_records_screened"] == 8733
            and report["aggregate_totals"]["raw_q1_spectrum_survivors"] == 49
            and report["aggregate_totals"]["raw_q1_certification_attempts"] == 49
            and report["aggregate_totals"]["character_certified_q1_survivors"] == 28,
            str(path),
            "selected radius-4 sweep totals match window outputs",
        ),
        "classification_counts_match": gate(
            report["aggregate_categories"]
            == {"phenomenologically obstructed": 28, "unresolved": 21}
            and report["aggregate_statuses"]
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 7,
                "missing_character_or_charge_level_data": 21,
                "negative_control_doublet_triplet_obstruction": 21,
            },
            str(path),
            "aggregate classification/status counts match the selected sweep",
        ),
        "no_viable_candidate_found": gate(
            report["viable_count"] == 0,
            str(path),
            "no viable candidate appears in the selected radius-4 aggregate",
        ),
        "markdown_exposes_selected_scope": gate(
            "Selected Radius-4 Adjacency Aggregate" in md_text
            and "not a global radius-4 theorem" not in md_text
            and "selected source set" in md_text
            and "viable count: `0`" in md_text,
            str(md_path),
            "markdown exposes the selected-frontier summary",
        ),
    }
    return {
        "scope": "verification for selected radius-4 adjacency aggregate",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_adjacency_aggregate_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
