#!/usr/bin/env python3
"""Aggregate all verified radius-6 targeted obstruction buckets."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

DEFAULT_AGGREGATES = [
    REPORTS / "phenomenology_guided_q1_radius6_dt_targeted_aggregate.json",
    REPORTS / "phenomenology_guided_q1_radius6_dangerous_targeted_aggregate.json",
    REPORTS / "phenomenology_guided_q1_radius6_nomass_targeted_aggregate.json",
    REPORTS / "phenomenology_guided_q1_radius6_mixed_targeted_aggregate.json",
]
DEFAULT_VERIFICATIONS = [
    REPORTS / "phenomenology_guided_q1_radius6_dt_targeted_aggregate_verification.json",
    REPORTS / "phenomenology_guided_q1_radius6_dangerous_targeted_aggregate_verification.json",
    REPORTS / "phenomenology_guided_q1_radius6_nomass_targeted_aggregate_verification.json",
    REPORTS / "phenomenology_guided_q1_radius6_mixed_targeted_aggregate_verification.json",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def build_report(aggregate_jsons: list[Path], verification_jsons: list[Path]) -> dict[str, Any]:
    aggregates = [load_json(path) for path in aggregate_jsons]
    verifications = [load_json(path) for path in verification_jsons]
    statuses: Counter[str] = Counter()
    for aggregate in aggregates:
        statuses.update(aggregate["summary"]["adjusted_statuses"])
    summary = {
        "targeted_buckets_closed": len(aggregates),
        "windows_closed": sum(item["summary"]["windows_closed"] for item in aggregates),
        "frontier_records_screened": sum(
            item["summary"]["frontier_records_screened"] for item in aggregates
        ),
        "all_bucket_frontiers_exhausted": all(
            item["summary"]["frontier_records_after_final_window"] == 0
            for item in aggregates
        ),
        "raw_q1_spectrum_survivors": sum(
            item["summary"]["raw_q1_spectrum_survivors"] for item in aggregates
        ),
        "direct_character_certified_q1_records": sum(
            item["summary"]["direct_character_certified_q1_records"]
            for item in aggregates
        ),
        "branch_completions_evaluated": sum(
            item["summary"]["branch_completions_evaluated"] for item in aggregates
        ),
        "desired_q1_branch_completions": sum(
            item["summary"]["desired_q1_branch_completions"] for item in aggregates
        ),
        "adjusted_desired_q1_candidates": sum(
            item["summary"]["adjusted_desired_q1_candidates"] for item in aggregates
        ),
        "mass_records_upgraded_by_exact_monoid": sum(
            item["summary"]["mass_records_upgraded_by_exact_monoid"]
            for item in aggregates
        ),
        "open_mass_monoid_solutions": sum(
            item["summary"]["open_mass_monoid_solutions"] for item in aggregates
        ),
        "viable_count": sum(item["summary"]["viable_count"] for item in aggregates),
        "adjusted_statuses": dict(sorted(statuses.items())),
    }
    gates = {
        "all_aggregate_verifications_pass": gate(
            all(item["all_gates_pass"] for item in verifications),
            ", ".join(str(path) for path in verification_jsons),
            "all imported targeted aggregate verifications passed",
        ),
        "all_frontiers_exhausted": gate(
            summary["all_bucket_frontiers_exhausted"],
            ", ".join(str(path) for path in aggregate_jsons),
            "every targeted obstruction bucket reports zero remaining frontier records",
        ),
        "no_open_uncertainty": gate(
            summary["open_mass_monoid_solutions"] == 0
            and "missing_character_or_charge_level_data"
            not in summary["adjusted_statuses"]
            and "no_certified_triplet_mass_operator_found"
            not in summary["adjusted_statuses"],
            "all-bucket adjusted statuses",
            "all character and exact mass-monoid uncertainties are closed",
        ),
        "no_viable_candidate": gate(
            summary["viable_count"] == 0,
            "all-bucket adjusted statuses",
            "no q1 candidate passes the current charge-level viability filter",
        ),
    }
    return {
        "scope": "all verified radius6 targeted obstruction buckets",
        "status": "radius6_all_targeted_obstruction_buckets_exhausted_no_viable_candidate",
        "summary": summary,
        "targeted_aggregate_reports": [str(path) for path in aggregate_jsons],
        "interpretation": (
            "The radius-6 targeted expansion of all four radius-5 obstruction buckets is "
            "closed under the current quotient-compatible q=1 charge-level filter. The "
            "5259/7914-style negative control is successfully converted into rejection "
            "criteria: q=1 candidates are retained only when their mass and proton tables "
            "avoid the certified doublet-triplet and dangerous-operator obstructions. No "
            "candidate in these exhausted targeted buckets satisfies that stronger filter."
        ),
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-6 All Targeted Obstruction Aggregate",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Interpretation", "", report["interpretation"], ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aggregate-json", action="append", default=None)
    parser.add_argument("--verification-json", action="append", default=None)
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius6_all_targeted_obstruction_aggregate.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius6_all_targeted_obstruction_aggregate.md"
        ),
    )
    args = parser.parse_args()
    aggregate_jsons = [Path(item) for item in (args.aggregate_json or DEFAULT_AGGREGATES)]
    verification_jsons = [
        Path(item) for item in (args.verification_json or DEFAULT_VERIFICATIONS)
    ]
    if len(aggregate_jsons) != len(verification_jsons):
        raise SystemExit("--aggregate-json and --verification-json counts must match")
    report = build_report(aggregate_jsons, verification_jsons)
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
