"""CICY geometry helpers for favourable ambient divisor bases."""

from __future__ import annotations

from collections import defaultdict
from itertools import product
from math import factorial
from typing import Iterable


Polynomial = dict[tuple[int, ...], int]


def _mul(poly: Polynomial, term: Polynomial, max_degrees: tuple[int, ...]) -> Polynomial:
    out: Polynomial = defaultdict(int)
    for a_exp, a_coeff in poly.items():
        for b_exp, b_coeff in term.items():
            exp = tuple(x + y for x, y in zip(a_exp, b_exp))
            if all(exp_i <= max_i for exp_i, max_i in zip(exp, max_degrees)):
                out[exp] += a_coeff * b_coeff
    return dict(out)


def ambient_dimensions(conf: list[list[int]]) -> tuple[int, ...]:
    return tuple(sum(row) - 1 for row in conf)


def triple_intersections(conf: list[list[int]]) -> dict[tuple[int, int, int], int]:
    """Compute d_ijk = integral_X J_i J_j J_k for a favourable CICY."""

    rows = len(conf)
    cols = len(conf[0]) if conf else 0
    max_degrees = ambient_dimensions(conf)
    top = max_degrees
    result: dict[tuple[int, int, int], int] = {}

    for i, j, k in product(range(rows), repeat=3):
        poly: Polynomial = {tuple(0 for _ in range(rows)): 1}
        divisor_exp = [0] * rows
        divisor_exp[i] += 1
        divisor_exp[j] += 1
        divisor_exp[k] += 1
        poly = _mul(poly, {tuple(divisor_exp): 1}, max_degrees)
        for col in range(cols):
            linear: Polynomial = {}
            for row in range(rows):
                degree = conf[row][col]
                if degree:
                    exp = [0] * rows
                    exp[row] = 1
                    linear[tuple(exp)] = degree
            poly = _mul(poly, linear, max_degrees)
        result[(i, j, k)] = poly.get(top, 0)
    return result


def line_bundle_index(k: Iterable[int], d: dict[tuple[int, int, int], int], c2_tx: list[int]) -> int:
    """Hirzebruch-Riemann-Roch index for O_X(k)."""

    vec = list(k)
    cubic = 0
    for i, ki in enumerate(vec):
        for j, kj in enumerate(vec):
            for l, kl in enumerate(vec):
                cubic += d[(i, j, l)] * ki * kj * kl
    linear = sum(c2i * ki for c2i, ki in zip(c2_tx, vec))
    numerator = 2 * cubic + linear
    if numerator % 12 != 0:
        raise ValueError(f"non-integral index numerator {numerator}")
    return numerator // 12


def bundle_c1(matrix: list[list[int]]) -> list[int]:
    return [sum(row) for row in matrix]


def bundle_c2(matrix: list[list[int]], d: dict[tuple[int, int, int], int]) -> list[int]:
    """Compute c2(V)_i = -1/2 d_ijk sum_a k_a^j k_a^k."""

    rows = len(matrix)
    cols = len(matrix[0]) if matrix else 0
    out: list[int] = []
    for i in range(rows):
        value = 0
        for a in range(cols):
            for j in range(rows):
                for k in range(rows):
                    value += d[(i, j, k)] * matrix[j][a] * matrix[k][a]
        if value % 2 != 0:
            raise ValueError(f"non-integral c2 component numerator {value}")
        out.append(-value // 2)
    return out


def bundle_index(matrix: list[list[int]], d: dict[tuple[int, int, int], int], c2_tx: list[int]) -> int:
    cols = len(matrix[0]) if matrix else 0
    return sum(line_bundle_index([row[a] for row in matrix], d, c2_tx) for a in range(cols))


def wedge2_index(matrix: list[list[int]], d: dict[tuple[int, int, int], int], c2_tx: list[int]) -> int:
    rows = len(matrix)
    cols = len(matrix[0]) if matrix else 0
    total = 0
    for a in range(cols):
        for b in range(a + 1, cols):
            total += line_bundle_index([matrix[i][a] + matrix[i][b] for i in range(rows)], d, c2_tx)
    return total


def sorted_matrix_key(matrix: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    columns = list(zip(*matrix))
    return tuple(sorted(tuple(col) for col in columns))


def multinomial_symmetry_check(d: dict[tuple[int, int, int], int]) -> bool:
    return all(d[key] == d[tuple(reversed(key))] for key in d)
