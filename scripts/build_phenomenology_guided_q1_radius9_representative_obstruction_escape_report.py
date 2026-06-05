#!/usr/bin/env python3
"""Classify representative obstructions and run a bounded escape scan."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/codex-mpl-cache")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_phenomenology_guided_q1_radius9_character_refined_dt_report import (  # noqa: E402
    full_candidate_record,
    proton_allowed_count,
    refined_classification,
    refined_mass_table,
    source_records,
)
from build_phenomenology_guided_q1_radius9_representative_survivor_rerank import (  # noqa: E402
    audit_triplet_operator,
)
from build_vectorlike_obstruction_report import load_5259_action_context  # noqa: E402
from string_theory.cohomology import ensure_pycicy_compat, make_pycicy, pycicy_config  # noqa: E402

KNOWN_FAILURE_OPERATORS = {
    "5bar_02*5_24",
    "5bar_04*5_34",
    "5bar_12*5_12",
    "5bar_23*5_23",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def operator_label(item: dict[str, Any]) -> str:
    return f"{item['fivebar']}*{item['five']}"


def role_counts(targets: list[dict[str, Any]]) -> Counter[str]:
    return Counter(
        target["obstruction_summary"]["first_obstructing_role"]
        for target in targets
        if target.get("obstruction_summary")
    )


def branch_minus_deficit(target: dict[str, Any]) -> dict[str, Any] | None:
    summary = target.get("obstruction_summary") or {}
    required = summary.get("required_image_ranks_for_branch")
    if required is None:
        return None
    first_leg = next(
        (
            leg
            for leg in target["matter_and_cup_leg_audits"]
            if leg["role"] == summary["first_obstructing_role"]
        ),
        None,
    )
    if first_leg is None:
        return None
    source = first_leg.get("source_representation")
    target_rep = first_leg.get("target_representation")
    return {
        "required_image_ranks": required,
        "source_multiplicities": None if source is None else source["multiplicities"],
        "target_multiplicities": None
        if target_rep is None
        else target_rep["multiplicities"],
        "plus_margin": None
        if source is None or target_rep is None
        else min(source["multiplicities"]["+"], target_rep["multiplicities"]["+"])
        - required["+"],
        "minus_margin": None
        if source is None or target_rep is None
        else min(source["multiplicities"]["-"], target_rep["multiplicities"]["-"])
        - required["-"],
    }


def obstruction_anatomy(rerank: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for target in rerank["ranked_targets"]:
        role = target["obstruction_summary"]["first_obstructing_role"]
        grouped[role].append(target)

    rows = []
    for role, targets in sorted(grouped.items()):
        first = targets[0]
        summary = first["obstruction_summary"]
        leg = next(
            item
            for item in first["matter_and_cup_leg_audits"]
            if item["role"] == role
        )
        rows.append(
            {
                "obstruction_role": role,
                "target_count": len(targets),
                "represented_weight": sum(target["weight"] for target in targets),
                "operators": sorted({target["operator"] for target in targets}),
                "source_windows": sorted({target["source"]["window"] for target in targets}),
                "line_bundle": leg["line_bundle"],
                "cohomology_key": leg["cohomology_key"],
                "representative_method": leg["representative_method"],
                "branch_actual": summary["branch_actual"],
                "computed_actual": summary["computed_actual"],
                "reason": summary["reason"],
                "rank_feasibility": branch_minus_deficit(first),
                "e1_total_degree_representations": leg[
                    "e1_total_degree_representations"
                ],
                "e2_resolution": leg.get("e2_resolution"),
                "escape_hint": escape_hint(role, summary, leg),
            }
        )
    return rows


def escape_hint(role: str, summary: dict[str, Any], leg: dict[str, Any]) -> str:
    if "requires an impossible image-rank split" in summary["reason"]:
        return (
            "avoid branch completions that demand image rank beyond an eigenspace "
            "source/target bound; require rank-feasible requested characters before promotion"
        )
    if leg.get("representative_method") == "dimension_certified_equivariant_e2":
        return (
            "avoid cup-dual branch assignments that request a non-regular character "
            "when dimension-certified E2 gives a regular representative"
        )
    if leg.get("representative_method") == "first_page_kernel":
        return (
            "avoid branch kernels whose requested dimension/character is smaller "
            "than the explicit equivariant d1 kernel"
        )
    return "requires a representative-compatible leg audit before promotion"


def scan_materialized_escape_candidates(
    *,
    windows: int,
    max_unique_operators: int,
    max_audits: int,
) -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    ensure_pycicy_compat()
    manifold = make_pycicy(pycicy_config(conf))
    context = load_5259_action_context()
    line_cache: dict[tuple[int, ...], dict[str, Any]] = {}

    operator_counts: Counter[str] = Counter()
    operator_weights: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    selected = []
    audited = []
    total_records = 0
    total_weight = 0
    triplet_only_records = 0
    skipped_known_operator_records = 0

    for source, weight, record in source_records(windows):
        total_records += 1
        total_weight += weight
        mass_table = refined_mass_table(record)
        classification = refined_classification(record, mass_table)
        status_counts[classification["status"]] += weight
        triplet_only = [
            item
            for item in mass_table
            if item["character_refined_support_class"] == "triplet_only_character_mass"
        ]
        if not triplet_only:
            continue
        triplet_only_records += 1
        for item in triplet_only:
            op = operator_label(item)
            operator_counts[op] += 1
            operator_weights[op] += weight
        novel = [
            item for item in triplet_only if operator_label(item) not in KNOWN_FAILURE_OPERATORS
        ]
        if not novel:
            skipped_known_operator_records += 1
            continue
        if len(selected) >= max_unique_operators:
            continue
        seen_ops = {item["operator"] for item in selected}
        for item in novel:
            op = operator_label(item)
            if op in seen_ops:
                continue
            candidate = full_candidate_record(
                source=source,
                weight=weight,
                record=record,
                mass_table=mass_table,
                classification=classification,
            )
            selected.append(
                {
                    "operator": op,
                    "source": source,
                    "weight": weight,
                    "candidate_label": candidate["label"],
                    "classification": classification,
                    "proton_allowed_count": proton_allowed_count(candidate),
                    "candidate": candidate,
                    "operator_record": item,
                }
            )
            seen_ops.add(op)
            if len(selected) >= max_unique_operators:
                break

    for item in selected[:max_audits]:
        audit = audit_triplet_operator(
            manifold=manifold,
            conf=conf,
            context=context,
            line_cache=line_cache,
            candidate=item["candidate"],
            operator=item["operator_record"],
        )
        audited.append(
            {
                "operator": item["operator"],
                "candidate_label": item["candidate_label"],
                "source": item["source"],
                "weight": item["weight"],
                "classification": item["classification"],
                "proton_allowed_count": item["proton_allowed_count"],
                "representative_status": audit["status"],
                "eligible_for_exact_cup_product_rank": audit[
                    "eligible_for_exact_cup_product_rank"
                ],
                "obstruction_summary": audit.get("obstruction_summary"),
                "unresolved_summary": audit.get("unresolved_summary"),
                "matter_leg_statuses": [
                    {
                        "role": leg["role"],
                        "status": leg["status"],
                        "reason": leg["reason"],
                        "branch_actual": leg.get("branch_actual"),
                        "computed_actual": leg.get("computed_actual"),
                        "representative_method": leg.get("representative_method"),
                    }
                    for leg in audit["matter_and_cup_leg_audits"]
                ],
            }
        )

    return {
        "bounds": {
            "windows": windows,
            "max_unique_operators": max_unique_operators,
            "max_audits": max_audits,
            "known_failure_operators_excluded_from_escape_audit": sorted(
                KNOWN_FAILURE_OPERATORS
            ),
        },
        "scanned": {
            "materialized_records": total_records,
            "represented_weight": total_weight,
            "records_with_triplet_only_shadow_operator": triplet_only_records,
            "records_skipped_because_only_known_failure_operators": skipped_known_operator_records,
            "classification_status_weight": dict(sorted(status_counts.items())),
        },
        "triplet_only_operator_rows": dict(sorted(operator_counts.items())),
        "triplet_only_operator_weight": dict(sorted(operator_weights.items())),
        "selected_escape_operator_count": len(selected),
        "audited_escape_target_count": len(audited),
        "audited_escape_targets": audited,
        "representative_compatible_targets": [
            item for item in audited if item["representative_status"] == "representative_compatible"
        ],
        "representative_unresolved_targets": [
            item for item in audited if item["representative_status"] == "representative_unresolved"
        ],
        "representative_obstructed_targets": [
            item for item in audited if item["representative_status"] == "representative_obstructed"
        ],
    }


def build_report(
    *,
    windows: int,
    max_unique_operators: int,
    max_audits: int,
    rerank_json: Path,
    prefilter_json: Path,
    prefilter_verification_json: Path,
) -> dict[str, Any]:
    rerank = load_json(rerank_json)
    prefilter = load_json(prefilter_json)
    prefilter_verification = load_json(prefilter_verification_json)
    anatomy = obstruction_anatomy(rerank)
    escape_scan = scan_materialized_escape_candidates(
        windows=windows,
        max_unique_operators=max_unique_operators,
        max_audits=max_audits,
    )
    compatible = escape_scan["representative_compatible_targets"]
    gates = {
        "imports_verified_prefilter": gate(
            prefilter["all_gates_pass"]
            and prefilter_verification["all_gates_pass"]
            and prefilter["summary"]["representative_compatible_weight"] == 0,
            f"{prefilter_json} + {prefilter_verification_json}",
            "classifier starts from the verified representative-prefilter closure",
        ),
        "obstruction_classes_cover_closed_frontier": gate(
            {item["obstruction_role"] for item in anatomy}
            == {
                "5_12:cup_H1_wedge2_V_dual",
                "5bar_02:physical_H1_wedge2_V",
                "5bar_04:physical_H1_wedge2_V",
                "5bar_23:physical_H1_wedge2_V",
            }
            and sum(item["represented_weight"] for item in anatomy) == 1962,
            str(rerank_json),
            "four representative obstruction classes account for all shadow-viable weight",
        ),
        "escape_scan_is_bounded": gate(
            escape_scan["bounds"]["max_unique_operators"] == max_unique_operators
            and escape_scan["bounds"]["max_audits"] == max_audits,
            "escape scan bounds",
            "escape scan is explicitly bounded and does not expand the radius frontier",
        ),
        "escape_scan_covers_materialized_q1_records": gate(
            escape_scan["scanned"]["represented_weight"] == 549038
            and escape_scan["scanned"]["materialized_records"] > 0,
            "materialized radius-9 source records",
            "escape scan traversed existing materialized q=1 source records",
        ),
        "no_representative_compatible_escape_target": gate(
            len(compatible) == 0,
            "audited escape targets",
            "bounded escape scan found no representative-compatible triplet mass target",
        ),
    }
    return {
        "title": "Radius-9 Representative Obstruction And Escape Report",
        "status": (
            "representative_compatible_escape_target_found"
            if compatible
            else "no_representative_compatible_escape_target_in_bounded_materialized_scan"
        ),
        "scope": (
            "classify representative-realizability obstructions and test a bounded "
            "representative-first escape scan over materialized radius-9 q=1 records"
        ),
        "source_artifacts": {
            "rerank_json": str(rerank_json),
            "prefilter_json": str(prefilter_json),
            "prefilter_verification_json": str(prefilter_verification_json),
        },
        "obstruction_anatomy": anatomy,
        "escape_scan": escape_scan,
        "interpretation": {
            "active_bottleneck": "representative-realizability, not cup-product rank",
            "search_guidance": (
                "future search should prefilter branch-completed characters by "
                "rank-feasible and E2-certified representative characters before "
                "lead/cup-product promotion"
            ),
            "grind_assessment": (
                "blind radius expansion is low-value until the grammar can generate "
                "mass operators outside the observed representative-failure shapes"
            ),
        },
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    scan = report["escape_scan"]
    lines = [
        f"# {report['title']}",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Obstruction Anatomy",
        "",
    ]
    for item in report["obstruction_anatomy"]:
        lines.append(
            f"- `{item['obstruction_role']}` weight `{item['represented_weight']}` "
            f"operators `{item['operators']}`: branch `{item['branch_actual']['multiplicities']}` "
            f"vs representative `{item['computed_actual']['multiplicities']}`; "
            f"{item['escape_hint']}"
        )
    lines.extend(
        [
            "",
            "## Bounded Escape Scan",
            "",
            f"- bounds: `{scan['bounds']}`",
            f"- scanned: `{scan['scanned']}`",
            f"- triplet-only operator rows: `{scan['triplet_only_operator_rows']}`",
            f"- selected escape operator count: `{scan['selected_escape_operator_count']}`",
            f"- audited escape target count: `{scan['audited_escape_target_count']}`",
            f"- representative-compatible targets: `{len(scan['representative_compatible_targets'])}`",
            f"- representative-unresolved targets: `{len(scan['representative_unresolved_targets'])}`",
            f"- representative-obstructed targets: `{len(scan['representative_obstructed_targets'])}`",
            "",
            "## Interpretation",
            "",
        ]
    )
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
    parser.add_argument("--max-unique-operators", type=int, default=24)
    parser.add_argument("--max-audits", type=int, default=24)
    parser.add_argument(
        "--rerank-json",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_representative_survivor_rerank.json"
        ),
    )
    parser.add_argument(
        "--prefilter-json",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_representative_prefilter_rollup.json"
        ),
    )
    parser.add_argument(
        "--prefilter-verification-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_prefilter_rollup_verification.json"
        ),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_obstruction_escape_report.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_obstruction_escape_report.md"
        ),
    )
    args = parser.parse_args()
    report = build_report(
        windows=args.windows,
        max_unique_operators=args.max_unique_operators,
        max_audits=args.max_audits,
        rerank_json=Path(args.rerank_json),
        prefilter_json=Path(args.prefilter_json),
        prefilter_verification_json=Path(args.prefilter_verification_json),
    )
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, md_out)
    print(f"status={report['status']}")
    print(
        "escape_scan="
        + json.dumps(
            {
                "selected": report["escape_scan"]["selected_escape_operator_count"],
                "audited": report["escape_scan"]["audited_escape_target_count"],
                "compatible": len(report["escape_scan"]["representative_compatible_targets"]),
                "unresolved": len(report["escape_scan"]["representative_unresolved_targets"]),
            },
            sort_keys=True,
        )
    )
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
