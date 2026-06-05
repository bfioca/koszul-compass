#!/usr/bin/env python3
"""Representative-prefiltered promotion rollup for radius-9 q=1 candidates."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def candidate_status(targets: list[dict[str, Any]]) -> str:
    statuses = {target["status"] for target in targets}
    if "representative_compatible" in statuses:
        return "representative_compatible"
    if "representative_unresolved" in statuses:
        return "representative_unresolved"
    return "representative_obstructed"


def first_reason(targets: list[dict[str, Any]]) -> dict[str, Any] | None:
    for target in targets:
        if target.get("obstruction_summary"):
            return target["obstruction_summary"]
    for target in targets:
        if target.get("unresolved_summary"):
            return target["unresolved_summary"]
    return None


def representative_targets_by_row(rerank: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for target in rerank["ranked_targets"]:
        out.setdefault(target["row_id"], []).append(target)
    return out


def promotion_records(refined: dict[str, Any], rerank: dict[str, Any]) -> list[dict[str, Any]]:
    targets_by_row = representative_targets_by_row(rerank)
    records = []
    for record in rerank["candidate_records"]:
        row_id = record["row_id"]
        targets = targets_by_row[row_id]
        status = candidate_status(targets)
        records.append(
            {
                "row_id": row_id,
                "candidate_label": record["candidate_label"],
                "source": record["source"],
                "weight": record["weight"],
                "selection_rule_stage": {
                    "status": "character_shadow_viable",
                    "source_status": record["classification"]["status"],
                    "source_category": record["classification"]["category"],
                },
                "representative_stage": {
                    "status": status,
                    "target_statuses": dict(Counter(target["status"] for target in targets)),
                    "first_failure": first_reason(targets),
                    "cup_product_eligible": any(
                        target["eligible_for_exact_cup_product_rank"] for target in targets
                    ),
                },
                "triplet_mass_targets": [
                    {
                        "operator": target["operator"],
                        "status": target["status"],
                        "eligible_for_exact_cup_product_rank": target[
                            "eligible_for_exact_cup_product_rank"
                        ],
                        "obstruction_summary": target.get("obstruction_summary"),
                        "unresolved_summary": target.get("unresolved_summary"),
                    }
                    for target in targets
                ],
            }
        )
    return records


def target_by_operator(rerank: dict[str, Any], operator: str) -> list[dict[str, Any]]:
    return [target for target in rerank["ranked_targets"] if target["operator"] == operator]


def build_report(
    *,
    windows: int,
    broad_rollup_json: Path,
    refined_json: Path,
    refined_verification_json: Path,
    representative_json: Path,
    representative_verification_json: Path,
) -> dict[str, Any]:
    broad = load_json(broad_rollup_json)
    refined = load_json(refined_json)
    refined_verification = load_json(refined_verification_json)
    representative = load_json(representative_json)
    representative_verification = load_json(representative_verification_json)
    records = promotion_records(refined, representative)
    weighted_statuses: Counter[str] = Counter()
    unweighted_statuses: Counter[str] = Counter()
    for record in records:
        status = record["representative_stage"]["status"]
        weighted_statuses[status] += record["weight"]
        unweighted_statuses[status] += 1

    eligible = [
        record for record in records if record["representative_stage"]["cup_product_eligible"]
    ]
    compatible = [
        record
        for record in records
        if record["representative_stage"]["status"] == "representative_compatible"
    ]
    unresolved = [
        record
        for record in records
        if record["representative_stage"]["status"] == "representative_unresolved"
    ]
    branch18 = target_by_operator(representative, "5bar_02*5_24")[0]
    five12 = target_by_operator(representative, "5bar_12*5_12")
    five23 = target_by_operator(representative, "5bar_23*5_23")[0]
    summary = {
        "windows_closed": windows,
        "adjusted_desired_q1_candidates": broad["summary"]["adjusted_desired_q1_candidates"],
        "character_shadow_viable_weight": refined["summary"]["refined_viable_candidate_weight"],
        "character_shadow_viable_rows": len(refined["refined_viable_candidate_records"]),
        "representative_prefilter_status_weight": dict(sorted(weighted_statuses.items())),
        "representative_prefilter_status_rows": dict(sorted(unweighted_statuses.items())),
        "representative_compatible_weight": sum(record["weight"] for record in compatible),
        "representative_unresolved_weight": sum(record["weight"] for record in unresolved),
        "representative_obstructed_weight": weighted_statuses["representative_obstructed"],
        "cup_product_eligible_weight": sum(record["weight"] for record in eligible),
        "cup_product_eligible_rows": len(eligible),
    }
    gates = {
        "imports_verified_radius9_rollup": gate(
            broad["summary"]["all_verified"] and broad["summary"]["windows_closed"] == windows,
            str(broad_rollup_json),
            "representative prefilter starts from the verified radius-9 frontier rollup",
        ),
        "imports_verified_character_shadow_report": gate(
            refined["all_gates_pass"]
            and refined_verification["all_gates_pass"]
            and refined["summary"]["refined_viable_candidate_weight"] == 1962,
            f"{refined_json} + {refined_verification_json}",
            "character-shadow viable candidates come from the verified refined DT report",
        ),
        "imports_verified_representative_rerank": gate(
            representative["all_gates_pass"]
            and representative_verification["all_gates_pass"]
            and representative["summary"]["all_targets_representative_obstructed"],
            f"{representative_json} + {representative_verification_json}",
            "representative prefilter uses the verified rerank with resolved representative obstructions",
        ),
        "all_shadow_viable_rows_promoted_through_prefilter": gate(
            len(records) == len(refined["refined_viable_candidate_records"]) == 14
            and sum(record["weight"] for record in records)
            == refined["summary"]["refined_viable_candidate_weight"]
            == 1962,
            "promotion_records",
            "every character-shadow viable row is classified at the representative stage",
        ),
        "no_representative_compatible_candidate": gate(
            summary["representative_compatible_weight"] == 0
            and summary["representative_unresolved_weight"] == 0
            and summary["representative_obstructed_weight"] == 1962
            and summary["cup_product_eligible_weight"] == 0,
            "representative prefilter status weights",
            "the current corrected q=1 frontier has no representative-compatible survivor",
        ),
        "branch18_regression_control": gate(
            branch18["candidate_label"] == "radius6_broad_adjacency_filtered_4_branch_18"
            and branch18["obstruction_summary"]["branch_actual"]["multiplicities"]
            == {"+": 2, "-": 0}
            and branch18["obstruction_summary"]["computed_actual"]["multiplicities"]
            == {"+": 1, "-": 1},
            "5bar_02*5_24",
            "branch 18 remains the impossible branch-character negative control",
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
            "5bar_12*5_12",
            "former fivebar_12 unresolved cases remain E2 cup-dual representative obstructions",
        ),
        "five23_kernel_regression_control": gate(
            five23["obstruction_summary"]["first_obstructing_role"]
            == "5bar_23:physical_H1_wedge2_V"
            and five23["obstruction_summary"]["branch_actual"]["multiplicities"]
            == {"+": 2, "-": 0}
            and five23["obstruction_summary"]["computed_actual"]["multiplicities"]
            == {"+": 2, "-": 1},
            "5bar_23*5_23",
            "former fivebar_23 map-construction failure remains an explicit kernel mismatch",
        ),
    }
    return {
        "title": f"Radius-9 Representative-Prefiltered q=1 Promotion Rollup Through Window {windows}",
        "status": f"radius9_representative_prefilter_windows1_{windows}_no_representative_compatible_candidate",
        "scope": (
            "apply representative-equivariant realizability before lead dossier "
            "or cup-product promotion"
        ),
        "source_artifacts": {
            "broad_rollup_json": str(broad_rollup_json),
            "character_shadow_json": str(refined_json),
            "character_shadow_verification_json": str(refined_verification_json),
            "representative_rerank_json": str(representative_json),
            "representative_rerank_verification_json": str(representative_verification_json),
        },
        "classification_hierarchy": {
            "spectrum_only": "q=1 spectrum candidate before operator/component gates",
            "character_shadow_viable": (
                "passes component-character and charge/operator selection rules, "
                "but representative realizability is not yet certified"
            ),
            "representative_obstructed": (
                "branch-completed character assignment is incompatible with the "
                "actual equivariant Koszul/E2 representatives"
            ),
            "representative_unresolved": (
                "representative maps are not yet available or dimension-certified"
            ),
            "representative_compatible": (
                "all mass-target legs and singlet insertions are representative-realizable"
            ),
            "cup_product_eligible": (
                "representative-compatible target eligible for exact mass-rank computation"
            ),
        },
        "summary": summary,
        "promotion_records": records,
        "regression_controls": {
            "branch18": branch18,
            "five12": five12,
            "five23": five23,
        },
        "promotion_policy": {
            "lead_dossier_allowed": bool(compatible),
            "cup_product_planning_allowed": bool(eligible),
            "reason": (
                "No candidate in the scanned radius-9 frontier is representative-compatible; "
                "lead dossier and cup-product promotion are blocked for this frontier."
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
    lines.extend(["", "## Classification Hierarchy", ""])
    for key, value in report["classification_hierarchy"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Promotion Policy",
            "",
            f"- lead dossier allowed: `{report['promotion_policy']['lead_dossier_allowed']}`",
            f"- cup-product planning allowed: `{report['promotion_policy']['cup_product_planning_allowed']}`",
            f"- reason: {report['promotion_policy']['reason']}",
            "",
            "## Representative Obstruction Classes",
            "",
        ]
    )
    role_counts = Counter(
        record["representative_stage"]["first_failure"]["first_obstructing_role"]
        for record in report["promotion_records"]
        if record["representative_stage"]["first_failure"]
        and "first_obstructing_role" in record["representative_stage"]["first_failure"]
    )
    for role, count in sorted(role_counts.items()):
        lines.append(f"- `{role}`: `{count}`")
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
        "--refined-json",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_character_refined_dt_windows1_45.json"
        ),
    )
    parser.add_argument(
        "--refined-verification-json",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_character_refined_dt_windows1_45_verification.json"
        ),
    )
    parser.add_argument(
        "--representative-json",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_representative_survivor_rerank.json"
        ),
    )
    parser.add_argument(
        "--representative-verification-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_survivor_rerank_verification.json"
        ),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_prefilter_rollup.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_representative_prefilter_rollup.md"
        ),
    )
    args = parser.parse_args()
    report = build_report(
        windows=args.windows,
        broad_rollup_json=Path(args.broad_rollup_json),
        refined_json=Path(args.refined_json),
        refined_verification_json=Path(args.refined_verification_json),
        representative_json=Path(args.representative_json),
        representative_verification_json=Path(args.representative_verification_json),
    )
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, md_out)
    print(f"status={report['status']}")
    print(f"summary={json.dumps(report['summary'], sort_keys=True)}")
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
