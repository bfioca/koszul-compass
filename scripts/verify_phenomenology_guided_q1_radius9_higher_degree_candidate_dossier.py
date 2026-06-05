#!/usr/bin/env python3
"""Verify the higher-degree candidate dossier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

EXPECTED_LEAD = "radius6_broad_adjacency_filtered_10_branch_50"
EXPECTED_OPERATOR = "5bar_02*5_34"
EXPECTED_MATRIX = [
    [0, 0, 1, 0, -1],
    [0, 0, 0, -1, 1],
    [0, 1, 1, -2, 0],
    [-1, 1, 0, 0, 0],
    [1, 0, -1, 1, -1],
    [0, -1, 0, 1, 0],
    [0, 1, -1, 0, 0],
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def leg_by_label(report: dict[str, Any], label: str) -> dict[str, Any]:
    for leg in report["cohomology_legs"]:
        if leg["label"] == label:
            return leg
    raise KeyError(label)


def verify(report_json: Path, report_md: Path) -> dict[str, Any]:
    report = load_json(report_json)
    md_text = report_md.read_text(encoding="utf-8")
    identity = report["candidate_identity"]
    operator = report["operator_certificate"]
    frontier = report["higher_order_mass_map_frontier"]
    proxy = report["ordinary_product_proxy"]["prefix_cohomology_scan"]
    dangerous = report["dangerous_operator_table"]
    verdict = report["verdict"]
    legs = {
        "5bar_02": leg_by_label(report, "5bar_02"),
        "5_34": leg_by_label(report, "5_34"),
        "e3-e2": leg_by_label(report, "e3-e2"),
        "e4-e0": leg_by_label(report, "e4-e0"),
    }
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"]
            and all(item["pass"] for item in report["gates"].values()),
            str(report_json),
            "builder-side dossier gates all pass",
        ),
        "frozen_candidate_identity": gate(
            report["status"] == "higher_order_mass_map_pending_for_frozen_candidate"
            and identity["label"] == EXPECTED_LEAD
            and identity["route"] == "5259/7914"
            and identity["matrix"] == EXPECTED_MATRIX
            and identity["source"]["window"] == 7
            and identity["weight"] == 1,
            str(report_json),
            "dossier freezes the first stable higher-degree lead",
        ),
        "q1_spectrum_and_frontier_counts": gate(
            identity["spectrum_certificate"]["desired_q1_three_family_signature"]
            and identity["spectrum_certificate"]["cohomology"]
            == {
                "V": [0, 6, 0, 0],
                "V_dual": [0, 0, 6, 0],
                "wedge2_V": [0, 8, 2, 0],
                "wedge2_V_dual": [0, 2, 8, 0],
            }
            and report["frontier_context"]["higher_degree_candidate_count"] == 136
            and report["frontier_context"]["higher_degree_summary"][
                "candidate_compatible_monomial_degrees_rows"
            ]
            == {"2": 120, "3": 16},
            str(report_json),
            "source spectrum and higher-degree frontier counts are stable",
        ),
        "operator_neutrality_and_selection_support": gate(
            operator["operator"] == EXPECTED_OPERATOR
            and operator["monomial"] == ["e3-e2", "e4-e0"]
            and operator["total_charge"]["coefficients"] == [0, 0, 0, 0, 0]
            and operator["total_line_bundle_sum"] == [0, 0, 0, 0, 0, 0, 0]
            and operator["z2_product_support"]["has_even_component"]
            and operator["triplet_pair_support"] == 1
            and operator["doublet_pair_support"] == 0
            and operator["proton_allowed_count"] == 0,
            str(report_json),
            "degree-2 monoid neutralizes the operator and gives triplet-only current-filter support",
        ),
        "representative_stack_is_exact": gate(
            legs["5bar_02"]["representative"]["computed_signature"] == "+1/-1"
            and legs["5bar_02"]["line_bundle"] == [1, 0, 1, -1, 0, 0, -1]
            and legs["5_34"]["representative"]["computed_signature"] == "+1/-0"
            and legs["5_34"]["line_bundle"] == [1, 0, 2, 0, 0, -1, 0]
            and legs["e3-e2"]["representative"]["computed_signature"] == "+6/-6"
            and legs["e3-e2"]["line_bundle"] == [-1, -1, -3, 0, 2, 1, 1]
            and legs["e4-e0"]["representative"]["computed_signature"] == "+2/-2"
            and legs["e4-e0"]["line_bundle"] == [-1, 1, 0, 1, -2, 0, 0]
            and all(
                leg["representative"]["status"] == "representative_compatible"
                for leg in legs.values()
            ),
            str(report_json),
            "all four cohomology legs are the expected representative-compatible lines",
        ),
        "dangerous_operator_table_is_closed_by_current_rules": gate(
            dangerous["total_checked"] == 20
            and dangerous["forbidden_by_current_selection_rules"] == 20
            and dangerous["allowed_by_current_selection_rules"] == 0
            and all(
                item["forbidden_by_current_selection_rules"]
                for item in dangerous["operators"]
            ),
            str(report_json),
            "all listed 10*5bar*5bar operators are forbidden by the current selection table",
        ),
        "ordinary_product_boundary_is_not_overclaimed": gate(
            report["ordinary_product_proxy"]["O_X_cohomology"] == [1, 0, 0, 1]
            and frontier["field_count"] == 4
            and frontier["ordinary_h1_degree_sum"] == 4
            and frontier["ordinary_cup_status"]
            == "not_a_simple_CY3_cubic_top_product"
            and proxy["ordinary_nonzero_prefix_counts_by_length"] == {"1": 24, "2": 8}
            and proxy["all_length_three_prefixes_have_zero_H3"]
            and proxy["all_orderings_end_in_H4_outside_CY3"],
            str(report_json),
            "ordinary cup-product proxy records the H4 boundary and absence of direct H3 prefixes",
        ),
        "higher_order_rank_conditions_are_explicit": gate(
            frontier["triplet_mass_block"]["matrix_dimensions_after_fixed_singlet_vevs"]
            == [1, 1]
            and frontier["triplet_mass_block"][
                "rank_needed_to_lift_colored_triplet_pair"
            ]
            == 1
            and frontier["triplet_mass_block"]["rank_status"]
            == "pending_higher_order_mass_map"
            and frontier["doublet_mass_block"][
                "matrix_dimensions_after_fixed_singlet_vevs"
            ]
            == [1, 0]
            and frontier["doublet_mass_block"][
                "rank_needed_to_preserve_light_doublet_pair"
            ]
            == 0
            and verdict["not_claimed"]
            == "simple CY3 cubic cup-product mass-rank verification",
            str(report_json),
            "dossier states the 1x1 triplet rank target and keeps higher-order map rank pending",
        ),
        "markdown_exposes_core_boundary": gate(
            f"Candidate: `{EXPECTED_LEAD}`" in md_text
            and f"Operator: `{EXPECTED_OPERATOR}`" in md_text
            and "ordinary cup status: `not_a_simple_CY3_cubic_top_product`"
            in md_text
            and "rank_status': 'pending_higher_order_mass_map'" in md_text
            and "not claimed: `simple CY3 cubic cup-product mass-rank verification`"
            in md_text,
            str(report_md),
            "markdown exposes the frozen candidate and higher-order pending boundary",
        ),
    }
    return {
        "scope": "verification for higher-degree candidate dossier",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_higher_degree_candidate_dossier.json"
        ),
    )
    parser.add_argument(
        "--report-md",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_higher_degree_candidate_dossier.md"
        ),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_higher_degree_candidate_dossier_verification.json"
        ),
    )
    args = parser.parse_args()
    result = verify(report_json=Path(args.report_json), report_md=Path(args.report_md))
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
