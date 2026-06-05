#!/usr/bin/env python3
"""Verify medium-priority map-scenario enumeration."""

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
    path = REPORTS / "phenomenology_guided_q1_radius2_medium_map_scenarios.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_medium_map_scenarios.md"
    current_path = REPORTS / "phenomenology_guided_q1_radius2_current_frontier.json"
    report = load_json(path)
    current = load_json(current_path)
    md_text = md_path.read_text(encoding="utf-8")
    records = report["records"]
    supported = [
        record for record in records if record["all_blocks_supported_by_two_term_rank_scenarios"]
    ]
    unsupported = [record for record in records if record["unsupported_block_count"] > 0]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"] and all(item["pass"] for item in report["gates"].values()),
            str(path),
            "medium map-scenario builder gates pass",
        ),
        "imports_current_medium_frontier": gate(
            current["summary"]["remaining_medium_records"] == 5
            and report["summary"]["medium_records"] == 5,
            f"{path}, {current_path}",
            "scenario report starts from the current five-record medium frontier",
        ),
        "two_term_and_three_term_split_matches": gate(
            len(supported) == 3
            and len(unsupported) == 2
            and sum(record["unsupported_block_count"] for record in records) == 4,
            str(path),
            "medium frontier splits into three two-term records and two three-term records",
        ),
        "desired_q1_scenarios_remain": gate(
            report["summary"]["total_scenarios"] == 14
            and report["summary"]["total_desired_q1_scenarios"] == 6
            and report["summary"]["records_with_desired_q1_scenarios"] == 3,
            str(path),
            "all two-term medium records still have desired q=1 rank scenarios",
        ),
        "markdown_matches_report": gate(
            "Status: `medium_two_term_desired_q1_scenarios_remain_possible`" in md_text
            and "two_term_supported_records: `3`" in md_text
            and "total_desired_q1_scenarios: `6`" in md_text,
            str(md_path),
            "markdown exposes medium scenario counts",
        ),
    }
    return {
        "scope": "verification for medium-priority map-scenario enumeration",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_medium_map_scenarios_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    Path(args.json_out).write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
