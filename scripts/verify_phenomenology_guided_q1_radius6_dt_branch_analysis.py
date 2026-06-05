#!/usr/bin/env python3
"""Verify the radius-6 DT-targeted branch-analysis artifact."""

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


def verify(*, report_json: Path, report_md: Path, scout_verification_json: Path) -> dict[str, Any]:
    report = load_json(report_json)
    scout_verification = load_json(scout_verification_json)
    md_text = report_md.read_text(encoding="utf-8")
    summary = report["summary"]
    desired = report["desired_q1_branch_candidate_records"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(report_json),
            "builder-side radius6 branch-analysis gates passed",
        ),
        "imports_verified_radius6_scout": gate(
            scout_verification["all_gates_pass"]
            and report["gates"]["imports_verified_radius6_scout"]["pass"],
            str(scout_verification_json),
            "branch analysis imports the verified radius6 targeted scout",
        ),
        "missing_character_accounting": gate(
            summary["unresolved_records"]
            == summary["records_evaluated"] + summary["records_skipped"]
            and summary["unresolved_records"] >= 0,
            str(report_json),
            "all radius6 missing-character records are either evaluated or explicitly skipped",
        ),
        "branch_accounting_matches": gate(
            report["gates"]["branch_accounting_matches"]["pass"]
            and summary["branches_evaluated"]
            == sum(
                item.get("branches_evaluated", 0)
                for item in report["record_branch_reports"]
            ),
            str(report_json),
            "branch summaries account for every evaluated branch",
        ),
        "desired_q1_certificates_have_tables": gate(
            report["gates"]["desired_q1_certificates_have_tables"]["pass"]
            and len(desired) == summary["desired_q1_branches"]
            and all(
                item["spectrum_certificate"]["desired_q1_three_family_signature"]
                and item["character_certificate"]["character_certified"]
                and item["mass_operator_table"] is not None
                and item["proton_decay_operator_table"] is not None
                for item in desired
            ),
            str(report_json),
            "every desired q1 branch emits spectrum, character, mass, proton, and classification evidence",
        ),
        "no_viable_branch": gate(
            report["status"] == "no_viable_branch_found_in_radius6_dt_branch_analysis"
            and summary["viable_branches"] == 0,
            str(report_json),
            "no evaluated radius6 branch completion passes the current charge-level filter",
        ),
        "skipped_frontier_explicit": gate(
            summary["records_skipped"] == len(report["skipped_records"])
            and (
                summary["records_skipped"] == 0
                or all(
                    item["reason"] == "branch_space_exceeds_configured_bound"
                    for item in report["skipped_records"]
                )
            ),
            str(report_json),
            "large unresolved branch spaces are either fully evaluated or preserved as explicit frontier records",
        ),
        "radius6_branch_frontier_closed": gate(
            summary["records_skipped"] == 0
            and summary["records_evaluated"] == summary["unresolved_records"]
            and report["gates"]["branch_accounting_matches"]["pass"],
            str(report_json),
            "all radius6 missing-character branch spaces are fully evaluated",
        ),
        "markdown_exposes_result": gate(
            "Radius-6 DT Branch Analysis" in md_text
            and "desired_q1_branches" in md_text
            and "records_skipped" in md_text,
            str(report_md),
            "markdown exposes branch-analysis totals",
        ),
    }
    return {
        "scope": "verification for radius6 DT-targeted branch analysis",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_branch_analysis.json"),
    )
    parser.add_argument(
        "--report-md",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_branch_analysis.md"),
    )
    parser.add_argument(
        "--scout-verification-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_targeted_scout_verification.json"),
    )
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_branch_analysis_verification.json"),
    )
    args = parser.parse_args()
    result = verify(
        report_json=Path(args.report_json),
        report_md=Path(args.report_md),
        scout_verification_json=Path(args.scout_verification_json),
    )
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
