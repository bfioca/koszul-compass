#!/usr/bin/env python3
"""Verify the No-Go Atlas v0 artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from no_go_atlas_prefilters import describe_prefilters, evaluate_prefilter  # noqa: E402


REQUIRED_SYNDROMES = {
    "geometry_no_recorded_free_symmetry",
    "z2_regular_vectorlike_excess_5259_7914",
    "z2xz2_regular_vectorlike_excess_7484",
    "degree_zero_bilinear_not_cy3_top_cup",
    "physical_5bar_representative_character_mismatch",
    "degree_one_representative_intersection_not_triplet_only",
    "higher_degree_monoid_downstream_obstructions",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def syndrome_by_id(report: dict[str, Any], syndrome_id: str) -> dict[str, Any]:
    for item in report["syndromes"]:
        if item["syndrome_id"] == syndrome_id:
            return item
    raise KeyError(syndrome_id)


def verify(report_json: Path, report_md: Path) -> dict[str, Any]:
    report = load_json(report_json)
    md_text = report_md.read_text(encoding="utf-8")
    syndromes = {item["syndrome_id"]: item for item in report["syndromes"]}
    survivor = report["survivor_certificates"][0]
    prefilters = describe_prefilters()
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"]
            and all(item["pass"] for item in report["gates"].values()),
            str(report_json),
            "builder-side atlas gates all pass",
        ),
        "required_syndromes_present": gate(
            set(syndromes) == REQUIRED_SYNDROMES
            and report["summary"]["syndrome_count"] == len(REQUIRED_SYNDROMES),
            str(report_json),
            "atlas contains the required v0 syndrome set",
        ),
        "scope_classes_are_honest": gate(
            report["summary"]["scope_class_counts"]
            == {
                "geometry-local": 1,
                "global-looking": 1,
                "grammar-local": 4,
                "presentation-local": 1,
            }
            and all(
                item["scope_class"]
                in {
                    "candidate-specific",
                    "grammar-local",
                    "presentation-local",
                    "geometry-local",
                    "global-looking",
                }
                for item in report["syndromes"]
            )
            and "must not be cited as a manifold-level impossibility theorem"
            in report["atlas_policy"]["scope_warning"],
            str(report_json),
            "scope classes and warning prevent local rules from being overstated",
        ),
        "source_verifications_imported": gate(
            all(
                item["all_gates_pass"]
                for item in report["source_verifications"].values()
            )
            and len(report["source_verifications"]) >= 8,
            str(report_json),
            "all imported source verifications are present and passing",
        ),
        "prefilters_are_executable_and_registered": gate(
            set(report["prefilter_registry"]) == set(prefilters)
            and set(report["summary"]["prefilter_ids"]).issubset(set(prefilters))
            and evaluate_prefilter(
                "no_recorded_free_symmetry",
                {
                    "requires_wilson_line_descent": True,
                    "free_symmetry_option_count": 0,
                },
            )
            and evaluate_prefilter(
                "vectorlike_excess",
                {
                    "actual_per_character_pair": [6, 3],
                    "allowed_pairs": [[3, 0], [4, 1]],
                    "max_vectorlike_pairs": 1,
                },
            )
            and evaluate_prefilter(
                "representative_character_mismatch",
                {
                    "leg_type": "physical_5bar_H1",
                    "requested_multiplicities": {"+": 2, "-": 0},
                    "computed_multiplicities": {"+": 1, "-": 1},
                    "representative_status": "representative_obstructed",
                },
            )
            and evaluate_prefilter(
                "degree_zero_bilinear_not_top_cup",
                {
                    "monomial_degree": 0,
                    "direct_total_cohomological_degree": 2,
                    "direct_target_group": "H2(O_X)",
                    "direct_target_dimension": 0,
                    "required_singlet_degree_for_top_cubic": 1,
                },
            )
            and evaluate_prefilter(
                "degree_one_doublet_triplet_inseparable",
                {
                    "singlet_degree": 1,
                    "triplet_pair_support": 1,
                    "doublet_pair_support": 1,
                },
            )
            and evaluate_prefilter(
                "higher_monoid_downstream_obstructed",
                {
                    "status": "higher_monoid_triplet_only_proton_safe_but_cup_5_unrealizable"
                },
            )
            and not evaluate_prefilter(
                "higher_monoid_downstream_obstructed",
                {"status": "higher_monoid_representative_compatible_candidate"},
            ),
            str(report_json),
            "prefilter registry is importable and predicate samples behave as expected",
        ),
        "2544_geometry_gate_has_replay": gate(
            syndromes["geometry_no_recorded_free_symmetry"]["geometry"] == "CICY2544"
            and syndromes["geometry_no_recorded_free_symmetry"]["scope_class"]
            == "geometry-local"
            and syndromes["geometry_no_recorded_free_symmetry"]["replay_counts"][
                "favourable_h11_ge_7_known_symmetry_rows"
            ]
            == 3
            and syndromes["geometry_no_recorded_free_symmetry"]["replay_counts"][
                "rows_with_no_recorded_free_symmetry"
            ]
            == 3
            and syndromes["geometry_no_recorded_free_symmetry"][
                "minimal_obstruction_core"
            ]["raw_free_symmetry_option_count"]
            == 0,
            str(report_json),
            "2544 syndrome records the no-recorded-free-symmetry replay",
        ),
        "7484_vectorlike_gate_has_replay": gate(
            syndromes["z2xz2_regular_vectorlike_excess_7484"]["geometry"]
            == "CICY7484"
            and syndromes["z2xz2_regular_vectorlike_excess_7484"][
                "minimal_obstruction_core"
            ]["best_actual_per_character_pair"]
            == [6, 3]
            and syndromes["z2xz2_regular_vectorlike_excess_7484"]["replay_counts"][
                "actual_character_count"
            ]
            == 12
            and not syndromes["z2xz2_regular_vectorlike_excess_7484"][
                "replay_counts"
            ]["has_actual_three_family_no_vectorlike_pair"],
            str(report_json),
            "7484 syndrome records the character-certified vectorlike near-miss",
        ),
        "5259_frontier_replay_counts_are_stable": gate(
            syndromes["degree_zero_bilinear_not_cy3_top_cup"]["replay_counts"][
                "degree_zero_bilinear_rows"
            ]
            == 1452
            and syndromes["physical_5bar_representative_character_mismatch"][
                "replay_counts"
            ]["degree_aware_failure_records"]
            == 333
            and syndromes["physical_5bar_representative_character_mismatch"][
                "minimal_obstruction_core"
            ]["requested"]["multiplicities"]
            == {"+": 2, "-": 0}
            and syndromes["physical_5bar_representative_character_mismatch"][
                "minimal_obstruction_core"
            ]["computed"]["multiplicities"]
            == {"+": 1, "-": 1}
            and syndromes["degree_one_representative_intersection_not_triplet_only"][
                "replay_counts"
            ]["intersection_forced_operator_records"]
            == 10004
            and syndromes["degree_one_representative_intersection_not_triplet_only"][
                "replay_counts"
            ]["cup_product_eligible_records"]
            == 0,
            str(report_json),
            "5259/7914 degree, representative, and degree-one intersection replay counts are stable",
        ),
        "higher_degree_counts_and_survivor_boundary": gate(
            syndromes["higher_degree_monoid_downstream_obstructions"][
                "replay_counts"
            ]["higher_degree_forced_operator_records"]
            == 10004
            and syndromes["higher_degree_monoid_downstream_obstructions"][
                "replay_counts"
            ]["downstream_obstructed_operator_records"]
            == 9868
            and syndromes["higher_degree_monoid_downstream_obstructions"][
                "replay_counts"
            ]["representative_candidate_records"]
            == 136
            and survivor["candidate_label"]
            == "radius6_broad_adjacency_filtered_10_branch_50"
            and survivor["operator_certificate"]["operator"] == "5bar_02*5_34"
            and survivor["operator_certificate"]["monomial"] == ["e3-e2", "e4-e0"]
            and survivor["pending_gate"]["gate"]
            == "higher_order_effective_mass_map_rank"
            and survivor["pending_gate"]["triplet_rank_condition"][
                "matrix_dimensions_after_fixed_singlet_vevs"
            ]
            == [1, 1],
            str(report_json),
            "higher-degree replay counts and branch-50 pending rank gate are stable",
        ),
        "nearest_no_go_boundaries_are_present": gate(
            {
                "cubic_only_gate",
                "doublet_support",
                "proton_unprotected",
                "cup_5_unrealizable",
            }.issubset(
                {item["boundary_id"] for item in survivor["nearest_no_go_boundaries"]}
            ),
            str(report_json),
            "branch-50 survivor includes the requested nearest no-go boundary classes",
        ),
        "markdown_summarizes_atlas": gate(
            "Status: `no_go_atlas_v0_built`" in md_text
            and "syndrome_count: `7`" in md_text
            and "survivor_radius6_broad_adjacency_filtered_10_branch_50"
            in md_text
            and "higher_order_effective_mass_map_rank" in md_text
            and "geometry_no_recorded_free_symmetry" in md_text
            and "z2xz2_regular_vectorlike_excess_7484" in md_text,
            str(report_md),
            "markdown exposes atlas summary, 2544/7484 syndromes, and branch-50 survivor",
        ),
    }
    return {
        "scope": "verification for No-Go Atlas v0",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json",
        default=str(REPORTS / "no_go_atlas_v0.json"),
    )
    parser.add_argument(
        "--report-md",
        default=str(REPORTS / "no_go_atlas_v0.md"),
    )
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "no_go_atlas_v0_verification.json"),
    )
    args = parser.parse_args()
    result = verify(report_json=Path(args.report_json), report_md=Path(args.report_md))
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
