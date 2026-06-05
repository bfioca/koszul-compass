#!/usr/bin/env python3
"""Verify the partial aggregate for completed batch-3 radius-4 windows."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_batch3_partial_aggregate.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_batch3_partial_aggregate.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    totals = report["aggregate_totals"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side batch-3 partial aggregate gates passed",
        ),
        "coverage_is_prefix": gate(
            report["coverage"]["frontier_size"] == 8755
            and report["coverage"]["covered_records"] == 3200
            and report["coverage"]["remaining_records"] == 5555
            and report["coverage"]["intervals"] == [[0, 1600], [1600, 3200]],
            str(path),
            "partial aggregate covers the first two contiguous batch-3 windows",
        ),
        "q1_counts_match": gate(
            totals["raw_q1_spectrum_survivors"] == 24
            and totals["raw_q1_certification_attempts"] == 24
            and totals["character_certified_q1_survivors"] == 23,
            str(path),
            "partial aggregate preserves q=1 scout counts before known-line closure",
        ),
        "final_classifications_closed": gate(
            report["initial_categories"] == {"phenomenologically obstructed": 23, "unresolved": 1}
            and report["initial_statuses"]
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 11,
                "missing_character_or_charge_level_data": 1,
                "negative_control_doublet_triplet_obstruction": 12,
            }
            and
            report["final_categories_after_known_line"] == {"phenomenologically obstructed": 24}
            and report["final_statuses_after_known_line"]
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 11,
                "negative_control_doublet_triplet_obstruction": 13,
            }
            and report["viable_count"] == 0,
            str(path),
            "known-line closure leaves no viable or unresolved candidate in completed windows",
        ),
        "markdown_exposes_partial_scope": gate(
            "Batch 3 Partial Aggregate" in md_text
            and "remaining_records': 5555" in md_text
            and "final categories after known-line" in md_text,
            str(md_path),
            "markdown exposes partial scope and final closed classifications",
        ),
    }
    return {
        "scope": "verification for batch-3 partial radius-4 aggregate",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_batch3_partial_aggregate_verification.json"
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
