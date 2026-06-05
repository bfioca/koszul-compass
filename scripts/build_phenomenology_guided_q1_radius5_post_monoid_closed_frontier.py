#!/usr/bin/env python3
"""Apply exact monoid mass audit to the final radius-5 aggregate frontier."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def build_report() -> dict[str, Any]:
    aggregate_path = REPORTS / "phenomenology_guided_q1_radius5_source_slices_0_128_closed_frontier.json"
    verification_path = (
        REPORTS / "phenomenology_guided_q1_radius5_source_slices_0_128_closed_frontier_verification.json"
    )
    audit_path = REPORTS / "phenomenology_guided_q1_radius5_unresolved_mass_monoid_audit.json"
    audit_verification_path = (
        REPORTS / "phenomenology_guided_q1_radius5_unresolved_mass_monoid_audit_verification.json"
    )
    aggregate = load_json(aggregate_path)
    verification = load_json(verification_path)
    audit = load_json(audit_path)
    audit_verification = load_json(audit_verification_path)

    adjusted_statuses = Counter(aggregate["summary"]["adjusted_statuses"])
    unresolved = adjusted_statuses.pop("no_certified_triplet_mass_operator_found", 0)
    upgraded = audit["summary"]["weighted_upgraded_monoid_obstructions"]
    adjusted_statuses["no_triplet_mass_in_certified_singlet_monoid"] += upgraded

    gates = {
        "final_radius5_aggregate_verified": gate(
            verification["all_gates_pass"] and aggregate["all_gates_pass"],
            str(aggregate_path),
            "post-monoid closure starts from the verified final radius-5 aggregate",
        ),
        "unresolved_mass_audit_verified": gate(
            audit_verification["all_gates_pass"] and audit["all_gates_pass"],
            str(audit_path),
            "exact monoid audit for unresolved mass records is verified",
        ),
        "all_unresolved_mass_records_upgraded": gate(
            unresolved == upgraded
            and audit["summary"]["weighted_open_monoid_solutions"] == 0,
            "final aggregate plus exact monoid audit",
            "all no-certified-triplet-mass records are upgraded to exact monoid obstructions",
        ),
        "no_viable_candidate": gate(
            aggregate["summary"]["viable_count"] == 0,
            str(aggregate_path),
            "no candidate passes the spectrum plus charge-level phenomenology filter",
        ),
    }
    summary = dict(aggregate["summary"])
    summary["pre_monoid_unresolved_mass_records"] = unresolved
    summary["mass_records_upgraded_by_exact_monoid"] = upgraded
    summary["open_mass_bound_uncertainties"] = audit["summary"][
        "weighted_open_monoid_solutions"
    ]
    summary["adjusted_statuses"] = dict(sorted(adjusted_statuses.items()))
    return {
        "scope": "final radius-5 prioritized source frontier after exact unresolved-mass monoid audit",
        "status": "radius5_source_slices_0_128_post_monoid_closed_no_viable_candidate",
        "summary": summary,
        "component_reports": {
            "final_radius5_aggregate": str(aggregate_path),
            "final_radius5_aggregate_verification": str(verification_path),
            "unresolved_mass_monoid_audit": str(audit_path),
            "unresolved_mass_monoid_audit_verification": str(audit_verification_path),
        },
        "interpretation": (
            "The prioritized radius-5 source surface is closed. The previous "
            "no-certified-triplet-mass unresolved bucket is upgraded by exact "
            "certified-singlet monoid feasibility: no nonnegative monoid solution "
            "exists for any candidate triplet mass charge in that bucket."
        ),
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-5 Post-Monoid Closed Frontier",
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
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_post_monoid_closed_frontier.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_post_monoid_closed_frontier.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
