#!/usr/bin/env python3
"""Verify an aggregate of radius-5 source-slice closures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def verify(
    *,
    aggregate_json: Path,
    aggregate_md: Path,
    expected_slices: int,
    expected_sources: int,
    expected_screened: int,
    expected_raw_q1: int,
    expected_bounded: int,
    expected_large: int,
    expected_desired: int,
) -> dict[str, Any]:
    report = load_json(aggregate_json)
    md_text = aggregate_md.read_text(encoding="utf-8")
    summary = report["summary"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(aggregate_json),
            "builder-side aggregate gates passed",
        ),
        "aggregate_counts_match": gate(
            summary["source_slices_closed"] == expected_slices
            and summary["radius4_sources_closed"] == expected_sources
            and summary["frontier_records_screened"] == expected_screened
            and summary["open_frontier_after_slices"] == 0
            and summary["raw_q1_spectrum_survivors"] == expected_raw_q1
            and summary["bounded_branch_completions_evaluated"] == expected_bounded
            and summary["large_branch_completions_counted"] == expected_large
            and summary["desired_q1_branch_completions"] == expected_desired,
            str(aggregate_json),
            "aggregate totals match expected slice closure counts",
        ),
        "no_viable_candidate": gate(
            summary["viable_count"] == 0,
            str(aggregate_json),
            "aggregate has no viable candidate",
        ),
        "markdown_exposes_aggregate": gate(
            report["title"] in md_text
            and "open_frontier_after_slices: `0`" in md_text
            and "viable_count: `0`" in md_text,
            str(aggregate_md),
            "markdown exposes aggregate closure totals",
        ),
    }
    return {
        "scope": "verification for radius5 source-slice aggregate",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aggregate-json", required=True)
    parser.add_argument("--aggregate-md", required=True)
    parser.add_argument("--expected-slices", type=int, required=True)
    parser.add_argument("--expected-sources", type=int, required=True)
    parser.add_argument("--expected-screened", type=int, required=True)
    parser.add_argument("--expected-raw-q1", type=int, required=True)
    parser.add_argument("--expected-bounded", type=int, required=True)
    parser.add_argument("--expected-large", type=int, required=True)
    parser.add_argument("--expected-desired", type=int, required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args()
    result = verify(
        aggregate_json=Path(args.aggregate_json),
        aggregate_md=Path(args.aggregate_md),
        expected_slices=args.expected_slices,
        expected_sources=args.expected_sources,
        expected_screened=args.expected_screened,
        expected_raw_q1=args.expected_raw_q1,
        expected_bounded=args.expected_bounded,
        expected_large=args.expected_large,
        expected_desired=args.expected_desired,
    )
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
