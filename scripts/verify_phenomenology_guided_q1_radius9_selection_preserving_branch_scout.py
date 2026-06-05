#!/usr/bin/env python3
"""Verify the radius-9 selection-preserving branch-character scout."""

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


def verify(report_json: Path, report_md: Path) -> dict[str, Any]:
    report = load_json(report_json)
    md_text = report_md.read_text(encoding="utf-8")
    summary = report["summary"]
    variants = report["branch_replacement_variants"]
    compatible = report["representative_compatible_variants"]
    cup_product = report["cup_product_eligible_variants"]
    compatible_labels = {item["variant_label"] for item in compatible}
    cup_labels = {item["variant_label"] for item in cup_product}
    pattern_by_name = {
        item["pattern"]: item for item in report["pattern_compatibility"]
    }
    q1_lost = [item for item in variants if not item["q1_preserved"]]
    compatible_seeds = {item["seed_label"] for item in compatible}
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"]
            and all(item["pass"] for item in report["gates"].values()),
            str(report_json),
            "builder-side selection-preserving scout gates passed",
        ),
        "expected_status": gate(
            report["status"]
            == "selection_preserving_branch_scout_found_representative_compatible_candidate"
            and report["scope"].startswith(
                "replace obstructed branch-character requests"
            ),
            str(report_json),
            "report is the selection-preserving representative-feasible branch scout",
        ),
        "seed_and_pattern_inputs_are_stable": gate(
            summary["windows_closed"] == 45
            and summary["seed_rows"] == 14
            and summary["seed_weight"] == 1962
            and summary["observed_triplet_only_operator_shape_count"] == 16
            and summary["feasible_pattern_count"] == 37,
            str(report_json),
            "scout starts from the certified pruned frontier and mined feasible patterns",
        ),
        "variant_accounting_is_stable": gate(
            summary["branch_replacement_variant_count"] == 28
            and len(variants) == 28
            and summary["matrix_certified_variant_count"] == 26
            and summary["q1_preserving_variant_count"] == 4
            and summary["q1_and_matrix_certified_variant_count"] == 4
            and summary["selection_preserving_variant_count"] == 4
            and summary["representative_compatible_count"] == 4
            and summary["representative_unresolved_count"] == 0
            and summary["cup_product_eligible_count"] == 4,
            str(report_json),
            "branch replacements, selection-preserving rows, and promoted rows are counted consistently",
        ),
        "failure_and_status_counts_are_selection_gated": gate(
            summary["failure_class_rows"]
            == {"q1_signature_lost": 24, "representative_compatible": 4}
            and summary["failure_class_weight"]
            == {"q1_signature_lost": 900, "representative_compatible": 3024}
            and summary["representative_status_rows"]
            == {"not_evaluated_q1_not_preserved": 24, "representative_compatible": 4}
            and all(
                item["representative_status"] == "not_evaluated_q1_not_preserved"
                and not item["promoted_to_lead_candidate"]
                and not item["cup_product_planning_allowed"]
                for item in q1_lost
            ),
            str(report_json),
            "q1-lost variants are blocked before representative audit or promotion",
        ),
        "matrix_certification_is_required_before_promotion": gate(
            all(
                item["matrix_certification"]["index_v"] == -6
                and item["matrix_certification"]["index_wedge2_v"] == -6
                and all(value >= 0 for value in item["matrix_certification"]["anomaly"])
                for item in variants
            )
            and all(
                item["matrix_certification"]["passes"]
                for item in variants
                if item["q1_preserved"]
            )
            and all(item["matrix_certification"]["passes"] for item in compatible),
            str(report_json),
            "all q1-preserving and promoted variants pass recomputed index, anomaly, and slope gates",
        ),
        "compatible_rows_are_actual_selection_preserving_rows": gate(
            compatible_labels == cup_labels
            and len(compatible) == 4
            and compatible_seeds
            == {
                "radius6_broad_adjacency_filtered_1_large_branch_q1_representative",
                "radius6_broad_adjacency_filtered_3_large_branch_q1_representative",
            }
            and all(
                item["operator"] == "5bar_12*5_12"
                and item["q1_preserved"]
                and item["matrix_certification"]["passes"]
                and item["refined_selection_status"]
                == "passes_refined_charge_character_dt_and_proton_filter"
                and item["proton_allowed_count"] == 0
                and item["representative_status"] == "representative_compatible"
                and item["promoted_to_lead_candidate"]
                and item["cup_product_planning_allowed"]
                for item in compatible
            ),
            str(report_json),
            "the only promoted branch-scout rows preserve q=1, refined DT/proton gates, and representative compatibility",
        ),
        "compatible_rows_preserve_q1_spectrum_shape": gate(
            all(
                item["mass_support_classes"]
                == {
                    "no_invariant_singlet_monomial": 2,
                    "triplet_only_character_mass": 1,
                }
                and item["vectorlike_prediction"]["net_families"] == 3
                and item["vectorlike_prediction"][
                    "colored_triplet_vectorlike_pairs"
                ]
                == 1
                and item["vectorlike_prediction"][
                    "electroweak_doublet_vectorlike_pairs"
                ]
                == 1
                for item in compatible
            ),
            str(report_json),
            "compatible rows keep the desired q=1 spectrum and triplet-only support pattern",
        ),
        "pattern_rollup_identifies_unique_compatible_branch": gate(
            pattern_by_name["5bar_12*5_12|first_obstructed_leg_feasible"][
                "compatible_weight"
            ]
            == 1512
            and pattern_by_name["5bar_12*5_12|all_obstructed_legs_feasible"][
                "compatible_weight"
            ]
            == 1512
            and all(
                item["compatible_weight"] == 0
                for name, item in pattern_by_name.items()
                if not name.startswith("5bar_12*5_12|")
            ),
            str(report_json),
            "pattern rollup isolates 5bar_12*5_12 as the only selection-preserving compatible replacement",
        ),
        "markdown_reports_branch_scout_boundary": gate(
            "representative_compatible_count: `4`" in md_text
            and "cup_product_eligible_count: `4`" in md_text
            and "q1_and_matrix_certified_variant_count: `4`" in md_text
            and "q1_signature_lost" in md_text
            and "not yet new full matrix/cup-product certificates" in md_text,
            str(report_md),
            "markdown exposes survivor counts, q1 loss boundary, and scout-level caveat",
        ),
    }
    return {
        "scope": "verification for radius-9 selection-preserving branch-character scout",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_selection_preserving_branch_scout.json"
        ),
    )
    parser.add_argument(
        "--report-md",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_selection_preserving_branch_scout.md"
        ),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_selection_preserving_branch_scout_verification.json"
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
