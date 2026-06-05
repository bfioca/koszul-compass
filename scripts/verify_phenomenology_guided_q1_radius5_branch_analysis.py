#!/usr/bin/env python3
"""Verify radius-5 bounded branch analysis."""

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
    analysis_json: Path,
    analysis_md: Path,
    expected_unresolved: int,
    expected_evaluated: int,
    expected_skipped: int,
    expected_branches: int,
) -> dict[str, Any]:
    path = analysis_json
    md_path = analysis_md
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    summary = report["summary"]
    desired_records = report["desired_q1_branch_candidate_records"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side radius-5 branch analysis gates passed",
        ),
        "all_radius5_incomplete_records_evaluated": gate(
            summary["unresolved_records"] == expected_unresolved
            and summary["records_evaluated"] == expected_evaluated
            and summary["records_skipped"] == expected_skipped
            and summary["branches_evaluated"] == expected_branches,
            str(path),
            "all radius-5 known-line-incomplete rows are branch-enumerated",
        ),
        "desired_q1_records_have_required_tables": gate(
            summary["desired_q1_branches"] == len(desired_records)
            and all(
                item["spectrum_certificate"]["desired_q1_three_family_signature"]
                and item["character_certificate"]["character_certified"]
                and item["mass_operator_table"] is not None
                and item["proton_decay_operator_table"] is not None
                for item in desired_records
            ),
            str(path),
            "every desired-q1 branch emits spectrum, character, mass, and proton tables",
        ),
        "summary_status_counts_cover_all_branches": gate(
            sum(summary["categories"].values()) == summary["branches_evaluated"]
            and sum(summary["statuses"].values()) == summary["branches_evaluated"],
            str(path),
            "category and status totals cover every evaluated branch",
        ),
        "markdown_exposes_branch_analysis": gate(
            "Radius-5 Branch Analysis" in md_text
            and f"branches_evaluated: `{expected_branches}`" in md_text
            and f"records_skipped: `{expected_skipped}`" in md_text,
            str(md_path),
            "markdown exposes radius-5 branch-closure totals",
        ),
    }
    return {
        "scope": "verification for radius-5 bounded branch analysis",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--analysis-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_branch_analysis.json"),
    )
    parser.add_argument(
        "--analysis-md",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_branch_analysis.md"),
    )
    parser.add_argument("--expected-unresolved", type=int, default=10)
    parser.add_argument("--expected-evaluated", type=int, default=10)
    parser.add_argument("--expected-skipped", type=int, default=0)
    parser.add_argument("--expected-branches", type=int, default=10422)
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius5_branch_analysis_verification.json"
        ),
    )
    args = parser.parse_args()
    result = verify(
        analysis_json=Path(args.analysis_json),
        analysis_md=Path(args.analysis_md),
        expected_unresolved=args.expected_unresolved,
        expected_evaluated=args.expected_evaluated,
        expected_skipped=args.expected_skipped,
        expected_branches=args.expected_branches,
    )
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
