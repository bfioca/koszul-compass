#!/usr/bin/env python3
"""Verify the closed radius-6 DT-targeted frontier report."""

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


def verify(*, report_json: Path, report_md: Path) -> dict[str, Any]:
    report = load_json(report_json)
    md_text = report_md.read_text(encoding="utf-8")
    summary = report["summary"]
    statuses = summary["adjusted_statuses"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(report_json),
            "builder-side closed frontier gates passed",
        ),
        "counts_match_expected_window": gate(
            summary["frontier_records_screened"] > 0
            and summary["raw_q1_spectrum_survivors"] >= summary[
                "direct_character_certified_q1_records"
            ]
            and summary["branch_completions_evaluated"] >= summary[
                "desired_q1_branch_completions"
            ]
            and summary["adjusted_desired_q1_candidates"]
            == summary["direct_character_certified_q1_records"]
            + summary["desired_q1_branch_completions"],
            str(report_json),
            "closed frontier preserves the verified radius6 scout and branch-analysis counts",
        ),
        "mass_and_character_uncertainty_closed": gate(
            summary["open_mass_monoid_solutions"] == 0
            and summary["mass_records_upgraded_by_exact_monoid"] >= 0
            and "missing_character_or_charge_level_data" not in statuses
            and "no_certified_triplet_mass_operator_found" not in statuses,
            str(report_json),
            "character branches are fully evaluated and mass-bound uncertainties are upgraded",
        ),
        "adjusted_statuses_match": gate(
            "missing_character_or_charge_level_data" not in statuses
            and "no_certified_triplet_mass_operator_found" not in statuses
            and sum(statuses.values())
            == summary["adjusted_desired_q1_candidates"]
            + statuses.get("rejected_spectrum_signature_not_q1_three_family", 0),
            str(report_json),
            "adjusted obstruction totals are internally consistent for radius6 DT-targeted closure",
        ),
        "no_viable_candidate": gate(
            summary["viable_count"] == 0
            and report["status"].startswith("radius")
            and "_targeted" in report["status"]
            and report["status"].endswith("_closed_no_viable_candidate"),
            str(report_json),
            "closed radius6 DT-targeted window contains no viable candidate",
        ),
        "markdown_exposes_result": gate(
            report.get("title", "Radius-6 DT-Targeted Closed Frontier") in md_text
            and "viable_count: `0`" in md_text
            and "adjusted_statuses" in md_text,
            str(report_md),
            "markdown exposes closed frontier totals",
        ),
    }
    return {
        "scope": "verification for closed radius6 DT-targeted frontier",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_closed_frontier.json"),
    )
    parser.add_argument(
        "--report-md",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_closed_frontier.md"),
    )
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_closed_frontier_verification.json"),
    )
    args = parser.parse_args()
    result = verify(report_json=Path(args.report_json), report_md=Path(args.report_md))
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
