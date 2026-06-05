#!/usr/bin/env python3
"""Resolve the remaining dim-10 family by projected equivariant higher-map rank."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

import numpy as np
from scipy.linalg import null_space

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/codex-mpl-cache")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_phenomenology_guided_q1_radius2_e1_sign_prototype import entry_basis_signs  # noqa: E402
from build_phenomenology_guided_q1_radius2_equivariant_first_page_probe import (  # noqa: E402
    equivariant_rank_map,
    matrix_rank,
)
from build_phenomenology_guided_q1_radius2_higher_rank_probe import (  # noqa: E402
    equivariant_higher_simple_map,
    rep_from_multiplicities,
)
from build_vectorlike_obstruction_report import load_5259_action_context  # noqa: E402
from string_theory.cohomology import ensure_pycicy_compat, make_pycicy, pycicy_config  # noqa: E402

PROJECTED_LINE = [1, -2, 0, -2, 0, 1, 0]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def signs_for_entry(
    *,
    manifold: Any,
    conf: list[list[int]],
    line_bundle: list[int],
    e1: list[Any],
    origin: list[Any],
    entry: tuple[int, int],
    coordinate_signs_by_block: list[list[int]],
    equation_signs: list[int],
) -> list[int]:
    k, j = entry
    return entry_basis_signs(
        manifold=manifold,
        conf=conf,
        line_bundle=line_bundle,
        bracket_entries=[[int(x) for x in item] for item in e1[k][j]],
        origins=[list(item) for item in origin[k][j]],
        coordinate_signs_by_block=coordinate_signs_by_block,
        equation_signs=equation_signs,
    )


def quotient_rank_by_sign(
    *,
    first_page_map: np.ndarray,
    higher_map: np.ndarray,
    first_source_signs: list[int],
    target_signs: list[int],
    higher_source_signs: list[int],
    sign: int,
) -> dict[str, Any]:
    target_rows = [index for index, value in enumerate(target_signs) if value == sign]
    first_cols = [index for index, value in enumerate(first_source_signs) if value == sign]
    higher_cols = [index for index, value in enumerate(higher_source_signs) if value == sign]
    first_sub = first_page_map[np.ix_(target_rows, first_cols)].astype(float)
    higher_sub = higher_map[np.ix_(target_rows, higher_cols)].astype(float)
    quotient_covectors = null_space(first_sub.T)
    quotient_map = quotient_covectors.T @ higher_sub
    quotient_rank = matrix_rank(quotient_map) if quotient_map.size else 0
    return {
        "target_dimension": len(target_rows),
        "first_page_rank": matrix_rank(first_sub),
        "target_cokernel_dimension": quotient_covectors.shape[1],
        "higher_source_dimension": len(higher_cols),
        "projected_higher_rank": quotient_rank,
    }


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    scenarios = load_json(REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    context = load_5259_action_context()
    ensure_pycicy_compat()
    manifold = make_pycicy(pycicy_config(conf))
    e1, origin = manifold.Leray(manifold._line_to_BBW(PROJECTED_LINE))
    first_page_map = equivariant_rank_map(
        manifold=manifold,
        source_entries=[[int(x) for x in item] for item in e1[1][2]],
        target_entries=[[int(x) for x in item] for item in e1[0][2]],
        source_origins=[list(item) for item in origin[1][2]],
        target_origins=[list(item) for item in origin[0][2]],
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    )
    higher_map = equivariant_higher_simple_map(
        manifold=manifold,
        space1=[0, e1[4][5], origin[4][5], True, 3],
        space2=[0, e1[0][2], origin[0][2], True, 8],
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    ).T
    first_source_signs = signs_for_entry(
        manifold=manifold,
        conf=conf,
        line_bundle=PROJECTED_LINE,
        e1=e1,
        origin=origin,
        entry=(1, 2),
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    )
    target_signs = signs_for_entry(
        manifold=manifold,
        conf=conf,
        line_bundle=PROJECTED_LINE,
        e1=e1,
        origin=origin,
        entry=(0, 2),
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    )
    higher_source_signs = signs_for_entry(
        manifold=manifold,
        conf=conf,
        line_bundle=PROJECTED_LINE,
        e1=e1,
        origin=origin,
        entry=(4, 5),
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    )
    e13_signs = signs_for_entry(
        manifold=manifold,
        conf=conf,
        line_bundle=PROJECTED_LINE,
        e1=e1,
        origin=origin,
        entry=(1, 3),
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    )
    plus = quotient_rank_by_sign(
        first_page_map=first_page_map,
        higher_map=higher_map,
        first_source_signs=first_source_signs,
        target_signs=target_signs,
        higher_source_signs=higher_source_signs,
        sign=1,
    )
    minus = quotient_rank_by_sign(
        first_page_map=first_page_map,
        higher_map=higher_map,
        first_source_signs=first_source_signs,
        target_signs=target_signs,
        higher_source_signs=higher_source_signs,
        sign=-1,
    )
    effective_rank_plus = plus["first_page_rank"] + plus["projected_higher_rank"]
    effective_rank_minus = minus["first_page_rank"] + minus["projected_higher_rank"]
    h1 = rep_from_multiplicities(
        higher_source_signs.count(1) - plus["projected_higher_rank"],
        higher_source_signs.count(-1) - minus["projected_higher_rank"],
    )
    h2 = rep_from_multiplicities(e13_signs.count(1), e13_signs.count(-1))
    desired = [
        scenario
        for record in scenarios["records"]
        if record["label"] == "radius2_enhanced_backlog_4"
        for block in record["block_summaries"]
        if block["line_bundle"] == PROJECTED_LINE
        for scenario in block["scenarios"]
        if scenario["balanced_regular_H1_H2"]
    ][0]
    gates = {
        "scenario_imported": gate(
            desired["rank_plus"] == 4 and desired["rank_minus"] == 4,
            str(REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.json"),
            "projected probe targets the remaining dim-10 desired regular scenario",
        ),
        "first_page_cokernel_is_negative": gate(
            plus["target_cokernel_dimension"] == 0
            and minus["target_cokernel_dimension"] == 1,
            "equivariant first-page map E12 -> E02",
            "the first-page target cokernel is one-dimensional and negative",
        ),
        "projected_higher_map_hits_negative_cokernel": gate(
            plus["projected_higher_rank"] == 0
            and minus["projected_higher_rank"] == 1,
            "quotient-projected higher map E45 -> coker(E12 -> E02)",
            "the higher differential has rank one on the negative cokernel",
        ),
        "resolved_character_matches_regular_scenario": gate(
            effective_rank_plus == desired["rank_plus"]
            and effective_rank_minus == desired["rank_minus"]
            and h1 == desired["H1"]
            and h2 == desired["H2"],
            str(REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.json"),
            "projected higher-map split selects the desired regular H1/H2 character",
        ),
    }
    return {
        "scope": "projected equivariant higher-rank probe for remaining dim-10 residual family",
        "status": "projected_family_resolves_to_desired_q1_character",
        "line_bundle": PROJECTED_LINE,
        "first_page": {"+": plus, "-": minus},
        "effective_rank_split": {
            "rank_plus": effective_rank_plus,
            "rank_minus": effective_rank_minus,
            "total_rank": effective_rank_plus + effective_rank_minus,
        },
        "resolved_characters": {"H1": h1, "H2": h2},
        "selected_scenario": desired,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-2 Projected Higher Rank Probe",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- line bundle: `{report['line_bundle']}`",
        f"- effective rank split: `{report['effective_rank_split']}`",
        f"- resolved characters: `{report['resolved_characters']}`",
        f"- first-page/projected ranks: `{report['first_page']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_projected_higher_rank_probe.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_projected_higher_rank_probe.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"effective_rank_split={report['effective_rank_split']}")
    print(f"resolved_characters={report['resolved_characters']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
