#!/usr/bin/env python3
"""Replay the radius-9 q=1 frontier with the representative grammar gate."""

from __future__ import annotations

import argparse
import copy
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from build_phenomenology_guided_q1_radius9_character_refined_dt_report import (  # noqa: E402
    source_records,
)
from phenomenology_guided_q1_representative_grammar_gate import (  # noqa: E402
    RepresentativeGrammarGate,
    apply_representative_grammar_boundary,
)


BRANCH18_LABEL = "radius6_broad_adjacency_filtered_4_branch_18"
BRANCH18_OPERATOR = "5bar_02*5_24"
FIVE12_OPERATOR = "5bar_12*5_12"
FIVE23_OPERATOR = "5bar_23*5_23"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def compact_target(target: dict[str, Any]) -> dict[str, Any]:
    return {
        "operator": target["operator"],
        "status": target["status"],
        "eligible_for_exact_cup_product_rank": target[
            "eligible_for_exact_cup_product_rank"
        ],
        "obstruction_summary": target.get("obstruction_summary"),
        "unresolved_summary": target.get("unresolved_summary"),
    }


def promotion_record_from_boundary(
    *,
    source: dict[str, Any],
    weight: int,
    record: dict[str, Any],
    boundary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "candidate_label": record.get("label"),
        "source": source,
        "weight": weight,
        "pre_representative_classification": record.get(
            "pre_representative_classification", record.get("classification")
        ),
        "post_representative_classification": record.get("classification"),
        "selection_rule_stage": boundary["selection_rule_stage"],
        "representative_grammar_stage": boundary["representative_grammar_stage"],
        "triplet_mass_targets": [
            compact_target(target) for target in boundary["triplet_mass_targets"]
        ],
    }


def first_target(records: list[dict[str, Any]], operator: str) -> dict[str, Any]:
    for record in records:
        for target in record["triplet_mass_targets"]:
            if target["operator"] == operator:
                return {
                    "candidate_label": record["candidate_label"],
                    "source": record["source"],
                    "weight": record["weight"],
                    **target,
                }
    raise KeyError(f"operator not found in replay records: {operator}")


def targets_by_operator(records: list[dict[str, Any]], operator: str) -> list[dict[str, Any]]:
    out = []
    for record in records:
        for target in record["triplet_mass_targets"]:
            if target["operator"] == operator:
                out.append(
                    {
                        "candidate_label": record["candidate_label"],
                        "source": record["source"],
                        "weight": record["weight"],
                        **target,
                    }
                )
    return out


