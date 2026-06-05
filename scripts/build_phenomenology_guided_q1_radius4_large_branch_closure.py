#!/usr/bin/env python3
"""Close the large selected radius-4 branch by aggregate constraints."""

from __future__ import annotations

import argparse
import copy
import itertools
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from build_cicy5259_quotient_wilson_line_report import (  # noqa: E402
    representation_record,
    sector_record,
)
from build_phenomenology_filter_report import candidate_certificate_from_5259_record  # noqa: E402
from build_phenomenology_guided_q1_radius2_enhanced_backlog import (  # noqa: E402
    SECTOR_LABELS,
    SECTOR_TARGET_KEYS,
    apply_monoid_obstruction_override,
    prediction_from_characters,
)
from build_phenomenology_guided_q1_radius4_unresolved_branch_analysis import (  # noqa: E402
    complete_characters_with_branch,
    possible_actuals_for_cohomology,
    unresolved_certs,
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def actual_trace(actual: dict[str, Any]) -> int:
    return sum(rep["nonidentity_trace"] for rep in actual.values())


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


def record_for_large_branch() -> dict[str, Any]:
    known = load_json(REPORTS / "phenomenology_guided_q1_radius4_known_line_resolved.json")
    for record in known["resolved_records"]:
        if (
            record["source_window"] == "window4"
            and record["source_filtered_label"] == "radius4_adjacency_filtered_0"
        ):
            return record
    raise KeyError("large branch source record not found")


def complete_sector_records(characters: dict[str, Any]) -> dict[str, Any]:
    completed = copy.deepcopy(characters)
    for sector_key, target_keys in SECTOR_TARGET_KEYS.items():
        sector = completed[sector_key]
        completed[sector_key] = sector_record(
            label=SECTOR_LABELS[sector_key],
            line_certificates=sector["line_certificates"],
            cohomology_degree_keys=target_keys,
        )
    return completed


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    branch = load_json(REPORTS / "phenomenology_guided_q1_radius4_unresolved_branch_analysis.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    source = record_for_large_branch()
    blocks = unresolved_certs(source["characters"])
    option_lists = [block["actual_options"] for block in blocks]
    total_branches = 1
    for options in option_lists:
        total_branches *= len(options)

    counts = Counter()
    q1_trace_patterns = Counter()
    q1_representative: tuple[dict[str, Any], ...] | None = None
    q1_support_signatures = set()
    for branch_actuals in itertools.product(*option_lists):
        completed_characters = complete_characters_with_branch(
            source["characters"], blocks, branch_actuals
        )
        prediction = prediction_from_characters(completed_characters)
        if (
            prediction["regular_character_rule_applies"]
            and prediction["net_families"] == 3
            and prediction["colored_triplet_vectorlike_pairs"] == 1
            and prediction["electroweak_doublet_vectorlike_pairs"] == 1
        ):
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

    if q1_representative is None:
        representative_filtered = None
        representative_status = None
    else:
        representative_characters = complete_characters_with_branch(
            source["characters"], blocks, q1_representative
        )
        representative = copy.deepcopy(source)
        representative["characters"] = representative_characters
        representative["character_certified"] = True
        representative["vectorlike_pair_prediction"] = prediction_from_characters(
            representative_characters
        )
        representative["radius4_large_branch_representative"] = {
            "method": "first_dimension_compatible_desired_q1_branch",
            "support_invariant_across_q1_branches": len(q1_support_signatures) == 1,
        }
        representative_filtered = candidate_certificate_from_5259_record(
            label="window4_radius4_adjacency_filtered_0_large_branch_q1_representative",
            record=representative,
            conf=conf,
        )
        representative_filtered["source_window"] = source["source_window"]
        representative_filtered["source_filtered_label"] = source[
            "source_filtered_label"
        ]
        representative_filtered["radius4_large_branch_representative"] = representative[
            "radius4_large_branch_representative"
        ]
        apply_monoid_obstruction_override(representative_filtered)
        representative_status = representative_filtered["classification"]["status"]

    all_q1_obstructed_by_representative = (
        representative_filtered is not None
        and representative_filtered["classification"]["category"]
        == "phenomenologically obstructed"
        and len(q1_support_signatures) == 1
    )
    gates = {
        "imports_branch_analysis": gate(
            branch["all_gates_pass"]
            and branch["summary"]["records_skipped"] == 1
            and branch["skipped_records"][0]["label"]
            == "window4/radius4_adjacency_filtered_0",
            str(REPORTS / "phenomenology_guided_q1_radius4_unresolved_branch_analysis.json"),
            "large-branch closure starts from the sole skipped branch-analysis record",
        ),
        "full_branch_space_counted": gate(
            total_branches == 531441
            and counts["desired_q1"] + counts["not_desired_q1"] == total_branches,
            "dimension-compatible large branch enumeration",
            "the full 12-block branch space is counted at aggregate level",
        ),
        "q1_support_is_invariant": gate(
            counts["desired_q1"] > 0 and len(q1_support_signatures) == 1,
            "large branch support signatures",
            "all desired-q1 completions have the same charged-matter support for mass/proton tables",
        ),
        "q1_representative_obstructed": gate(
            all_q1_obstructed_by_representative,
            "large branch q=1 representative",
            "the support-invariant desired-q1 branch representative is phenomenologically obstructed",
        ),
    }
    return {
        "scope": "aggregate closure of the large selected radius-4 branch space",
        "status": "large_branch_all_q1_completions_obstructed"
        if all_q1_obstructed_by_representative
        else "large_branch_not_closed",
        "summary": {
            "total_branches": total_branches,
            "desired_q1_branches": counts["desired_q1"],
            "not_desired_q1_branches": counts["not_desired_q1"],
            "q1_support_signature_count": len(q1_support_signatures),
            "q1_representative_status": representative_status,
            "viable_q1_branches": 0 if all_q1_obstructed_by_representative else None,
        },
        "q1_trace_patterns": {
            str(key): value for key, value in sorted(q1_trace_patterns.items())
        },
        "unresolved_blocks": [
            {
                "sector": block["sector_key"],
                "summand_index": block["summand_index"],
                "summand_pair": block["summand_pair"],
                "line_bundle": block["line_bundle"],
                "cohomology": block["cohomology"],
                "option_count": len(block["actual_options"]),
            }
            for block in blocks
        ],
        "q1_representative_candidate": representative_filtered,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-4 Large Branch Closure",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The large 12-block branch space is closed at aggregate level: "
                "desired-q1 completions all share the same charged-matter support, "
                "so one q=1 representative suffices for the charge-level mass/proton "
                "filter. That representative is obstructed by the same filter."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_large_branch_closure.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_large_branch_closure.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
