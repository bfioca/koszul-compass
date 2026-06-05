#!/usr/bin/env python3
"""Verify selected radius-4 batch-4 scout aggregate."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_batch4_aggregate.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_batch4_aggregate.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    totals = report["aggregate_totals"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side batch-4 aggregate gates passed",
        ),
        "coverage_complete": gate(
            report["coverage"]["frontier_size"] == 8269
            and report["coverage"]["covered_records"] == 8269
            and report["coverage"]["remaining_records"] == 0,
            str(path),
            "batch-4 aggregate covers the complete selected scout frontier",
        ),
        "q1_counts_match": gate(
            totals["raw_q1_spectrum_survivors"] == 48
            and totals["raw_q1_certification_attempts"] == 48
            and totals["character_certified_q1_survivors"] == 9,
            str(path),
            "batch-4 q=1 survivor counts match window totals",
        ),
        "classification_counts_match": gate(
            report["categories"] == {"phenomenologically obstructed": 9, "unresolved": 39}
            and report["statuses"]
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 4,
                "missing_character_or_charge_level_data": 39,
                "negative_control_doublet_triplet_obstruction": 5,
            }
            and report["viable_count"] == 0,
            str(path),
            "batch-4 scout classifications show no viable candidate",
        ),
        "markdown_exposes_result": gate(
            "Selected Radius-4 Batch 4 Scout Aggregate" in md_text
            and "remaining_records': 0" in md_text
            and "missing_character_or_charge_level_data" in md_text,
            str(md_path),
            "markdown exposes complete scout coverage and unresolved character queue",
        ),
    }
    return {
        "scope": "verification for selected radius-4 batch-4 scout aggregate",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_batch4_aggregate_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
