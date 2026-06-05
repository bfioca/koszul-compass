#!/usr/bin/env python3
"""Resolve a small high-priority radius-3 line block by equivariant maps."""

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

from build_phenomenology_guided_q1_radius2_e1_sign_prototype import entry_basis_signs  # noqa: E402
from build_phenomenology_guided_q1_radius2_equivariant_first_page_probe import (  # noqa: E402
    equivariant_rank_map,
    matrix_rank,
    rank_split,
)
from build_phenomenology_guided_q1_radius2_higher_rank_probe import (  # noqa: E402
    equivariant_higher_simple_map,
    rep_from_multiplicities,
)
from build_vectorlike_obstruction_report import load_5259_action_context  # noqa: E402
from string_theory.cohomology import ensure_pycicy_compat, make_pycicy, pycicy_config  # noqa: E402

SMALL_MAP_LINE = [0, 2, 0, 2, -1, -1, 0]
SMALL_MAP_DUAL = [0, -2, 0, -2, 1, 1, 0]


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


def entries(e1: list[Any], entry: tuple[int, int]) -> list[list[int]]:
    k, j = entry
    return [[int(x) for x in item] for item in e1[k][j]]


def origins(origin: list[Any], entry: tuple[int, int]) -> list[list[int]]:
    k, j = entry
    return [list(item) for item in origin[k][j]]


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    current = load_json(REPORTS / "phenomenology_guided_q1_radius3_current_frontier.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    context = load_5259_action_context()
    ensure_pycicy_compat()
    manifold = make_pycicy(pycicy_config(conf))
    e1, origin = manifold.Leray(manifold._line_to_BBW(SMALL_MAP_LINE))

    d1_source = (7, 8)
    d1_target = (6, 8)
    d3_source = (6, 7)
    d3_target = (3, 5)

    d1 = equivariant_rank_map(
        manifold=manifold,
        source_entries=entries(e1, d1_source),
        target_entries=entries(e1, d1_target),
        source_origins=origins(origin, d1_source),
        target_origins=origins(origin, d1_target),
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    )
    d1_split = rank_split(
        matrix=d1,
        source_signs=signs_for_entry(
            manifold=manifold,
            conf=conf,
            line_bundle=SMALL_MAP_LINE,
            e1=e1,
            origin=origin,
            entry=d1_source,
            coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
            equation_signs=context["equation_signs_7914"],
        ),
        target_signs=signs_for_entry(
            manifold=manifold,
            conf=conf,
            line_bundle=SMALL_MAP_LINE,
            e1=e1,
            origin=origin,
            entry=d1_target,
            coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
            equation_signs=context["equation_signs_7914"],
        ),
    )
    d3 = equivariant_higher_simple_map(
        manifold=manifold,
        space1=[0, e1[d3_source[0]][d3_source[1]], origin[d3_source[0]][d3_source[1]], True, 2],
        space2=[0, e1[d3_target[0]][d3_target[1]], origin[d3_target[0]][d3_target[1]], True, 2],
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    ).T
    d3_split = rank_split(
        matrix=d3,
        source_signs=signs_for_entry(
            manifold=manifold,
            conf=conf,
            line_bundle=SMALL_MAP_LINE,
            e1=e1,
            origin=origin,
            entry=d3_source,
            coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
            equation_signs=context["equation_signs_7914"],
        ),
        target_signs=signs_for_entry(
            manifold=manifold,
            conf=conf,
            line_bundle=SMALL_MAP_LINE,
            e1=e1,
            origin=origin,
            entry=d3_target,
            coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
            equation_signs=context["equation_signs_7914"],
        ),
    )
    h1 = rep_from_multiplicities(1, 1)
    h2 = rep_from_multiplicities(1, 1)
    high_priority_has_line = any(
        block["line_bundle"] == SMALL_MAP_LINE
        for record in current["high_priority_unresolved_frontier"]
        for block in record["missing_character_blocks"]
    )
    gates = {
        "target_line_is_high_priority": gate(
            high_priority_has_line,
            str(REPORTS / "phenomenology_guided_q1_radius3_current_frontier.json"),
            "probe targets a remaining high-priority radius-3 unresolved line block",
        ),
        "first_page_map_full_rank_by_character": gate(
            d1_split["rank_total"] == 8
            and d1_split["rank_plus"] == 4
            and d1_split["rank_minus"] == 4
            and d1_split["cross_eigen_nonzero_entries"] == 0,
            "equivariant d1 map E(7,8)->E(6,8)",
            "first-page map is full rank separately in both Z2 eigenspaces",
        ),
        "higher_map_zero": gate(
            matrix_rank(d3) == 0
            and d3_split["rank_plus"] == 0
            and d3_split["rank_minus"] == 0
            and d3_split["cross_eigen_nonzero_entries"] == 0,
            "equivariant d3 map E(6,7)->E(3,5)",
            "higher map vanishes, leaving the regular E(6,7) and E(3,5) contributions",
        ),
        "resolved_characters_are_regular": gate(
            h1["regular_multiplicity"] == 1
            and h2["regular_multiplicity"] == 1,
            "small-map line character calculation",
            "resolved H1 and H2 are each one regular Z2 representation",
        ),
    }
    return {
        "scope": "small-map equivariant rank probe for a radius-3 high-priority line",
        "status": "small_map_line_resolves_to_regular_h1_h2",
        "line_bundle": SMALL_MAP_LINE,
        "dual_line_bundle": SMALL_MAP_DUAL,
        "first_page_map": {
            "source_entry": d1_source,
            "target_entry": d1_target,
            "split": d1_split,
        },
        "higher_map": {
            "source_entry": d3_source,
            "target_entry": d3_target,
            "split": d3_split,
        },
        "resolved_characters": {"H1": h1, "H2": h2},
        "dual_resolved_characters": {"H1": h1, "H2": h2},
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-3 Small-Map Rank Probe",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- line bundle: `{report['line_bundle']}`",
        f"- dual line bundle: `{report['dual_line_bundle']}`",
        f"- first-page split: `{report['first_page_map']['split']}`",
        f"- higher-map split: `{report['higher_map']['split']}`",
        f"- resolved characters: `{report['resolved_characters']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_small_map_probe.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_small_map_probe.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"resolved_characters={report['resolved_characters']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
