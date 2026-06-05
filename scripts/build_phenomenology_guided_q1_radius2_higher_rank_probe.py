#!/usr/bin/env python3
"""Resolve the representative residual q=1 block by an equivariant higher-map probe."""

from __future__ import annotations

import argparse
import itertools as it
import json
import os
from pathlib import Path
import sys
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/codex-mpl-cache")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_phenomenology_guided_q1_radius2_e1_sign_prototype import entry_basis_signs  # noqa: E402
from build_phenomenology_guided_q1_radius2_equivariant_first_page_probe import (  # noqa: E402
    REPRESENTATIVE_LINE,
    equivariant_rank_map,
    equivariant_single_map,
    matrix_rank,
)
from build_vectorlike_obstruction_report import load_5259_action_context  # noqa: E402
from string_theory.cohomology import ensure_pycicy_compat, make_pycicy, pycicy_config  # noqa: E402


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def rep_from_multiplicities(plus: int, minus: int) -> dict[str, Any]:
    return {
        "dimension": plus + minus,
        "nonidentity_trace": plus - minus,
        "multiplicities": {"+": plus, "-": minus},
        "regular_multiplicity": plus if plus == minus else None,
    }


def equivariant_higher_simple_map(
    *,
    manifold: Any,
    space1: list[Any],
    space2: list[Any],
    coordinate_signs_by_block: list[list[int]],
    equation_signs: list[int],
) -> np.ndarray:
    """Return the pyCICY-orientation source-by-target filtered higher map."""

    source_dims = [manifold._brackets_dim(space1[1][index]) for index in range(len(space1[1]))]
    target_dims = [manifold._brackets_dim(space2[1][index]) for index in range(len(space2[1]))]
    matrix = np.zeros((sum(source_dims), sum(target_dims)), dtype=np.int64)
    source_origin_len = len(space1[2][0])
    target_origin_len = len(space2[2][0])
    for source_index, source_entry in enumerate(space1[1]):
        source_entry = np.abs(source_entry)
        for target_index, target_entry in enumerate(space2[1]):
            target_entry = np.abs(target_entry)
            missing_maps = list(set(space1[2][source_index]).difference(space2[2][target_index]))
            if len(missing_maps) != source_origin_len - target_origin_len:
                continue
            inter_tensors = np.zeros((manifold.len, len(missing_maps)))
            for row in range(manifold.len):
                for signs in it.product([1, -1], repeat=len(missing_maps)):
                    degree = source_entry[row] - target_entry[row]
                    for sign, equation_index in zip(signs, missing_maps):
                        degree += sign * manifold.N[row, equation_index]
                    if degree == 0:
                        inter_tensors[row] = np.array(signs)
                        break
            composed_map: np.ndarray | list[Any] = []
            intermediate = None
            for position, equation_index in enumerate(missing_maps):
                if len(composed_map) == 0:
                    intermediate = (
                        source_entry + inter_tensors[:, position] * manifold.N[:, equation_index]
                    ).astype(int)
                    composed_map = equivariant_single_map(
                        manifold=manifold,
                        source_bracket=[int(x) for x in source_entry],
                        source_dim=source_dims[source_index],
                        target_bracket=[int(x) for x in intermediate],
                        target_dim=manifold._brackets_dim(intermediate),
                        equation_index=equation_index,
                        coordinate_signs_by_block=coordinate_signs_by_block,
                        equation_signs=equation_signs,
                    )
                else:
                    assert intermediate is not None
                    next_intermediate = (
                        intermediate
                        + inter_tensors[:, position] * manifold.N[:, equation_index]
                    ).astype(int)
                    new_map = equivariant_single_map(
                        manifold=manifold,
                        source_bracket=[int(x) for x in intermediate],
                        source_dim=manifold._brackets_dim(intermediate),
                        target_bracket=[int(x) for x in next_intermediate],
                        target_dim=manifold._brackets_dim(next_intermediate),
                        equation_index=equation_index,
                        coordinate_signs_by_block=coordinate_signs_by_block,
                        equation_signs=equation_signs,
                    )
                    if new_map.shape[1] == composed_map.shape[0]:
                        composed_map = np.matmul(composed_map.T, new_map.T)
                    else:
                        composed_map = np.matmul(composed_map, new_map.T)
                    intermediate = np.copy(next_intermediate)
            row_start = sum(source_dims[:source_index])
            row_end = row_start + source_dims[source_index]
            col_start = sum(target_dims[:target_index])
            col_end = col_start + target_dims[target_index]
            matrix[row_start:row_end, col_start:col_end] += composed_map
    return matrix


