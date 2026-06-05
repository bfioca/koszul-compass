#!/usr/bin/env python3
"""Aggregate closure for a large skipped radius-6 targeted branch."""

from __future__ import annotations

import argparse
import copy
from collections import Counter
import itertools
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from build_phenomenology_filter_report import candidate_certificate_from_5259_record  # noqa: E402
from build_phenomenology_guided_q1_radius2_enhanced_backlog import (  # noqa: E402
    apply_monoid_obstruction_override,
    prediction_from_characters,
)
from build_phenomenology_guided_q1_radius5_branch_analysis import (  # noqa: E402
    complete_characters_with_branch,
    unresolved_certs,
)
from phenomenology_guided_q1_representative_grammar_gate import (  # noqa: E402
    RepresentativeGrammarGate,
    apply_representative_grammar_boundary,
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def support_signature(characters: dict[str, Any]) -> dict[str, list[Any]]:
    support: dict[str, list[Any]] = {}
    for sector_key, sector in characters.items():
        entries = []
        for cert in sector["line_certificates"]:
            if any(cert["cohomology"]):
                entries.append(
                    {
                        "summand_index": cert.get("summand_index"),
                        "summand_pair": cert.get("summand_pair"),
                        "line_bundle": cert["line_bundle"],
                        "actual_keys": sorted(cert["actual"]),
                    }
                )
        support[sector_key] = entries
    return support


def source_record_for_skipped_label(scout: dict[str, Any], label: str) -> dict[str, Any]:
    for filtered, certified in zip(
        scout["filtered_candidate_records"], scout["certified_records"]
    ):
        if filtered["label"] == label:
            record = copy.deepcopy(certified)
            record["radius6_filtered_label"] = filtered["label"]
            record["radius6_source_label"] = filtered.get("radius6_source_label")
            return record
    raise KeyError(f"skipped source record not found: {label}")


def is_target_q1(prediction: dict[str, Any]) -> bool:
    return (
        prediction["regular_character_rule_applies"]
        and prediction["net_families"] == 3
        and prediction["colored_triplet_vectorlike_pairs"] == 1
        and prediction["electroweak_doublet_vectorlike_pairs"] == 1
    )


def build_report(
    *,
    scout_json: Path,
    branch_json: Path,
    skipped_label: str | None,
    title: str,
    status: str,
    scope: str,
) -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    scout = load_json(scout_json)
    branch = load_json(branch_json)
    conf = split["full_picard_presentation_7914"]["conf"]
    skipped_records = branch["skipped_records"]
    if skipped_label is None:
        if len(skipped_records) != 1:
            raise SystemExit("--skipped-label is required when skipped record count is not one")
        skipped = skipped_records[0]
    else:
        skipped = next(
            (item for item in skipped_records if item["label"] == skipped_label),
            None,
        )
        if skipped is None:
            raise SystemExit(f"skipped label not found in branch report: {skipped_label}")
    source = source_record_for_skipped_label(scout, skipped["label"])
    blocks = unresolved_certs(source["characters"])
    option_lists = [block["actual_options"] for block in blocks]
    total_branches = 1
    for options in option_lists:
        total_branches *= len(options)

    counts: Counter[str] = Counter()
    q1_trace_patterns: Counter[tuple[int, int, int]] = Counter()
    q1_representative: tuple[dict[str, Any], ...] | None = None
    q1_support_signatures = set()
    for branch_actuals in itertools.product(*option_lists):
        completed_characters = complete_characters_with_branch(
            source["characters"], blocks, branch_actuals
        )
        prediction = prediction_from_characters(completed_characters)
        if is_target_q1(prediction):
            counts["desired_q1"] += 1
            q1_trace_patterns[
                (
                    completed_characters["V"]["cohomology_characters"]["H1"][
                        "nonidentity_trace"
                    ],
                    completed_characters["wedge2_V"]["cohomology_characters"]["H1"][
                        "nonidentity_trace"
                    ],
                    completed_characters["wedge2_V"]["cohomology_characters"]["H2"][
                        "nonidentity_trace"
                    ],
                )
            ] += 1
            if q1_representative is None:
                q1_representative = branch_actuals
            q1_support_signatures.add(
                json.dumps(support_signature(completed_characters), sort_keys=True)
            )
        else:
            counts["not_desired_q1"] += 1

    representative_filtered = None
    representative_status = None
    representative_category = None
    representative_boundary = None
    representative_gate = RepresentativeGrammarGate()
    if q1_representative is not None:
        representative_characters = complete_characters_with_branch(
            source["characters"], blocks, q1_representative
        )
        representative = copy.deepcopy(source)
        representative["characters"] = representative_characters
        representative["character_certified"] = True
        representative["vectorlike_pair_prediction"] = prediction_from_characters(
            representative_characters
        )
        representative["radius6_large_branch_representative"] = {
            "method": "first_dimension_compatible_desired_q1_branch",
            "support_invariant_across_q1_branches": len(q1_support_signatures) == 1,
            "represented_q1_branches": counts["desired_q1"],
        }
        representative_filtered = candidate_certificate_from_5259_record(
            label=f"{skipped['label']}_large_branch_q1_representative",
            record=representative,
            conf=conf,
        )
        representative_filtered["radius6_filtered_label"] = skipped["label"]
        representative_filtered["radius6_source_label"] = source.get(
            "radius6_source_label"
        )
        representative_filtered["radius6_large_branch_representative"] = representative[
            "radius6_large_branch_representative"
        ]
        apply_monoid_obstruction_override(representative_filtered)
        representative_boundary = apply_representative_grammar_boundary(
            filtered_record=representative_filtered,
            grammar_gate=representative_gate,
            source={
                "kind": "active_large_branch_closure",
                "scout_json": str(scout_json),
                "branch_json": str(branch_json),
                "skipped_label": skipped["label"],
            },
            weight=counts["desired_q1"],
        )
        representative_status = representative_filtered["classification"]["status"]
        representative_category = representative_filtered["classification"]["category"]

    representative_stage = (
        {}
        if representative_boundary is None
        else representative_boundary["representative_grammar_stage"]
    )
    representative_selection = (
        {}
        if representative_boundary is None
        else representative_boundary["selection_rule_stage"]
    )
    support_invariant = len(q1_support_signatures) == 1
    representative_promoted = bool(
        representative_stage.get("promoted_to_lead_candidate") and support_invariant
    )
    representative_pruned = bool(
        support_invariant
        and representative_selection.get("category") == "viable"
        and representative_stage.get("status") == "representative_obstructed"
    )
    representative_unresolved = bool(
        support_invariant
        and representative_selection.get("category") == "viable"
        and representative_stage.get("status") == "representative_unresolved"
    )
    promoted_q1_branches = counts["desired_q1"] if representative_promoted else 0
    pruned_q1_branches = counts["desired_q1"] if representative_pruned else 0
    unresolved_q1_branches = counts["desired_q1"] if representative_unresolved else 0
    all_q1_classified_by_representative = (
        representative_filtered is not None
        and support_invariant
        and (
            representative_category in {"phenomenologically obstructed", "unresolved"}
            or representative_promoted
        )
    )
    gates = {
        "imports_branch_analysis": gate(
            branch["all_gates_pass"]
            and branch["summary"]["records_skipped"] >= 1
            and skipped["branch_space_size"] == total_branches,
            str(branch_json),
            "large closure starts from a skipped radius6 branch",
        ),
        "full_branch_space_counted": gate(
            counts["desired_q1"] + counts["not_desired_q1"] == total_branches,
            "dimension-compatible large branch enumeration",
            "the full branch space is counted at aggregate level",
        ),
        "q1_support_is_invariant": gate(
            counts["desired_q1"] > 0 and support_invariant,
            "radius6 large branch support signatures",
            "all desired-q1 completions have the same charged-matter support for mass/proton tables",
        ),
        "representative_grammar_boundary_applied": gate(
            representative_filtered is None
            or "representative_grammar_gate" in representative_filtered,
            "representative grammar gate",
            "the q1 representative is classified at the representative grammar boundary",
        ),
        "q1_representative_classified_or_promoted": gate(
            all_q1_classified_by_representative,
            "radius6 large branch q1 representative",
            "the support-invariant desired-q1 representative is either promoted or classified as non-viable",
        ),
    }
    return {
        "scope": scope,
        "status": status if all_q1_classified_by_representative else f"{status}_not_closed",
        "summary": {
            "skipped_label": skipped["label"],
            "total_branches": total_branches,
            "desired_q1_branches": counts["desired_q1"],
            "not_desired_q1_branches": counts["not_desired_q1"],
            "q1_support_signature_count": len(q1_support_signatures),
            "q1_representative_category": representative_category,
            "q1_representative_status": representative_status,
            "representative_selection_rule_status": representative_selection.get(
                "status"
            ),
            "representative_grammar_status": representative_stage.get("status"),
            "representative_grammar_pruned_q1_branches": pruned_q1_branches,
            "representative_grammar_unresolved_q1_branches": unresolved_q1_branches,
            "representative_grammar_promoted_q1_branches": promoted_q1_branches,
            "cup_product_eligible_q1_branches": (
                counts["desired_q1"]
                if representative_stage.get("cup_product_planning_allowed")
                and support_invariant
                else 0
            ),
            "viable_q1_branches": (
                promoted_q1_branches if all_q1_classified_by_representative else None
            ),
        },
        "q1_trace_patterns": {
            str(key): value for key, value in sorted(q1_trace_patterns.items())
        },
        "unresolved_blocks": skipped["unresolved_blocks"],
        "q1_representative_candidate": representative_filtered,
        "title": title,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        f"# {report['title']}",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scout-json", required=True)
    parser.add_argument("--branch-json", required=True)
    parser.add_argument("--skipped-label", default=None)
    parser.add_argument("--title", default="Radius-6 Large Branch Closure")
    parser.add_argument(
        "--status",
        default="radius6_large_branch_all_q1_completions_classified",
    )
    parser.add_argument(
        "--scope",
        default="aggregate closure of a large radius6 targeted branch space",
    )
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--md-out", required=True)
    args = parser.parse_args()
    report = build_report(
        scout_json=Path(args.scout_json),
        branch_json=Path(args.branch_json),
        skipped_label=args.skipped_label,
        title=args.title,
        status=args.status,
        scope=args.scope,
    )
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
