"""Equivariance diagnostics for candidate line-bundle sums."""

from __future__ import annotations

from typing import Any

from .cicy import sorted_matrix_key
from .cicy_symmetry import cicy_7484_topological_equivariance_report
from .novelty import permute_rows


def invariant_under_row_action(matrix: list[list[int]], row_permutation: tuple[int, ...]) -> bool:
    """Check whether row action preserves a line-bundle sum up to column order."""

    return sorted_matrix_key(matrix) == sorted_matrix_key(permute_rows(matrix, row_permutation))


def cicy_7484_symmetry_diagnostics(matrix: list[list[int]]) -> dict[str, Any]:
    """Necessary ambient divisor-action checks for the CICY 7484 candidate.

    The raw `cicylist.m` entry for CICY 7484 contains order-four symmetry
    data with both a row-swapping ambient action and a separate order-four
    action that does not permute ambient rows. This diagnostic only checks the
    induced ambient-row action on divisor charges. It is not a full proof of a
    linearized/equivariant bundle lift.
    """

    identity = tuple(range(len(matrix)))
    row_swap = (1, 0, 2)
    return {
        "scope": "necessary ambient-row action diagnostic only",
        "symmetry_options_from_cicylist": [
            {
                "label": "order_4_identity_ambient_rows",
                "ambient_row_permutation": list(identity),
                "line_bundle_sum_invariant_up_to_columns": invariant_under_row_action(matrix, identity),
                "interpretation": "Compatible with the divisor-charge action; full equivariant lift not proven.",
            },
            {
                "label": "order_4_row_swap_ambient_rows",
                "ambient_row_permutation": list(row_swap),
                "line_bundle_sum_invariant_up_to_columns": invariant_under_row_action(matrix, row_swap),
                "interpretation": "Fails if this row-swap action is the required Wilson-line symmetry.",
            },
        ],
        "full_wilson_line_equivariance_proven": False,
    }


def cicy_7484_raw_symmetry_diagnostics(
    cicylist_path: str, matrix: list[list[int]]
) -> dict[str, Any]:
    return cicy_7484_topological_equivariance_report(cicylist_path, matrix)
