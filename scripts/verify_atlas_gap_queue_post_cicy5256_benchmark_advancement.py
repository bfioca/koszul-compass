#!/usr/bin/env python3
"""Verify queue advancement after the CICY5256 benchmark-pool audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPORTS = ROOT / "reports"

EXPECTED_STATUS = "atlas_gap_queue_advanced_to_cicy5452_gutall_benchmark_pool_engine_audit"
EXPECTED_CLOSED_TARGET = "CICY5256_gutall_benchmark_pool_engine_audit"
EXPECTED_CLOSURE = "cicy5256_gutall_benchmark_pool_engine_gap_current_data"
EXPECTED_OPEN_TARGET = "CICY5452_gutall_benchmark_pool_engine_audit"
EXPECTED_NEXT_PARENT = "CICY5452_gutall_benchmark_pool"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def verify(report_json: Path, report_md: Path) -> dict[str, Any]:
    report = load_json(report_json)
    md_text = report_md.read_text(encoding="utf-8")
    summary = report["summary"]
    closure = report["new_closure"]
    open_target = report["open_targets"][0]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"]
            and all(item["pass"] for item in report["gates"].values()),
            str(report_json),
            "builder-side queue advancement gates all pass",
        ),
        "source_verifications_all_pass": gate(
            all(
                item["all_gates_pass"]
                for item in report["source_verifications"].values()
            ),
            json.dumps(report["source_verifications"], sort_keys=True),
            "all imported source verifications are green",
        ),
        "summary_is_expected": gate(
            summary["status"] == EXPECTED_STATUS
            and summary["newly_closed_target_id"] == EXPECTED_CLOSED_TARGET
            and summary["new_closure_id"] == EXPECTED_CLOSURE
            and summary["top_open_target_id"] == EXPECTED_OPEN_TARGET
            and summary["next_parent_target_id"] == EXPECTED_NEXT_PARENT
            and summary["open_target_count"] == 1
            and summary["closed_target_count"] == 21
            and summary["candidate_claim_count"] == 0,
            json.dumps(summary, sort_keys=True),
            "queue closes CICY5256 and opens the CICY5452 benchmark-pool audit",
        ),
        "closure_records_cicy5256_engine_gap": gate(
            closure["target_id"] == EXPECTED_CLOSED_TARGET
            and closure["closure_id"] == EXPECTED_CLOSURE
            and closure["closed_gate"]
            == "geometry_specific_equivariant_representative_and_component_mass_engine"
            and closure["evidence_counts"]["cicy"] == 5256
            and closure["evidence_counts"]["model_count"] == 2891
            and closure["evidence_counts"]["model_counts_by_symmetry_order"]
            == {"2": 763, "4": 2128}
            and closure["evidence_counts"]["algebraic_benchmark_failure_count"] == 0
            and closure["evidence_counts"]["raw_free_action_count"] == 6
            and closure["evidence_counts"]["raw_free_order_counts"] == {"2": 2, "4": 4}
            and closure["evidence_counts"]["raw_free_group_structure_counts"]
            == {"2": 2, "2x2": 4}
            and closure["evidence_counts"]["order2_ambient_lift_ready_count"] == 763
            and closure["evidence_counts"]["order4_ambient_lift_ready_count"] == 544
            and closure["evidence_counts"]["order4_ambient_lift_obstructed_count"]
            == 1584
            and not closure["evidence_counts"][
                "geometry_specific_representative_mass_engine_available"
            ]
            and not closure["evidence_counts"][
                "geometry_specific_wilson_component_engine_available"
            ]
            and not closure["evidence_counts"][
                "generic_representative_promotion_engine_available"
            ]
            and closure["evidence_counts"]["matched_current_engine_artifact_count"]
            == 0
            and closure["no_go_atlas_extensions"][0]["syndrome_id"]
            == "cicy5256_gutall_benchmark_pool_engine_gap_current_data",
            json.dumps(closure, sort_keys=True),
            "closure records the CICY5256 current-engine gap obstruction",
        ),
        "open_target_is_cicy5452_gutall_pool": gate(
            open_target["target_id"] == EXPECTED_OPEN_TARGET
            and open_target["parent_target_id"] == EXPECTED_NEXT_PARENT
            and open_target["candidate_status"] == "not_a_candidate_claim"
            and open_target["fresh_raw_rank"] == 18
            and open_target["selected_raw_record"]["num"] == 5452
            and open_target["selected_raw_record"]["h11"] == 5
            and open_target["selected_raw_record"]["h21"] == 29
            and open_target["selected_raw_record"]["eta"] == -48
            and open_target["selected_raw_record"]["model_count"] == 2884
            and open_target["selected_raw_record"]["model_counts_by_symmetry_order"]
            == {"2": 762, "4": 2122}
            and open_target["selected_raw_record"]["symmetry_orders_in_cicy_entry"]
            == [2, 4],
            json.dumps(open_target, sort_keys=True),
            "only open target is the next bounded fresh GUTall benchmark pool, CICY5452",
        ),
        "markdown_reports_advancement": gate(
            f"Status: `{EXPECTED_STATUS}`" in md_text
            and f"`{EXPECTED_CLOSED_TARGET}` -> `{EXPECTED_CLOSURE}`" in md_text
            and f"### `{EXPECTED_OPEN_TARGET}`" in md_text,
            str(report_md),
            "markdown exposes closure and next open target",
        ),
    }
    return {
        "scope": "verification for post-CICY5256 benchmark queue advancement",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "summary": {
            "status": summary["status"],
            "closed_target_count": summary["closed_target_count"],
            "new_closure_id": summary["new_closure_id"],
            "top_open_target_id": summary["top_open_target_id"],
        },
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json",
        type=Path,
        default=REPORTS
        / "atlas_gap_queue_post_cicy5256_benchmark_advancement.json",
    )
    parser.add_argument(
        "--report-md",
        type=Path,
        default=REPORTS
        / "atlas_gap_queue_post_cicy5256_benchmark_advancement.md",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=REPORTS
        / "atlas_gap_queue_post_cicy5256_benchmark_advancement_verification.json",
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
