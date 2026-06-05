#!/usr/bin/env python3
"""Verify the radius-9 representative-repaired grammar report."""

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
    spec = report["generator_gate_spec"]
    replay = report["operator_shape_replay"]
    smoke = report["negative_control_smoke"]
    unresolved = replay["representative_unresolved_operator_shapes"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"]
            and all(item["pass"] for item in report["gates"].values()),
            str(report_json),
            "builder-side representative grammar repair gates passed",
        ),
        "expected_status": gate(
            report["status"]
            == "radius9_representative_repaired_grammar_no_promoted_candidate"
            and report["scope"].startswith("promote representative-realizability"),
            str(report_json),
            "report is the representative-repaired q=1 grammar artifact",
        ),
        "summary_replays_prefilter_boundary": gate(
            summary["windows_closed"] == 45
            and summary["materialized_q1_weight"] == 549038
            and summary["character_shadow_viable_rows"] == 14
            and summary["character_shadow_viable_weight"] == 1962
            and summary["representative_grammar_promoted_rows"] == 0
            and summary["representative_grammar_promoted_weight"] == 0
            and summary["representative_grammar_pruned_rows"] == 14
            and summary["representative_grammar_pruned_weight"] == 1962
            and summary["cup_product_eligible_weight"] == 0,
            str(report_json),
            "repaired grammar prunes every current character-shadow survivor",
        ),
        "operator_shape_inventory_accounted": gate(
            summary["observed_triplet_only_operator_shape_count"] == 16
            and replay["missing_operator_shapes"] == []
            and replay["unexpected_extra_operator_shapes"] == []
            and replay["status_counts"]
            == {"representative_obstructed": 15, "representative_unresolved": 1}
            and summary["representative_compatible_observed_operator_shape_count"]
            == 0,
            str(report_json),
            "all observed triplet-only operator shapes are closed or escape-audited",
        ),
        "unresolved_shape_is_nonpromotable": gate(
            len(unresolved) == 1
            and unresolved[0]["operator"] == "5bar_34*5_34"
            and unresolved[0]["classification"]["status"]
            == "character_refined_doublet_mass_obstruction"
            and unresolved[0]["proton_allowed_count"] == 1,
            str(report_json),
            "the only representative-unresolved operator shape is outside the promotion gate",
        ),
        "negative_control_reproduced_by_reusable_gate": gate(
            smoke["candidate_label"] == "radius6_broad_adjacency_filtered_4_branch_18"
            and smoke["operator"] == "5bar_02*5_24"
            and smoke["representative_grammar_status"] == "representative_obstructed"
            and not smoke["promoted_to_lead_candidate"]
            and smoke["obstruction_summary"]["branch_actual"]["multiplicities"]
            == {"+": 2, "-": 0}
            and smoke["obstruction_summary"]["computed_actual"]["multiplicities"]
            == {"+": 1, "-": 1},
            str(report_json),
            "new gate module reproduces the branch-18 shadow collision",
        ),
        "generator_spec_has_complete_labels_and_hooks": gate(
            set(spec["promotion_labels"])
            == {
                "spectrum_only",
                "character_shadow_viable",
                "representative_obstructed",
                "representative_unresolved",
                "representative_compatible",
                "cup_product_eligible",
            }
            and len(spec["required_triplet_mass_target_audit"]) == 4
            and len(spec["rank_feasibility_rules"]) == 4
            and len(spec["future_builder_patch_points"]) == 3
            and "before lead dossier" in spec["placement"],
            str(report_json),
            "generator-facing gate spec contains labels, leg audits, rank rules, and hook points",
        ),
        "markdown_reports_repair_boundary": gate(
            "representative_grammar_promoted_weight: `0`" in md_text
            and "status counts: `{'representative_obstructed': 15, 'representative_unresolved': 1}`"
            in md_text
            and "character-shadow viability is no longer a promotion label" in md_text,
            str(report_md),
            "markdown exposes repaired grammar no-promotion boundary",
        ),
    }
    return {
        "scope": "verification for radius-9 representative-repaired grammar report",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_grammar_repair_report.json"
        ),
    )
    parser.add_argument(
        "--report-md",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_grammar_repair_report.md"
        ),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_grammar_repair_report_verification.json"
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
