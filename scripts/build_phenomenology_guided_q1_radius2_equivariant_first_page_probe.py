#!/usr/bin/env python3
"""Probe equivariant first-page Koszul map ranks for a residual q=1 block."""

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

from build_phenomenology_guided_q1_radius2_e1_sign_prototype import (  # noqa: E402
    entry_basis_signs,
    monomial_sign,
)
from build_vectorlike_obstruction_report import load_5259_action_context  # noqa: E402
from string_theory.cohomology import ensure_pycicy_compat, make_pycicy, pycicy_config  # noqa: E402

REPRESENTATIVE_LINE = [1, 0, -2, -1, -1, 1, 0]
SOURCE_ENTRY = (4, 5)
TARGET_ENTRY = (3, 5)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def matrix_rank(matrix: np.ndarray) -> int:
    return int(np.linalg.matrix_rank(matrix))


def equivariant_single_map(
    *,
    manifold: Any,
    source_bracket: list[int],
    source_dim: int,
    target_bracket: list[int],
    target_dim: int,
    equation_index: int,
    coordinate_signs_by_block: list[list[int]],
    equation_signs: list[int],
) -> np.ndarray:
    target_abs = np.array([abs(entry) for entry in target_bracket])
    source_abs = np.array([abs(entry) for entry in source_bracket])
    zero = np.zeros(manifold.len)
    monomial_length = int(np.sum(manifold.M[:, 0]) + manifold.len)
    if np.array_equal(source_abs, zero):
        source_basis = np.zeros((1, monomial_length)).astype(int)
    else:
        source_basis = manifold._makepoly(source_abs, source_dim)
    moduli = target_abs - source_abs
    moduli_dim = manifold._brackets_dim(moduli)
    moduli_basis = manifold._makepoly(moduli, moduli_dim)
    if np.array_equal(target_abs, zero):
        target_basis = np.zeros((1, monomial_length)).astype(int)
    else:
        target_basis = manifold._makepoly(target_abs, target_dim)

    matrix = np.zeros((target_dim, source_dim), dtype=np.int64)
    allowed_character = equation_signs[equation_index]
    for source_index, source_monomial in enumerate(source_basis):
        for moduli_index, moduli_monomial in enumerate(moduli_basis):
            moduli_character = monomial_sign(
                monomial=[int(x) for x in moduli_monomial],
                coordinate_signs_by_block=coordinate_signs_by_block,
            )
            if moduli_character != allowed_character:
                continue
            target_monomial = []
            for source_power, moduli_power in zip(source_monomial, moduli_monomial):
                if moduli_power >= 0:
                    target_monomial.append(source_power + moduli_power)
                elif abs(moduli_power) > source_power:
                    target_monomial = []
                    break
                else:
                    target_monomial.append(source_power + moduli_power)
            if target_monomial:
                target_index = np.where(
                    np.all(target_monomial == target_basis, axis=1)
                )[0][0]
                matrix[target_index, source_index] = manifold.moduli[equation_index][
                    moduli_index
                ]
    return matrix


def equivariant_rank_map(
    *,
    manifold: Any,
    source_entries: list[list[int]],
    target_entries: list[list[int]],
    source_origins: list[list[int]],
    target_origins: list[list[int]],
    coordinate_signs_by_block: list[list[int]],
    equation_signs: list[int],
) -> np.ndarray:
    source_dims = [manifold._brackets_dim(entry) for entry in source_entries]
    target_dims = [manifold._brackets_dim(entry) for entry in target_entries]
    matrix = np.zeros((sum(target_dims), sum(source_dims)), dtype=np.int64)
    for source_index, source_dim in enumerate(source_dims):
        mappings = manifold._lorigin(source_origins[source_index], target_origins)
        col_start = sum(source_dims[:source_index])
        col_end = sum(source_dims[: source_index + 1])
        for equation_index, (allowed, target_index) in enumerate(mappings):
            if not allowed:
                continue
            koszul_sign = 1
            for position, origin_index in enumerate(source_origins[source_index]):
                if origin_index == equation_index:
                    koszul_sign = 1 if position % 2 == 0 else -1
                    break
            block = equivariant_single_map(
                manifold=manifold,
                source_bracket=source_entries[source_index],
                source_dim=source_dim,
                target_bracket=target_entries[target_index],
                target_dim=target_dims[target_index],
                equation_index=equation_index,
                coordinate_signs_by_block=coordinate_signs_by_block,
                equation_signs=equation_signs,
            )
            row_start = sum(target_dims[:target_index])
            row_end = sum(target_dims[: target_index + 1])
            matrix[row_start:row_end, col_start:col_end] += koszul_sign * block
    return matrix


