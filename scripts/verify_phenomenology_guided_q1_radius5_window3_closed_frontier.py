#!/usr/bin/env python3
"""Verify radius-5 window 3 closed-frontier summary."""

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
    expected_after: int,
    expected_raw_q1: int,
    expected_missing: int,
    expected_bounded_records: int,
    expected_large_records: int,
    expected_bounded_branches: int,
    expected_large_branches: int,
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
            "builder-side radius5 window3 closed-frontier gates passed",
        ),
        "window3_counts_match": gate(
            summary["frontier_records_screened"] == expected_screened
            and summary["frontier_records_after_window"] == expected_after
            and summary["raw_q1_spectrum_survivors"] == expected_raw_q1
            and summary["missing_character_records"] == expected_missing
            and summary["bounded_records_evaluated"] == expected_bounded_records
            and summary["large_records_closed"] == expected_large_records
            and summary["bounded_branch_completions_evaluated"] == expected_bounded_branches
            and summary["large_branch_completions_counted"] == expected_large_branches
            and summary["desired_q1_branch_completions"] == expected_desired,
            str(path),
            "window3 closed-frontier counts match scout, bounded branch, and large closure reports",
        ),
        "no_viable_candidate": gate(
            summary["viable_count"] == 0,
            str(path),
            "window3 has no viable q1 branch completion",
        ),
        "markdown_exposes_window3": gate(
            report.get("title", "Radius-5 Window 3 Closed Frontier") in md_text
            and f"frontier_records_after_window: `{expected_after}`" in md_text
            and "viable_count: `0`" in md_text,
            str(md_path),
            "markdown exposes radius5 window3 closure totals",
        ),
    }
    return {
        "scope": "verification for radius5 window3 closed frontier",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--frontier-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_window3_closed_frontier.json"),
    )
    parser.add_argument(
        "--frontier-md",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_window3_closed_frontier.md"),
    )
    parser.add_argument("--expected-screened", type=int, default=1230)
    parser.add_argument("--expected-after", type=int, default=0)
    parser.add_argument("--expected-raw-q1", type=int, default=6)
    parser.add_argument("--expected-missing", type=int, default=6)
    parser.add_argument("--expected-bounded-records", type=int, default=5)
    parser.add_argument("--expected-large-records", type=int, default=1)
    parser.add_argument("--expected-bounded-branches", type=int, default=1989)
    parser.add_argument("--expected-large-branches", type=int, default=531441)
    parser.add_argument("--expected-desired", type=int, default=41772)
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius5_window3_closed_frontier_verification.json"
        ),
    )
    args = parser.parse_args()
    result = verify(
        frontier_json=Path(args.frontier_json),
        frontier_md=Path(args.frontier_md),
        expected_screened=args.expected_screened,
        expected_after=args.expected_after,
        expected_raw_q1=args.expected_raw_q1,
        expected_missing=args.expected_missing,
        expected_bounded_records=args.expected_bounded_records,
        expected_large_records=args.expected_large_records,
        expected_bounded_branches=args.expected_bounded_branches,
        expected_large_branches=args.expected_large_branches,
        expected_desired=args.expected_desired,
    )
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
