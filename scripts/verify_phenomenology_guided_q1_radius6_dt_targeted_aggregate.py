#!/usr/bin/env python3
"""Verify aggregate closure for the radius-6 DT-targeted frontier."""

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
            "builder-side aggregate gates passed",
        ),
        "expected_totals_match": gate(
            summary["windows_closed"] == 3
            and summary["frontier_records_screened"] == 6149
            and summary["frontier_records_after_final_window"] == 0
            and summary["raw_q1_spectrum_survivors"] == 19
            and summary["branch_completions_evaluated"] == 34164
            and summary["desired_q1_branch_completions"] == 4740
            and summary["adjusted_desired_q1_candidates"] == 4743,
            str(report_json),
            "aggregate totals match the three verified radius6 DT-targeted windows",
        ),
        "uncertainties_closed": gate(
            summary["open_mass_monoid_solutions"] == 0
            and "missing_character_or_charge_level_data" not in statuses
            and "no_certified_triplet_mass_operator_found" not in statuses,
            str(report_json),
            "aggregate has no remaining character or mass-bound uncertainty buckets",
        ),
        "adjusted_statuses_match": gate(
            statuses
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 1,
                "negative_control_doublet_triplet_obstruction": 4728,
                "no_triplet_mass_in_certified_singlet_monoid": 14,
                "rejected_spectrum_signature_not_q1_three_family": 29424,
            },
            str(report_json),
            "aggregate adjusted obstruction totals match expected closure",
        ),
        "no_viable_candidate": gate(
            summary["viable_count"] == 0
            and report["status"]
            == "radius6_dt_targeted_frontier_exhausted_no_viable_candidate",
            str(report_json),
            "exhausted radius6 DT-targeted frontier contains no viable candidate",
        ),
        "markdown_exposes_aggregate": gate(
            "Radius-6 DT-Targeted Aggregate" in md_text
            and "frontier_records_after_final_window: `0`" in md_text
            and "viable_count: `0`" in md_text,
            str(report_md),
            "markdown exposes aggregate closure totals",
        ),
    }
    return {
        "scope": "verification for aggregate radius6 DT-targeted frontier closure",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_targeted_aggregate.json"),
    )
    parser.add_argument(
        "--report-md",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_targeted_aggregate.md"),
    )
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_targeted_aggregate_verification.json"),
    )
    args = parser.parse_args()
    result = verify(report_json=Path(args.report_json), report_md=Path(args.report_md))
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
