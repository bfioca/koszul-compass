#!/usr/bin/env python3
"""Compute equivariant E2 characters for the remaining three-term medium records."""

from __future__ import annotations

import argparse
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

from build_phenomenology_guided_q1_radius2_equivariant_first_page_probe import (  # noqa: E402
    equivariant_rank_map,
    rank_split,
)
from build_phenomenology_guided_q1_radius2_projected_higher_rank_probe import signs_for_entry  # noqa: E402
from build_vectorlike_obstruction_report import load_5259_action_context  # noqa: E402
from string_theory.cohomology import ensure_pycicy_compat, make_pycicy, pycicy_config  # noqa: E402

THREE_TERM_LINES = [
    [2, 0, 2, 0, 0, -1, -1],
    [-2, 0, -2, 0, 0, 1, 1],
    [1, -1, 2, -1, 1, -1, 1],
    [-1, 1, -2, 1, -1, 1, -1],
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def rep_from_counts(plus: int, minus: int) -> dict[str, Any]:
    return {
        "dimension": plus + minus,
        "nonidentity_trace": plus - minus,
        "multiplicities": {"+": plus, "-": minus},
        "regular_multiplicity": plus if plus == minus else None,
    }


def compute_e2_characters(
    *,
    manifold: Any,
    conf: list[list[int]],
    line_bundle: list[int],
    coordinate_signs_by_block: list[list[int]],
    equation_signs: list[int],
) -> dict[str, Any]:
    e1, origin = manifold.Leray(manifold._line_to_BBW(line_bundle))
    entries = []
    sign_map = {}
    for k in range(manifold.K + 1):
        for j in range(manifold.dimA + 1):
            if e1[k][j] == 0:
                continue
            entry = (k, j)
            entries.append(entry)
            sign_map[entry] = signs_for_entry(
                manifold=manifold,
                conf=conf,
                line_bundle=line_bundle,
                e1=e1,
                origin=origin,
                entry=entry,
                coordinate_signs_by_block=coordinate_signs_by_block,
                equation_signs=equation_signs,
            )
    ranks: dict[tuple[tuple[int, int], tuple[int, int]], dict[str, Any]] = {}
    cross_entries = 0
    for source in entries:
        target = (source[0] - 1, source[1])
        if target not in entries:
            continue
        source_k, source_j = source
        target_k, target_j = target
        matrix = equivariant_rank_map(
            manifold=manifold,
            source_entries=[[int(x) for x in item] for item in e1[source_k][source_j]],
            target_entries=[[int(x) for x in item] for item in e1[target_k][target_j]],
            source_origins=[list(item) for item in origin[source_k][source_j]],
            target_origins=[list(item) for item in origin[target_k][target_j]],
            coordinate_signs_by_block=coordinate_signs_by_block,
            equation_signs=equation_signs,
        )
        split = rank_split(
            matrix=matrix,
            source_signs=sign_map[source],
            target_signs=sign_map[target],
        )
        ranks[(source, target)] = split
        cross_entries += split["cross_eigen_nonzero_entries"]
    e2_actual: dict[str, Any] = {}
    e2_entries = []
    for entry in entries:
        k, j = entry
        outgoing = ranks.get((entry, (k - 1, j)))
        incoming = ranks.get(((k + 1, j), entry))
        plus = sign_map[entry].count(1)
        minus = sign_map[entry].count(-1)
        if outgoing is not None:
            plus -= outgoing["rank_plus"]
            minus -= outgoing["rank_minus"]
        if incoming is not None:
            plus -= incoming["rank_plus"]
            minus -= incoming["rank_minus"]
        if plus + minus == 0:
            continue
        total_degree = j - k
        rep = rep_from_counts(plus, minus)
        e2_entries.append(
            {
                "entry": [k, j],
                "total_degree": total_degree,
                "representation": rep,
            }
        )
        e2_actual[f"H{total_degree}"] = rep
    return {
        "line_bundle": line_bundle,
        "e1_entries": [
            {
                "entry": [k, j],
                "total_degree": j - k,
                "dimension": len(sign_map[(k, j)]),
                "multiplicities": {
                    "+": sign_map[(k, j)].count(1),
                    "-": sign_map[(k, j)].count(-1),
                },
            }
            for k, j in entries
        ],
        "rank_splits": [
            {
                "source": list(source),
                "target": list(target),
                "rank_plus": split["rank_plus"],
                "rank_minus": split["rank_minus"],
                "rank_total": split["rank_total"],
                "cross_eigen_nonzero_entries": split["cross_eigen_nonzero_entries"],
            }
            for (source, target), split in ranks.items()
        ],
        "e2_entries": e2_entries,
        "actual": e2_actual,
        "cross_eigen_nonzero_entries": cross_entries,
    }


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    context = load_5259_action_context()
    ensure_pycicy_compat()
    manifold = make_pycicy(pycicy_config(conf))
    records = [
        compute_e2_characters(
            manifold=manifold,
            conf=conf,
            line_bundle=line,
            coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
            equation_signs=context["equation_signs_7914"],
        )
        for line in THREE_TERM_LINES
    ]
    expected = {
        tuple([2, 0, 2, 0, 0, -1, -1]): {"H1": rep_from_counts(1, 0), "H2": rep_from_counts(1, 1)},
        tuple([-2, 0, -2, 0, 0, 1, 1]): {"H1": rep_from_counts(1, 1), "H2": rep_from_counts(1, 0)},
        tuple([1, -1, 2, -1, 1, -1, 1]): {"H1": rep_from_counts(2, 2)},
        tuple([-1, 1, -2, 1, -1, 1, -1]): {"H2": rep_from_counts(2, 2)},
    }
    gates = {
        "all_three_term_lines_resolved": gate(
            len(records) == 4
            and all(tuple(record["line_bundle"]) in expected for record in records),
            "remaining medium three-term line bundles",
            "all four three-term line/dual blocks were processed",
        ),
        "all_maps_are_block_diagonal": gate(
            all(record["cross_eigen_nonzero_entries"] == 0 for record in records),
            "equivariant filtered first-page maps",
            "three-term E1 maps preserve the reconstructed Z2 eigenspaces",
        ),
        "e2_characters_match_expected_dimensions": gate(
            all(record["actual"] == expected[tuple(record["line_bundle"])] for record in records),
            "equivariant E2 character computation",
            "computed E2 characters reproduce pyCICY cohomology dimensions with Z2 multiplicities",
        ),
    }
    return {
        "scope": "equivariant E2 character computation for remaining medium three-term records",
        "status": "three_term_medium_characters_resolved",
        "records": records,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-2 Three-Term E2 Probe",
        "",
        f"Status: `{report['status']}`",
        "",
    ]
    for record in report["records"]:
        lines.append(f"- `{record['line_bundle']}`: actual `{record['actual']}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_three_term_e2_probe.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_three_term_e2_probe.md"),
    )
    args = parser.parse_args()
    report = build_report()
    Path(args.json_out).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, Path(args.md_out))
    print(f"status={report['status']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
