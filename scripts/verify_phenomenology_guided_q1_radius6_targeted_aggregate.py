#!/usr/bin/env python3
"""Generic verifier for radius-6 targeted aggregate frontier reports."""

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
    closed_reports = [load_json(Path(path)) for path in report["closed_window_reports"]]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(report_json),
            "builder-side aggregate gates passed",
        ),
        "window_totals_match": gate(
            summary["windows_closed"] == len(closed_reports)
            and summary["frontier_records_screened"]
            == sum(item["summary"]["frontier_records_screened"] for item in closed_reports)
            and summary["raw_q1_spectrum_survivors"]
            == sum(item["summary"]["raw_q1_spectrum_survivors"] for item in closed_reports)
            and summary["adjusted_desired_q1_candidates"]
            == sum(item["summary"]["adjusted_desired_q1_candidates"] for item in closed_reports),
            str(report_json),
            "aggregate totals equal the sum of closed window reports",
        ),
        "frontier_exhausted": gate(
            summary["frontier_records_after_final_window"] == 0,
            str(report_json),
            "final targeted window exhausts the frontier",
        ),
        "uncertainties_closed": gate(
            summary["open_mass_monoid_solutions"] == 0
            and "missing_character_or_charge_level_data" not in statuses
            and "no_certified_triplet_mass_operator_found" not in statuses,
            str(report_json),
            "aggregate has no remaining character or mass-bound uncertainty buckets",
        ),
        "status_accounting_consistent": gate(
            sum(statuses.values())
            == summary["adjusted_desired_q1_candidates"]
            + statuses.get("rejected_spectrum_signature_not_q1_three_family", 0),
            str(report_json),
            "adjusted status totals are internally consistent",
        ),
        "no_viable_candidate": gate(
            summary["viable_count"] == 0,
            str(report_json),
            "aggregate targeted frontier contains no viable candidate",
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
        "scope": "generic verification for radius6 targeted aggregate closure",
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
        default=str(REPORTS / "phenomenology_guided_q1_radius6_targeted_aggregate_verification.json"),
    )
    args = parser.parse_args()
    result = verify(report_json=Path(args.report_json), report_md=Path(args.report_md))
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
