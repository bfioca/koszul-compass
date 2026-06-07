#!/usr/bin/env python3
"""Verify the CICY5256 GUTall benchmark pool engine audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPORTS = ROOT / "reports"

EXPECTED_STATUS = "cicy5256_gutall_benchmark_pool_engine_gap_current_data"
EXPECTED_TARGET = "CICY5256_gutall_benchmark_pool_engine_audit"
EXPECTED_NEXT_TARGET = "CICY5452_gutall_benchmark_pool_engine_audit"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def verify(report_json: Path, report_md: Path) -> dict[str, Any]:
    report = load_json(report_json)
    md_text = report_md.read_text(encoding="utf-8")
    algebraic = report["algebraic_pool_summary"]
    raw = report["raw_free_action_summary"]
    lift = report["ambient_lift_readiness"]["by_symmetry_order"]
    engine = report["promotion_engine_inventory"]
    extension = report["no_go_atlas_extension"]
    classification = report["classification"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"]
            and all(item["pass"] for item in report["gates"].values()),
            str(report_json),
            "builder-side audit gates all pass",
        ),
        "source_verifications_all_pass": gate(
            all(
                item["all_gates_pass"]
                for item in report["source_verifications"].values()
            ),
            json.dumps(report["source_verifications"], sort_keys=True),
            "all imported source verifications are green",
        ),
        "status_and_target_are_expected": gate(
            report["status"] == EXPECTED_STATUS
            and report["queue_target_id"] == EXPECTED_TARGET
            and report["source_target_id"] == "CICY5256_gutall_benchmark_pool"
            and report["next_step"]["recommended_next_target_id"]
            == EXPECTED_NEXT_TARGET,
            json.dumps(
                {
                    "status": report["status"],
                    "queue_target_id": report["queue_target_id"],
                    "next": report["next_step"]["recommended_next_target_id"],
                },
                sort_keys=True,
            ),
            "audit closes the CICY5256 queue target as a current engine gap",
        ),
        "geometry_is_cicy5256": gate(
            report["parent_geometry"]["num"] == 5256
            and report["parent_geometry"]["h11"] == 5
            and report["parent_geometry"]["h21"] == 29
            and report["parent_geometry"]["eta"] == -48
            and report["parent_geometry"]["symmetry_orders_in_cicy_entry"] == [2, 4]
            and report["parent_geometry"]["ambient_coordinate_block_sizes"]
            == [2, 2, 2, 2, 4],
            json.dumps(report["parent_geometry"], sort_keys=True),
            "geometry metadata matches the CICY5256 favourable P1^4 x P3 presentation",
        ),
        "algebraic_pool_is_clean": gate(
            algebraic["model_count"] == 2891
            and algebraic["model_counts_by_symmetry_order"]
            == {"2": 763, "4": 2128}
            and algebraic["unique_model_key_count"] == 2891
            and algebraic["failure_count"] == 0
            and algebraic["failure_counts_by_check"] == {},
            json.dumps(
                {
                    "model_count": algebraic["model_count"],
                    "by_order": algebraic["model_counts_by_symmetry_order"],
                    "unique": algebraic["unique_model_key_count"],
                    "failures": algebraic["failure_count"],
                },
                sort_keys=True,
            ),
            "all CICY5256 GUTall models pass c1/index/anomaly/duplicate gates",
        ),
        "raw_actions_are_recorded_and_row_trivial": gate(
            raw["free_option_count"] == 6
            and raw["free_order_counts"] == {"2": 2, "4": 4}
            and raw["free_group_structure_counts"] == {"2": 2, "2x2": 4}
            and raw["free_row_trivial_count"] == 6
            and raw["all_free_options_row_trivial"]
            and raw["all_free_options_record_invariant_polynomial_basis"],
            json.dumps(
                {
                    "free_option_count": raw["free_option_count"],
                    "free_order_counts": raw["free_order_counts"],
                    "free_group_structure_counts": raw["free_group_structure_counts"],
                    "row_trivial": raw["all_free_options_row_trivial"],
                },
                sort_keys=True,
            ),
            "raw cicylist actions provide row-trivial Z2 and Z2xZ2 data",
        ),
        "ambient_lift_readiness_counts_match": gate(
            lift["2"]["model_count"] == 763
            and lift["2"]["any_direct_sum_equivariant_lift_count"] == 763
            and lift["2"]["no_direct_sum_equivariant_lift_count"] == 0
            and lift["2"]["lift_option_count_distribution"] == {"2": 763}
            and lift["4"]["model_count"] == 2128
            and lift["4"]["any_direct_sum_equivariant_lift_count"] == 544
            and lift["4"]["no_direct_sum_equivariant_lift_count"] == 1584
            and lift["4"]["lift_option_count_distribution"]
            == {"0": 1584, "4": 544},
            json.dumps(lift, sort_keys=True),
            "ambient projective lift readiness is finite and reproducible",
        ),
        "promotion_engine_gap_is_precise": gate(
            engine["generic_algebraic_index_anomaly_engine_available"]
            and engine["generic_raw_free_action_parser_available"]
            and engine["generic_ambient_line_bundle_lift_readiness_engine_available"]
            and not engine["geometry_specific_wilson_component_engine_available"]
            and not engine["geometry_specific_representative_mass_engine_available"]
            and not engine["generic_representative_promotion_engine_available"]
            and engine["matched_current_engine_artifacts"] == []
            and engine["first_missing_gate"]
            == "geometry_specific_equivariant_representative_and_component_mass_engine",
            json.dumps(engine, sort_keys=True),
            "gap is below ambient lift readiness and above component/representative promotion",
        ),
        "no_go_extension_is_scoped": gate(
            extension["syndrome_id"]
            == "cicy5256_gutall_benchmark_pool_engine_gap_current_data"
            and extension["scope_class"] == "grammar-local"
            and extension["cheap_prefilter"]
            == "geometry_specific_engine_missing_current_data"
            and extension["minimal_obstruction_core"]["model_count"] == 2891
            and extension["minimal_obstruction_core"][
                "algebraic_benchmark_failure_count"
            ]
            == 0
            and extension["minimal_obstruction_core"]["raw_free_action_count"] == 6
            and not extension["minimal_obstruction_core"][
                "geometry_specific_representative_mass_engine_available"
            ],
            json.dumps(extension, sort_keys=True),
            "No-Go Atlas extension records a current-engine gap, not a physical no-go",
        ),
        "no_candidate_overclaimed": gate(
            classification["candidate_status"] == "not_a_candidate_claim"
            and not classification["mssm_candidate_verified"]
            and classification["pool_status"] == EXPECTED_STATUS,
            json.dumps(classification, sort_keys=True),
            "audit makes no MSSM candidate claim",
        ),
        "markdown_exposes_boundary": gate(
            f"Status: `{EXPECTED_STATUS}`" in md_text
            and "model_count: `2891`" in md_text
            and "free_option_count: `6`" in md_text
            and "geometry_specific_engine_missing_current_data" in md_text
            and EXPECTED_NEXT_TARGET in md_text,
            str(report_md),
            "markdown exposes model count, raw actions, prefilter, and next target",
        ),
    }
    return {
        "scope": "verification for CICY5256 GUTall benchmark pool engine audit",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "summary": {
            "status": report["status"],
            "model_count": algebraic["model_count"],
            "order2_lift_ready": lift["2"]["any_direct_sum_equivariant_lift_count"],
            "order4_lift_ready": lift["4"]["any_direct_sum_equivariant_lift_count"],
            "next_target": report["next_step"]["recommended_next_target_id"],
        },
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json",
        type=Path,
        default=REPORTS / "cicy5256_gutall_benchmark_pool_engine_audit.json",
    )
    parser.add_argument(
        "--report-md",
        type=Path,
        default=REPORTS / "cicy5256_gutall_benchmark_pool_engine_audit.md",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=REPORTS
        / "cicy5256_gutall_benchmark_pool_engine_audit_verification.json",
    )
    args = parser.parse_args()
    result = verify(args.report_json, args.report_md)
    args.out_json.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
