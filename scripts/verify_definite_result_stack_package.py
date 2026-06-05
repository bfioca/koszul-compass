#!/usr/bin/env python3
"""Verify the definite result-stack package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(name: str) -> Any:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def verify() -> dict[str, Any]:
    package = load_json("definite_result_stack_package.json")
    final = load_json("final_deliverable_verification.json")
    favourable_no_go = load_json("outside_regime_free_symmetry_no_go_verification.json")
    nonfav = load_json("nonfavourable_extension_report_verification.json")
    cicy5259 = load_json("cicy5259_certifiability_upgrade_verification.json")
    memo = (REPORTS / "definite_result_stack_memo.md").read_text(encoding="utf-8")
    artifact_table = (
        REPORTS / "definite_result_stack_artifact_table.md"
    ).read_text(encoding="utf-8")
    blocker_table = (
        REPORTS / "definite_result_stack_dependency_blockers.md"
    ).read_text(encoding="utf-8")

    stack = {item["id"]: item for item in package["result_stack"]}
    gates = {
        "package_status_and_verifiers": gate(
            package["status"] == "coherent_result_stack_ready_to_package"
            and package["verification_summary"]["all_current_stack_verifiers_pass"]
            and final["all_gates_pass"]
            and favourable_no_go["all_gates_pass"]
            and nonfav["all_gates_pass"]
            and cicy5259["all_gates_pass"],
            "reports/definite_result_stack_package.json",
            "package records all upstream verifiers passing",
        ),
        "five_result_nodes_present": gate(
            set(stack)
            == {
                "benchmark_reproduction",
                "cicy2544_positive_favourable_outside_regime",
                "favourable_quotient_no_go",
                "cicy7484_quotient_descent_near_miss",
                "cicy5259_nonfavourable_pilot_upgrade",
            },
            "reports/definite_result_stack_package.json",
            "five coherent result-stack nodes are present",
        ),
        "benchmark_numbers": gate(
            stack["benchmark_reproduction"]["key_numbers"]["GUTall_models"] == 63325
            and stack["benchmark_reproduction"]["key_numbers"]["sms202_models"] == 202
            and stack["benchmark_reproduction"]["key_numbers"][
                "adaptive_slope_failures"
            ]
            == 0
            and stack["benchmark_reproduction"]["key_numbers"][
                "pycicy_failure_count"
            ]
            == 0,
            "reports/dataset_summary.json",
            "benchmark reproduction counts are packaged",
        ),
        "cicy2544_numbers": gate(
            stack["cicy2544_positive_favourable_outside_regime"]["key_numbers"][
                "spectrum_10_anti10_5bar_5"
            ]
            == [3, 0, 4, 1]
            and stack["cicy2544_positive_favourable_outside_regime"]["key_numbers"][
                "hard_gate_segment"
            ]
            == [0, 1, 2]
            and stack["cicy2544_positive_favourable_outside_regime"]["key_numbers"][
                "trivial_summand_count"
            ]
            == 0,
            "reports/outside_regime_higgs_candidate_certificate.json",
            "CICY2544 clean upstairs one-Higgs evidence is packaged",
        ),
        "favourable_no_go_numbers": gate(
            stack["favourable_quotient_no_go"]["key_numbers"][
                "canonical_h11_ge7_recorded_free"
            ]
            == 62
            and stack["favourable_quotient_no_go"]["key_numbers"][
                "favourable_h11_ge7_recorded_free"
            ]
            == 0
            and stack["favourable_quotient_no_go"]["key_numbers"][
                "favourable_known_symmetry_nums"
            ]
            == [2544, 3929, 4335],
            "reports/outside_regime_free_symmetry_no_go.json",
            "favourable/free no-go counts are packaged",
        ),
        "cicy7484_numbers": gate(
            stack["cicy7484_quotient_descent_near_miss"]["key_numbers"][
                "actual_per_character_pair_5bar_5"
            ]
            == [6, 3]
            and stack["cicy7484_quotient_descent_near_miss"]["key_numbers"][
                "trivial_summand_count"
            ]
            == 2,
            "reports/best_candidate_certificate.json",
            "CICY7484 near-miss evidence is packaged",
        ),
        "cicy5259_numbers": gate(
            stack["cicy5259_nonfavourable_pilot_upgrade"]["key_numbers"][
                "pilot_spectrum_10_anti10_5bar_5"
            ]
            == [6, 0, 16, 10]
            and stack["cicy5259_nonfavourable_pilot_upgrade"]["key_numbers"][
                "rank_defect"
            ]
            == 1
            and stack["cicy5259_nonfavourable_pilot_upgrade"]["key_numbers"][
                "full_nonfavourable_certifiable_targets_now"
            ]
            == 0,
            "reports/cicy5259_certifiability_upgrade_report.json",
            "CICY5259 partial-certification evidence is packaged",
        ),
        "markdown_outputs_present": gate(
            "CICY 2544 gives a finite h11=7" in memo
            and "reports/cicy5259_certifiability_upgrade_report.json" in artifact_table
            and "CICY5259 non-favourable pilot" in blocker_table
            and "Next Mathematical Inputs" in blocker_table,
            "reports/definite_result_stack_memo.md + reports/definite_result_stack_artifact_table.md + reports/definite_result_stack_dependency_blockers.md",
            "memo, artifact table, and blocker table contain expected stack markers",
        ),
    }
    return {
        "scope": "verification for definite result-stack package",
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "definite_result_stack_package_verification.json"),
    )
    args = parser.parse_args()

    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"all_gates_pass={result['all_gates_pass']}")
    print(f"json_out={out}")
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
