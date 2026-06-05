#!/usr/bin/env python3
"""Detect the remaining radius-3 small-map sign-consistency conflict."""

from __future__ import annotations

import argparse
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

from build_phenomenology_guided_q1_radius2_equivariant_first_page_probe import (  # noqa: E402
    equivariant_rank_map,
    matrix_rank,
    rank_split,
)
from build_phenomenology_guided_q1_radius2_higher_rank_probe import (  # noqa: E402
    equivariant_higher_simple_map,
)
from build_phenomenology_guided_q1_radius2_projected_higher_rank_probe import (  # noqa: E402
    signs_for_entry,
)
from build_vectorlike_obstruction_report import load_5259_action_context  # noqa: E402
from string_theory.cohomology import ensure_pycicy_compat, make_pycicy, pycicy_config  # noqa: E402

CONFLICT_LINE = [-1, 2, 0, 1, 1, -1, 0]
CONFLICT_DUAL = [1, -2, 0, -1, -1, 1, 0]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def sign_constraints(matrix: Any, source_signs: list[int]) -> dict[int, list[int]]:
    constraints: dict[int, set[int]] = {}
    for row in range(matrix.shape[0]):
        seen = {
            source_signs[col]
            for col in range(matrix.shape[1])
            if matrix[row, col] != 0
        }
        if seen:
            constraints[row] = seen
    return {row: sorted(values) for row, values in sorted(constraints.items())}


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    current = load_json(REPORTS / "phenomenology_guided_q1_radius3_current_frontier.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    context = load_5259_action_context()
    ensure_pycicy_compat()
    manifold = make_pycicy(pycicy_config(conf))
    e1, origin = manifold.Leray(manifold._line_to_BBW(CONFLICT_LINE))

    first_page = equivariant_rank_map(
        manifold=manifold,
        source_entries=[[int(x) for x in item] for item in e1[4][5]],
        target_entries=[[int(x) for x in item] for item in e1[3][5]],
        source_origins=[list(item) for item in origin[4][5]],
        target_origins=[list(item) for item in origin[3][5]],
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    )
    higher = equivariant_higher_simple_map(
        manifold=manifold,
        space1=[0, e1[6][7], origin[6][7], True, 2],
        space2=[0, e1[3][5], origin[3][5], True, 2],
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    ).T
    first_source_signs = signs_for_entry(
        manifold=manifold,
        conf=conf,
        line_bundle=CONFLICT_LINE,
        e1=e1,
        origin=origin,
        entry=(4, 5),
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    )
    higher_source_signs = signs_for_entry(
        manifold=manifold,
        conf=conf,
        line_bundle=CONFLICT_LINE,
        e1=e1,
        origin=origin,
        entry=(6, 7),
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    )
    target_signs = signs_for_entry(
        manifold=manifold,
        conf=conf,
        line_bundle=CONFLICT_LINE,
        e1=e1,
        origin=origin,
        entry=(3, 5),
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    )
    first_constraints = sign_constraints(first_page, first_source_signs)
    higher_constraints = sign_constraints(higher, higher_source_signs)
    conflicts = []
    for row in sorted(set(first_constraints).intersection(higher_constraints)):
        if first_constraints[row] != higher_constraints[row]:
            conflicts.append(
                {
                    "target_row": row,
                    "first_page_requires": first_constraints[row],
                    "higher_map_requires": higher_constraints[row],
                    "naive_target_sign": target_signs[row],
                }
            )
    high_priority_has_line = any(
        block["line_bundle"] == CONFLICT_LINE
        for record in current["high_priority_unresolved_frontier"]
        for block in record["missing_character_blocks"]
    )
    first_split = rank_split(
        matrix=first_page,
        source_signs=first_source_signs,
        target_signs=target_signs,
    )
    higher_split = rank_split(
        matrix=higher,
        source_signs=higher_source_signs,
        target_signs=target_signs,
    )
    gates = {
        "target_line_is_high_priority": gate(
            high_priority_has_line,
            str(REPORTS / "phenomenology_guided_q1_radius3_current_frontier.json"),
            "probe targets one of the remaining high-priority unresolved line blocks",
        ),
        "first_page_is_equivariant": gate(
            first_split["rank_total"] == 4
            and first_split["cross_eigen_nonzero_entries"] == 0,
            "d1 map E(4,5)->E(3,5)",
            "first-page map is block diagonal in the reconstructed Z2 eigenspaces",
        ),
        "higher_map_needed_but_crosses_signs": gate(
            matrix_rank(higher) == 1
            and higher_split["cross_eigen_nonzero_entries"] == 1,
            "higher map E(6,7)->E(3,5)",
            "the pyCICY-required rank-one higher map crosses reconstructed eigenspaces",
        ),
        "shared_target_row_conflict_identified": gate(
            conflicts
            == [
                {
                    "target_row": 0,
                    "first_page_requires": [-1],
                    "higher_map_requires": [1],
                    "naive_target_sign": -1,
                }
            ],
            "target E(3,5) sign constraints",
            "the same target basis row is forced to opposite signs by d1 and the higher map",
        ),
    }
    return {
        "scope": "radius-3 high-priority sign-consistency conflict probe",
        "status": "character_certificate_blocked_by_sign_constraint_conflict",
        "line_bundle": CONFLICT_LINE,
        "dual_line_bundle": CONFLICT_DUAL,
        "first_page_split": first_split,
        "higher_map_split": higher_split,
        "first_page_constraints": first_constraints,
        "higher_map_constraints": higher_constraints,
        "conflicts": conflicts,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-3 Sign-Conflict Probe",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- line bundle: `{report['line_bundle']}`",
        f"- dual line bundle: `{report['dual_line_bundle']}`",
        f"- first-page split: `{report['first_page_split']}`",
        f"- higher-map split: `{report['higher_map_split']}`",
        f"- conflicts: `{report['conflicts']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_sign_conflict_probe.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_sign_conflict_probe.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"conflicts={report['conflicts']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