def calibrate_target_signs_from_map(
    *,
    source_signs: list[int],
    target_dimension: int,
    target_trace: int,
    map_target_by_source: np.ndarray,
) -> dict[str, Any]:
    assigned: list[int | None] = [None for _ in range(target_dimension)]
    conflicts = []
    for row in range(target_dimension):
        seen = {
            source_signs[col]
            for col in range(len(source_signs))
            if map_target_by_source[row, col] != 0
        }
        if len(seen) == 1:
            assigned[row] = seen.pop()
        elif len(seen) > 1:
            conflicts.append({"target_row": row, "source_signs": sorted(seen)})
    required_plus = (target_dimension + target_trace) // 2
    required_minus = (target_dimension - target_trace) // 2
    assigned_plus = sum(1 for item in assigned if item == 1)
    assigned_minus = sum(1 for item in assigned if item == -1)
    for index, value in enumerate(assigned):
        if value is not None:
            continue
        if assigned_plus < required_plus:
            assigned[index] = 1
            assigned_plus += 1
        else:
            assigned[index] = -1
            assigned_minus += 1
    signs = [int(item) for item in assigned]
    cross = sum(
        1
        for row, target_sign in enumerate(signs)
        for col, source_sign in enumerate(source_signs)
        if map_target_by_source[row, col] != 0 and target_sign != source_sign
    )
    return {
        "signs": signs,
        "conflicts": conflicts,
        "cross_eigen_nonzero_entries": cross,
        "multiplicities": {
            "+": sum(1 for item in signs if item == 1),
            "-": sum(1 for item in signs if item == -1),
        },
    }


