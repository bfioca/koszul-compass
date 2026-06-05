#!/usr/bin/env python3
"""Enumerate map-character scenarios for medium-priority radius-2 records."""

from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def multiplicities(dimension: int, trace: int) -> dict[str, int]:
    return {"+": (dimension + trace) // 2, "-": (dimension - trace) // 2}


def representation_record(dimension: int, trace: int) -> dict[str, Any]:
    mult = multiplicities(dimension, trace)
    return {
        "dimension": dimension,
        "nonidentity_trace": trace,
        "multiplicities": mult,
        "regular_multiplicity": mult["+"] if mult["+"] == mult["-"] else None,
    }


def add_rep(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    return representation_record(
        a["dimension"] + b["dimension"],
        a["nonidentity_trace"] + b["nonidentity_trace"],
    )


def two_term_map_scenarios(cert: dict[str, Any]) -> list[dict[str, Any]]:
    source_totals = {int(key): value for key, value in cert["source_totals"].items()}
    degrees = sorted(source_totals)
    if len(degrees) != 2 or degrees[1] != degrees[0] + 1:
        return []
    low, high = degrees
    source = source_totals[low]
    target = source_totals[high]
    low_dim = cert["cohomology"][low]
    high_dim = cert["cohomology"][high]
    if source["dimension"] - low_dim != target["dimension"] - high_dim:
        return []
    total_rank = source["dimension"] - low_dim
    scenarios = []
    for rank_plus in range(total_rank + 1):
        rank_minus = total_rank - rank_plus
        if (
            rank_plus > source["multiplicities"]["+"]
            or rank_plus > target["multiplicities"]["+"]
            or rank_minus > source["multiplicities"]["-"]
            or rank_minus > target["multiplicities"]["-"]
        ):
            continue
        h_low_plus = source["multiplicities"]["+"] - rank_plus
        h_low_minus = source["multiplicities"]["-"] - rank_minus
        h_high_plus = target["multiplicities"]["+"] - rank_plus
        h_high_minus = target["multiplicities"]["-"] - rank_minus
        scenarios.append(
            {
                "rank_plus": rank_plus,
                "rank_minus": rank_minus,
                f"H{low}": representation_record(h_low_plus + h_low_minus, h_low_plus - h_low_minus),
                f"H{high}": representation_record(h_high_plus + h_high_minus, h_high_plus - h_high_minus),
            }
        )
    return scenarios


def unresolved_certs(record: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for sector_key, sector in record["characters"].items():
        for cert in sector["line_certificates"]:
            if cert["actual_character_computed"] or not any(cert["cohomology"]):
                continue
            else:
                out.append({"sector": sector_key, "cert": cert})
    return out


def aggregate_choice(record: dict[str, Any], choices: list[dict[str, Any]]) -> dict[str, Any]:
    totals = {
        ("wedge2_V", "H1"): record["characters"]["wedge2_V"]["cohomology_characters"]["H1"],
        ("wedge2_V", "H2"): record["characters"]["wedge2_V"]["cohomology_characters"]["H2"],
        ("wedge2_V_dual", "H1"): record["characters"]["wedge2_V_dual"]["cohomology_characters"]["H1"],
        ("wedge2_V_dual", "H2"): record["characters"]["wedge2_V_dual"]["cohomology_characters"]["H2"],
    }
    for choice in choices:
        sector = choice["sector"]
        scenario = choice["scenario"]
        for key in ("H1", "H2"):
            if key in scenario and (sector, key) in totals:
                totals[(sector, key)] = add_rep(totals[(sector, key)], scenario[key])
    h1 = totals[("wedge2_V", "H1")]
    h2 = totals[("wedge2_V", "H2")]
    prediction = {
        "regular_character_rule_applies": h1["regular_multiplicity"] is not None
        and h2["regular_multiplicity"] is not None,
        "h1_wedge2_regular_multiplicity": h1["regular_multiplicity"],
        "h2_wedge2_regular_multiplicity": h2["regular_multiplicity"],
        "colored_triplet_vectorlike_pairs": h2["regular_multiplicity"],
        "electroweak_doublet_vectorlike_pairs": h2["regular_multiplicity"],
        "net_families": (
            h1["regular_multiplicity"] - h2["regular_multiplicity"]
            if h1["regular_multiplicity"] is not None
            and h2["regular_multiplicity"] is not None
            else None
        ),
    }
    return {
        "wedge2_V_H1": h1,
        "wedge2_V_H2": h2,
        "wedge2_V_dual_H1": totals[("wedge2_V_dual", "H1")],
        "wedge2_V_dual_H2": totals[("wedge2_V_dual", "H2")],
        "vectorlike_prediction": prediction,
    }


def desired_q1(prediction: dict[str, Any]) -> bool:
    return (
        prediction["regular_character_rule_applies"]
        and prediction["net_families"] == 3
        and prediction["colored_triplet_vectorlike_pairs"] == 1
    )


def summarize_record(record: dict[str, Any]) -> dict[str, Any]:
    blocks = []
    scenario_lists = []
    unsupported = []
    for index, item in enumerate(unresolved_certs(record)):
        scenarios = two_term_map_scenarios(item["cert"])
        block = {
            "block_index": index,
            "sector": item["sector"],
            "summand_pair": item["cert"].get("summand_pair"),
            "line_bundle": item["cert"]["line_bundle"],
            "cohomology": item["cert"]["cohomology"],
            "source_totals": item["cert"]["source_totals"],
            "scenario_count": len(scenarios),
            "scenarios": scenarios,
        }
        blocks.append(block)
        if scenarios:
            scenario_lists.append(
                [
                    {"sector": item["sector"], "block_index": index, "scenario": scenario}
                    for scenario in scenarios
                ]
            )
        else:
            unsupported.append(block)
    aggregate_scenarios = []
    prediction_counter: Counter[str] = Counter()
    desired_count = 0
    if not unsupported:
        for choices in itertools.product(*scenario_lists):
            aggregate = aggregate_choice(record, list(choices))
            prediction = aggregate["vectorlike_prediction"]
            prediction_counter[json.dumps(prediction, sort_keys=True)] += 1
            if desired_q1(prediction):
                desired_count += 1
            aggregate_scenarios.append(
                {
                    "choice": [
                        {
                            "block_index": choice["block_index"],
                            "sector": choice["sector"],
                            "rank_plus": choice["scenario"]["rank_plus"],
                            "rank_minus": choice["scenario"]["rank_minus"],
                        }
                        for choice in choices
                    ],
                    "desired_q1": desired_q1(prediction),
                    **aggregate,
                }
            )
    return {
        "label": record["label"],
        "source_window": record["source_window"],
        "source_filtered_label": record["source_filtered_label"],
        "current_prediction_after_enhancement": record["vectorlike_pair_prediction"],
        "block_summaries": blocks,
        "unsupported_block_count": len(unsupported),
        "all_blocks_supported_by_two_term_rank_scenarios": not unsupported,
        "scenario_product_count": len(aggregate_scenarios),
        "desired_q1_scenario_count": desired_count,
        "prediction_outcomes": [
            {"count": count, "prediction": json.loads(key)}
            for key, count in sorted(prediction_counter.items())
        ],
        "aggregate_scenarios": aggregate_scenarios,
    }


def build_report() -> dict[str, Any]:
    residual = load_json(REPORTS / "phenomenology_guided_q1_radius2_residual_backlog.json")
    enhanced = load_json(REPORTS / "phenomenology_guided_q1_radius2_enhanced_backlog.json")
    medium_labels = {
        item["label"]
        for item in residual["records"]
        if item["priority_bucket"] == "medium_priority_small_map_backlog"
    }
    records = [
        summarize_record(record)
        for record in enhanced["enhanced_records"]
        if record["label"] in medium_labels
    ]
    supported_records = [
        record for record in records if record["all_blocks_supported_by_two_term_rank_scenarios"]
    ]
    desired_records = [record for record in records if record["desired_q1_scenario_count"] > 0]
    gates = {
        "imports_medium_frontier": gate(
            len(medium_labels) == 5 and len(records) == 5,
            str(REPORTS / "phenomenology_guided_q1_radius2_residual_backlog.json"),
            "scenario report starts from the five medium-priority residual records",
        ),
        "two_term_subset_identified": gate(
            len(supported_records) == 3
            and sum(record["unsupported_block_count"] for record in records) == 4,
            "medium residual blocks",
            "three medium records have two-term map scenarios and two records remain three-term unsupported",
        ),
        "desired_q1_scenarios_exist_in_two_term_subset": gate(
            len(desired_records) == 3
            and all(record["desired_q1_scenario_count"] > 0 for record in supported_records),
            "medium two-term rank-scenario enumeration",
            "each two-term medium record has at least one rank scenario with desired q=1 wedge character",
        ),
    }
    return {
        "scope": "rank-scenario enumeration for medium-priority residual radius-2 character maps",
        "status": "medium_two_term_desired_q1_scenarios_remain_possible",
        "summary": {
            "medium_records": len(records),
            "two_term_supported_records": len(supported_records),
            "unsupported_three_term_records": len(records) - len(supported_records),
            "total_scenarios": sum(record["scenario_product_count"] for record in records),
            "total_desired_q1_scenarios": sum(
                record["desired_q1_scenario_count"] for record in records
            ),
            "records_with_desired_q1_scenarios": len(desired_records),
        },
        "records": records,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-2 Medium Map Scenarios",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Records", ""])
    for record in report["records"]:
        lines.append(
            "- "
            f"`{record['label']}` from `{record['source_window']}/{record['source_filtered_label']}`: "
            f"supported `{record['all_blocks_supported_by_two_term_rank_scenarios']}`, "
            f"scenarios `{record['scenario_product_count']}`, "
            f"desired q1 `{record['desired_q1_scenario_count']}`, "
            f"unsupported blocks `{record['unsupported_block_count']}`"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_medium_map_scenarios.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_medium_map_scenarios.md"),
    )
    args = parser.parse_args()
    report = build_report()
    Path(args.json_out).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, Path(args.md_out))
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
