#!/usr/bin/env python3
"""Verify the first radius-5 window closed-frontier summary."""

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


def verify(
    *,
    frontier_json: Path,
    frontier_md: Path,
    expected_screened: int,
    expected_raw_q1: int,
    expected_missing_closed: int,
    expected_branches: int,
    expected_desired: int,
) -> dict[str, Any]:
    path = frontier_json
    md_path = frontier_md
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    summary = report["summary"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side radius5 window1 closed-frontier gates passed",
        ),
        "window_counts_match": gate(
            summary["radius4_sources_selected"] == 8
            and summary["frontier_records_screened"] == expected_screened
            and summary["raw_q1_spectrum_survivors"] == expected_raw_q1
            and summary["missing_character_records_branch_closed"] == expected_missing_closed
            and summary["branch_completions_evaluated"] == expected_branches
            and summary["desired_q1_branch_completions"] == expected_desired,
            str(path),
            "radius5 window1 closure counts match scout and branch-analysis reports",
        ),
        "no_open_missing_or_viable": gate(
            "missing_character_or_charge_level_data" not in summary["adjusted_statuses"]
            and summary["viable_count"] == 0,
            str(path),
            "radius5 window1 has no open missing-character rows and no viable candidate",
        ),
        "markdown_exposes_window": gate(
            "Closed Frontier" in md_text
            and f"raw_q1_spectrum_survivors: `{expected_raw_q1}`" in md_text
            and "viable_count: `0`" in md_text,
            str(md_path),
            "markdown exposes radius5 window1 closure totals",
        ),
    }
    return {
        "scope": "verification for first radius5 window closed frontier",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--frontier-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_window1_closed_frontier.json"),
    )
    parser.add_argument(
        "--frontier-md",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_window1_closed_frontier.md"),
    )
    parser.add_argument("--expected-raw-q1", type=int, default=16)
    parser.add_argument("--expected-screened", type=int, default=1600)
    parser.add_argument("--expected-missing-closed", type=int, default=10)
    parser.add_argument("--expected-branches", type=int, default=10422)
    parser.add_argument("--expected-desired", type=int, default=1596)
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_window1_closed_frontier_verification.json"),
    )
    args = parser.parse_args()
    result = verify(
        frontier_json=Path(args.frontier_json),
        frontier_md=Path(args.frontier_md),
        expected_screened=args.expected_screened,
        expected_raw_q1=args.expected_raw_q1,
        expected_missing_closed=args.expected_missing_closed,
        expected_branches=args.expected_branches,
        expected_desired=args.expected_desired,
    )
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
