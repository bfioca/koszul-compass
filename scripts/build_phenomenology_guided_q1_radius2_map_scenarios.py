#!/usr/bin/env python3
"""Enumerate equivariant map-character scenarios for residual radius-2 records."""

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
    h1_dim = cert["cohomology"][low]
    h2_dim = cert["cohomology"][high]
    if source["dimension"] - h1_dim != target["dimension"] - h2_dim:
        return []
    total_rank = source["dimension"] - h1_dim
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
        h1_plus = source["multiplicities"]["+"] - rank_plus
        h1_minus = source["multiplicities"]["-"] - rank_minus
        h2_plus = target["multiplicities"]["+"] - rank_plus
        h2_minus = target["multiplicities"]["-"] - rank_minus
        h1_trace = h1_plus - h1_minus
        h2_trace = h2_plus - h2_minus
        scenarios.append(
            {
                "rank_plus": rank_plus,
                "rank_minus": rank_minus,
                "H1": representation_record(h1_plus + h1_minus, h1_trace),
                "H2": representation_record(h2_plus + h2_minus, h2_trace),
                "balanced_regular_H1_H2": h1_trace == 0 and h2_trace == 0,
            }
        )
    return scenarios


def unresolved_certs_by_block(record: dict[str, Any]) -> list[dict[str, Any]]:
    certs = []
    for sector_key, sector in record["characters"].items():
        for cert in sector["line_certificates"]:
            if cert["actual_character_computed"] or not any(cert["cohomology"]):
                continue
            certs.append({"sector": sector_key, "cert": cert})
    return certs


def aggregate_for_choice(record: dict[str, Any], choices: list[dict[str, Any]]) -> dict[str, Any]:
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
            if (sector, key) in totals:
                totals[(sector, key)] = add_rep(totals[(sector, key)], scenario[key])
    h1 = totals[("wedge2_V", "H1")]
    h2 = totals[("wedge2_V", "H2")]
    return {
        "wedge2_V_H1": h1,
        "wedge2_V_H2": h2,
        "wedge2_V_dual_H1": totals[("wedge2_V_dual", "H1")],
        "wedge2_V_dual_H2": totals[("wedge2_V_dual", "H2")],
        "vectorlike_prediction": {
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
        },
    }


def summarize_record(record: dict[str, Any]) -> dict[str, Any]:
    block_summaries = []
    scenario_lists = []
    unsupported_blocks = []
    for index, item in enumerate(unresolved_certs_by_block(record)):
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
        block_summaries.append(block)
        if scenarios:
            scenario_lists.append(
                [
                    {"sector": item["sector"], "block_index": index, "scenario": scenario}
                    for scenario in scenarios
                ]
            )
        else:
            unsupported_blocks.append(block)

    aggregate_summaries = []
    prediction_counter: Counter[str] = Counter()
    desired_q1_scenario_count = 0
    if not unsupported_blocks:
        for choices in itertools.product(*scenario_lists):
            aggregate = aggregate_for_choice(record, list(choices))
            prediction = aggregate["vectorlike_prediction"]
            key = json.dumps(prediction, sort_keys=True)
            prediction_counter[key] += 1
            desired = (
                prediction["regular_character_rule_applies"]
                and prediction["net_families"] == 3
                and prediction["colored_triplet_vectorlike_pairs"] == 1
            )
            if desired:
                desired_q1_scenario_count += 1
            aggregate_summaries.append(
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
                    "desired_q1": desired,
                    **aggregate,
                }
            )

    predictions = [
        {"count": count, "prediction": json.loads(key)}
        for key, count in sorted(prediction_counter.items())
    ]
    return {
        "label": record["label"],
        "source_window": record["source_window"],
        "source_filtered_label": record["source_filtered_label"],
        "current_prediction_after_enhancement": record["vectorlike_pair_prediction"],
        "all_blocks_supported_by_two_term_rank_scenarios": not unsupported_blocks,
        "unsupported_block_count": len(unsupported_blocks),
        "block_summaries": block_summaries,
        "scenario_product_count": len(aggregate_summaries),
        "desired_q1_scenario_count": desired_q1_scenario_count,
        "prediction_outcomes": predictions,
        "aggregate_scenarios": aggregate_summaries,
    }


def build_report() -> dict[str, Any]:
    residual = load_json(REPORTS / "phenomenology_guided_q1_radius2_residual_backlog.json")
    enhanced = load_json(REPORTS / "phenomenology_guided_q1_radius2_enhanced_backlog.json")
    high_labels = {
        item["label"]
        for item in residual["records"]
        if item["priority_bucket"] == "high_priority_q1_or_adjacent"
    }
    records = [
        summarize_record(record)
        for record in enhanced["enhanced_records"]
        if record["label"] in high_labels
    ]
    desired_records = [
        record for record in records if record["desired_q1_scenario_count"] > 0
    ]
    gates = {
        "imports_high_priority_residue": gate(
            len(high_labels) == 4 and len(records) == 4,
            str(REPORTS / "phenomenology_guided_q1_radius2_residual_backlog.json"),
            "scenario report starts from the four high-priority residual records",
        ),
        "two_term_rank_scenarios_cover_high_priority_blocks": gate(
            all(record["all_blocks_supported_by_two_term_rank_scenarios"] for record in records)
            and sum(record["unsupported_block_count"] for record in records) == 0,
            "high-priority residual blocks",
            "all high-priority unresolved blocks are two-term rank-scenario cases",
        ),
        "desired_q1_scenarios_exist": gate(
            len(desired_records) == 4
            and all(record["desired_q1_scenario_count"] > 0 for record in records),
            "rank-scenario enumeration",
            "each high-priority residual record has at least one rank scenario with desired q=1 wedge character",
        ),
    }
    return {
        "scope": "rank-scenario enumeration for high-priority residual radius-2 character maps",
        "status": "desired_q1_rank_scenarios_remain_possible",
        "summary": {
            "records": len(records),
            "records_with_desired_q1_scenarios": len(desired_records),
            "total_scenarios": sum(record["scenario_product_count"] for record in records),
            "total_desired_q1_scenarios": sum(
                record["desired_q1_scenario_count"] for record in records
            ),
        },
        "records": records,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-2 High-Priority Map Scenarios",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
        f"- records: `{report['summary']['records']}`",
        f"- records with desired q=1 scenarios: `{report['summary']['records_with_desired_q1_scenarios']}`",
        f"- total rank scenarios: `{report['summary']['total_scenarios']}`",
        f"- desired q=1 rank scenarios: `{report['summary']['total_desired_q1_scenarios']}`",
        "",
        "## Records",
        "",
    ]
    for record in report["records"]:
        lines.append(
            "- "
            f"`{record['label']}` from `{record['source_window']}/{record['source_filtered_label']}`: "
            f"scenarios `{record['scenario_product_count']}`, "
            f"desired q=1 `{record['desired_q1_scenario_count']}`, "
            f"outcomes `{record['prediction_outcomes']}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The high-priority residue cannot be closed by representation "
                "bounds alone. Each record has balanced equivariant-rank scenarios "
                "that would restore the desired q=1 wedge character, so the next "
                "certificate step must compute the actual equivariant map rank split."
            ),
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"records={report['summary']['records']}")
    print(f"total_scenarios={report['summary']['total_scenarios']}")
    print(f"desired_q1_scenarios={report['summary']['total_desired_q1_scenarios']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
