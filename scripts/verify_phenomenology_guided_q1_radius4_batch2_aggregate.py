#!/usr/bin/env python3
"""Verify the selected radius-4 batch-2 aggregate."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_batch2_aggregate.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_batch2_aggregate.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    gates = {
        "builder_gates_pass": gate(report["all_gates_pass"], str(path), "builder-side aggregate gates passed"),
        "coverage_matches_batch2": gate(
            report["coverage"]["frontier_size"] == 8743
            and report["coverage"]["covered_records"] == 8743
            and report["coverage"]["remaining_records"] == 0
            and report["coverage"]["intervals"] == [[0, 1600], [1600, 3200], [3200, 4800], [4800, 6400], [6400, 8000], [8000, 8743]],
            str(path),
            "batch-2 windows cover the selected frontier contiguously",
        ),
        "counts_match": gate(
            report["aggregate_totals"]["raw_q1_spectrum_survivors"] == 42
            and report["aggregate_totals"]["character_certified_q1_survivors"] == 18
            and report["aggregate_categories"] == {"phenomenologically obstructed": 18, "unresolved": 24}
            and report["viable_count"] == 0,
            str(path),
            "batch-2 q=1 survivor and classification counts match",
        ),
        "status_histogram_matches": gate(
            report["aggregate_statuses"] == {
                "dangerous_10_5bar_5bar_operator_allowed": 6,
                "missing_character_or_charge_level_data": 24,
                "negative_control_doublet_triplet_obstruction": 12,
            },
            str(path),
            "batch-2 status histogram matches window outputs",
        ),
        "markdown_exposes_summary": gate(
            "raw_q1_spectrum_survivors" in md_text
            and "viable count: `0`" in md_text
            and "source batch: `{'source_start': 16, 'source_limit': 16}`" in md_text,
            str(md_path),
            "markdown exposes batch-2 aggregate summary",
        ),
    }
    return {
        "scope": "verification for selected radius-4 batch-2 aggregate",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", default=str(REPORTS / "phenomenology_guided_q1_radius4_batch2_aggregate_verification.json"))
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
