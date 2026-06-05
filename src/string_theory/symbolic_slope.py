"""Exact slope certificate for the CICY 7484 deformation candidate."""

from __future__ import annotations

from fractions import Fraction
import math
from math import sqrt
from typing import Any


def _format_quadratic_equation(a: int, b: int, c: int) -> str:
    sign_b = "+" if b >= 0 else "-"
    sign_c = "+" if c >= 0 else "-"
    return f"{a}*lambda^2 {sign_b} {abs(b)}*lambda {sign_c} {abs(c)} = 0"


def cicy_7484_kahler_ray_for_kappa_ratio(ratio: int) -> dict[str, Any]:
    """Interior ray with `kappa3 / kappa1 = ratio` and `t1=t2`.

    For CICY 7484, setting `t1=t2=1` gives

        kappa3 / kappa1 = (2 + 4 r + r^2) / (r (2 + r))

    with `r=t3`. This solves the slope-zero equations for any line-bundle
    column lying in the integer hyperplane `k1 + k2 + ratio*k3 = 0`.
    """

    if ratio <= 1:
        return {
            "kappa_ratio": ratio,
            "kahler_ray": None,
            "r_value": None,
            "interior_kahler_ray_exists": False,
        }
    discriminant = (2 * ratio - 4) ** 2 + 8 * (ratio - 1)
    r_value = (4 - 2 * ratio + sqrt(discriminant)) / (2 * (ratio - 1))
    return {
        "kappa_ratio": ratio,
        "kahler_ray": ["1", "1", "r"],
        "r_formula": "(4 - 2 m + sqrt((2 m - 4)^2 + 8 (m - 1))) / (2 (m - 1))",
        "r_value": r_value,
        "kappa_vector": [1, 1, ratio],
        "column_hyperplane": f"k1 + k2 + {ratio} k3 = 0",
        "interior_kahler_ray_exists": r_value > 0,
        "line_bundle_summands_stable": True,
        "all_columns_in_hyperplane_have_zero_slope": True,
        "direct_sum_polystable_for_columns_in_hyperplane": r_value > 0,
    }


def cicy_7484_kahler_ray_for_positive_kappa(kappa: list[int]) -> dict[str, Any] | None:
    """Exact CICY 7484 Kähler-ray test for a positive kappa vector.

    Writing `x=t1/t3` and `y=t2/t3`, the CICY 7484 Kähler map is proportional to

        (2y+1, 2x+1, 2xy+2x+2y+1).

    For a positive ray `(p,q,r)`, the scale `lambda` must solve

        lambda^2 p q + lambda (p + q - 2r) - 1 = 0.
    """

    if len(kappa) != 3 or any(value <= 0 for value in kappa):
        return None
    p, q, r = [Fraction(value, 1) for value in kappa]
    discriminant = (p + q - 2 * r) ** 2 + 4 * p * q
    lambda_value = (
        float(2 * r - p - q) + math.sqrt(float(discriminant))
    ) / float(2 * p * q)
    if lambda_value <= 0:
        return None
    x_value = (lambda_value * float(q) - 1.0) / 2.0
    y_value = (lambda_value * float(p) - 1.0) / 2.0
    if x_value <= 0 or y_value <= 0:
        return None
    return {
        "kappa_vector": [int(value) for value in kappa],
        "scale_equation": _format_quadratic_equation(
            int(p * q), int(p + q - 2 * r), -1
        ),
        "lambda_positive_root_float": lambda_value,
        "kahler_ray": [x_value, y_value, 1.0],
        "kahler_point_interior": True,
    }


def cicy_7484_positive_kappa_ray_exists(kappa: list[int]) -> bool:
    """Fast exact feasibility test for positive CICY 7484 kappa rays.

    In CICY 7484, a positive Kähler ray gives kappa proportional to

        (2y + 1, 2x + 1, 2xy + 2x + 2y + 1)

    with `x=t1/t3>0` and `y=t2/t3>0`. Therefore the third component strictly
    dominates the first two. Conversely, the quadratic scale equation used by
    `cicy_7484_kahler_ray_for_positive_kappa` gives positive `x,y` exactly in
    that chamber.
    """

    return (
        len(kappa) == 3
        and all(value > 0 for value in kappa)
        and kappa[2] > kappa[0]
        and kappa[2] > kappa[1]
    )


