"""Novelty and equivalence diagnostics for line-bundle matrices."""

from __future__ import annotations

from itertools import permutations
from typing import Any

from .cicy import sorted_matrix_key


Matrix = list[list[int]]


def _columns(conf: Matrix) -> list[tuple[int, ...]]:
    return list(zip(*conf))


def row_permutations_preserving_config(conf: Matrix) -> list[tuple[int, ...]]:
    """Return ambient-row permutations preserving `conf` up to column order."""

    rows = len(conf)
    original_columns = sorted(_columns(conf))
    out: list[tuple[int, ...]] = []
    for perm in permutations(range(rows)):
        permuted_conf = [conf[i] for i in perm]
        if sorted(_columns(permuted_conf)) == original_columns:
            out.append(tuple(perm))
    return out


def permute_rows(matrix: Matrix, perm: tuple[int, ...]) -> Matrix:
    return [matrix[i] for i in perm]


def canonical_matrix_key(
    matrix: Matrix,
    *,
    row_permutations: list[tuple[int, ...]] | None = None,
) -> tuple[tuple[int, ...], ...]:
    """Canonical key under line-bundle column permutations and selected row perms."""

    perms = row_permutations or [tuple(range(len(matrix)))]
    return min(sorted_matrix_key(permute_rows(matrix, perm)) for perm in perms)


def build_dataset_keys(
    entries: list[tuple[int, int, Matrix]],
    cicy_confs: dict[int, Matrix] | None,
) -> dict[str, Any]:
    exact_column_keys = set()
    row_permutation_keys = set()
    by_cicy_symmetry: dict[tuple[int, int], int] = {}
    row_perm_cache: dict[int, list[tuple[int, ...]]] = {}
    for cicy_num, symmetry_order, matrix in entries:
        exact_column_keys.add((cicy_num, symmetry_order, sorted_matrix_key(matrix)))
        if cicy_confs is not None and cicy_num in cicy_confs:
            if cicy_num not in row_perm_cache:
                row_perm_cache[cicy_num] = row_permutations_preserving_config(cicy_confs[cicy_num])
            row_perms = row_perm_cache[cicy_num]
        else:
            row_perms = [tuple(range(len(matrix)))]
        row_permutation_keys.add(
            (
                cicy_num,
                symmetry_order,
                canonical_matrix_key(matrix, row_permutations=row_perms),
            )
        )
        by_cicy_symmetry[(cicy_num, symmetry_order)] = by_cicy_symmetry.get((cicy_num, symmetry_order), 0) + 1
    return {
        "exact_column_keys": exact_column_keys,
        "row_permutation_keys": row_permutation_keys,
        "by_cicy_symmetry": by_cicy_symmetry,
    }


def novelty_record(
    *,
    cicy_num: int,
    symmetry_order: int,
    matrix: Matrix,
    conf: Matrix,
    dataset_keys: dict[str, Any],
) -> dict[str, Any]:
    row_perms = row_permutations_preserving_config(conf)
    exact_key = (cicy_num, symmetry_order, sorted_matrix_key(matrix))
    row_perm_key = (
        cicy_num,
        symmetry_order,
        canonical_matrix_key(matrix, row_permutations=row_perms),
    )
    return {
        "row_permutations_preserving_config": [list(perm) for perm in row_perms],
        "known_same_cicy_symmetry_count": dataset_keys["by_cicy_symmetry"].get((cicy_num, symmetry_order), 0),
        "novel_under_column_permutation": exact_key not in dataset_keys["exact_column_keys"],
        "novel_under_row_and_column_permutation": row_perm_key not in dataset_keys["row_permutation_keys"],
    }