def rank_split(
    *,
    matrix: np.ndarray,
    source_signs: list[int],
    target_signs: list[int],
) -> dict[str, Any]:
    cross_eigen_nonzero = 0
    for row, target_sign in enumerate(target_signs):
        for col, source_sign in enumerate(source_signs):
            if matrix[row, col] and target_sign != source_sign:
                cross_eigen_nonzero += 1
    splits = {}
    for label, sign in (("+", 1), ("-", -1)):
        rows = [index for index, value in enumerate(target_signs) if value == sign]
        cols = [index for index, value in enumerate(source_signs) if value == sign]
        submatrix = matrix[np.ix_(rows, cols)] if rows and cols else np.zeros((len(rows), len(cols)))
        splits[label] = {
            "rows": rows,
            "columns": cols,
            "shape": list(submatrix.shape),
            "rank": matrix_rank(submatrix),
        }
    return {
        "rank_total": matrix_rank(matrix),
        "nonzero_entries": int(np.count_nonzero(matrix)),
        "cross_eigen_nonzero_entries": cross_eigen_nonzero,
        "rank_plus": splits["+"]["rank"],
        "rank_minus": splits["-"]["rank"],
        "splits": splits,
    }


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    scenarios = load_json(REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.json")
    sign_probe = load_json(REPORTS / "phenomenology_guided_q1_radius2_e1_sign_prototype.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    context = load_5259_action_context()
    ensure_pycicy_compat()
    manifold = make_pycicy(pycicy_config(conf))
    bbw = manifold._line_to_BBW(REPRESENTATIVE_LINE)
    e1, origin = manifold.Leray(bbw)
    source_k, source_j = SOURCE_ENTRY
    target_k, target_j = TARGET_ENTRY
    source_entries = [[int(x) for x in item] for item in e1[source_k][source_j]]
    target_entries = [[int(x) for x in item] for item in e1[target_k][target_j]]
    source_origins = [list(item) for item in origin[source_k][source_j]]
    target_origins = [list(item) for item in origin[target_k][target_j]]
    source_signs = entry_basis_signs(
        manifold=manifold,
        conf=conf,
        line_bundle=REPRESENTATIVE_LINE,
        bracket_entries=source_entries,
        origins=source_origins,
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    )
    target_signs = entry_basis_signs(
        manifold=manifold,
        conf=conf,
        line_bundle=REPRESENTATIVE_LINE,
        bracket_entries=target_entries,
        origins=target_origins,
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    )
    raw_matrix = manifold._rank_map(
        e1[source_k][source_j],
        e1[target_k][target_j],
        origin[source_k][source_j],
        origin[target_k][target_j],
        False,
        True,
    )
    equivariant_matrix = equivariant_rank_map(
        manifold=manifold,
        source_entries=source_entries,
        target_entries=target_entries,
        source_origins=source_origins,
        target_origins=target_origins,
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    )
    raw_split = rank_split(
        matrix=raw_matrix,
        source_signs=source_signs,
        target_signs=target_signs,
    )
    equivariant_split = rank_split(
        matrix=equivariant_matrix,
        source_signs=source_signs,
        target_signs=target_signs,
    )
    gates = {
        "imports_sign_probe": gate(
            sign_probe["all_gates_pass"]
            and sign_probe["representative_line"] == REPRESENTATIVE_LINE,
            str(REPORTS / "phenomenology_guided_q1_radius2_e1_sign_prototype.json"),
            "first-page probe starts from verified E1 basis signs",
        ),
        "representative_frontier_block_imported": gate(
            scenarios["records"][0]["block_summaries"][0]["line_bundle"]
            == REPRESENTATIVE_LINE,
            str(REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.json"),
            "probe targets the representative high-priority residual block",
        ),
        "raw_pycicy_map_is_not_equivariant_restricted": gate(
            raw_split["cross_eigen_nonzero_entries"] > 0,
            "pyCICY generic first-page map",
            "unrestricted generic coefficients mix reconstructed Z2 eigenspaces",
        ),
        "equivariant_filtered_map_preserves_eigenspaces": gate(
            equivariant_split["cross_eigen_nonzero_entries"] == 0
            and equivariant_split["rank_total"] == 4
            and equivariant_split["rank_plus"] == 2
            and equivariant_split["rank_minus"] == 2,
            "equation-character-filtered first-page map",
            "equivariant coefficient filtering gives a block-diagonal rank split",
        ),
    }
    return {
        "scope": "equivariant first-page map-rank probe for representative residual q=1 block",
        "status": "equivariant_first_page_rank_split_computed",
        "representative_line": REPRESENTATIVE_LINE,
        "source_entry": {"k": source_k, "j": source_j, "dimension": len(source_signs)},
        "target_entry": {"k": target_k, "j": target_j, "dimension": len(target_signs)},
        "source_sign_multiplicities": {
            "+": sum(1 for item in source_signs if item == 1),
            "-": sum(1 for item in source_signs if item == -1),
        },
        "target_sign_multiplicities": {
            "+": sum(1 for item in target_signs if item == 1),
            "-": sum(1 for item in target_signs if item == -1),
        },
        "raw_pycicy_map_split": raw_split,
        "equivariant_filtered_map_split": equivariant_split,
        "next_step": (
            "Propagate the same equation-character coefficient filtering through "
            "pyCICY E2 projections and higher-Leray maps to compute the actual "
            "rank split for the effective rank-five residual block."
        ),
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    eq = report["equivariant_filtered_map_split"]
    raw = report["raw_pycicy_map_split"]
    lines = [
        "# Radius-2 Equivariant First-Page Probe",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- representative line: `{report['representative_line']}`",
        f"- source entry: `{report['source_entry']}`",
        f"- target entry: `{report['target_entry']}`",
        f"- raw pyCICY cross-eigenspace nonzeros: `{raw['cross_eigen_nonzero_entries']}`",
        f"- equivariant filtered rank split: `rank_+={eq['rank_plus']}`, `rank_-={eq['rank_minus']}`, total `{eq['rank_total']}`",
        f"- equivariant filtered cross-eigenspace nonzeros: `{eq['cross_eigen_nonzero_entries']}`",
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
        default=str(REPORTS / "phenomenology_guided_q1_radius2_equivariant_first_page_probe.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_equivariant_first_page_probe.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"equivariant_split={report['equivariant_filtered_map_split']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
