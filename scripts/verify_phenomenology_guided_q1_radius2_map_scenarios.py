#!/usr/bin/env python3
"""Verify high-priority residual map-scenario enumeration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

DESIRED_Q1 = {
    "colored_triplet_vectorlike_pairs": 1,
    "electroweak_doublet_vectorlike_pairs": 1,
    "h1_wedge2_regular_multiplicity": 4,
    "h2_wedge2_regular_multiplicity": 1,
    "net_families": 3,
    "regular_character_rule_applies": True,
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def verify() -> dict[str, Any]:
    path = REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.md"
    residual_path = REPORTS / "phenomenology_guided_q1_radius2_residual_backlog.json"
    report = load_json(path)
    residual = load_json(residual_path)
    md_text = md_path.read_text(encoding="utf-8")
    records = report["records"]

    desired_outcome_counts = []
    nonregular_outcome_counts = []
    for record in records:
        desired = [
            item
            for item in record["prediction_outcomes"]
            if item["prediction"] == DESIRED_Q1
        ]
        nonregular = [
            item
            for item in record["prediction_outcomes"]
            if item["prediction"].get("regular_character_rule_applies") is False
        ]
        desired_outcome_counts.append(desired[0]["count"] if desired else 0)
        nonregular_outcome_counts.append(nonregular[0]["count"] if nonregular else 0)

    verification_gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"] and all(item["pass"] for item in report["gates"].values()),
            str(path),
            "map-scenario builder gates pass",
        ),
        "imports_high_priority_residual_records": gate(
            residual["summary"]["priority_buckets"]["high_priority_q1_or_adjacent"] == 4
            and report["summary"]["records"] == 4
            and len(records) == 4,
            f"{residual_path}, {path}",
            "scenario enumeration imports the four high-priority residual records",
        ),
        "scenario_counts_match": gate(
            report["summary"]["total_scenarios"] == 36
            and report["summary"]["total_desired_q1_scenarios"] == 12
            and report["summary"]["records_with_desired_q1_scenarios"] == 4
            and all(record["scenario_product_count"] == 9 for record in records)
            and all(record["desired_q1_scenario_count"] == 3 for record in records),
            str(path),
            "each high-priority record has nine rank scenarios and three desired-q1 scenarios",
        ),
        "block_scenarios_are_two_term_rank_splits": gate(
            all(
                record["all_blocks_supported_by_two_term_rank_scenarios"]
                and record["unsupported_block_count"] == 0
                and [block["scenario_count"] for block in record["block_summaries"]]
                == [3, 3]
                for record in records
            ),
            str(path),
            "each high-priority record has two supported two-term map blocks with three rank splits each",
        ),
        "outcomes_are_desired_or_nonregular": gate(
            desired_outcome_counts == [3, 3, 3, 3]
            and nonregular_outcome_counts == [6, 6, 6, 6],
            str(path),
            "rank scenarios either give the desired q=1 regular wedge character or a nonregular unresolved character",
        ),
        "markdown_matches_report": gate(
            "records: `4`" in md_text
            and "total rank scenarios: `36`" in md_text
            and "desired q=1 rank scenarios: `12`" in md_text
            and "actual equivariant map rank split" in md_text,
            str(md_path),
            "markdown exposes scenario counts and actual-rank bottleneck",
        ),
    }
    return {
        "scope": "verification for high-priority residual map-scenario enumeration",
        "all_gates_pass": all(item["pass"] for item in verification_gates.values()),
        "gates": verification_gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius2_map_scenarios_verification.json"
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
