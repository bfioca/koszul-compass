#!/usr/bin/env python3
"""Verify the selected radius-4 post-exhaustion obstruction report."""

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
    report_path = (
        REPORTS / "phenomenology_guided_q1_radius4_post_exhaustion_obstruction_report.json"
    )
    md_path = (
        REPORTS / "phenomenology_guided_q1_radius4_post_exhaustion_obstruction_report.md"
    )
    report = load_json(report_path)
    md_text = md_path.read_text(encoding="utf-8")
    surface = report["selected_radius4_surface"]
    totals = surface["combined_aggregate_totals"]
    categories = surface["combined_initial_categories"]
    statuses = surface["combined_initial_statuses"]
    accounting = report["post_exhaustion_accounting"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(report_path),
            "builder-side post-exhaustion gates passed",
        ),
        "combined_frontier_counts_match": gate(
            surface["combined_frontier_size"] == 17476
            and totals["raw_q1_spectrum_survivors"] == 91
            and totals["character_certified_q1_survivors"] == 46
            and categories == {"phenomenologically obstructed": 46, "unresolved": 45},
            str(report_path),
            "combined selected radius-4 surface preserves aggregate q=1 counts",
        ),
        "initial_obstruction_statuses_match": gate(
            statuses
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 13,
                "missing_character_or_charge_level_data": 45,
                "negative_control_doublet_triplet_obstruction": 33,
            },
            str(report_path),
            "initial aggregate obstruction statuses match the two source batches",
        ),
        "character_frontier_exhausted": gate(
            accounting["aggregate_unresolved_records"] == 45
            and accounting["known_line_resolution_attempted_records"] == 45
            and accounting["known_line_character_incomplete_candidates"] == 27
            and accounting["verified_branch_closed_character_incomplete_candidates"] == 27
            and accounting["open_character_incomplete_candidates"] == 0
            and accounting["raw_missing_character_blocks"] == 70
            and accounting["open_missing_character_blocks"] == 0
            and accounting["raw_missing_serre_orbits"] == 25
            and accounting["open_missing_serre_orbits"] == 0,
            str(report_path),
            "selected known-line character demand is fully branch-closed",
        ),
        "mass_uncertainty_and_obstruction_explicit": gate(
            len(accounting["mass_bound_unresolved_candidates"]) == 1
            and accounting["mass_bound_unresolved_candidates"][0]["candidate"]
            == "batch2:window2_radius4_adjacency_filtered_4_known_line_resolved"
            and len(accounting["exact_mass_bound_closed_candidates"]) == 1
            and accounting["exact_mass_bound_closed_candidates"][0]["upgraded_status"]
            == "no_triplet_mass_in_certified_singlet_monoid"
            and accounting["open_mass_bound_uncertainties"] == []
            and len(accounting["no_triplet_mass_obstructions"]) == 1
            and accounting["no_triplet_mass_obstructions"][0]["candidate"]
            == "batch2:window2_radius4_adjacency_filtered_6_known_line_resolved",
            str(report_path),
            "mass-level special rows are identified, and the degree-bound row is exactly closed",
        ),
        "markdown_exposes_scope_and_caveat": gate(
            "bounded_no_go_for_selected_radius4_surface" in md_text
            and "not an all-CICY or all-radius no-go" in md_text
            and "final_viable_count: `0`" in md_text,
            str(md_path),
            "markdown states the bounded no-go and its scope caveat",
        ),
        "markdown_exposes_exact_mass_closure": gate(
            "exact_mass_bound_closed_candidates: `1`" in md_text
            and "open_mass_bound_uncertainties: `0`" in md_text
            and "final_open_uncertainty_count: `0`" in md_text,
            str(md_path),
            "markdown states that the residual mass-bound uncertainty is closed",
        ),
    }
    return {
        "scope": "verification for selected radius-4 post-exhaustion obstruction report",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_post_exhaustion_obstruction_report_verification.json"
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
