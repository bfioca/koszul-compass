#!/usr/bin/env python3
"""Verify final radius-5 post-monoid closed frontier report."""

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


def verify(*, frontier_json: Path, frontier_md: Path) -> dict[str, Any]:
    report = load_json(frontier_json)
    md_text = frontier_md.read_text(encoding="utf-8")
    summary = report["summary"]
    statuses = summary["adjusted_statuses"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(frontier_json),
            "builder-side post-monoid final frontier gates passed",
        ),
        "final_counts_preserved": gate(
            summary["source_slices_closed"] == 16
            and summary["radius4_sources_closed"] == 128
            and summary["frontier_records_screened"] == 70477
            and summary["raw_q1_spectrum_survivors"] == 444
            and summary["desired_q1_branch_completions"] == 285316
            and summary["viable_count"] == 0,
            str(frontier_json),
            "post-monoid report preserves final radius-5 aggregate counts",
        ),
        "mass_uncertainty_closed": gate(
            summary["pre_monoid_unresolved_mass_records"] == 578
            and summary["mass_records_upgraded_by_exact_monoid"] == 578
            and summary["open_mass_bound_uncertainties"] == 0
            and "no_certified_triplet_mass_operator_found" not in statuses,
            str(frontier_json),
            "all final mass-bound uncertainties are upgraded by exact monoid audit",
        ),
        "status_totals_adjusted": gate(
            statuses["no_triplet_mass_in_certified_singlet_monoid"] == 2463
            and statuses["dangerous_10_5bar_5bar_operator_allowed"] == 250544
            and statuses["negative_control_doublet_triplet_obstruction"] == 32448,
            str(frontier_json),
            "adjusted obstruction totals include exact monoid upgrades",
        ),
        "markdown_exposes_post_monoid_closure": gate(
            "open_mass_bound_uncertainties: `0`" in md_text
            and "mass_records_upgraded_by_exact_monoid: `578`" in md_text,
            str(frontier_md),
            "markdown exposes post-monoid closure totals",
        ),
    }
    return {
        "scope": "verification for final radius5 post-monoid closed frontier",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--frontier-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_post_monoid_closed_frontier.json"),
    )
    parser.add_argument(
        "--frontier-md",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_post_monoid_closed_frontier.md"),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius5_post_monoid_closed_frontier_verification.json"
        ),
    )
    args = parser.parse_args()
    result = verify(frontier_json=Path(args.frontier_json), frontier_md=Path(args.frontier_md))
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
