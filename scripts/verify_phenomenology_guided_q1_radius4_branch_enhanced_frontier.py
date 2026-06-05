#!/usr/bin/env python3
"""Verify the branch-enhanced selected radius-4 frontier."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_branch_enhanced_frontier.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_branch_enhanced_frontier.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side branch-enhanced frontier gates passed",
        ),
        "frontier_accounting_matches": gate(
            report["summary"]["raw_q1_spectrum_survivors"] == 49
            and report["summary"]["strict_obstructed_count"] == 35
            and report["summary"]["branch_exhausted_nonviable_records"] == 13
            and report["summary"]["large_branch_closed_records"] == 1
            and report["summary"]["effective_viable_count"] == 0,
            str(path),
            "all selected radius-4 q=1 survivors are strict-obstructed, branch-exhausted, or large-branch closed",
        ),
        "branch_counts_match": gate(
            report["summary"]["branches_evaluated"] == 646
            and report["summary"]["desired_q1_branches"] == 102
            and report["summary"]["viable_branches"] == 0,
            str(path),
            "branch-enhanced frontier imports bounded branch-analysis counts",
        ),
        "large_branch_closure_imported": gate(
            report["summary"]["large_branch_desired_q1_branches"] == 41553
            and report["large_branch_closure"]["representative_classification"][
                "status"
            ]
            == "dangerous_10_5bar_5bar_operator_allowed",
            str(path),
            "the sole large branch is closed by support-invariant q=1 representative obstruction",
        ),
        "markdown_exposes_summary": gate(
            "strict_obstructed_count: `35`" in md_text
            and "branch_exhausted_nonviable_records: `13`" in md_text
            and "large_branch_closed_records: `1`" in md_text
            and "effective_viable_count: `0`" in md_text,
            str(md_path),
            "markdown exposes branch-enhanced frontier summary",
        ),
    }
    return {
        "scope": "verification for branch-enhanced selected radius-4 frontier",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_branch_enhanced_frontier_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
