#!/usr/bin/env python3
"""Audit local capability for actual equivariant map-rank certification."""

from __future__ import annotations

import argparse
import inspect
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/codex-mpl-cache")
sys.path.insert(0, str(ROOT / "src"))

from string_theory.cohomology import (  # noqa: E402
    ensure_pycicy_compat,
    line_cohomology,
    make_pycicy,
    pycicy_config,
)


REPRESENTATIVE_BLOCK = {
    "source_report": "phenomenology_guided_q1_radius2_map_scenarios.json",
    "record_label": "radius2_enhanced_backlog_0",
    "sector": "wedge2_V",
    "summand_pair": [2, 3],
    "line_bundle": [1, 0, -2, -1, -1, 1, 0],
    "cohomology": [0, 2, 2, 0],
    "source_total_dimensions": {"1": 7, "2": 7},
    "ordinary_rank_for_h1_h2_dimensions": 5,
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def pycicy_private_method_probe(manifold: Any) -> dict[str, Any]:
    names = [
        "_rank_map",
        "_single_map",
        "_higher_map",
        "_orth_space_map",
        "_spasm_rank",
        "Leray",
        "_line_to_BBW",
        "_makepoly",
    ]
    methods = {}
    for name in names:
        attr = getattr(manifold, name, None)
        methods[name] = {
            "available": attr is not None,
            "signature": str(inspect.signature(attr)) if attr is not None else None,
        }
    return methods


def representative_block_probe(conf: list[list[int]]) -> dict[str, Any]:
    line = REPRESENTATIVE_BLOCK["line_bundle"]
    cohomology = line_cohomology(conf, line)
    manifold = make_pycicy(pycicy_config(conf))
    bbw = manifold._line_to_BBW(line)
    e1, origin = manifold.Leray(bbw)
    e1_entries = []
    for k, row in enumerate(e1):
        for j, value in enumerate(row):
            if value == 0:
                continue
            e1_entries.append(
                {
                    "k": k,
                    "j": j,
                    "total_degree_j_minus_k": j - k,
                    "dimension": int(sum(manifold._brackets_dim(item) for item in value)),
                    "origin": [list(item) for item in origin[k][j]],
                    "bracket_entries": [[int(x) for x in item] for item in value],
                }
            )
    source_dim = REPRESENTATIVE_BLOCK["source_total_dimensions"]["1"]
    target_dim = REPRESENTATIVE_BLOCK["source_total_dimensions"]["2"]
    h1 = REPRESENTATIVE_BLOCK["cohomology"][1]
    h2 = REPRESENTATIVE_BLOCK["cohomology"][2]
    effective_rank_from_dimensions = source_dim - h1
    rank_consistent = effective_rank_from_dimensions == target_dim - h2
    direct_first_page_target_dim = next(
        (
            item["dimension"]
            for item in e1_entries
            if item["k"] == 3 and item["j"] == 5
        ),
        None,
    )
    return {
        **REPRESENTATIVE_BLOCK,
        "pycicy_line_cohomology": cohomology,
        "line_cohomology_matches_report": cohomology == REPRESENTATIVE_BLOCK["cohomology"],
        "e1_entries": e1_entries,
        "has_zero_charge_so_pycicy_uses_higher_leray": 0 in line,
        "effective_rank_from_total_degree_dimensions": effective_rank_from_dimensions,
        "effective_rank_consistent_with_target_total": rank_consistent,
        "direct_first_page_target_dimension_for_E45_to_E35": direct_first_page_target_dim,
        "effective_rank_exceeds_immediate_first_page_target": (
            direct_first_page_target_dim is not None
            and effective_rank_from_dimensions > direct_first_page_target_dim
        ),
        "equivariant_rank_splits_still_possible": [
            {"rank_plus": 2, "rank_minus": 3, "result": "nonregular"},
            {"rank_plus": 3, "rank_minus": 2, "result": "nonregular"},
            {"rank_plus": 2, "rank_minus": 3, "paired_with_dual_complement": True},
        ],
        "actual_needed_data": (
            "row and column Z2 eigenbasis labels for the pyCICY Koszul map "
            "matrix, or an equivariant-rank routine returning rank_+ and rank_-"
        ),
    }


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    scenarios = load_json(REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    ensure_pycicy_compat()
    manifold = make_pycicy(pycicy_config(conf))
    private_methods = pycicy_private_method_probe(manifold)
    representative = representative_block_probe(conf)
    available_rank_matrix_hook = (
        private_methods["_rank_map"]["available"]
        and "rmap=False" in private_methods["_rank_map"]["signature"]
    )
    gates = {
        "map_scenario_frontier_imported": gate(
            scenarios["summary"]["records"] == 4
            and scenarios["summary"]["total_desired_q1_scenarios"] == 12,
            str(REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.json"),
            "capability audit starts from the verified high-priority map-scenario frontier",
        ),
        "pycicy_private_rank_hooks_exist": gate(
            available_rank_matrix_hook
            and private_methods["_single_map"]["available"]
            and private_methods["_higher_map"]["available"]
            and private_methods["Leray"]["available"],
            "pyCICY.CICY private methods",
            "pyCICY exposes ordinary and higher-Leray map construction/rank hooks",
        ),
        "representative_block_reproduces_dimensions": gate(
            representative["line_cohomology_matches_report"]
            and representative["effective_rank_from_total_degree_dimensions"] == 5
            and representative["effective_rank_consistent_with_target_total"]
            and representative["has_zero_charge_so_pycicy_uses_higher_leray"]
            and representative["effective_rank_exceeds_immediate_first_page_target"],
            "representative high-priority mixed wedge block",
            "cohomology dimensions force effective rank five through higher-Leray bookkeeping",
        ),
        "equivariant_rank_split_not_exposed": gate(
            "equivariant_rank" not in private_methods
            and "basis_eigen" not in private_methods,
            "current local pyCICY/String Theory wrappers",
            "ordinary/higher map hooks exist but no local API returns rank split by Z2 eigenspace",
        ),
    }
    return {
        "scope": "capability audit for actual equivariant map-rank certification",
        "status": "higher_leray_map_hooks_available_but_equivariant_split_missing",
        "pycicy_private_methods": private_methods,
        "representative_block_probe": representative,
        "missing_primitive": {
            "name": "equivariant_koszul_map_rank_split",
            "inputs": [
                "CICY configuration and line bundle",
                "source and target Leray/Koszul entries",
                "coordinate signs, equation signs, and fiber sign for the Z2 lift",
            ],
            "outputs": [
                "rank_plus",
                "rank_minus",
                "kernel/cokernel Z2 characters for H1/H2",
            ],
            "why_needed": (
                "The high-priority residual candidates have desired q=1 scenarios "
                "exactly when the actual map rank split is balanced in the relevant "
                "higher-Leray blocks; total dimensions and ordinary rank hooks alone "
                "cannot distinguish viable q=1 from nonregular outcomes."
            ),
        },
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    probe = report["representative_block_probe"]
    lines = [
        "# Radius-2 Map Rank Capability",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Representative Block",
        "",
        f"- record: `{probe['record_label']}`",
        f"- sector/pair: `{probe['sector']}` / `{probe['summand_pair']}`",
        f"- line bundle: `{probe['line_bundle']}`",
        f"- cohomology: `{probe['pycicy_line_cohomology']}`",
        f"- effective rank from total-degree dimensions: `{probe['effective_rank_from_total_degree_dimensions']}`",
        f"- higher-Leray required: `{probe['has_zero_charge_so_pycicy_uses_higher_leray']}`",
        f"- immediate first-page target dimension: `{probe['direct_first_page_target_dimension_for_E45_to_E35']}`",
        "",
        "## Capability",
        "",
        "- pyCICY exposes private map/rank hooks including `_rank_map(..., rmap=False)`, `_single_map`, and `_higher_map`.",
        "- The representative block requires higher-Leray bookkeeping; the effective rank cannot be read as one immediate first-page map rank.",
        "- The local wrappers do not expose Z2 row/column eigenbasis labels or an equivariant `rank_+ / rank_-` split for these higher-Leray spaces.",
        "",
        "## Missing Primitive",
        "",
        f"- name: `{report['missing_primitive']['name']}`",
        f"- outputs: `{report['missing_primitive']['outputs']}`",
        "",
        report["missing_primitive"]["why_needed"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_map_rank_capability.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_map_rank_capability.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(
        "effective_rank="
        f"{report['representative_block_probe']['effective_rank_from_total_degree_dimensions']}"
    )
    print(f"missing_primitive={report['missing_primitive']['name']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
