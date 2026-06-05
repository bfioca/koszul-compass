#!/usr/bin/env python3
"""Verify a radius-6 closed frontier report with large branch closures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def verify(*, report_json: Path, report_md: Path) -> dict[str, Any]:
    report = load_json(report_json)
    md_text = report_md.read_text(encoding="utf-8")
    summary = report["summary"]
    statuses = summary["adjusted_statuses"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(report_json),
            "builder-side large-aware closed frontier gates passed",
        ),
        "counts_consistent": gate(
            summary["adjusted_desired_q1_candidates"]
            == summary["direct_character_certified_q1_records"]
            + summary["bounded_desired_q1_branch_completions"]
            + summary["large_desired_q1_branch_completions"]
            and sum(statuses.values())
            == summary["adjusted_desired_q1_candidates"]
            + statuses.get("rejected_spectrum_signature_not_q1_three_family", 0),
            str(report_json),
            "direct, bounded, and large branch counts are internally consistent",
        ),
        "uncertainties_closed": gate(
            summary["open_mass_monoid_solutions"] == 0
            and "missing_character_or_charge_level_data" not in statuses
            and "no_certified_triplet_mass_operator_found" not in statuses,
            str(report_json),
            "no character or mass-bound uncertainty buckets remain",
        ),
        "no_viable_candidate": gate(
            summary["viable_count"] == 0
            and report["status"].endswith("_closed_no_viable_candidate"),
            str(report_json),
            "large-aware closed frontier contains no viable candidate",
        ),
        "markdown_exposes_result": gate(
            report["title"] in md_text
            and "viable_count: `0`" in md_text
            and "large_branch_completions_counted" in md_text,
            str(report_md),
            "markdown exposes large-aware closure totals",
        ),
    }
    return {
        "scope": "verification for radius6 large-aware closed frontier",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-json", required=True)
    parser.add_argument("--report-md", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args()
    result = verify(report_json=Path(args.report_json), report_md=Path(args.report_md))
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