def cicy_7484_family_symbolic_slope(n: int) -> dict[str, Any]:
    """Exact slope-zero certificate for K(n) on CICY 7484.

    For the CICY 7484 intersection form and the candidate

        K(n) = [[1-n, -4+n, 1, 1, 1],
                [3-n,    n, -1,-1,-1],
                [ -1,    1, 0, 0, 0]],

    the slope equations reduce to `t1=t2` and

        kappa_3 / kappa_1 = 4 - 2n.

    Setting `t1=t2=1` and `r=t3/t1`, this becomes

        (2 + 4r + r^2) / (r(2+r)) = 4 - 2n.

    A positive solution is

        r(n) = (2n + sqrt(4n^2 - 12n + 10) - 2) / (3 - 2n),

    whenever this expression is positive. For integer n this holds for n <= 1.
    """

    discriminant = 4 * n * n - 12 * n + 10
    denominator = 3 - 2 * n
    if denominator == 0:
        positive_ratio = None
    else:
        positive_ratio = (2 * n + sqrt(discriminant) - 2) / denominator
    feasible = positive_ratio is not None and positive_ratio > 0
    ratio = 4 - 2 * n
    return {
        "n": n,
        "slope_equations": [
            "t1 = t2",
            "kappa3 = (4 - 2 n) kappa1",
        ],
        "kappa": [
            "4 t3 (2 t2 + t3)",
            "4 t3 (2 t1 + t3)",
            "4 (2 t1 t2 + 2 t1 t3 + 2 t2 t3 + t3^2)",
        ],
        "kahler_ray": ["1", "1", "r(n)"],
        "kappa_vector": [1, 1, ratio],
        "r_formula": "(2 n + sqrt(4 n^2 - 12 n + 10) - 2) / (3 - 2 n)",
        "r_value": positive_ratio,
        "integer_slope_feasible_condition": "n <= 1",
        "slope_feasible_exact": feasible,
        "kahler_point_interior": feasible,
    }


def cicy_7484_family_polystability_certificate(n: int) -> dict[str, Any]:
    """Exact poly-stability certificate for the line-bundle direct sum.

    Each summand of `K(n)` is a line bundle, hence stable. A direct sum of
    stable sheaves with the same slope is poly-stable. The symbolic slope
    certificate supplies an interior Kähler ray where all five slopes vanish.
    """

    slope = cicy_7484_family_symbolic_slope(n)
    polystable = slope["slope_feasible_exact"] and slope["kahler_point_interior"]
    return {
        "scope": "exact line-bundle direct-sum poly-stability certificate",
        "line_bundle_summands_stable": True,
        "all_summand_slopes_zero_on_exact_interior_ray": slope["slope_feasible_exact"],
        "kahler_point_interior": slope["kahler_point_interior"],
        "direct_sum_polystable": polystable,
        "justification": (
            "Line bundles are stable; a direct sum of stable line bundles with equal "
            "slope zero is poly-stable."
        ),
    }


def cicy_7484_family_anomaly(n: int) -> list[int]:
    return [16 + 8 * n, 8 + 8 * n, 12 - 16 * n + 8 * n * n]


def cicy_7484_family_symbolic_gate(n: int) -> dict[str, Any]:
    slope = cicy_7484_family_symbolic_slope(n)
    polystability = cicy_7484_family_polystability_certificate(n)
    anomaly = cicy_7484_family_anomaly(n)
    return {
        **slope,
        "polystability_certificate": polystability,
        "anomaly": anomaly,
        "anomaly_nonnegative_ambient": all(value >= 0 for value in anomaly),
        "symbolic_slope_and_anomaly_pass": slope["slope_feasible_exact"]
        and all(value >= 0 for value in anomaly),
        "exact_polystable_and_anomaly_pass": polystability["direct_sum_polystable"]
        and all(value >= 0 for value in anomaly),
    }
