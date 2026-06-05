#!/usr/bin/env python3
"""Post-exhaustion obstruction report for the selected radius-4 q=1 search."""

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


def add_counts(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    out = dict(left)
    for key, value in right.items():
        out[key] = out.get(key, 0) + value
    return dict(sorted(out.items()))


def find_records_by_status(report: dict[str, Any], status: str) -> list[dict[str, Any]]:
    rows = []
    for record in report.get("filtered_candidate_records", []):
        classification = record.get("classification", {})
        if classification.get("status") == status:
            rows.append(
                {
                    "candidate": f"{report['batch']}:{record['label']}",
                    "category": classification.get("category"),
                    "reason": classification.get("reason"),
                    "source_window": record.get("source_window"),
                    "source_filtered_label": record.get("source_filtered_label"),
                }
            )
    return rows


def build_report() -> dict[str, Any]:
    adjacency = load_json(REPORTS / "phenomenology_guided_q1_radius4_adjacency_aggregate.json")
    batch2 = load_json(REPORTS / "phenomenology_guided_q1_radius4_batch2_aggregate.json")
    combined = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_known_line_combined_frontier.json"
    )
    demand = load_json(REPORTS / "phenomenology_guided_q1_radius4_missing_line_demand.json")
    exhausted = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_cumulative16_exhausted_frontier.json"
    )
    exact_mass_audit_path = (
        REPORTS / "phenomenology_guided_q1_radius4_mass_bound_exact_monoid_audit.json"
    )
    exact_mass_audit = (
        load_json(exact_mass_audit_path) if exact_mass_audit_path.exists() else None
    )
    resolved_1 = load_json(REPORTS / "phenomenology_guided_q1_radius4_known_line_resolved.json")
    resolved_2 = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_batch2_known_line_resolved.json"
    )

    aggregate_totals = add_counts(
        adjacency["aggregate_totals"], batch2["aggregate_totals"]
    )
    aggregate_categories = add_counts(
        adjacency["aggregate_categories"], batch2["aggregate_categories"]
    )
    aggregate_statuses = add_counts(
        adjacency["aggregate_statuses"], batch2["aggregate_statuses"]
    )
    aggregate_frontier_records = (
        adjacency["coverage"]["frontier_size"] + batch2["coverage"]["frontier_size"]
    )
    aggregate_unresolved = (
        adjacency["aggregate_categories"].get("unresolved", 0)
        + batch2["aggregate_categories"].get("unresolved", 0)
    )
    mass_bound_unresolved = (
        find_records_by_status(resolved_1, "no_certified_triplet_mass_operator_found")
        + find_records_by_status(resolved_2, "no_certified_triplet_mass_operator_found")
    )
    no_triplet_mass_obstructions = (
        find_records_by_status(resolved_1, "no_triplet_mass_in_certified_singlet_monoid")
        + find_records_by_status(resolved_2, "no_triplet_mass_in_certified_singlet_monoid")
    )
    exact_mass_closed_candidates: list[dict[str, Any]] = []
    if (
        exact_mass_audit is not None
        and exact_mass_audit.get("status")
        == "mass_bound_unresolved_row_upgraded_to_monoid_obstruction"
        and exact_mass_audit.get("all_gates_pass")
    ):
        exact_mass_closed_candidates.append(
            {
                "candidate": exact_mass_audit["candidate"],
                "upgraded_status": exact_mass_audit["upgraded_classification"]["status"],
                "reason": exact_mass_audit["upgraded_classification"]["reason"],
                "evidence": str(exact_mass_audit_path),
            }
        )
    open_mass_bound_uncertainties = [
        row
        for row in mass_bound_unresolved
        if row["candidate"]
        not in {closed["candidate"] for closed in exact_mass_closed_candidates}
    ]

    gates = {
        "source_aggregate_gates_pass": gate(
            adjacency["all_gates_pass"] and batch2["all_gates_pass"],
            (
                f"{REPORTS / 'phenomenology_guided_q1_radius4_adjacency_aggregate.json'}, "
                f"{REPORTS / 'phenomenology_guided_q1_radius4_batch2_aggregate.json'}"
            ),
            "both selected radius-4 aggregate builders verified their window coverage",
        ),
        "aggregate_unresolved_matches_known_line_attempts": gate(
            aggregate_unresolved == combined["summary"]["attempted_unresolved_records"] == 45,
            str(REPORTS / "phenomenology_guided_q1_radius4_known_line_combined_frontier.json"),
            "all aggregate unresolved rows were routed through known-line resolution",
        ),
        "known_line_character_queue_exhausted": gate(
            demand["summary"]["known_line_incomplete_candidates"]
            == exhausted["summary"]["raw_known_line_incomplete_candidates"]
            == exhausted["summary"]["closed_candidates"]
            and exhausted["summary"]["open_known_line_incomplete_candidates"] == 0
            and exhausted["summary"]["cumulative16_adjusted_missing_blocks"] == 0
            and exhausted["summary"]["cumulative16_adjusted_unique_missing_serre_orbits"] == 0,
            str(REPORTS / "phenomenology_guided_q1_radius4_cumulative16_exhausted_frontier.json"),
            "verified branch closures remove every selected missing-character demand",
        ),
        "no_viable_candidate_in_bounded_surface": gate(
            adjacency["viable_count"] == 0
            and batch2["viable_count"] == 0
            and combined["summary"]["viable_count"] == 0
            and exhausted["status"]
            == "selected_radius4_frontier_exhausted_no_viable_candidate_found",
            "aggregate, known-line, and cumulative16 reports",
            "no selected radius-4 candidate is certified viable under the 5259-derived filter",
        ),
        "mass_bound_uncertainty_is_explicit": gate(
            len(mass_bound_unresolved) == demand["summary"]["mass_level_unresolved_candidates"] == 1,
            str(REPORTS / "phenomenology_guided_q1_radius4_missing_line_demand.json"),
            "the only residual non-character uncertainty is the recorded monomial-bound mass audit",
        ),
        "exact_mass_bound_audit_closes_uncertainty": gate(
            len(mass_bound_unresolved) == 1
            and len(exact_mass_closed_candidates) == 1
            and len(open_mass_bound_uncertainties) == 0,
            str(exact_mass_audit_path),
            "the residual mass-bound row is upgraded to an exact singlet-monoid obstruction",
        ),
    }

    return {
        "scope": (
            "post-exhaustion accounting for the first two selected radius-4 "
            "source batches around the 5259/7914 q=1 negative control"
        ),
        "status": "selected_radius4_post_exhaustion_no_viable_candidate_found",
        "negative_control": {
            "route": "CICY 5259 via favourable ineffective split 7914",
            "classification": "phenomenologically_obstructed_by_current_charge_level_evidence",
            "report": str(REPORTS / "cicy5259_lead_phenomenology_dossier.json"),
            "filter_rule": (
                "reject q=1 candidates whose certified line-bundle and Wilson-line "
                "selection rules lift triplets and doublets together or allow dangerous "
                "10*5bar*5bar operators"
            ),
        },
        "selected_radius4_surface": {
            "source_batches": [
                {
                    "name": "batch1",
                    "frontier_size": adjacency["coverage"]["frontier_size"],
                    "raw_q1_spectrum_survivors": adjacency["aggregate_totals"][
                        "raw_q1_spectrum_survivors"
                    ],
                    "initial_character_certified_q1_survivors": adjacency[
                        "aggregate_totals"
                    ]["character_certified_q1_survivors"],
                    "initial_unresolved": adjacency["aggregate_categories"].get(
                        "unresolved", 0
                    ),
                    "viable_count": adjacency["viable_count"],
                },
                {
                    "name": "batch2",
                    "frontier_size": batch2["coverage"]["frontier_size"],
                    "raw_q1_spectrum_survivors": batch2["aggregate_totals"][
                        "raw_q1_spectrum_survivors"
                    ],
                    "initial_character_certified_q1_survivors": batch2[
                        "aggregate_totals"
                    ]["character_certified_q1_survivors"],
                    "initial_unresolved": batch2["aggregate_categories"].get(
                        "unresolved", 0
                    ),
                    "viable_count": batch2["viable_count"],
                },
            ],
            "combined_frontier_size": aggregate_frontier_records,
            "combined_aggregate_totals": aggregate_totals,
            "combined_initial_categories": aggregate_categories,
            "combined_initial_statuses": aggregate_statuses,
        },
        "post_exhaustion_accounting": {
            "aggregate_unresolved_records": aggregate_unresolved,
            "known_line_resolution_attempted_records": combined["summary"][
                "attempted_unresolved_records"
            ],
            "known_line_character_incomplete_candidates": demand["summary"][
                "known_line_incomplete_candidates"
            ],
            "verified_branch_closed_character_incomplete_candidates": exhausted["summary"][
                "closed_candidates"
            ],
            "open_character_incomplete_candidates": exhausted["summary"][
                "open_known_line_incomplete_candidates"
            ],
            "raw_missing_character_blocks": demand["summary"]["raw_missing_blocks"],
            "open_missing_character_blocks": exhausted["summary"][
                "cumulative16_adjusted_missing_blocks"
            ],
            "raw_missing_serre_orbits": demand["summary"]["unique_missing_serre_orbits"],
            "open_missing_serre_orbits": exhausted["summary"][
                "cumulative16_adjusted_unique_missing_serre_orbits"
            ],
            "mass_bound_unresolved_candidates": mass_bound_unresolved,
            "exact_mass_bound_closed_candidates": exact_mass_closed_candidates,
            "open_mass_bound_uncertainties": open_mass_bound_uncertainties,
            "no_triplet_mass_obstructions": no_triplet_mass_obstructions,
            "effective_no_triplet_mass_obstructions": len(no_triplet_mass_obstructions)
            + len(exact_mass_closed_candidates),
            "final_viable_count": 0,
            "final_open_uncertainty_count": len(open_mass_bound_uncertainties),
        },
        "bounded_conclusion": {
            "classification": "bounded_no_go_for_selected_radius4_surface",
            "claim": (
                "Within the first two selected radius-4 source batches, every q=1 "
                "spectrum survivor is either already phenomenologically obstructed, "
                "branch-closed with no viable character assignment, or upgraded from "
                "mass-bound uncertainty to an exact certified-singlet monoid obstruction."
            ),
            "not_claimed": (
                "This is not an all-CICY or all-radius no-go; it is a verified "
                "post-exhaustion statement for the selected radius-4 search surface."
            ),
            "next_search_surface": [
                "expand beyond the selected radius-4 source batches",
                "increase radius from the obstruction records that still have q=1-like spectrum pressure",
                "use the exact monoid obstruction as a stronger triplet-mass filter in the next radius/source expansion",
            ],
        },
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    surface = report["selected_radius4_surface"]
    accounting = report["post_exhaustion_accounting"]
    conclusion = report["bounded_conclusion"]
    lines = [
        "# Radius-4 Post-Exhaustion Obstruction Report",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Negative Control Filter",
        "",
        f"- route: `{report['negative_control']['route']}`",
        f"- classification: `{report['negative_control']['classification']}`",
        f"- filter rule: {report['negative_control']['filter_rule']}",
        "",
        "## Selected Radius-4 Surface",
        "",
        f"- combined_frontier_size: `{surface['combined_frontier_size']}`",
        f"- raw_q1_spectrum_survivors: `{surface['combined_aggregate_totals']['raw_q1_spectrum_survivors']}`",
        f"- initial_character_certified_q1_survivors: `{surface['combined_aggregate_totals']['character_certified_q1_survivors']}`",
        f"- initial_unresolved_records: `{surface['combined_initial_categories'].get('unresolved', 0)}`",
        f"- initial_viable_count: `0`",
        "",
        "## Post-Exhaustion Accounting",
        "",
    ]
    for key, value in accounting.items():
        if key in {
            "mass_bound_unresolved_candidates",
            "exact_mass_bound_closed_candidates",
            "open_mass_bound_uncertainties",
            "no_triplet_mass_obstructions",
        }:
            lines.append(f"- {key}: `{len(value)}`")
            for row in value:
                status = row.get("upgraded_status")
                suffix = f" ({status})" if status else ""
                lines.append(f"  - `{row['candidate']}`{suffix}: {row['reason']}")
        else:
            lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Bounded Conclusion",
            "",
            f"- classification: `{conclusion['classification']}`",
            f"- claim: {conclusion['claim']}",
            f"- not_claimed: {conclusion['not_claimed']}",
            "- next_search_surface:",
        ]
    )
    for item in conclusion["next_search_surface"]:
        lines.append(f"  - {item}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_post_exhaustion_obstruction_report.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_post_exhaustion_obstruction_report.md"
        ),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"all_gates_pass={report['all_gates_pass']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
