#!/usr/bin/env python3
"""Verify selected radius-4 branch-closed no-go summary."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_selected_branch_closed_no_go.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_selected_branch_closed_no_go.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    summary = report["summary"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side selected branch-closed no-go gates passed",
        ),
        "coverage_counts_match": gate(
            summary["source_records_expanded"] == 63
            and summary["frontier_records"] == 34500
            and summary["covered_records"] == 34500
            and summary["raw_q1_spectrum_survivors"] == 200,
            str(path),
            "selected radius-4 coverage and raw q1 totals match source coverage report",
        ),
        "component_counts_match": gate(
            summary["batch1_2_raw_q1_survivors"] == 91
            and summary["batch3_raw_q1_survivors"] == 61
            and summary["batch4_raw_q1_survivors"] == 48
            and summary["known_line_incomplete_records_branch_closed"] == 71
            and summary["explicit_branch_completions_evaluated_for_batches3_4"] == 31874
            and summary["desired_q1_branch_completions_for_batches3_4"] == 2646,
            str(path),
            "component branch-closure counts match post-exhaustion, batch3, and batch4 reports",
        ),
        "no_open_uncertainty_or_viable_candidate": gate(
            summary["mass_bound_cases_upgraded_by_exact_monoid"] == 12
            and summary["open_character_frontier_count"] == 0
            and summary["open_mass_bound_uncertainties"] == 0
            and summary["viable_count"] == 0,
            str(path),
            "selected radius-4 no-go has no open character frontier, mass uncertainty, or viable candidate",
        ),
        "markdown_exposes_no_go": gate(
            "Selected Radius-4 Branch-Closed No-Go" in md_text
            and "raw_q1_spectrum_survivors: `200`" in md_text
            and "viable_count: `0`" in md_text,
            str(md_path),
            "markdown exposes selected radius-4 branch-closed no-go totals",
        ),
    }
    return {
        "scope": "verification for selected radius-4 branch-closed no-go",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_selected_branch_closed_no_go_verification.json"
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