def build_report(*, windows: int, broad_rollup_json: Path) -> dict[str, Any]:
    broad = load_json(broad_rollup_json)
    grammar_gate = RepresentativeGrammarGate()
    total_records = 0
    total_weight = 0
    selection_status_rows: Counter[str] = Counter()
    selection_status_weight: Counter[str] = Counter()
    representative_rows: Counter[str] = Counter()
    representative_weight: Counter[str] = Counter()
    candidate_records = []
    promoted_records = []
    pruned_records = []
    unresolved_records = []
    cup_product_records = []

    for source, weight, original in source_records(windows):
        total_records += 1
        total_weight += weight
        record = copy.deepcopy(original)
        boundary = apply_representative_grammar_boundary(
            filtered_record=record,
            grammar_gate=grammar_gate,
            source=source,
            weight=weight,
        )
        selection_status = boundary["selection_rule_stage"]["status"]
        representative_status = boundary["representative_grammar_stage"]["status"]
        selection_status_rows[selection_status] += 1
        selection_status_weight[selection_status] += weight
        representative_rows[representative_status] += 1
        representative_weight[representative_status] += weight

        if boundary["selection_rule_stage"]["category"] != "viable":
            continue
        compact = promotion_record_from_boundary(
            source=source,
            weight=weight,
            record=record,
            boundary=boundary,
        )
        candidate_records.append(compact)
        if representative_status == "representative_compatible":
            promoted_records.append(compact)
        elif representative_status == "representative_unresolved":
            unresolved_records.append(compact)
        else:
            pruned_records.append(compact)
        if boundary["representative_grammar_stage"]["cup_product_planning_allowed"]:
            cup_product_records.append(compact)

    branch18 = next(
        (
            {
                "candidate_label": record["candidate_label"],
                "source": record["source"],
                "weight": record["weight"],
                **target,
            }
            for record in candidate_records
            if record["candidate_label"] == BRANCH18_LABEL
            for target in record["triplet_mass_targets"]
            if target["operator"] == BRANCH18_OPERATOR
        ),
        None,
    )
    five12 = targets_by_operator(candidate_records, FIVE12_OPERATOR)
    five23 = first_target(candidate_records, FIVE23_OPERATOR)
    summary = {
        "windows_closed": windows,
        "materialized_q1_records_generated": total_records,
        "materialized_q1_weight_generated": total_weight,
        "selection_rule_candidate_rows": len(candidate_records),
        "selection_rule_candidate_weight": sum(record["weight"] for record in candidate_records),
        "representative_grammar_pruned_rows": len(pruned_records),
        "representative_grammar_pruned_weight": sum(record["weight"] for record in pruned_records),
        "representative_grammar_unresolved_rows": len(unresolved_records),
        "representative_grammar_unresolved_weight": sum(
            record["weight"] for record in unresolved_records
        ),
        "representative_compatible_rows": len(promoted_records),
        "representative_compatible_weight": sum(
            record["weight"] for record in promoted_records
        ),
        "cup_product_eligible_rows": len(cup_product_records),
        "cup_product_eligible_weight": sum(record["weight"] for record in cup_product_records),
        "selection_rule_status_rows": dict(sorted(selection_status_rows.items())),
        "selection_rule_status_weight": dict(sorted(selection_status_weight.items())),
        "representative_status_rows": dict(sorted(representative_rows.items())),
        "representative_status_weight": dict(sorted(representative_weight.items())),
    }
    gates = {
        "imports_verified_broad_rollup": gate(
            broad["summary"]["all_verified"]
            and broad["summary"]["windows_closed"] == windows,
            str(broad_rollup_json),
            "generation replay starts from the verified materialized radius-9 frontier",
        ),
        "generated_weight_matches_frontier": gate(
            total_weight == broad["summary"]["adjusted_desired_q1_candidates"]
            and total_weight == 549038
            and total_records == 4065,
            "radius-9 source_records replay",
            "all materialized q=1 candidate records are replayed exactly once",
        ),
        "selection_rule_candidates_match_shadow_frontier": gate(
            summary["selection_rule_candidate_rows"] == 14
            and summary["selection_rule_candidate_weight"] == 1962,
            "representative generation replay",
            "the replay regenerates the corrected character-shadow survivor set",
        ),
        "representative_gate_prunes_all_shadow_candidates": gate(
            summary["representative_grammar_pruned_rows"] == 14
            and summary["representative_grammar_pruned_weight"] == 1962
            and summary["representative_compatible_weight"] == 0
            and summary["cup_product_eligible_weight"] == 0,
            "representative grammar stage",
            "no current radius-9 character-shadow survivor is promotion-ready",
        ),
        "no_unresolved_selection_rule_survivor": gate(
            summary["representative_grammar_unresolved_rows"] == 0
            and summary["representative_grammar_unresolved_weight"] == 0,
            "representative grammar stage",
            "every refined survivor is resolved, not merely postponed",
        ),
        "branch18_regression_control": gate(
            branch18 is not None
            and branch18["obstruction_summary"]["branch_actual"]["multiplicities"]
            == {"+": 2, "-": 0}
            and branch18["obstruction_summary"]["computed_actual"]["multiplicities"]
            == {"+": 1, "-": 1},
            BRANCH18_OPERATOR,
            "branch 18 remains pruned by the representative shadow-collision gate",
        ),
        "five12_e2_regression_control": gate(
            len(five12) == 2
            and all(
                target["obstruction_summary"]["first_obstructing_role"]
                == "5_12:cup_H1_wedge2_V_dual"
                and target["obstruction_summary"]["branch_actual"]["multiplicities"]
                == {"+": 0, "-": 2}
                and target["obstruction_summary"]["computed_actual"]["multiplicities"]
                == {"+": 1, "-": 1}
                for target in five12
            ),
            FIVE12_OPERATOR,
            "the 5_12 cup-dual E2 mismatch remains a generation-time prune",
        ),
        "five23_kernel_regression_control": gate(
            five23["obstruction_summary"]["first_obstructing_role"]
            == "5bar_23:physical_H1_wedge2_V"
            and five23["obstruction_summary"]["branch_actual"]["multiplicities"]
            == {"+": 2, "-": 0}
            and five23["obstruction_summary"]["computed_actual"]["multiplicities"]
            == {"+": 2, "-": 1},
            FIVE23_OPERATOR,
            "the 5bar_23 first-page kernel mismatch remains a generation-time prune",
        ),
    }
    return {
        "title": "Radius-9 Representative-Gated Generation Replay Rollup",
        "status": "radius9_representative_generation_replay_zero_promotion_ready_candidates",
        "scope": (
            "replay the materialized radius-9 q=1 frontier with RepresentativeGrammarGate "
            "as the generation-time promotion boundary"
        ),
        "source_artifacts": {
            "broad_rollup_json": str(broad_rollup_json),
            "reusable_gate_module": "scripts/phenomenology_guided_q1_representative_grammar_gate.py",
        },
        "summary": summary,
        "promotion_records": candidate_records,
        "representative_compatible_records": promoted_records,
        "representative_unresolved_records": unresolved_records,
        "representative_pruned_records": pruned_records,
        "cup_product_eligible_records": cup_product_records,
        "regression_controls": {
            "branch18": branch18,
            "five12": five12,
            "five23": five23,
        },
        "interpretation": {
            "generation_boundary": (
                "character-shadow viable branches are no longer promotion-ready; "
                "representative compatibility is required before lead or cup-product labels"
            ),
            "current_frontier_result": (
                "the repaired generation grammar yields zero representative-compatible "
                "candidates on the materialized radius-9 frontier"
            ),
        },
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        f"# {report['title']}",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Regression Controls", ""])
    controls = report["regression_controls"]
    lines.append(
        f"- branch18 `{BRANCH18_OPERATOR}`: `{controls['branch18']['status']}`"
    )
    lines.append(f"- five12 `{FIVE12_OPERATOR}` targets: `{len(controls['five12'])}`")
    lines.append(f"- five23 `{FIVE23_OPERATOR}`: `{controls['five23']['status']}`")
    lines.extend(["", "## Interpretation", ""])
    for key, value in report["interpretation"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Gates", ""])
    for key, item in report["gates"].items():
        lines.append(f"- {key}: `{item['pass']}` - {item['note']}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", type=int, default=45)
    parser.add_argument(
        "--broad-rollup-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius9_broad_windows1_45_rollup.json"),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_generation_replay_rollup.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_generation_replay_rollup.md"
        ),
    )
    args = parser.parse_args()
    report = build_report(
        windows=args.windows,
        broad_rollup_json=Path(args.broad_rollup_json),
    )
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_markdown(report, md_out)
    print(f"status={report['status']}")
    print(f"summary={json.dumps(report['summary'], sort_keys=True)}")
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