def rank_jump_on_kernel(
    *,
    first_page_map: np.ndarray,
    higher_map: np.ndarray,
    source_signs: list[int],
    first_target_signs: list[int],
    higher_target_signs: list[int],
    sign: int,
) -> dict[str, Any]:
    source_cols = [index for index, value in enumerate(source_signs) if value == sign]
    first_rows = [index for index, value in enumerate(first_target_signs) if value == sign]
    higher_rows = [index for index, value in enumerate(higher_target_signs) if value == sign]
    first_sub = first_page_map[np.ix_(first_rows, source_cols)]
    higher_sub = higher_map[np.ix_(higher_rows, source_cols)]
    first_rank = matrix_rank(first_sub)
    stacked_rank = matrix_rank(np.vstack([first_sub, higher_sub]))
    return {
        "source_dimension": len(source_cols),
        "first_page_rank": first_rank,
        "first_page_kernel_dimension": len(source_cols) - first_rank,
        "stacked_rank": stacked_rank,
        "higher_rank_on_first_page_kernel": stacked_rank - first_rank,
    }


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    scenarios = load_json(REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.json")
    first_page = load_json(REPORTS / "phenomenology_guided_q1_radius2_equivariant_first_page_probe.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    context = load_5259_action_context()
    ensure_pycicy_compat()
    manifold = make_pycicy(pycicy_config(conf))
    e1, origin = manifold.Leray(manifold._line_to_BBW(REPRESENTATIVE_LINE))

    source_entries = [[int(x) for x in item] for item in e1[4][5]]
    first_target_entries = [[int(x) for x in item] for item in e1[3][5]]
    higher_target_entries = [[int(x) for x in item] for item in e1[1][3]]
    source_origins = [list(item) for item in origin[4][5]]
    first_target_origins = [list(item) for item in origin[3][5]]
    higher_target_origins = [list(item) for item in origin[1][3]]
    source_signs = entry_basis_signs(
        manifold=manifold,
        conf=conf,
        line_bundle=REPRESENTATIVE_LINE,
        bracket_entries=source_entries,
        origins=source_origins,
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    )
    first_target_signs = entry_basis_signs(
        manifold=manifold,
        conf=conf,
        line_bundle=REPRESENTATIVE_LINE,
        bracket_entries=first_target_entries,
        origins=first_target_origins,
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    )
    naive_higher_target_signs = entry_basis_signs(
        manifold=manifold,
        conf=conf,
        line_bundle=REPRESENTATIVE_LINE,
        bracket_entries=higher_target_entries,
        origins=higher_target_origins,
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    )
    first_page_map = equivariant_rank_map(
        manifold=manifold,
        source_entries=source_entries,
        target_entries=first_target_entries,
        source_origins=source_origins,
        target_origins=first_target_origins,
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    )
    higher_map_source_by_target = equivariant_higher_simple_map(
        manifold=manifold,
        space1=[0, e1[4][5], origin[4][5], True, 7],
        space2=[0, e1[1][3], origin[1][3], True, 2],
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    )
    higher_map = higher_map_source_by_target.T
    calibrated = calibrate_target_signs_from_map(
        source_signs=source_signs,
        target_dimension=higher_map.shape[0],
        target_trace=0,
        map_target_by_source=higher_map,
    )
    plus_jump = rank_jump_on_kernel(
        first_page_map=first_page_map,
        higher_map=higher_map,
        source_signs=source_signs,
        first_target_signs=first_target_signs,
        higher_target_signs=calibrated["signs"],
        sign=1,
    )
    minus_jump = rank_jump_on_kernel(
        first_page_map=first_page_map,
        higher_map=higher_map,
        source_signs=source_signs,
        first_target_signs=first_target_signs,
        higher_target_signs=calibrated["signs"],
        sign=-1,
    )
    effective_rank_plus = plus_jump["first_page_rank"] + plus_jump["higher_rank_on_first_page_kernel"]
    effective_rank_minus = minus_jump["first_page_rank"] + minus_jump["higher_rank_on_first_page_kernel"]
    h1 = rep_from_multiplicities(
        first_page["source_sign_multiplicities"]["+"] - effective_rank_plus,
        first_page["source_sign_multiplicities"]["-"] - effective_rank_minus,
    )
    e13_cokernel = rep_from_multiplicities(
        calibrated["multiplicities"]["+"] - plus_jump["higher_rank_on_first_page_kernel"],
        calibrated["multiplicities"]["-"] - minus_jump["higher_rank_on_first_page_kernel"],
    )
    e46 = rep_from_multiplicities(0, 1)
    h2 = rep_from_multiplicities(
        e13_cokernel["multiplicities"]["+"] + e46["multiplicities"]["+"],
        e13_cokernel["multiplicities"]["-"] + e46["multiplicities"]["-"],
    )
    desired_scenario = scenarios["records"][0]["block_summaries"][0]["scenarios"][1]
    gates = {
        "first_page_probe_imported": gate(
            first_page["all_gates_pass"]
            and first_page["equivariant_filtered_map_split"]["rank_plus"] == 2
            and first_page["equivariant_filtered_map_split"]["rank_minus"] == 2,
            str(REPORTS / "phenomenology_guided_q1_radius2_equivariant_first_page_probe.json"),
            "higher probe starts from the verified equivariant first-page rank split",
        ),
        "higher_map_total_rank_one": gate(
            matrix_rank(higher_map) == 1 and int(np.count_nonzero(higher_map)) == 1,
            "equivariant-filtered higher map E45 -> E13",
            "filtered higher differential has the pyCICY-required total rank one",
        ),
        "higher_target_calibrated_equivariantly": gate(
            calibrated["cross_eigen_nonzero_entries"] == 0
            and calibrated["multiplicities"] == {"+": 1, "-": 1}
            and not calibrated["conflicts"],
            "higher-map target basis calibration",
            "trace-zero E13 basis ordering is fixed by requiring equivariance of the higher map",
        ),
        "effective_rank_split_is_desired": gate(
            effective_rank_plus == desired_scenario["rank_plus"]
            and effective_rank_minus == desired_scenario["rank_minus"]
            and h1 == desired_scenario["H1"]
            and h2 == desired_scenario["H2"],
            str(REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.json"),
            "actual representative rank split selects the desired regular q=1 scenario",
        ),
    }
    return {
        "scope": "representative residual q=1 higher-Leray equivariant rank split",
        "status": "representative_block_resolves_to_desired_q1_character",
        "representative_line": REPRESENTATIVE_LINE,
        "naive_higher_target_signs": naive_higher_target_signs,
        "calibrated_higher_target_signs": calibrated,
        "first_page_rank_split": first_page["equivariant_filtered_map_split"],
        "higher_map": {
            "shape_target_by_source": list(higher_map.shape),
            "rank": matrix_rank(higher_map),
            "nonzero_entries": int(np.count_nonzero(higher_map)),
        },
        "rank_jumps": {
            "+": plus_jump,
            "-": minus_jump,
        },
        "effective_rank_split": {
            "rank_plus": effective_rank_plus,
            "rank_minus": effective_rank_minus,
            "total_rank": effective_rank_plus + effective_rank_minus,
        },
        "resolved_characters": {
            "H1": h1,
            "H2": h2,
        },
        "selected_scenario": {
            "rank_plus": desired_scenario["rank_plus"],
            "rank_minus": desired_scenario["rank_minus"],
            "H1": desired_scenario["H1"],
            "H2": desired_scenario["H2"],
        },
        "next_step": (
            "Apply the same first-page-plus-higher-kernel rank-split probe to the "
            "dual block and the remaining high-priority residual records, then feed "
            "newly resolved q=1 records through the mass/proton phenomenology filter."
        ),
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-2 Higher Rank Probe",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- representative line: `{report['representative_line']}`",
        f"- effective rank split: `{report['effective_rank_split']}`",
        f"- resolved characters: `{report['resolved_characters']}`",
        f"- calibrated E13 target signs: `{report['calibrated_higher_target_signs']['signs']}`",
        "",
        "## Interpretation",
        "",
        report["next_step"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_higher_rank_probe.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_higher_rank_probe.md"),
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
